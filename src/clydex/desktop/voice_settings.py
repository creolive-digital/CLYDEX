"""Functional voice/presentation controls, sharing Core's existing exact approvals."""
from dataclasses import asdict, replace

from clydex.core.contracts import canonical_json
from clydex.core.errors import PermissionDenied
from clydex.desktop.activations import DesktopActivations
from clydex.desktop.hotkeys import parse_hotkey
from clydex.voice.config import VoiceConfig


class VoiceControls:
    def _init_voice_controls(self):
        self._activations = DesktopActivations(dict(open=self._open_voice_window,
            activate=lambda: self._activate_voice('tray'), hotkey=lambda: self._activate_voice('hotkey'),
            mute=lambda: self.mute_microphone(True), unmute=lambda: self.mute_microphone(False),
            stop=self.stop, exit=self._exit_voice_window, voice_status=self._core.voice.snapshot))
        self._core.register_resource(self._activations)
        self._core.voice.privacy.background_indicator = lambda: self._activations.tray_available
        if self._core.voice.config.hotkey_enabled or self._core.voice.config.tray_enabled:
            self._intelligence_work(self._restore_activations)

    def _restore_activations(self):
        self._activations.configure(self._core.voice.config, self._engine.cancel_token)
        return {'voice_refresh': True}

    def _open_voice_window(self):
        import webview
        if webview.windows:
            self._core.voice.set_visible(True)
            webview.windows[0].show()

    def _exit_voice_window(self):
        import webview
        self._core.close()
        if webview.windows:
            webview.windows[0].destroy()

    def _activate_voice(self, source):
        if self._core.queue.busy:
            self._core.stop()
            return False
        self._open_voice_window()
        accepted = self._core.activate_voice(source)
        if not accepted:
            self._core.voice.events.emit('warning', code='unmute_or_enable_microphone_first')
        return accepted

    def voice_settings(self):
        with self._lock:
            if self._core.voice.privacy.refresh():
                return {'locked': True}
            if self._core.queue.busy:
                return {'busy': True}
            voices, devices = [], []
            warnings = []
            try:
                devices = self._core.voice.devices.list()
            except Exception:
                warnings.append('audio_devices_unavailable')
            try:
                voices = self._core.voice.sapi.voices()
            except Exception:
                warnings.append('installed_sapi_voices_unavailable')
            config = self._core.voice.config
            try:
                self._core.voice.recognizer.cached_path(config.model)
                model_status = 'cached_local'
            except Exception:
                model_status = 'not_prepared_no_automatic_download'
            return dict(configuration=asdict(config), voice=self._core.voice.snapshot(), devices=devices,
                        sapi_voices=voices, model_status=model_status, warnings=warnings,
                        personality=self._core.personality.snapshot(), activations=dict(self._activations.status))

    def configure_voice(self, values):
        if not isinstance(values, dict) or any(k.endswith('_digest') for k in values):
            raise ValueError('Invalid voice settings.')
        # Detach arguments before asynchronous queueing.
        values = dict(values)
        replace(self._core.voice.config, **values)
        parse_hotkey(values.get('hotkey', self._core.voice.config.hotkey))
        with self._lock:
            def review():
                config, artifacts = self._core.voice.approved_configuration(values, self._engine.cancel_token)
                args = dict(configuration=canonical_json(config), artifacts=artifacts)
                def apply(a):
                    import json
                    approved = json.loads(a['configuration'])
                    self._core.voice.configure(approved, self._engine.cancel_token)
                    self._engine.speech_mode = self._core.voice.config.mode
                    self._device = self._core.voice.config.input_device
                    self._activations.configure(self._core.voice.config, self._engine.cancel_token)
                    return {'voice_refresh': True}
                return self._engine.execute_tool('voice.configure', 'local speech and microphone policy', args,
                    apply, 'Apply this exact local voice configuration? Microphone use needs per-session unmute. '
                    'Background wake capture also needs explicit arming and remains visibly indicated. '
                    'No model will be downloaded. Local neural/wake assets use the displayed license/provenance/hashes.')
            return self._intelligence_work(review)

    def download_speech_model(self, model):
        replace(VoiceConfig(), fast_model=model)
        with self._lock:
            args = dict(model=model, directory=str(self._core.paths.directory('models')))
            def apply(a):
                result = self._core.voice.recognizer.download(a['model'], self._engine.cancel_token)
                return dict(result, voice_refresh=True)
            return self._intelligence_work(lambda: self._engine.execute_tool('voice.download', 'public local Whisper model',
                args, apply, 'Download public Faster Whisper model files from Hugging Face into the displayed '
                'runtime model directory? Size depends on the selected model and may require several GiB. '
                'No prompt/audio/credential is uploaded, no paid API is used. Cancellation may wait for native download cleanup.'))

    def configure_personality(self, values, address=None):
        if not isinstance(values, dict):
            raise ValueError('Invalid presentation settings.')
        config = replace(self._core.personality.config, **values)
        if address is None:
            address = self._core.personality.address
        if not isinstance(address, str):
            raise ValueError('Invalid personal addressing.')
        if address:
            self._core.personality._validate_address(address)
        with self._lock:
            args = dict(configuration=canonical_json(asdict(config)), address=address)
            def apply(a):
                import json
                self._core.personality.configure(json.loads(a['configuration']), a['address'])
                return {'voice_refresh': True}
            return self._intelligence_work(lambda: self._engine.execute_tool('personality.configure', 'local presentation policy',
                args, apply, 'Apply presentation preferences? An optional personal address is encrypted locally '
                'and will need private-context review before cloud use. This never grants operating permissions.'))

    def mute_microphone(self, muted=True):
        if type(muted) is not bool:
            return False
        if muted:
            self._core.voice.mute()
            return True
        try:
            self._core.voice.unmute()
            return True
        except PermissionDenied:
            self._core.voice.events.emit('warning', code='enable_microphone_policy_before_unmuting')
            return False

    def arm_voice_wake(self):
        with self._lock:
            args = dict(configuration=canonical_json(asdict(self._core.voice.config)))
            def apply(a):
                if canonical_json(asdict(self._core.voice.config)) != a['configuration']:
                    raise PermissionDenied('Voice configuration changed after wake review.')
                self._core.voice.arm(self._engine.cancel_token)
                return {'voice_refresh': True}
            return self._intelligence_work(lambda: self._engine.execute_tool('voice.arm', 'local Hey CLYDEX detector', args,
                apply, 'Start local background wake listening until Stop/mute/lock? No raw ambient recording is saved '
                'or transmitted. A wake is not authentication and cannot approve operating actions.'))

    def set_voice_visible(self, visible):
        if type(visible) is not bool:
            return False
        self._core.voice.set_visible(visible)
        if not visible and not self._activations.tray_available:
            # Background capture needs a visible, reachable native mute/Stop control.
            self._core.voice.mute()
        return True
