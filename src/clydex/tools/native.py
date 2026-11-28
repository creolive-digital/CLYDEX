"""Reviewed bounded native operations using the existing owned child lifecycle."""
import json
import os
import re
import sys
import shutil

from clydex.core.contracts import canonical_json
from clydex.core.processes import run_process
from clydex.tools.developer import readonly_sql


def worker(kind, data, token, timeout=30):
    result = run_process(worker_command(),
                         input=canonical_json({'kind': kind, 'data': data}),
                         cancel=token, timeout=timeout, max_output_bytes=262144, memory_limit_bytes=536870912)
    value = json.loads(result.stdout)
    if not value.get('ok'):
        raise ValueError('Native helper unavailable or failed; no automatic retry.')
    return value['result']


def worker_command():
    return [sys.executable, '--internal-worker'] if getattr(sys, 'frozen', False) else [sys.executable, '-m', 'clydex.tools.worker']


def sql_request(a, token, mode, profiles, credentials):
    profile = profiles(a['profile'])
    if profile['kind'] != 'sql' or profile['mode'] != mode or not profile['least_privilege_attested']:
        raise ValueError('Select an explicitly least-privilege SQL profile for this action class.')
    query = a['query']
    if mode == 'read':
        readonly_sql(query)
    elif mode == 'write':
        if not re.match(r'^\s*(INSERT|UPDATE|DELETE|MERGE)\b', query, re.I) or re.search(r'\b(ALTER|DROP|CREATE|GRANT|REVOKE|EXEC|BACKUP|RESTORE)\b', query, re.I):
            raise ValueError('DDL, security, dynamic and destructive schema commands require schema review.')
    elif not re.match(r'^\s*(CREATE|ALTER|DROP|TRUNCATE)\b', query, re.I):
        raise ValueError('Schema tool accepts explicitly reviewed schema statements only.')
    secret = credentials.get('operating.' + a['profile'])
    if not secret:
        raise ValueError('SQL credential is unconfigured.')
    return worker('sql', dict(profile=profile, secret=secret, query=query, mode=mode), token)


def media(a, token):
    if os.name != 'nt':
        raise ValueError('Windows media controls unavailable.')
    import ctypes
    token.check()
    key = {'play_pause': 0xB3, 'volume_up': 0xAF, 'volume_down': 0xAE, 'mute': 0xAD}[a['operation']]
    ctypes.windll.user32.keybd_event(key, 0, 0, 0)
    ctypes.windll.user32.keybd_event(key, 0, 2, 0)
    token.check()
    return dict(operation=a['operation'], dispatched=True)


def gpu(a, token):
    executable = shutil.which('nvidia-smi')
    if not executable:
        return dict(status='unavailable', source='nvidia-smi', gpu=[], scope='system GPU counters; not CLYDEX process utilization')
    result = run_process([executable, '--query-gpu=name,utilization.gpu,memory.used,memory.total', '--format=csv,noheader,nounits'],
                         cancel=token, timeout=8, max_output_bytes=8192)
    rows = []
    if result.returncode == 0:
        for line in result.stdout.splitlines()[:8]:
            values = [v.strip() for v in line.split(',')]
            if len(values) == 4:
                rows.append(dict(name=values[0], utilization_percent=values[1], memory_used_mib=values[2], memory_total_mib=values[3]))
    return dict(status='observed' if rows else 'unavailable', source='nvidia-smi', gpu=rows,
                scope='system GPU counters; not CLYDEX process utilization')
