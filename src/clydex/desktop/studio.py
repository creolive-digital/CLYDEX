"""Launch the local Stitch interface backed by the Clydex voice engine."""
import os
import queue
import threading


from clydex.core.application import CoreApplication
from clydex.core.errors import PermissionDenied
from clydex.desktop.intelligence import IntelligenceControls
from clydex.desktop.voice_settings import VoiceControls


RECOGNITION_MODES = ('en', 'en-accurate', 'auto')


class Studio(VoiceControls, IntelligenceControls):
    def __init__(self, core=None):
        self._core = core or CoreApplication()
        self._engine = self._core.engine
        self._lock = threading.RLock()
        self._busy = False
        self._recording = False
        self._state = 'READY'
        self._stream = None
        self._device = self._core.voice.config.input_device
        self._shown_review = None
        self._init_voice_controls()

    def _start(self, state, work, *args):
        if self._busy or self._core.queue.busy or self._core.voice.privacy.refresh():
            return False
        self._busy = True
        self._state = state
        try:
            self._core.submit(work, *args)
        except (queue.Full, RuntimeError):
            self._busy = False
            self._state = 'READY'
            return False
        return True

    def send(self, message):
        with self._lock:
            if not isinstance(message, str) or len(message) > 16000:
                return False
            text = message.strip()
            return bool(text) and self._start('THINKING', self._engine.text_worker, text)

    def microphone(self, check=False):
        with self._lock:
            if self._recording:
                self._engine.stop_event.set()
                self._state = 'STOPPING'
                return True
            if self._busy:
                return False
            try:
                self._core.voice.privacy.capture_allowed(self._core.voice.config)
            except PermissionDenied:
                self._core.voice.events.emit('warning', code='unmute_or_enable_microphone_first')
                return False
            self._engine.stop_event.clear()
            self._recording = True
            started = self._start('OPENING MICROPHONE', self._engine.record_worker, self._device, bool(check))
            if not started:
                self._recording = False
            return started

    def test_voice(self):
        def play():
            try:
                self._engine.speak_with_audio_meter('Clydex voice output is ready.')
            except Exception as exc:
                self._engine.report_error(exc)
            finally:
                self._engine.events.put(('done', None))
        with self._lock:
            return self._start('PREPARING SPEECH', play)

    def inputs(self):
        import sounddevice as sd
        hosts = sd.query_hostapis()
        return [{'id':i,'name':f"{d['name']} ({hosts[d['hostapi']]['name']})"}
                for i,d in enumerate(sd.query_devices()) if d['max_input_channels'] and d['name'].strip()]

    def select_input(self, device):
        with self._lock:
            if not self._busy:
                self._device = None if device == '' else int(device)
                self._core.voice.devices.validate(self._device, 'input')
                if self._core.voice.snapshot()['background_armed']:
                    self._core.voice.mute()
                self._core.voice.settings.configure({'input_device': self._device})

    def speak_replies(self, enabled):
        if type(enabled) is not bool:
            return False
        with self._lock:
            self._core.store.set_setting('speak_replies', enabled)
            self._engine.speak_preference = enabled
        return True

    def recognition_mode(self, mode):
        with self._lock:
            if not self._busy and mode in RECOGNITION_MODES and mode != self._engine.speech_mode:
                self._core.store.set_setting('recognition_mode', mode)
                self._engine.speech_mode = mode
                self._core.voice.settings.configure({'mode': mode,
                    'recognition_language': 'auto' if mode == 'auto' else 'en'})
            return self._engine.speech_mode

    def sound_settings(self):
        os.startfile('ms-settings:sound')

    def decide(self, review_id, approve):
        return self._engine.decide(review_id, approve)

    def clear(self):
        with self._lock:
            if self._busy:
                return False
            self._engine.history.clear()
            self._engine.history_local_only = False
            self._engine.apps.clear()
            self._engine.inbox.messages.clear()
            return True

    def snapshot(self):
        with self._lock:
            messages = []
            intelligence_events = []
            voice_events = []
            while True:
                try:
                    kind, value = self._engine.events.get_nowait()
                except queue.Empty:
                    break
                if kind == 'status':
                    self._state = value
                elif kind == 'record_done':
                    self._recording = False
                    self._state = 'TRANSCRIBING'
                elif kind == 'audio_stream':
                    self._stream = value
                elif kind == 'done':
                    self._busy = self._recording = False
                    self._stream = None
                    self._state = 'READY'
                elif kind in ('user','bot','mic_info','error'):
                    messages.append([kind,value])
                elif kind in ('provider_state', 'provider_delta', 'history_state', 'memory_suggestion', 'intelligence_result'):
                    intelligence_events.append([kind, value])
                elif kind in ('voice_event', 'voice_telemetry'):
                    voice_events.append([kind, value])
            level, bands, wave = 0., [], []
            stream = self._stream
            if stream and self._state in ('RECORDING','CHECKING MIC','SPEAKING'):
                level, bands, wave = stream.read_display()
            review = self._engine.pending_review()
            voice = self._core.voice.snapshot()
            self._activations.update(voice)
            self._busy = self._core.queue.busy
            self._recording = voice['state'] == 'listening' and self._busy
            if voice['locked']:
                review, messages, intelligence_events, voice_events = None, [], [], []
            if review and review['id'] != self._shown_review:
                self._shown_review = review['id']
                import webview
                if webview.windows:
                    webview.windows[0].show()
            return dict(messages=messages, intelligence_events=intelligence_events, voice_events=voice_events, voice=voice,
                        state=self._state, busy=self._busy,
                        recording=self._recording, rate=stream.rate if stream else 0,
                        level=level, bands=list(bands), wave=wave, review=review)

    def stop(self):
        with self._lock:
            self._core.stop()
            if self._busy:
                self._state = 'STOPPING'
            return True

    def _close(self):
        self._core.close()


