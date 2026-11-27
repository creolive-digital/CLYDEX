"""Bounded non-secret JSON settings with atomic replacement outside source."""
import json
import os
from pathlib import Path
import tempfile


def read_settings(path: Path) -> dict:
    if not path.exists():
        return {}
    if path.stat().st_size > 65536:
        raise ValueError('Settings file exceeds its size limit.')
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError('Settings must be an object.')
    return value


def write_settings(path: Path, value: dict) -> None:
    encoded = json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2)
    if len(encoded.encode('utf-8')) > 65536:
        raise ValueError('Settings exceed their size limit.')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as file:
            temporary = Path(file.name)
            file.write(encoded)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()
