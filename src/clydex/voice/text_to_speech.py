"""Local synthesis only: installed Windows SAPI or explicitly approved Piper CLI."""
import locale
import re
import time
import unicodedata

from clydex.core.errors import ClydexError
from clydex.core.processes import run_process
from clydex.voice.artifacts import LocalArtifacts
from clydex.voice.contracts import PCMChunk
from clydex.voice.privacy import require_active


class SpeechUnavailable(ClydexError):
    code = 'speech_output_unavailable'


def synthesis_language(text: str, preference: str) -> str:
    if preference != 'auto':
        return preference.split('-')[0]
    # Script detection routes synthesis; it does not establish recognition accuracy.
    sinhala = bool(re.search('[\u0d80-\u0dff]', text))
    tamil = bool(re.search('[\u0b80-\u0bff]', text))
    if sinhala and tamil:
        return 'mixed'
    if sinhala:
        return 'si'
    if tamil:
        return 'ta'
    if any(c.isalpha() and 'LATIN' not in unicodedata.name(c, '') for c in text):
        return 'und'
    return 'en'


def phrases(text: str, limit: int = 180):
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) > 1300:
        raise ValueError('Spoken text exceeds its bound.')
    while text:
        end = min(len(text), limit)
        if end < len(text):
            cut = text.rfind(' ', 0, end)
            if cut > limit // 2:
                end = cut
        yield text[:end]
        text = text[end:].lstrip()


def token_metadata(token) -> dict:
    def attribute(name):
        try:
            return str(token.GetAttribute(name))
        except Exception:
            return ''
    languages = set()
    for code in attribute('Language').split(';'):
        try:
            language = locale.windows_locale.get(int(code, 16), '').split('_')[0]
            if language:
                languages.add(language)
        except ValueError:
            pass
    return dict(id=str(token.Id), name=str(token.GetDescription()), gender=attribute('Gender').casefold(),
                languages=sorted(languages))


class SapiSynthesizer:
    def __init__(self, dispatch=None, com=None):
        self.dispatch, self.com = dispatch, com

    def _bindings(self):
        if self.dispatch is not None and self.com is not None:
            return self.dispatch, self.com
        import pythoncom
        from win32com.client import Dispatch
        return self.dispatch or Dispatch, self.com or pythoncom

    def voices(self) -> list[dict]:
        dispatch, com = self._bindings()
        com.CoInitialize()
        try:
            voice = dispatch('SAPI.SpVoice')
            tokens = voice.GetVoices()
            return [token_metadata(tokens.Item(i)) for i in range(min(tokens.Count, 128))]
        finally:
            com.CoUninitialize()

    def synthesize(self, text, config, cancel, guard):
        require_active(cancel, guard)
        dispatch, com = self._bindings()
        com.CoInitialize()
        voice = None
        try:
            voice = dispatch('SAPI.SpVoice')
            tokens = voice.GetVoices()
            available = [(tokens.Item(i), token_metadata(tokens.Item(i))) for i in range(tokens.Count)]
            language = synthesis_language(text, config.tts_language)
            matches = [(token, data) for token, data in available
                       if language in data['languages'] and (not config.voice_id or data['id'] == config.voice_id)]
            if not matches:
                raise SpeechUnavailable('Selected local voice/language is unavailable; answer remains on screen.')
            matches.sort(key=lambda pair: pair[1]['gender'] != 'male')
            voice.Voice, _ = matches[0]
            voice.Rate, voice.Volume = config.speech_rate, config.volume
            for part in phrases(text):
                require_active(cancel, guard)
                memory = dispatch('SAPI.SpMemoryStream')
                audio_format = dispatch('SAPI.SpAudioFormat')
                audio_format.Type = 22  # Actual SAPI 22.05 kHz / 16-bit / mono PCM.
                memory.Format = audio_format
                voice.AudioOutputStream = memory
                voice.Speak(part, 17)  # Async + literal text; never execute SSML/XML.
                deadline = time.monotonic() + 60
                while not voice.WaitUntilDone(20):
                    require_active(cancel, guard)
                    if time.monotonic() >= deadline:
                        raise SpeechUnavailable('Local synthesis exceeded its deadline.')
                require_active(cancel, guard)
                data = bytes(memory.GetData())
                if len(data) > 4 * 1024 * 1024 or len(data) % 2:
                    raise SpeechUnavailable('Invalid or oversized local speech output.')
                if data:
                    yield PCMChunk(data, int(memory.Format.GetWaveFormatEx().SamplesPerSec))
                voice.AudioOutputStream = None
        finally:
            try:
                if voice is not None:
                    voice.Speak('', 3)  # Async purge on this same COM-owning worker.
                    voice.WaitUntilDone(-1)  # Retain ownership until native work is really done.
                    voice.AudioOutputStream = None
                    voice = None
            finally:
                com.CoUninitialize()


class PiperSynthesizer:
    def __init__(self, paths, runner=run_process):
        self.artifacts, self.runner = LocalArtifacts(paths), runner

    def synthesize(self, text, config, cancel, guard):
        require_active(cancel, guard)
        manifest, files = self.artifacts.manifest(config.piper_manifest, 'piper', config.piper_manifest_digest, cancel)
        if synthesis_language(text, config.tts_language) not in {code.split('-')[0] for code in manifest['languages']}:
            raise SpeechUnavailable('This licensed local neural model does not declare the requested language.')
        # Executable/model/config hashes were explicitly approved by the owner.
        # Fixed arguments and stdin prevent speech text from becoming shell options.
        for part in phrases(text):
            require_active(cancel, guard)
            result = self.runner([str(files['executable']), '--model', str(files['model']), '--config', str(files['config']),
                    '--output-raw', '--length-scale', str(2 ** (-config.speech_rate / 10)),
                    '--volume', str(config.volume / 100)], input=part + '\n', cwd=str(files['model'].parent),
                    timeout=60, cancel=cancel, max_output_bytes=8 * 1024 * 1024, binary_output=True)
            require_active(cancel, guard)
            if result.returncode or not isinstance(result.stdout, bytes) or len(result.stdout) % 2:
                raise SpeechUnavailable('Local neural synthesis failed or returned invalid PCM.')
            if result.stdout:
                yield PCMChunk(result.stdout, manifest['sample_rate'])
