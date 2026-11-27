"""One headless voice runtime; model/tool requests still use the existing Core queue."""
from contextlib import contextmanager
from dataclasses import asdict, replace
import hashlib
import threading
import time

from clydex.automation.tasks import CancellationToken
from clydex.core.errors import Cancelled, PermissionDenied
from clydex.voice.artifacts import LocalArtifacts
from clydex.voice.audio_input import SoundDeviceInput
from clydex.voice.audio_output import SoundDeviceOutput
from clydex.voice.config import VoiceSettings
from clydex.voice.conversation import VoiceConversation, VoiceLifecycle
from clydex.voice.devices import SoundDevices
from clydex.voice.events import VoiceEvents, VoiceState
from clydex.voice.privacy import VoicePrivacy, require_active
from clydex.voice.speech_to_text import WhisperRecognizer
from clydex.voice.text_to_speech import PiperSynthesizer, SapiSynthesizer, SpeechUnavailable
from clydex.voice.wake_word import OpenWakeWordDetector


class VoiceRuntime:
    def __init__(self, paths, sink, *, privacy=None, capture=None, recognizer=None, output=None, wake_factory=None):
        self.paths, self.sink = paths, sink
        self.settings = VoiceSettings(paths)
        self.events = VoiceEvents(sink)
        self.privacy = privacy or VoicePrivacy()
        self.lifecycle = VoiceLifecycle(self.events)
        self.capture = capture or SoundDeviceInput(self.events, sink)
        self.recognizer = recognizer or WhisperRecognizer(paths, self.events)
        self.output = output or SoundDeviceOutput(self.events, sink)
        self.devices, self.sapi = SoundDevices(), SapiSynthesizer()
        self.piper = PiperSynthesizer(paths)
        self.conversation = VoiceConversation(self.capture, self.recognizer, self.lifecycle, self.events)
        self.wake_factory = wake_factory or OpenWakeWordDetector
        self.on_activation, self.on_stop = None, None
        self._closed, self._armed, self._foreground = threading.Event(), threading.Event(), threading.Event()
        self._guard, self._duplex, self._capture_lock = threading.RLock(), threading.RLock(), threading.RLock()
        self._bg_cancel, self._wake_thread = CancellationToken(), None
        self._privacy_thread = None
        self._foreground_depth, self._cooldown = 0, 0.
        self._foreground_tokens = []
        self._wake_status = 'off'
        self.privacy.on_lock = self._locked

    def start(self) -> None:
        """Own a lock-screen watcher even when no frontend is polling events."""
        with self._guard:
            if self._closed.is_set():
                raise Cancelled('Voice runtime is closed.')
            if self._privacy_thread is None:
                self._privacy_thread = threading.Thread(target=self._watch_privacy,
                    name='clydex-voice-privacy', daemon=True)
                self._privacy_thread.start()

    def _watch_privacy(self) -> None:
        while not self._closed.wait(.1):
            self.privacy.refresh()

    @property
    def config(self):
        return self.settings.config

    def _locked(self):
        self.stop()
        self.events.emit('privacy_locked', VoiceState.SLEEPING)
        if self.on_stop:
            self.on_stop()

    def snapshot(self):
        locked = self.privacy.refresh()
        return dict(state=self.lifecycle.state.value, muted=self.privacy.muted, locked=locked,
                    visible=self.privacy.visible, background_armed=self._armed.is_set(),
                    wake_capture_active=self.capture.wake_active.is_set() if isinstance(self.capture, SoundDeviceInput) else False,
                    wake_status=self._wake_status, half_duplex=True,
                    microphone_enabled=self.config.microphone_enabled)

    def unmute(self):
        self.privacy.unmute(self.config)
        self.events.emit('microphone_unmuted')

    def mute(self):
        self.privacy.muted = True
        self.stop()
        self.events.emit('microphone_muted')
        if self.on_stop:
            self.on_stop()

    def set_visible(self, visible: bool):
        if type(visible) is not bool:
            raise ValueError('Invalid visibility state.')
        self.privacy.visible = visible
        if not visible and not self.config.background_listening:
            self.mute()

    def approved_configuration(self, values: dict, cancel) -> tuple[dict, dict]:
        if not isinstance(values, dict) or any(key.endswith('_digest') for key in values):
            raise ValueError('Artifact approval fingerprints are supplied by trusted code.')
        config = replace(self.config, **values)
        for key, direction in (('input_device', 'input'), ('output_device', 'output')):
            if key in values and values[key] is not None and values[key] != getattr(self.config, key):
                self.devices.validate(values[key], direction)
        artifacts, updates = LocalArtifacts(self.paths), {}
        for path, kind, enabled in ((config.piper_manifest, 'piper', config.tts_provider == 'piper'),
                                    (config.wake_manifest, 'openwakeword', config.wake_enabled)):
            if enabled:
                manifest, _ = artifacts.manifest(path, kind, cancel=cancel)
                prefix = 'piper' if kind == 'piper' else 'wake'
                digest = hashlib.sha256(artifacts.path(path).read_bytes()).hexdigest()
                updates[prefix + '_manifest_digest'] = digest
                updates[prefix] = {'manifest_sha256': digest, 'license': manifest['license'],
                                   'provenance': manifest['provenance'], 'files': manifest['files']}
        effective = replace(config, **{k: v for k, v in updates.items() if k.endswith('_digest')})
        return asdict(effective), {k: v for k, v in updates.items() if not k.endswith('_digest')}

    def configure(self, values: dict, cancel):
        config = replace(self.config, **values)
        # Recheck the exact manifest approved in the queued review before persisting.
        if config.wake_enabled:
            LocalArtifacts(self.paths).manifest(config.wake_manifest, 'openwakeword', config.wake_manifest_digest, cancel)
        if config.tts_provider == 'piper':
            LocalArtifacts(self.paths).manifest(config.piper_manifest, 'piper', config.piper_manifest_digest, cancel)
        self._disarm()
        self.settings.configure(asdict(config))
        if not config.microphone_enabled:
            self.privacy.muted = True
        self.events.emit('configuration_changed')
        self.lifecycle.transition(VoiceState.STANDBY)

    @contextmanager
    def foreground(self, cancel):
        # Background worker only detects a wake. It never owns an AI/tool loop.
        # Native stream ownership is handed back before a Core task can proceed.
        self.start()
        with self._duplex:
            with self._guard:
                self._foreground_depth += 1
                self._foreground_tokens.append(cancel)
                self._foreground.set()
                self._bg_cancel.set()
                if self._armed.is_set():
                    self._wake_status = 'paused_for_core'
            acquired = False
            try:
                while not acquired:
                    cancel.check()
                    acquired = self._capture_lock.acquire(timeout=.02)
                cancel.check()
                yield
            finally:
                if acquired:
                    self._capture_lock.release()
                with self._guard:
                    self._foreground_depth -= 1
                    self._foreground_tokens.remove(cancel)
                    if self._foreground_depth == 0:
                        self._cooldown = time.monotonic() + self.config.playback_cooldown_ms / 1000
                        self._foreground.clear()

    def run(self, engine, device=None, check_only=False, wake=False):
        config = replace(self.config, mode=engine.speech_mode,
                         input_device=device if device is not None else self.config.input_device)
        def guard():
            self.privacy.capture_allowed(config)
        with self.foreground(engine.cancel_token):
            engine.stop_event.clear()
            def dispatch(text):
                engine.cancel_token.check()
                guard()
                engine.ask(text)
                # Acoustic tail guard, not an echo canceller. Never capture playback.
                deadline = time.monotonic() + config.playback_cooldown_ms / 1000
                while time.monotonic() < deadline:
                    require_active(engine.cancel_token, guard)
                    time.sleep(.02)
            self.conversation.run(config, engine.cancel_token, engine.stop_event, guard, dispatch,
                                  check_only=check_only, wake=wake)

    def speak(self, text, cancel):
        if not text.strip():
            return
        config = self.config
        def guard():
            self.privacy.output_allowed(config)
        with self.foreground(cancel):
            require_active(cancel, guard)
            self.lifecycle.transition(VoiceState.SPEAKING)
            self.events.emit('synthesis_started', VoiceState.SPEAKING, provider=config.tts_provider)
            provider = self.sapi if config.tts_provider == 'sapi' else self.piper
            try:
                self.output.play(provider.synthesize(text, config, cancel, guard), config, cancel, guard)
            except SpeechUnavailable:
                self.events.emit('warning', code='synthesis_language_or_voice_unavailable', fallback=config.tts_fallback)
                if config.tts_fallback == 'en':
                    fallback = replace(config, tts_provider='sapi', voice_id='', tts_language='en')
                    self.output.play(self.sapi.synthesize('The answer is on screen. The selected local speech language '
                        'is unavailable.', fallback, cancel, guard), fallback, cancel, guard)
            finally:
                if cancel.is_set():
                    self.lifecycle.transition(VoiceState.INTERRUPTED)
                else:
                    self.lifecycle.transition(VoiceState.STANDBY)

    def _background_guard(self):
        if self._closed.is_set() or self._foreground.is_set() or not self._armed.is_set():
            raise Cancelled('Background listening is paused.')
        self.privacy.capture_allowed(self.config)

    def arm(self, cancel):
        if not self.config.wake_enabled or not self.config.background_listening:
            raise PermissionDenied('Enable wake and background listening policy before arming.')
        self.privacy.capture_allowed(self.config)
        # This verifies real local artifacts, never a renamed generic model.
        LocalArtifacts(self.paths).manifest(self.config.wake_manifest, 'openwakeword',
                                           self.config.wake_manifest_digest, cancel)
        with self._guard:
            if self._closed.is_set():
                raise Cancelled('Voice runtime is closed.')
            self._armed.set()
            self._wake_status = 'armed_owner_attested_model'
            if self._wake_thread is None or not self._wake_thread.is_alive():
                self._wake_thread = threading.Thread(target=self._wake_loop, name='clydex-local-wake', daemon=True)
                self._wake_thread.start()
        self.events.emit('background_armed', VoiceState.STANDBY)

    def _wake_loop(self):
        detector, signature = None, None
        while not self._closed.wait(.05):
            if not self._armed.is_set() or self._foreground.is_set() or time.monotonic() < self._cooldown:
                continue
            token = CancellationToken()
            with self._guard:
                self._bg_cancel = token
            try:
                actual_signature = (self.config.wake_manifest_digest, self.config.wake_threshold)
                if signature != actual_signature:
                    detector = self.wake_factory(self.paths, self.config, token)
                    signature = actual_signature
                with self._capture_lock:
                    self._background_guard()
                    self._wake_status = 'listening_owner_attested_model'
                    detected = self.capture.wake_frames(self.config, token, self._background_guard, detector.accept)
                self._wake_status = 'waiting_for_core'
                if detected and not token.is_set() and self.on_activation:
                    self.on_activation('wake')
                    self._cooldown = time.monotonic() + 2
            except Cancelled:
                continue
            except Exception:
                self._armed.clear()
                self._wake_status = 'unavailable_or_policy_blocked'
                self.events.emit('warning', code='wake_unavailable_or_policy_blocked')
            finally:
                if detector is not None:
                    try:
                        detector.reset()
                    except Exception:
                        self._armed.clear()
                        self._wake_status = 'unavailable_or_policy_blocked'

    def _disarm(self):
        self._armed.clear()
        self._bg_cancel.set()
        self._wake_status = 'off'

    def stop(self):
        with self._guard:
            self._disarm()
            for token in self._foreground_tokens:
                token.set()
        self.lifecycle.transition(VoiceState.INTERRUPTED)

    def close(self):
        self.stop()
        self._closed.set()

    def wait_closed(self):
        if self._privacy_thread and self._privacy_thread is not threading.current_thread():
            self._privacy_thread.join()
        if self._wake_thread and self._wake_thread is not threading.current_thread():
            self._wake_thread.join()
        self.recognizer.wait_closed()
