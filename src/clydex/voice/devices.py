"""Audio and installed-voice discovery does not open a microphone or play sound."""
from dataclasses import asdict, dataclass
from typing import Protocol


@dataclass(frozen=True)
class AudioDevice:
    id: int
    name: str
    host: str
    input_channels: int
    output_channels: int
    default_rate: float


class DeviceManager(Protocol):
    def list(self) -> list[dict]: ...


class SoundDevices:
    def list(self) -> list[dict]:
        import sounddevice as sd
        hosts = sd.query_hostapis()
        return [asdict(AudioDevice(i, str(d['name']), str(hosts[d['hostapi']]['name']),
                                  int(d['max_input_channels']), int(d['max_output_channels']),
                                  float(d['default_samplerate']))) for i, d in enumerate(sd.query_devices())
                if d['name'].strip()]

    def validate(self, device: int | None, direction: str) -> None:
        if direction not in ('input', 'output'):
            raise ValueError('Invalid audio direction.')
        if device is not None and not any(d['id'] == device and d[direction + '_channels'] > 0 for d in self.list()):
            raise ValueError('Selected audio device is unavailable or has the wrong direction.')
