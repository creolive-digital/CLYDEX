"""Rolling audio snapshot and calibrated log-frequency bands for Clydex Studio."""
import threading
import time

BANDS = 36
LOW_HZ = 80
HIGH_HZ = 8000
FLOOR_DB = -72


class SpectrumStream:
    """The audio worker publishes PCM. Only the display thread takes an FFT."""
    def __init__(self, rate):
        import numpy as np
        self.rate = rate
        self.np = np
        self.size = 2**round(np.log2(rate*.08))
        self.buffer = np.zeros(self.size, dtype=np.float32)
        self.cursor = 0
        self.updated = 0.0
        self.lock = threading.Lock()
        self.window = np.hanning(self.size)
        self.normalization = 2/(self.size*np.sum(self.window**2))
        self.upper_hz = min(HIGH_HZ, rate/2)
        edges = np.geomspace(LOW_HZ, self.upper_hz, BANDS+1)
        frequencies = np.fft.rfftfreq(self.size, 1/rate)
        self.bins = np.searchsorted(frequencies, edges)
        self.bins[-1] = np.searchsorted(frequencies, edges[-1], side='right')

    def push(self, mono):
        samples = mono.ravel()[-self.size:]
        with self.lock:
            first = min(len(samples), self.size-self.cursor)
            self.buffer[self.cursor:self.cursor+first] = samples[:first]
            rest = len(samples)-first
            if rest:
                self.buffer[:rest] = samples[first:]
            self.cursor = (self.cursor+len(samples)) % self.size
            self.updated = time.monotonic()

    def read(self):
        level, bands, _ = self.read_display()
        return level, bands

    def read_display(self):
        np = self.np
        with self.lock:
            if time.monotonic()-self.updated > .25:
                return 0., [0.]*BANDS, []
            x = np.concatenate((self.buffer[self.cursor:],self.buffer[:self.cursor]))
        rms = float(np.sqrt(np.mean(x*x)))
        power = abs(np.fft.rfft(x*self.window))**2*self.normalization
        # Prefix sums allow adjacent narrow bands to have zero bins without duplication.
        cumulative = np.concatenate(([0.],np.cumsum(power)))
        db = 10*np.log10(np.maximum(np.diff(cumulative[self.bins]),1e-14))
        return rms, np.clip((db-FLOOR_DB)/-FLOOR_DB,0,1).tolist(), x[-256:].tolist()
