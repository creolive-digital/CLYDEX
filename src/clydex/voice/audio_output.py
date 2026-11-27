"""Actual local PCM playback and metering; no simulated visemes or loopback capture."""
from clydex.voice.events import VoiceState
from clydex.voice.privacy import require_active
from clydex.voice.spectrum import SpectrumStream


class SoundDeviceOutput:
    def __init__(self, events, legacy_sink, stream_factory=None):
        self.events, self.sink, self.factory = events, legacy_sink, stream_factory

    def play(self, chunks, config, cancel, guard):
        import numpy as np
        import sounddevice as sd
        played, total, began, completed = 0, 0, False, False
        try:
            for chunk in chunks:
                require_active(cancel, guard)
                if (chunk.channels != 1 or chunk.sample_width != 2 or not 8000 <= chunk.sample_rate <= 48000
                        or len(chunk.data) % 2):
                    raise ValueError('Unsupported speech PCM format.')
                total += len(chunk.data)
                if total > 16 * 1024 * 1024:
                    raise ValueError('Speech output exceeded its memory bound.')
                samples = np.frombuffer(chunk.data, dtype='<i2').reshape(-1, 1)
                spectrum = SpectrumStream(chunk.sample_rate)
                with (self.factory or sd.OutputStream)(device=config.output_device, samplerate=chunk.sample_rate,
                        channels=1, dtype='int16', blocksize=1024) as stream:
                    self.sink(('audio_stream', spectrum))
                    self.sink(('status', 'SPEAKING'))
                    if not began:
                        began = True
                        self.events.emit('playback_started', VoiceState.SPEAKING, sample_rate=chunk.sample_rate)
                    for offset in range(0, len(samples), 1024):
                        require_active(cancel, guard)
                        pcm = samples[offset:offset + 1024]
                        stream.write(pcm)
                        played += len(pcm)
                        spectrum.push(pcm[:, 0].astype(np.float32) / 32768.)
                        self.events.audio(spectrum, 'output')
                    require_active(cancel, guard)
            completed = True
        finally:
            if hasattr(chunks, 'close'):
                chunks.close()
            self.sink(('audio_stream', None))
            self.events.emit('playback_stopped', frames_played=played, completed=completed and not cancel.is_set())
