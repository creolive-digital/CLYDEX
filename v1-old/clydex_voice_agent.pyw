"""Launch the local Stitch interface backed by the Clydex voice engine."""
from pathlib import Path
import os
import queue
import threading
import winreg

import webview

from clydex_engine import VoiceEngine


VOICE_SETTINGS = r'Software\CLYDEX\Voice'
RECOGNITION_MODES = ('en', 'en-accurate', 'auto')


class Studio:
    def __init__(self):
        self._engine = VoiceEngine()
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, VOICE_SETTINGS) as key:
                mode, _ = winreg.QueryValueEx(key, 'RecognitionMode')
                if mode in RECOGNITION_MODES:
                    self._engine.speech_mode = mode
        except OSError:
            pass
        self._lock = threading.RLock()
        self._busy = False
        self._recording = False
        self._state = 'READY'
        self._stream = None
        self._device = None
        self._shown_review = None

    def _start(self, state, work, *args):
        if self._busy:
            return False
        self._busy = True
        self._state = state
        threading.Thread(target=work, args=args, daemon=True).start()
        return True

    def send(self, message):
        with self._lock:
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
            self._engine.stop_event.clear()
            self._recording = True
            return self._start('OPENING MICROPHONE', self._engine.record_worker,
                               self._device, bool(check))

    def test_voice(self):
        def play():
            try:
                self._engine.speak_with_audio_meter('Clydex voice output is ready.')
            except Exception as exc:
                self._engine.events.put(('error', str(exc)))
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

    def speak_replies(self, enabled):
        self._engine.speak_preference = bool(enabled)

    def recognition_mode(self, mode):
        with self._lock:
            if not self._busy and mode in RECOGNITION_MODES and mode != self._engine.speech_mode:
                self._engine.speech_mode = mode
                try:
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, VOICE_SETTINGS) as key:
                        winreg.SetValueEx(key, 'RecognitionMode', 0, winreg.REG_SZ, mode)
                except OSError:
                    pass  # The selection still applies for this session.
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
            self._engine.apps.clear()
            self._engine.inbox.messages.clear()
            return True

    def snapshot(self):
        with self._lock:
            messages = []
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
            level, bands, wave = 0., [], []
            stream = self._stream
            if stream and self._state in ('RECORDING','CHECKING MIC','SPEAKING'):
                level, bands, wave = stream.read_display()
            review = self._engine.pending_review()
            if review and review['id'] != self._shown_review:
                self._shown_review = review['id']
                if webview.windows:
                    webview.windows[0].show()
            return dict(messages=messages, state=self._state, busy=self._busy,
                        recording=self._recording, rate=stream.rate if stream else 0,
                        level=level, bands=list(bands), wave=wave, review=review)

    def _close(self):
        self._engine.close()


if __name__ == '__main__':
    studio = Studio()
    _here = Path(__file__).resolve().parent
    page = _here / 'studio_ui' / 'index.html'
    window = webview.create_window('CLYDEX Voice Agent', str(page), js_api=studio,
                                   width=1220, height=780, min_size=(760,510),
                                   background_color='#0E1416')
    window.events.closed += studio._close
    webview.start(gui='edgechromium')
