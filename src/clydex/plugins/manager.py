"""Bounded manifest validation and explicitly trusted owned-process runtime."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import time
import uuid

from clydex.core.contracts import canonical_json
from clydex.core.processes import run_process
from clydex.plugins.sdk import EVENTS, validate_response
from clydex.security.schema import check_schema, detached

PLUGIN_ID = re.compile(r'^[a-z][a-z0-9_.-]{2,63}$')
SEMVER = re.compile(r'^\d{1,4}\.\d{1,4}\.\d{1,4}$')


def manifest(value):
    expected = {'sdk_version', 'id', 'version', 'name', 'description', 'compatibility', 'entry',
                'permissions', 'dependencies', 'tools', 'events'}
    if type(value) is not dict or set(value) != expected or value['sdk_version'] != 1:
        raise ValueError('Invalid plugin manifest fields/version.')
    if (not isinstance(value['id'], str) or not PLUGIN_ID.fullmatch(value['id'])
            or not isinstance(value['version'], str) or not SEMVER.fullmatch(value['version'])
            or value['compatibility'] != 'clydex-v2-sdk1'):
        raise ValueError('Unsupported plugin identity/version/compatibility.')
    for key, maximum in (('name', 100), ('description', 2000), ('entry', 120)):
        if type(value[key]) is not str or not value[key] or len(value[key]) > maximum:
            raise ValueError('Invalid plugin metadata.')
    entry = Path(value['entry'])
    if entry.is_absolute() or entry.drive or '..' in entry.parts or entry.suffix != '.py' or ':' in str(entry):
        raise ValueError('Unsafe plugin entry path.')
    if type(value['dependencies']) is not list or value['dependencies']:
        raise ValueError('Automatic dependency installation is not supported; use stdlib-only reviewed packages.')
    if (type(value['permissions']) is not list or value['permissions'] != ['plugins.execute']
            or type(value['events']) is not list or any(x not in EVENTS for x in value['events'])
            or type(value['tools']) is not list or not 1 <= len(value['tools']) <= 16):
        raise ValueError('Invalid plugin capability declarations.')
    seen = set()
    for tool in value['tools']:
        if type(tool) is not dict or set(tool) != {'name', 'description', 'inputSchema', 'outputSchema'}:
            raise ValueError('Invalid plugin tool contract.')
        if (type(tool['name']) is not str or not PLUGIN_ID.fullmatch(tool['name']) or tool['name'] in seen
                or type(tool['description']) is not str or len(tool['description']) > 1000):
            raise ValueError('Invalid or duplicate plugin tool.')
        seen.add(tool['name'])
        check_schema(tool['inputSchema'])
        check_schema(tool['outputSchema'])
        if tool['inputSchema']['type'] != 'object' or tool['outputSchema']['type'] != 'object':
            raise ValueError('Plugin tools require object contracts.')
    return detached(value)


def package_snapshot(root):
    root = Path(root).resolve(strict=True)
    files, total, inspected = {}, 0, 0
    deadline = time.monotonic() + 3
    def visit(folder, depth):
        nonlocal total, inspected
        if depth > 5:
            raise ValueError('Plugin package nesting exceeds its bound.')
        for path in folder.iterdir():
            inspected += 1
            if inspected > 256 or time.monotonic() > deadline:
                raise ValueError('Plugin package inspection exceeds its bound.')
            if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
                raise ValueError('Plugin package links are forbidden.')
            if path.is_dir():
                visit(path, depth + 1)
            elif path.is_file():
                total += path.stat().st_size
                if len(files) >= 64 or total > 2 * 1024 * 1024:
                    raise ValueError('Plugin package exceeds file/byte limits.')
                relative = path.relative_to(root).as_posix()
                if path.suffix.lower() not in ('.py', '.json', '.md', '.txt'):
                    raise ValueError('Only reviewed source/manifest/documentation files are supported.')
                files[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
            else:
                raise ValueError('Unsupported plugin file type.')
    visit(root, 0)
    if 'plugin.json' not in files:
        raise ValueError('Plugin manifest missing.')
    value = manifest(json.loads((root / 'plugin.json').read_text(encoding='utf-8')))
    if value['entry'] not in files:
        raise ValueError('Plugin entry missing.')
    digest = hashlib.sha256(canonical_json(files).encode('utf-8')).hexdigest()
    return dict(manifest=value, files=files, digest=digest)


class PluginManager:
    def __init__(self, root, repository, selections):
        self.root, self.repository, self.selections = Path(root), repository, selections
        self.root.mkdir(parents=True, exist_ok=True)
        self.health = {}

    def candidate(self, selection):
        item = self.selections.get(selection)
        if item['kind'] != 'plugin':
            raise ValueError('Select a local plugin folder.')
        return package_snapshot(self.selections.path(selection))

    def install(self, selection, expected_digest, key):
        if str(uuid.UUID(key)) != key:
            raise ValueError('Canonical local plugin identity required.')
        source = self.selections.path(selection)
        snapshot = self.candidate(selection)
        if snapshot['digest'] != expected_digest:
            raise ValueError('Plugin changed during review.')
        target = self.root / key
        if target.resolve().parent != self.root.resolve():
            raise ValueError('Plugin installation escaped its runtime directory.')
        if target.exists():
            raise ValueError('Plugin installation identity already exists.')
        target.mkdir()
        try:
            for name, digest in snapshot['files'].items():
                data = (source / name).read_bytes()
                if hashlib.sha256(data).hexdigest() != digest:
                    raise ValueError('Plugin file changed during installation.')
                output = target / name
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(data)
            return self.repository.save('plugin', key, dict(**snapshot, enabled=False, trusted_code=False), 0)
        except Exception:
            shutil.rmtree(target)
            raise

    def remove(self, key):
        if str(uuid.UUID(key)) != key:
            raise ValueError('Canonical local plugin identity required.')
        target = self.root / key
        if target.is_symlink() or getattr(target, 'is_junction', lambda: False)() or target.resolve().parent != self.root.resolve():
            raise ValueError('Unsafe plugin removal target.')
        if target.exists():
            shutil.rmtree(target)

    def invoke(self, a, token):
        from clydex.security.schema import validate
        record = self.repository.get('plugin', a['plugin'])['value']
        if not record['enabled'] or not record['trusted_code']:
            raise ValueError('Executable plugin is disabled or not explicitly trusted.')
        root = self.root / a['plugin']
        if package_snapshot(root)['digest'] != record['digest']:
            raise ValueError('Plugin source changed; disable and reinstall for review.')
        tool = next((t for t in record['manifest']['tools'] if t['name'] == a['tool']), None)
        if tool is None:
            raise ValueError('Plugin tool is not declared.')
        validate(a['arguments'], tool['inputSchema'])
        packet = dict(sdk_version=1, operation='tool', tool=a['tool'], arguments=a['arguments'], configuration={})
        try:
            from clydex.tools.native import worker_command
            entry = root / record['manifest']['entry']
            result = run_process(worker_command(),
                                 cwd=str(root), input=canonical_json(dict(kind='plugin', data=dict(entry=str(entry),
                                     sha256=record['files'][record['manifest']['entry']], request=packet))), timeout=30, cancel=token,
                                 max_output_bytes=65536, memory_limit_bytes=536870912, env={k: v for k, v in os.environ.items()
                                     if k.upper() in ('SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PATH')})
            if result.returncode:
                raise ValueError('Plugin failed; private diagnostic output is discarded.')
            value = validate_response(json.loads(result.stdout), tool['outputSchema'])
            self.health[a['plugin']] = 'complete'
            return dict(result=value, untrusted=True)
        except Exception:
            self.health[a['plugin']] = 'failed'
            raise
