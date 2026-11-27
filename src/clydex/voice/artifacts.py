"""Owner-attested local voice assets. No built-in wake/voice file is invented."""
import hashlib
import json
import re

from clydex.core.errors import PermissionDenied
from clydex.voice.config import language_code, model_relative


class LocalArtifacts:
    def __init__(self, paths):
        self.paths = paths

    def path(self, relative: str):
        model_relative(relative)
        if not relative or self.paths is None:
            raise PermissionDenied('No approved local model artifact is configured.')
        root = self.paths.directory('models').resolve()
        path = (root / relative).resolve()
        if root not in path.parents or not path.is_file():
            raise PermissionDenied('Model artifact must be an existing file under runtime models.')
        return path

    def manifest(self, relative: str, kind: str, expected_digest: str | None = None, cancel=None) -> tuple[dict, dict]:
        path = self.path(relative)
        if path.stat().st_size > 65536:
            raise ValueError('Artifact manifest exceeds supported size.')
        encoded = path.read_bytes()
        if len(encoded) > 65536:
            raise ValueError('Artifact manifest exceeds supported size.')
        if expected_digest is not None and hashlib.sha256(encoded).hexdigest() != expected_digest:
            raise PermissionDenied('Artifact manifest changed after approval.')
        manifest = json.loads(encoded)
        if not isinstance(manifest, dict):
            raise ValueError('Invalid artifact manifest.')
        expected = {'model', 'config', 'executable'} if kind == 'piper' else {'model', 'melspec', 'embedding'}
        if (manifest.get('kind') != kind or manifest.get('rights_confirmed') is not True
                or not isinstance(manifest.get('license'), str) or not manifest['license'].strip()
                or not isinstance(manifest.get('provenance'), str) or not manifest['provenance'].strip()
                or not isinstance(manifest.get('files'), dict) or set(manifest['files']) != expected):
            raise PermissionDenied('Local artifact license/provenance/file declaration is incomplete.')
        if kind == 'openwakeword' and (manifest.get('phrase') != 'Hey CLYDEX'
                                      or manifest.get('phrase_validated') is not True):
            raise PermissionDenied('Owner validation of the actual Hey CLYDEX model is required.')
        if kind == 'piper' and (manifest.get('original_voice') is not True or not manifest.get('voice_name')):
            raise PermissionDenied('Choose a licensed original voice, never an actor imitation.')
        languages = manifest.get('languages')
        if not isinstance(languages, list) or not languages or len(languages) > 20:
            raise ValueError('Declare actual model languages.')
        for language in languages:
            language_code(language)
        files = {}
        for key, entry in manifest['files'].items():
            if (not isinstance(entry, dict) or set(entry) != {'path', 'sha256'}
                    or not isinstance(entry['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', entry['sha256'])):
                raise ValueError('Each artifact needs its exact path and SHA256.')
            path = self.path(entry['path'])
            if path.stat().st_size > 2 * 1024**3:
                raise ValueError('Artifact exceeds supported 2 GiB per-file size.')
            digest = hashlib.sha256()
            with path.open('rb') as file:
                for part in iter(lambda: file.read(65536), b''):
                    if cancel:
                        cancel.check()
                    digest.update(part)
            if digest.hexdigest() != entry['sha256']:
                raise PermissionDenied('Artifact hash changed; review its provenance again.')
            files[key] = path
        if kind == 'piper':
            if files['executable'].suffix.casefold() != '.exe' or files['model'].suffix.casefold() != '.onnx':
                raise ValueError('Use a local Piper executable and ONNX model.')
            if files['config'].stat().st_size > 1024 * 1024:
                raise ValueError('Voice configuration is too large.')
            data = json.loads(files['config'].read_text(encoding='utf-8'))
            rate = data.get('audio', {}).get('sample_rate')
            if type(rate) is not int or not 8000 <= rate <= 48000:
                raise ValueError('Unsupported model audio format.')
            manifest = dict(manifest, sample_rate=rate)
        elif any(path.suffix.casefold() != '.onnx' for path in files.values()):
            raise ValueError('Wake artifacts must be local ONNX files.')
        return manifest, files
