"""Safe native metadata, SAPI-to-RAM and activation lifecycle verification.

No microphone stream, speaker playback, model download, AI request or key press.
Temporary hotkey/tray registration is removed before return. This is not live
voice quality, pronunciation, wake accuracy or end-to-end hardware acceptance.
"""
import json
from pathlib import Path
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from clydex.automation.tasks import CancellationToken
from clydex.desktop.hotkeys import GlobalHotkey
from clydex.desktop.tray import SystemTray
from clydex.voice.config import VoiceConfig
from clydex.voice.devices import SoundDevices
from clydex.voice.privacy import desktop_locked
from clydex.voice.text_to_speech import SapiSynthesizer


def verify() -> dict:
    assert not desktop_locked(), 'Run the native check on an unlocked interactive Windows desktop.'
    devices = SoundDevices().list()  # Enumeration opens no input/output stream.
    sapi = SapiSynthesizer()
    voices = sapi.voices()
    began, cpu = time.monotonic(), time.process_time()
    chunks = list(sapi.synthesize('Clydex synthetic verification. The microphone remains off.',
                                VoiceConfig(), CancellationToken(), lambda: None))
    duration = time.monotonic() - began
    cpu = time.process_time() - cpu
    assert chunks and all(c.data and c.channels == 1 and c.sample_width == 2 for c in chunks)
    result = dict(native='passed', voices=[dict(name=v['name'], gender=v['gender'], languages=v['languages'])
                                           for v in voices],
                  input_device_entries=sum(d['input_channels'] > 0 for d in devices),
                  output_device_entries=sum(d['output_channels'] > 0 for d in devices),
                  synthesis_wall_seconds=round(duration, 4), synthesis_process_cpu_seconds=round(cpu, 4),
                  pcm_bytes=sum(len(c.data) for c in chunks),
                  pcm_audio_seconds=round(sum(len(c.data) / (2 * c.sample_rate) for c in chunks), 3),
                  sample_rates=sorted({c.sample_rate for c in chunks}),
                  microphone='not opened', speakers='not opened', quality='unverified')
    del chunks
    hotkey = GlobalHotkey('CTRL+ALT+F24', lambda: None)
    actions = {key: lambda: None for key in ('open', 'activate', 'mute', 'unmute', 'stop', 'exit')}
    refreshed = threading.Event()
    def voice_status():
        refreshed.set()
        return dict(muted=True, background_armed=False, state='standby', wake_status='off')
    actions['voice_status'] = voice_status
    tray = SystemTray(actions)
    try:
        hotkey.start()
        tray.start()
        assert refreshed.wait(1), 'Native tray status did not refresh without a frontend.'
        tray.update('CLYDEX synthetic check — microphone muted')
        result.update(hotkey=hotkey.status, tray=tray.status)
    finally:
        hotkey.close()
        tray.close()
        hotkey.wait_closed()
        tray.wait_closed()
    assert hotkey.status == 'off' and tray.status == 'off', 'Native registration cleanup failed.'
    result['activation_cleanup'] = 'passed; no activation/input was generated'
    return result


if __name__ == '__main__':
    print(json.dumps(verify()))
