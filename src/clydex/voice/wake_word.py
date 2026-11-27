"""Optional local custom wake detector; no generic model or download fallback."""
import math
import numbers
import time

from clydex.core.errors import SpeechInputError
from clydex.voice.artifacts import LocalArtifacts


class OpenWakeWordDetector:
    def __init__(self, paths, config, cancel, factory=None, clock=time.monotonic):
        manifest, files = LocalArtifacts(paths).manifest(config.wake_manifest, 'openwakeword',
                                                        config.wake_manifest_digest, cancel)
        cancel.check()
        if factory is None:
            try:
                from openwakeword.model import Model
            except ImportError as exc:
                raise SpeechInputError('Optional openWakeWord runtime is not installed; wake listening stays off.') from exc
            factory = Model
        self.model = factory(wakeword_models=[str(files['model'])], inference_framework='onnx',
                             melspec_model_path=str(files['melspec']), embedding_model_path=str(files['embedding']),
                             ncpu=1, enable_speex_noise_suppression=False, vad_threshold=0,
                             custom_verifier_models={})
        self.key = manifest.get('output_key', files['model'].stem)
        if not isinstance(self.key, str) or not self.key or len(self.key) > 100:
            raise ValueError('Invalid model output label.')
        self.threshold, self.clock, self.hits, self.last = config.wake_threshold, clock, 0, -math.inf

    def accept(self, pcm16, cancel) -> bool:
        cancel.check()
        predictions = self.model.predict(pcm16)
        cancel.check()
        score = predictions.get(self.key) if isinstance(predictions, dict) else None
        if isinstance(score, bool) or not isinstance(score, numbers.Real):
            raise SpeechInputError('Custom wake model returned invalid confidence.')
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise SpeechInputError('Custom wake model returned invalid confidence.')
        self.hits = self.hits + 1 if score >= self.threshold else 0
        if self.hits >= 2 and self.clock() - self.last >= 2:
            self.last, self.hits = self.clock(), 0
            return True
        return False

    def reset(self):
        self.hits = 0
        self.model.reset()
