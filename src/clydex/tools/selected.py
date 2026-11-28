"""Native-selected, expiring local capabilities; never arbitrary bridge paths."""
import hashlib
import os
from pathlib import Path
import threading
import time
import uuid


def file_digest(path):
    if path.stat().st_size > 2 * 1024 * 1024:
        raise ValueError('Selected text/script file exceeds 2 MiB.')
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SelectedPaths:
    def __init__(self, clock=time.monotonic):
        self.clock, self._items, self._lock = clock, {}, threading.RLock()

    def add(self, path, kind):
        if kind not in ('file', 'folder', 'script', 'plugin'):
            raise ValueError('Unsupported selection kind.')
        original = Path(path).absolute()
        if original.is_symlink() or getattr(original, 'is_junction', lambda: False)():
            raise ValueError('Link selections are not allowed.')
        resolved = original.resolve(strict=True)
        if (kind in ('folder', 'plugin')) != resolved.is_dir():
            raise ValueError('Selected path type mismatch.')
        digest = file_digest(resolved) if resolved.is_file() else ''
        if kind == 'script' and resolved.suffix.lower() not in ('.ps1', '.py'):
            raise ValueError('Select a Python or PowerShell script.')
        key = str(uuid.uuid4())
        with self._lock:
            self._items = {k: v for k, v in self._items.items() if v['expires'] > self.clock()}
            if len(self._items) >= 32:
                raise ValueError('Selection limit reached.')
            self._items[key] = dict(path=resolved, kind=kind, sha256=digest, expires=self.clock() + 1800)
        return key

    def get(self, key):
        with self._lock:
            item = self._items.get(key)
            if not item or item['expires'] <= self.clock():
                raise ValueError('Native selection expired; select it again.')
            return dict(item)

    def path(self, key, relative='', *, allow_missing=False):
        item = self.get(key)
        root = item['path']
        if type(relative) is not str or len(relative) > 260 or '\x00' in relative:
            raise ValueError('Invalid selected relative path.')
        relative_path = Path(relative)
        if relative_path.is_absolute() or relative_path.drive or any(p in ('..', '.') for p in relative_path.parts) or ':' in relative:
            raise ValueError('Unsafe selected relative path.')
        if root.is_file() and relative:
            raise ValueError('A file selection cannot grant directory access.')
        candidate = root / relative if relative else root
        current = candidate
        while current != root.parent:
            if current.is_symlink() or getattr(current, 'is_junction', lambda: False)():
                raise ValueError('Links/reparse traversal are not allowed.')
            current = current.parent
        resolved = candidate.resolve(strict=not allow_missing)
        if resolved != root and root not in resolved.parents:
            raise ValueError('Selected path escaped its root.')
        return resolved

    def snapshot(self):
        with self._lock:
            return [dict(id=k, kind=v['kind'], name=v['path'].name, path=str(v['path']), sha256=v['sha256'],
                         expires_in=max(0, int(v['expires'] - self.clock()))) for k, v in self._items.items() if v['expires'] > self.clock()]

    def clear(self):
        with self._lock:
            self._items.clear()

    def inspect(self, a, token):
        token.check()
        path = self.path(a['selection'], a['relative'])
        if a['operation'] == 'list':
            if not path.is_dir():
                raise ValueError('Select a folder to list.')
            entries = []
            with os.scandir(path) as iterator:
                for entry in iterator:
                    token.check()
                    if len(entries) >= 200:
                        return dict(entries=entries, truncated=True)
                    entries.append(dict(name=entry.name, directory=entry.is_dir(follow_symlinks=False), link=entry.is_symlink()))
            return dict(entries=entries, truncated=False)
        if a['operation'] == 'metadata':
            return dict(name=path.name, directory=path.is_dir(), bytes=path.stat().st_size,
                        sha256=file_digest(path) if path.is_file() else None)
        digest = file_digest(path)
        content = path.read_bytes()
        if len(content) > 65536:
            raise ValueError('Selected text exceeds 64 KiB; choose a smaller file.')
        return dict(name=path.name, text=content.decode('utf-8-sig'), sha256=digest)

    def modify(self, a, token):
        token.check()
        path = self.path(a['selection'], a['relative'], allow_missing=True)
        operation = a['operation']
        if operation == 'mkdir':
            if a['text'] or a['expected_sha256'] or path.exists():
                raise ValueError('Directory creation requires an absent path.')
            path.mkdir()
        else:
            digest = file_digest(path) if path.is_file() else ''
            if digest != a['expected_sha256'] or (path.exists() and path.is_dir() and operation != 'delete'):
                raise ValueError('Selected file changed; refresh its checksum.')
            if operation == 'delete':
                if a['text']:
                    raise ValueError('Deletion accepts no content.')
                path.rmdir() if path.is_dir() else path.unlink()
            else:
                data = a['text'].encode('utf-8')
                if path.exists():
                    # Recheck immediately before replacement; this is not an OS sandbox.
                    if file_digest(path) != digest:
                        raise ValueError('Selected file changed.')
                    path.write_bytes(data)
                else:
                    with path.open('xb') as output:
                        output.write(data)
        token.check()
        return dict(operation=operation, name=path.name, completed=True)
