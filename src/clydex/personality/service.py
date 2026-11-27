"""Owned presentation configuration; optional addressing is encrypted locally."""
import base64
from dataclasses import asdict, dataclass, replace
import getpass

from clydex.core.errors import PermissionDenied
from clydex.core.settings import read_settings, write_settings
from clydex.personality import policy
from clydex.personality.profiles import LENGTHS, PROFILES, TONES
from clydex.security.content import validate_private_text
from clydex.security.encryption import LocalCipher
from clydex.voice.config import language_code


@dataclass(frozen=True)
class PersonalityConfig:
    mode: str = 'personal'
    tone: str = 'calm'
    response_length: str = 'balanced'
    response_language: str = 'auto'
    spoken_characters: int = 420
    speak_in_focus: bool = False

    def __post_init__(self):
        if self.mode not in PROFILES or self.tone not in TONES or self.response_length not in LENGTHS:
            raise ValueError('Invalid presentation profile.')
        language_code(self.response_language)
        if type(self.spoken_characters) is not int or not 80 <= self.spoken_characters <= 800:
            raise ValueError('Invalid spoken response limit.')
        if type(self.speak_in_focus) is not bool:
            raise ValueError('Invalid focus speech preference.')


class PersonalityService:
    def __init__(self, paths=None, cipher=None, owner=None):
        self.path = paths.directory('settings') / 'personality.json' if paths else None
        self.cipher, self.owner = cipher or LocalCipher(), owner or getpass.getuser()
        value = read_settings(self.path) if self.path else {}
        if set(value) - {'presentation', 'address_encrypted'}:
            raise ValueError('Invalid personality configuration.')
        self.config = PersonalityConfig(**value.get('presentation', {}))
        self._address_blob = value.get('address_encrypted', '')
        self.address = self.cipher.open(base64.b64decode(self._address_blob, validate=True), self.owner) if self._address_blob else ''
        if self.address:
            self._validate_address(self.address)

    @staticmethod
    def _validate_address(value):
        validate_private_text(value, 80)
        if any(c in value for c in '\n\r\0'):
            raise ValueError('Personal addressing must be one short line.')

    @property
    def privacy_mode(self) -> bool:
        return self.config.mode == 'privacy'

    def configure(self, values: dict, address: str | None = None) -> dict:
        config = replace(self.config, **values)
        if address is not None and not isinstance(address, str):
            raise ValueError('Invalid personal addressing.')
        blob, actual = self._address_blob, self.address
        if address is not None:
            if address:
                self._validate_address(address)
                blob = base64.b64encode(self.cipher.seal(address, self.owner)).decode('ascii')
            else:
                blob = ''
            actual = address
        if self.path:
            write_settings(self.path, dict(presentation=asdict(config), address_encrypted=blob))
        self.config, self.address, self._address_blob = config, actual, blob
        return self.snapshot()

    def snapshot(self):
        return dict(presentation=asdict(self.config), address=self.address, profiles=list(PROFILES))

    def context(self) -> dict:
        # Address is private data, so the existing outbound compartment review applies.
        return {'personal_address': self.address} if self.address else {}

    def instructions(self, task_type: str) -> str:
        if task_type not in ('planning', 'conversation', 'summary'):
            raise PermissionDenied('Unknown presentation task.')
        return policy.instructions(self.config, task_type)

    def spoken(self, answer: str) -> str:
        if self.config.mode in ('focus', 'gaming') and not self.config.speak_in_focus:
            return ''
        return policy.spoken_text(answer, self.config.spoken_characters)
