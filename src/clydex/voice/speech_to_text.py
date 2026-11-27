"""Faster Whisper adapter. Local cache closure is checked before model creation."""
from concurrent.futures import Future
from dataclasses import replace
import math
from pathlib import Path
import threading

from clydex.core.errors import SpeechInputError
from clydex.voice.config import VoiceConfig
from clydex.voice.contracts import AudioBuffer, Transcript
from clydex.voice.privacy import require_active


def decode(model, samples, language, cancel=None, config=None, guard=lambda: None) -> Transcript:
    config = config or VoiceConfig()
    def check():
        if cancel:
            require_active(cancel, guard)
    options = dict(language=language, temperature=0.0, condition_on_previous_text=False,
                   without_timestamps=len(samples) <= 12 * 16000, vad_filter=True,
                   vad_parameters={'min_silence_duration_ms': config.silence_ms, 'speech_pad_ms': 250})
    def attempt(beam):
        check()
        source, info = model.transcribe(samples, beam_size=beam, **options)
        segments = []
        try:
            for segment in source:
                check()
                if len(segments) >= 128:
                    raise SpeechInputError('Too many recognition segments; no command dispatched.')
                segments.append(segment)
        finally:
            if hasattr(source, 'close'):
                source.close()
        check()
        return segments, info
    segments, info = attempt(3)
    if not segments:
        options['vad_parameters'] = dict(options['vad_parameters'], threshold=.3, min_speech_duration_ms=100)
        segments, info = attempt(5)
    elif any(s.avg_logprob < -.85 for s in segments):
        retry, retry_info = attempt(5)
        if retry and min(s.avg_logprob for s in retry) > min(s.avg_logprob for s in segments):
            segments, info = retry, retry_info
    for segment in segments:
        if (not math.isfinite(segment.avg_logprob) or not math.isfinite(segment.no_speech_prob)
                or not 0 <= segment.no_speech_prob <= 1 or segment.avg_logprob < config.min_avg_logprob
                or segment.no_speech_prob > config.max_no_speech):
            raise SpeechInputError('I could not confidently hear that. Please repeat the command.')
    text = ' '.join(s.text.strip() for s in segments).strip()
    if not text or len(text) > 16000 or '\0' in text:
        raise SpeechInputError('I did not hear clear speech. Please try again.')
    probability = getattr(info, 'language_probability', None)
    if language is None and probability is None:
        raise SpeechInputError('Recognition language confidence is unavailable; select a language or repeat.')
    if probability is not None and (not math.isfinite(probability) or not 0 <= probability <= 1
            or (language is None and probability < config.min_language_probability)):
        raise SpeechInputError('Recognition language is uncertain; select a language or repeat.')
    return Transcript(text, getattr(info, 'language', language), min(s.avg_logprob for s in segments), probability)


class WhisperRecognizer:
    def __init__(self, paths, events, model_factory=None, downloader=None):
        self.paths, self.events = paths, events
        self.factory, self.downloader = model_factory, downloader
        self._lock = threading.RLock()
        self._future, self._name = None, None

    def cached_path(self, name: str) -> Path:
        if self.paths is None:
            raise SpeechInputError('Configure the runtime model directory first.')
        downloader = self.downloader
        if downloader is None:
            from faster_whisper.utils import download_model
            downloader = download_model
        path = Path(downloader(name, cache_dir=str(self.paths.directory('models')),
                                                       local_files_only=True, use_auth_token=False))
        root = self.paths.directory('models').resolve()
        if root not in path.resolve().parents:
            raise SpeechInputError('Recognition model must be cached under the CLYDEX models directory.')
        for required in ('model.bin', 'config.json', 'tokenizer.json', 'preprocessor_config.json'):
            if not (path / required).is_file():
                raise SpeechInputError('Local recognition model is incomplete; review model preparation.')
        if not any(path.glob('vocabulary.*')):
            raise SpeechInputError('Local recognition model lacks its vocabulary.')
        return path

    def prepare(self, name: str) -> Future:
        replace(VoiceConfig(), fast_model=name)  # Trusted supported model names only.
        with self._lock:
            if self._future is not None:
                if not self._future.done():
                    if name == self._name:
                        return self._future
                    raise SpeechInputError('Another recognition model is still loading.')
                if name == self._name and self._future.exception() is None:
                    return self._future
            future = Future()
            self._future, self._name = future, name
            def load():
                try:
                    path = self.cached_path(name)
                    factory = self.factory
                    if factory is None:
                        from faster_whisper import WhisperModel
                        factory = WhisperModel
                    model = factory(str(path), device='cpu', compute_type='int8',
                        local_files_only=True, download_root=str(self.paths.directory('models')),
                        use_auth_token=False, cpu_threads=2, num_workers=1)
                    future.set_result(model)
                except Exception:
                    future.set_exception(SpeechInputError('Local model unavailable. Use Review model download/preparation; '
                                                          'no automatic download was attempted.'))
            threading.Thread(target=load, name='clydex-speech-model', daemon=True).start()
            return future

    def download(self, name: str, cancel) -> dict:
        replace(VoiceConfig(), fast_model=name)
        if self.paths is None:
            raise ValueError('Runtime models directory required.')
        cancel.check()
        downloader = self.downloader
        if downloader is None:
            from faster_whisper.utils import download_model
            downloader = download_model
        # Called only inside the trusted exact voice.download action. No key/token,
        # arbitrary repository, remote Python code or background auto-download.
        downloader(name, cache_dir=str(self.paths.directory('models')),
                                          local_files_only=False, use_auth_token=False)
        cancel.check()
        path = self.cached_path(name)
        return {'model': name, 'status': 'cached', 'bytes': sum(p.stat().st_size for p in path.iterdir() if p.is_file())}

    def recognize(self, audio: AudioBuffer, config, cancel, guard=lambda: None) -> Transcript:
        import numpy as np
        require_active(cancel, guard)
        data = np.asarray(audio.samples, dtype=np.float32)
        if data.ndim != 1 or not data.size or data.nbytes > 16 * 1024 * 1024 or not np.isfinite(data).all():
            raise SpeechInputError('Invalid bounded recognition audio.')
        if audio.sample_rate != 16000:
            import av
            frame = av.AudioFrame.from_ndarray(data.reshape(1, -1), format='flt', layout='mono')
            frame.sample_rate = audio.sample_rate
            resampler = av.AudioResampler(format='flt', layout='mono', rate=16000)
            frames = resampler.resample(frame) + resampler.resample(None)
            if not frames:
                raise SpeechInputError('Audio too short for recognition.')
            data = np.concatenate([f.to_ndarray().reshape(-1) for f in frames])
        future = self.prepare(config.model)
        self.events.emit('recognition_progress', stage='loading_local_model')
        while not future.done():
            require_active(cancel, guard)
            try:
                future.result(.05)
            except TimeoutError:
                pass
        require_active(cancel, guard)
        self.events.emit('recognition_progress', stage='decoding')
        result = decode(future.result(), data, config.language, cancel, config, guard)
        require_active(cancel, guard)
        return result

    def wait_closed(self):
        if self._future:
            try:
                self._future.result()
            except Exception:
                pass
