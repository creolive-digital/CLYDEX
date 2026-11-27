"""Synthetic audio only: no hardware capture, playback, model download or AI call."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import threading
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import numpy as np

from clydex.automation.tasks import CancellationToken
from clydex.core.config import RuntimePaths
from clydex.core.errors import Cancelled, PermissionDenied, SpeechInputError
from clydex.voice.artifacts import LocalArtifacts
from clydex.voice.audio_input import SoundDeviceInput
from clydex.voice.audio_output import SoundDeviceOutput
from clydex.voice.config import VoiceConfig, VoiceSettings
from clydex.voice.contracts import AudioBuffer, PCMChunk, Transcript
from clydex.voice.conversation import VoiceConversation, VoiceLifecycle
from clydex.voice.events import VoiceEvents, VoiceState
from clydex.voice.privacy import VoicePrivacy
from clydex.voice.speech_to_text import WhisperRecognizer, decode
from clydex.voice.text_to_speech import PiperSynthesizer, SapiSynthesizer, SpeechUnavailable, synthesis_language
from clydex.voice.vad import SilenceDetector
from clydex.voice.wake_word import OpenWakeWordDetector


def manifest_fixture(paths, kind):
    """Bytes are dummy test assets, not trained models or licensed production voices."""
    root = paths.directory('models')
    slots = ('model', 'config', 'executable') if kind == 'piper' else ('model', 'melspec', 'embedding')
    files = {}
    for slot in slots:
        name = kind + '_' + slot + ('.exe' if slot == 'executable' else '.json' if slot == 'config' else '.onnx')
        raw = b'{"audio":{"sample_rate":22050}}' if slot == 'config' else b'synthetic fixture bytes'
        (root / name).write_bytes(raw)
        files[slot] = {'path': name, 'sha256': hashlib.sha256(raw).hexdigest()}
    data = dict(kind=kind, rights_confirmed=True, license='synthetic test fixture only', provenance='test fixture',
                languages=['en'], files=files, voice_name='Synthetic', original_voice=True,
                phrase='Hey CLYDEX', phrase_validated=True)
    relative = kind + '.manifest.json'
    raw = json.dumps(data).encode()
    (root / relative).write_bytes(raw)
    return relative, hashlib.sha256(raw).hexdigest(), data


class VoiceUnitTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.paths = RuntimePaths(Path(self.folder.name))
        self.paths.ensure()
        self.items = []
        self.events = VoiceEvents(self.items.append)
        self.token = CancellationToken()

    def test_default_config_is_muted_and_no_background_technology_is_enabled(self):
        config = VoiceSettings(self.paths).config
        self.assertFalse(config.microphone_enabled)
        self.assertFalse(config.wake_enabled or config.continuous or config.background_listening)
        self.assertFalse(config.hotkey_enabled or config.tray_enabled)
        self.assertEqual(config.tts_provider, 'sapi')
        self.assertEqual(config.voice_id, '')
        self.assertTrue(VoicePrivacy(probe=lambda: False).muted)

    def test_config_validation_and_multilingual_model_selection(self):
        for field, value in (('max_recording_seconds', 0), ('max_recording_seconds', 61), ('volume', True),
                             ('noise_floor', float('nan')), ('wake_threshold', float('inf')),
                             ('piper_manifest', '../outside'), ('wake_manifest', 'C:/private'),
                             ('fast_model', 'arbitrary/vendor'), ('recognition_language', 'singlish'),
                             ('tts_provider', 'cloud'), ('hotkey', 'no modifiers')):
            with self.subTest(field=field), self.assertRaises(ValueError):
                replace(VoiceConfig(), **{field: value})
        self.assertEqual(VoiceConfig(mode='en-accurate', recognition_language='si').model, 'small')
        self.assertEqual(VoiceConfig(mode='auto').model, 'base')
        settings = VoiceSettings(self.paths)
        settings.configure({'volume': 42, 'recognition_language': 'ta'})
        self.assertEqual(VoiceSettings(self.paths).config.volume, 42)

    def test_vad_requires_sustained_speech_and_ends_after_silence(self):
        config = replace(VoiceConfig(), min_speech_ms=80, silence_ms=200)
        detector = SilenceDetector(config)
        for _ in range(3):
            detector.accept(.1)
        self.assertFalse(detector.started)
        detector.accept(0.)
        for _ in range(4):
            detector.accept(.1)
        self.assertTrue(detector.started)
        for _ in range(9):
            detector.accept(0.)
        self.assertFalse(detector.finished)
        self.assertTrue(detector.accept(0.))

    def test_vad_silence_noise_and_duration_bounds(self):
        config = replace(VoiceConfig(), initial_silence_seconds=1, max_recording_seconds=1)
        detector = SilenceDetector(config)
        for _ in range(50):
            detector.accept(.0001)
        self.assertTrue(detector.finished)
        self.assertFalse(detector.started)
        with self.assertRaises(ValueError):
            detector.accept(float('nan'))

    def test_capture_uses_transient_copy_and_closes_before_return(self):
        frame = np.full((320, 1), .1, dtype=np.float32)
        closed = []
        class Stream:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
            def __enter__(self):
                for _ in range(20):
                    self.kwargs['callback'](frame, 320, None, None)
                return self
            def __exit__(self, *args):
                closed.append(True)
        ticks = iter(i * .04 for i in range(1000))
        capture = SoundDeviceInput(self.events, self.items.append, Stream, lambda: next(ticks))
        audio = capture.capture(replace(VoiceConfig(), max_recording_seconds=1, min_speech_ms=80),
                                self.token, threading.Event(), lambda: None)
        self.assertTrue(closed)
        self.assertFalse(capture.lock.locked())
        self.assertEqual(len(audio.samples), 20 * 320)
        frame[:] = 0
        self.assertGreater(float(np.max(audio.samples)), 0)
        self.assertEqual(list(self.paths.directory('tmp').iterdir()), [])
        self.assertEqual(self.items[-2][0], 'audio_stream')

    def test_capture_precancel_and_privacy_never_open_native_stream(self):
        factory = Mock()
        capture = SoundDeviceInput(self.events, self.items.append, factory)
        self.token.set()
        with self.assertRaises(Cancelled):
            capture.capture(VoiceConfig(), self.token, threading.Event(), lambda: None)
        factory.assert_not_called()
        with self.assertRaises(PermissionDenied):
            capture.capture(VoiceConfig(), CancellationToken(), threading.Event(),
                            lambda: (_ for _ in ()).throw(PermissionDenied()))
        factory.assert_not_called()

    def test_decode_uncertain_nonfinite_or_empty_cannot_dispatch(self):
        for avg, silence in ((-1.2, .8), (-.2, .99), (float('nan'), .1), (-.2, float('nan')), (-.2, 2.)):
            model = Mock()
            model.transcribe.return_value = ([SimpleNamespace(text='delete files', avg_logprob=avg,
                                                              no_speech_prob=silence)], None)
            with self.subTest(avg=avg, silence=silence), self.assertRaises(SpeechInputError):
                decode(model, [0] * 16000, 'en')
        model.transcribe.return_value = ([], None)
        with self.assertRaises(SpeechInputError):
            decode(model, [0] * 16000, 'en')

    def test_decode_cancellation_between_segments_and_language_confidence(self):
        model = Mock()
        def segments():
            yield SimpleNamespace(text='synthetic', avg_logprob=-.2, no_speech_prob=.01)
            self.token.set()
            yield SimpleNamespace(text='never execute', avg_logprob=-.2, no_speech_prob=.01)
        model.transcribe.return_value = (segments(), SimpleNamespace(language='en', language_probability=.99))
        with self.assertRaises(Cancelled):
            decode(model, [0] * 16000, 'en', self.token)
        model.transcribe.return_value = ([SimpleNamespace(text='synthetic', avg_logprob=-.2, no_speech_prob=.01)],
                                         SimpleNamespace(language='si', language_probability=.1))
        with self.assertRaises(SpeechInputError):
            decode(model, [0] * 16000, None)
        model.transcribe.return_value = ([SimpleNamespace(text='synthetic', avg_logprob=-.2, no_speech_prob=.01)], None)
        with self.assertRaises(SpeechInputError):
            decode(model, [0] * 16000, None)

    def test_whisper_never_implicitly_downloads_missing_tokenizer(self):
        cache = self.paths.directory('models') / 'fixture-cache'
        cache.mkdir()
        for name in ('model.bin', 'config.json', 'preprocessor_config.json', 'vocabulary.json'):
            (cache / name).write_text('{}')
        downloader, factory = Mock(return_value=str(cache)), Mock()
        recognizer = WhisperRecognizer(self.paths, self.events, factory, downloader)
        with self.assertRaises(SpeechInputError):
            recognizer.prepare('base').result(3)
        self.assertTrue(downloader.call_args.kwargs['local_files_only'])
        self.assertFalse(downloader.call_args.kwargs['use_auth_token'])
        factory.assert_not_called()
        (cache / 'tokenizer.json').write_text('{}')
        recognizer.prepare('base').result(3)
        self.assertTrue(factory.call_args.kwargs['local_files_only'])
        self.assertFalse(factory.call_args.kwargs['use_auth_token'])
        self.assertEqual(factory.call_args.kwargs['device'], 'cpu')

    def test_whisper_explicit_download_uses_only_approved_name_and_runtime_cache(self):
        cache = self.paths.directory('models') / 'fixture'
        cache.mkdir()
        for name in ('model.bin', 'config.json', 'tokenizer.json', 'preprocessor_config.json', 'vocabulary.json'):
            (cache / name).write_text('{}')
        downloader = Mock(return_value=str(cache))
        recognizer = WhisperRecognizer(self.paths, self.events, downloader=downloader)
        self.assertEqual(recognizer.download('base', self.token)['status'], 'cached')
        self.assertFalse(downloader.call_args_list[0].kwargs['local_files_only'])
        self.assertFalse(downloader.call_args_list[0].kwargs['use_auth_token'])
        self.assertTrue(downloader.call_args_list[1].kwargs['local_files_only'])
        with self.assertRaises(ValueError):
            recognizer.download('untrusted/repository', self.token)

    def test_owned_model_loading_cannot_be_silently_replaced(self):
        recognizer = WhisperRecognizer(self.paths, self.events)
        from concurrent.futures import Future
        recognizer._name, recognizer._future = 'base', Future()
        self.assertIs(recognizer.prepare('base'), recognizer._future)
        with self.assertRaises(SpeechInputError):
            recognizer.prepare('small')
        recognizer._future.set_result(Mock())
        recognizer.wait_closed()

    def test_privacy_mute_lock_and_background_are_fail_closed(self):
        lock = [False]
        on_lock = Mock()
        privacy = VoicePrivacy(probe=lambda: lock[0], on_lock=on_lock)
        config = replace(VoiceConfig(), microphone_enabled=True)
        with self.assertRaises(PermissionDenied):
            privacy.capture_allowed(config)
        privacy.unmute(config)
        privacy.capture_allowed(config)
        privacy.visible = False
        with self.assertRaises(PermissionDenied):
            privacy.capture_allowed(config)
        with self.assertRaises(PermissionDenied):
            privacy.capture_allowed(replace(config, background_listening=True))
        privacy.background_indicator = lambda: True
        privacy.capture_allowed(replace(config, background_listening=True))
        lock[0] = True
        with self.assertRaises(PermissionDenied):
            privacy.capture_allowed(config)
        self.assertTrue(privacy.muted)
        on_lock.assert_called_once()
        lock[0] = False
        privacy.refresh()
        self.assertTrue(privacy.muted)

    def test_privacy_probe_failure_blocks_both_capture_and_playback(self):
        privacy = VoicePrivacy(probe=Mock(side_effect=OSError))
        with self.assertRaises(PermissionDenied):
            privacy.unmute(replace(VoiceConfig(), microphone_enabled=True))
        with self.assertRaises(PermissionDenied):
            privacy.output_allowed(VoiceConfig())

    def test_output_uses_same_pcm_for_meter_and_checks_cancel_each_block(self):
        token, written, closed = self.token, [], []
        class Stream:
            def __init__(self, **kwargs):
                pass
            def __enter__(self):
                return self
            def write(self, block):
                written.append(block.copy())
                token.set()
            def __exit__(self, *args):
                closed.append(True)
        generator_closed = []
        def chunks():
            try:
                yield PCMChunk(np.full(4096, 3000, dtype='<i2').tobytes(), 22050)
            finally:
                generator_closed.append(True)
        output = SoundDeviceOutput(self.events, self.items.append, Stream)
        with self.assertRaises(Cancelled):
            output.play(chunks(), VoiceConfig(), token, lambda: None)
        self.assertEqual(len(written), 1)
        self.assertTrue(closed and generator_closed)
        self.assertFalse(self.items[-1][1]['details']['completed'])

    def test_output_rejects_unsupported_format_without_playing(self):
        factory = Mock()
        output = SoundDeviceOutput(self.events, self.items.append, factory)
        with self.assertRaises(ValueError):
            output.play(iter([PCMChunk(b'odd', 22050)]), VoiceConfig(), self.token, lambda: None)
        factory.assert_not_called()

    def test_sapi_literal_async_pcm_and_cooperative_purge(self):
        token = Mock()
        token.Id, token.GetDescription.return_value = 'fixture-voice', 'Synthetic voice'
        token.GetAttribute.side_effect = lambda key: '409' if key == 'Language' else 'Male'
        voice, memory, fmt = Mock(), Mock(), Mock()
        voice.GetVoices.return_value = SimpleNamespace(Count=1, Item=lambda _: token)
        voice.WaitUntilDone.return_value = True
        memory.GetData.return_value = b'\0\0' * 100
        fmt.GetWaveFormatEx.return_value = SimpleNamespace(SamplesPerSec=22050)
        def dispatch(name):
            return {'SAPI.SpVoice': voice, 'SAPI.SpMemoryStream': memory, 'SAPI.SpAudioFormat': fmt}[name]
        com = Mock()
        provider = SapiSynthesizer(dispatch, com)
        audio = list(provider.synthesize('<speak>literal fixture</speak>', VoiceConfig(), self.token, lambda: None))
        self.assertEqual(audio[0].sample_rate, 22050)
        self.assertEqual(voice.Speak.call_args_list[0].args[1], 17)
        self.assertEqual(voice.Speak.call_args_list[-1].args, ('', 3))
        com.CoUninitialize.assert_called_once()
        def wait(ms):
            if ms != -1:
                self.token.set()
                return False
            return True
        voice.WaitUntilDone.side_effect = wait
        with self.assertRaises(Cancelled):
            list(provider.synthesize('synthetic', VoiceConfig(), self.token, lambda: None))

    def test_sapi_language_unavailability_is_explicit(self):
        token = Mock()
        token.Id, token.GetDescription.return_value = 'fixture', 'English fixture'
        token.GetAttribute.return_value = '409'
        voice = Mock()
        voice.GetVoices.return_value = SimpleNamespace(Count=1, Item=lambda _: token)
        sapi = SapiSynthesizer(Mock(return_value=voice), Mock())
        with self.assertRaises(SpeechUnavailable):
            list(sapi.synthesize('fixture', replace(VoiceConfig(), tts_language='ta'), self.token, lambda: None))
        self.assertEqual(synthesis_language('\u0d85\u0dba\u0dd4\u0db6\u0ddd\u0dc0\u0db1\u0dca', 'auto'), 'si')
        self.assertEqual(synthesis_language('\u0b85\u0bae\u0bcd\u0bae\u0bbe', 'auto'), 'ta')
        self.assertEqual(synthesis_language('\u4f60\u597d', 'auto'), 'und')

    def test_piper_fixed_args_binary_pcm_and_artifact_mutation_rejection(self):
        relative, digest, data = manifest_fixture(self.paths, 'piper')
        runner = Mock(return_value=SimpleNamespace(returncode=0, stdout=b'\0\0' * 20))
        provider = PiperSynthesizer(self.paths, runner)
        config = replace(VoiceConfig(), tts_provider='piper', piper_manifest=relative, piper_manifest_digest=digest)
        text = 'literal $(never execute) --no-options'
        self.assertEqual(len(list(provider.synthesize(text, config, self.token, lambda: None))), 1)
        args, kwargs = runner.call_args.args[0], runner.call_args.kwargs
        self.assertNotIn(text, args)
        self.assertEqual(kwargs['input'], text + '\n')
        self.assertTrue(kwargs['binary_output'])
        (self.paths.directory('models') / data['files']['executable']['path']).write_bytes(b'changed')
        with self.assertRaises(PermissionDenied):
            list(provider.synthesize(text, config, self.token, lambda: None))
        self.assertEqual(runner.call_count, 1)

    def test_binary_pcm_process_preserves_non_utf8_bytes(self):
        from clydex.core.processes import run_process
        result = run_process([sys.executable, '-c', 'import sys; sys.stdout.buffer.write(bytes([0,255,128,10]))'],
            input='synthetic', cwd=self.paths.directory('tmp'), timeout=5, cancel=self.token,
            max_output_bytes=32, binary_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, bytes([0, 255, 128, 10]))

    def test_custom_wake_only_uses_explicit_local_artifacts(self):
        relative, digest, _ = manifest_fixture(self.paths, 'openwakeword')
        model = Mock()
        model.predict.return_value = {'openwakeword_model': np.float32(.99)}
        factory = Mock(return_value=model)
        config = replace(VoiceConfig(), wake_enabled=True, wake_manifest=relative, wake_manifest_digest=digest)
        detector = OpenWakeWordDetector(self.paths, config, self.token, factory)
        self.assertFalse(detector.accept(np.zeros(1280, dtype=np.int16), self.token))
        self.assertTrue(detector.accept(np.zeros(1280, dtype=np.int16), self.token))
        self.assertEqual(len(factory.call_args.kwargs['wakeword_models']), 1)
        self.assertIn('melspec_model_path', factory.call_args.kwargs)
        self.assertEqual(factory.call_args.kwargs['inference_framework'], 'onnx')
        detector.reset()
        model.reset.assert_called_once()

    def test_generic_wake_model_without_actual_phrase_validation_is_rejected(self):
        relative, _, data = manifest_fixture(self.paths, 'openwakeword')
        data['phrase'], data['phrase_validated'] = 'generic assistant', False
        path = self.paths.directory('models') / relative
        path.write_text(json.dumps(data))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        factory = Mock()
        with self.assertRaises(PermissionDenied):
            OpenWakeWordDetector(self.paths, replace(VoiceConfig(), wake_manifest=relative,
                wake_manifest_digest=digest), self.token, factory)
        factory.assert_not_called()
        with self.assertRaises(ValueError):
            LocalArtifacts(self.paths).path('../outside.onnx')


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.items = []
        self.events = VoiceEvents(self.items.append)
        self.lifecycle = VoiceLifecycle(self.events)

    def test_invalid_state_transition_is_rejected(self):
        with self.assertRaises(RuntimeError):
            self.lifecycle.transition(VoiceState.TRANSCRIBING)
        for state in (VoiceState.WAKE_DETECTED, VoiceState.LISTENING, VoiceState.TRANSCRIBING, VoiceState.THINKING,
                      VoiceState.WAITING_FOR_APPROVAL, VoiceState.THINKING, VoiceState.SPEAKING,
                      VoiceState.INTERRUPTED, VoiceState.SLEEPING, VoiceState.STANDBY):
            self.lifecycle.transition(state)
        kinds = [event[1]['kind'] for event in self.items]
        self.assertIn('approval_waiting', kinds)
        self.assertIn('speech_interrupted', kinds)
        self.assertIn('wake_detected', kinds)

    def test_continuous_followup_silence_sleeps_without_another_request(self):
        capture, recognizer, dispatch = Mock(), Mock(), Mock()
        capture.capture.side_effect = [AudioBuffer([.1] * 1000, 16000), SpeechInputError('silence')]
        recognizer.recognize.return_value = Transcript('synthetic question', 'en', -.2)
        session = VoiceConversation(capture, recognizer, self.lifecycle, self.events)
        session.run(replace(VoiceConfig(), continuous=True), CancellationToken(), threading.Event(), lambda: None, dispatch)
        dispatch.assert_called_once_with('synthetic question')
        self.assertEqual(self.lifecycle.state, VoiceState.SLEEPING)
        self.assertEqual(capture.capture.call_count, 2)

    def test_canceled_transcription_never_reaches_dispatch(self):
        capture, recognizer, dispatch = Mock(), Mock(), Mock()
        capture.capture.return_value = AudioBuffer([.1] * 1000, 16000)
        recognizer.recognize.side_effect = Cancelled()
        session = VoiceConversation(capture, recognizer, self.lifecycle, self.events)
        with self.assertRaises(Cancelled):
            session.run(VoiceConfig(), CancellationToken(), threading.Event(), lambda: None, dispatch)
        dispatch.assert_not_called()
        self.assertEqual(self.lifecycle.state, VoiceState.INTERRUPTED)

    def test_sleep_words_are_local_and_never_authorize_tools(self):
        for text in ('go to sleep', 'stop', 'cancel'):
            capture, recognizer, dispatch = Mock(), Mock(), Mock()
            capture.capture.return_value = AudioBuffer([.1] * 1000, 16000)
            recognizer.recognize.return_value = Transcript(text, 'en', -.2)
            session = VoiceConversation(capture, recognizer, self.lifecycle, self.events)
            session.run(VoiceConfig(), CancellationToken(), threading.Event(), lambda: None, dispatch)
            dispatch.assert_not_called()
