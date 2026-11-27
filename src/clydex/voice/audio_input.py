"""Bounded transient capture. Native streams close before any transcription/action."""
from collections import deque
import queue
import threading

from clydex.core.errors import SpeechInputError
from clydex.voice.contracts import AudioBuffer
from clydex.voice.events import VoiceState
from clydex.voice.privacy import require_active
from clydex.voice.spectrum import SpectrumStream
from clydex.voice.vad import SilenceDetector


class SoundDeviceInput:
    def __init__(self, events, legacy_sink, stream_factory=None, clock=None):
        import time
        self.events, self.sink, self.factory = events, legacy_sink, stream_factory
        self.clock = clock or time.monotonic
        self.lock = threading.Lock()
        self.wake_active = threading.Event()

    def capture(self, config, cancel, finish, guard, *, check_only=False, listen_seconds=None):
        import numpy as np
        import sounddevice as sd
        require_active(cancel, guard)
        if not self.lock.acquire(blocking=False):
            raise SpeechInputError('An audio input stream already owns this microphone.')
        samples, pending = [], queue.Queue(maxsize=25)
        overflow = threading.Event()
        rate, spectrum = 16000, None
        try:
            info = sd.query_devices(config.input_device, 'input') if self.factory is None else {'default_samplerate': 16000}
            rate = int(info['default_samplerate'])
            if not 8000 <= rate <= 192000:
                raise SpeechInputError('Unsupported microphone sample rate.')
            block = max(1, rate // 50)
            spectrum = SpectrumStream(rate)
            detector = SilenceDetector(config)
            pre_roll = deque(maxlen=config.min_speech_ms // 20 + 10)
            count, peak, begun = 0, 0., self.clock()
            def callback(indata, frames, timing, status):
                if cancel.is_set():
                    return
                if status or frames != block or len(indata) != frames:
                    overflow.set()
                    return
                try:
                    pending.put_nowait(indata[:, 0].copy())
                except queue.Full:
                    overflow.set()
            factory = self.factory or sd.InputStream
            with factory(device=config.input_device, samplerate=rate, channels=1, dtype='float32',
                         blocksize=block, callback=callback):
                self.sink(('audio_stream', spectrum))
                self.sink(('status', 'CHECKING MIC' if check_only else 'RECORDING'))
                self.events.emit('listening_started', VoiceState.LISTENING, device=config.input_device, sample_rate=rate)
                while True:
                    require_active(cancel, guard)
                    if overflow.is_set():
                        raise SpeechInputError('Audio overflow; discard this recording and try again.')
                    if finish.is_set():
                        break
                    elapsed = self.clock() - begun
                    if elapsed >= (5 if check_only else config.max_recording_seconds):
                        break
                    if listen_seconds is not None and elapsed >= listen_seconds and not detector.started:
                        break
                    try:
                        frame = pending.get(timeout=.02)
                    except queue.Empty:
                        continue
                    if not np.isfinite(frame).all():
                        raise SpeechInputError('Invalid microphone samples.')
                    rms = float(np.sqrt(np.mean(frame * frame)))
                    peak = max(peak, float(np.max(np.abs(frame))))
                    spectrum.push(frame)
                    self.events.audio(spectrum, 'input')
                    if check_only:
                        continue
                    pre_roll.append(frame)
                    was_started = detector.started
                    detector.accept(rms)
                    if detector.started:
                        if not was_started:
                            samples.extend(pre_roll)
                            count = sum(len(part) for part in samples)
                            pre_roll.clear()
                        else:
                            samples.append(frame)
                            count += len(frame)
                        if count * 4 > 16 * 1024 * 1024:
                            raise SpeechInputError('Transient recording reached its memory limit.')
                    if detector.finished:
                        break
            require_active(cancel, guard)
            if check_only:
                self.sink(('mic_info', 'Signal detected.' if peak >= .00015 else 'No usable microphone signal.'))
                return AudioBuffer(np.empty(0, dtype=np.float32), rate)
            if not samples or not detector.started:
                raise SpeechInputError('No confident speech activity; no request was dispatched.')
            return AudioBuffer(np.concatenate(samples), rate)
        finally:
            # No WAV/file/cache. Dropping transient frames and releasing the stream
            # is required before any user text is dispatched to Core.
            samples.clear()
            while not pending.empty():
                pending.get_nowait()
            self.sink(('audio_stream', None))
            self.events.emit('listening_stopped')
            self.lock.release()

    def wake_frames(self, config, cancel, guard, accept) -> bool:
        """Wake detector gets bounded 80 ms / 16 kHz int16 frames, never a recording."""
        import numpy as np
        import sounddevice as sd
        require_active(cancel, guard)
        if not self.lock.acquire(blocking=False):
            return False
        pending, overflow = queue.Queue(maxsize=6), threading.Event()
        def callback(indata, frames, timing, status):
            if cancel.is_set():
                return
            if status or frames != 1280 or len(indata) != frames:
                overflow.set()
                return
            try:
                pending.put_nowait(indata[:, 0].copy())
            except queue.Full:
                overflow.set()
        try:
            with (self.factory or sd.InputStream)(device=config.input_device, samplerate=16000, channels=1,
                    dtype='int16', blocksize=1280, callback=callback):
                self.wake_active.set()
                self.events.emit('wake_listening_started', VoiceState.LISTENING, sample_rate=16000)
                while True:
                    require_active(cancel, guard)
                    if overflow.is_set():
                        raise SpeechInputError('Wake audio overflow; detection was stopped.')
                    try:
                        frame = pending.get(timeout=.02)
                    except queue.Empty:
                        continue
                    if frame.dtype != np.int16 or len(frame) != 1280:
                        raise SpeechInputError('Invalid wake input frame.')
                    if accept(frame, cancel):
                        return True
        finally:
            self.wake_active.clear()
            self.events.emit('wake_listening_stopped')
            self.lock.release()
