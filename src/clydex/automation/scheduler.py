"""Disabled-by-default triggers; one scheduler submits into the existing queue."""
from datetime import datetime, timedelta, timezone
from collections import deque
import hashlib
import queue
import re
import threading
import time
from zoneinfo import ZoneInfo

from clydex.automation.workflows.schema import exact, identifier, text

TRIGGERS = ('manual', 'voice', 'time', 'system', 'email', 'network', 'webhook')


def validate_trigger(value):
    exact(value, ('name', 'kind', 'workflow', 'enabled', 'source', 'cooldown', 'missed', 'schedule'))
    text(value['name'])
    identifier(value['workflow'])
    if (value['kind'] not in TRIGGERS or type(value['enabled']) is not bool
            or type(value['source']) is not str or len(value['source']) > 200
            or type(value['cooldown']) is not int or not 1 <= value['cooldown'] <= 86400
            or value['missed'] not in ('skip', 'once')):
        raise ValueError('Invalid trigger policy.')
    schedule = value['schedule']
    exact(schedule, ('timezone', 'time', 'interval_seconds'))
    if type(schedule['timezone']) is not str:
        raise ValueError('Select a named timezone.')
    ZoneInfo(schedule['timezone'])
    if (type(schedule['time']) is not str or not re.fullmatch(r'([01]\d|2[0-3]):[0-5]\d', schedule['time'])
            or type(schedule['interval_seconds']) is not int or not (schedule['interval_seconds'] == 0 or
                60 <= schedule['interval_seconds'] <= 86400)):
        raise ValueError('Invalid bounded time schedule.')
    if value['kind'] not in ('manual', 'voice', 'time') and not value['source']:
        raise ValueError('Event triggers require an explicitly configured source identity.')
    return value


def next_daily(schedule, now):
    zone = ZoneInfo(schedule['timezone'])
    current = datetime.fromtimestamp(now, timezone.utc).astimezone(zone)
    hour, minute = map(int, schedule['time'].split(':'))
    for day in range(3):
        date = current.date() + timedelta(days=day)
        candidate = datetime(date.year, date.month, date.day, hour, minute, tzinfo=zone, fold=0)
        stamp = candidate.timestamp()
        # Skip nonexistent spring-forward local times. Fall-back fires fold 0 once.
        returned = datetime.fromtimestamp(stamp, zone)
        if stamp > now and (returned.hour, returned.minute) == (hour, minute):
            return stamp
    raise ValueError('No valid schedule occurrence found.')


class TriggerScheduler:
    def __init__(self, repository, submit, run, allowed, *, clock=time.time, start=True):
        self.repository, self.submit, self.run, self.allowed = repository, submit, run, allowed
        self.clock, self.armed, self._next, self._last = clock, set(), {}, {}
        self._lock, self._closed = threading.RLock(), threading.Event()
        self._events = deque(maxlen=16)
        self._thread = None
        if start:
            self._thread = threading.Thread(target=self._loop, name='clydex-scheduler', daemon=True)
            self._thread.start()

    def arm(self, keys):
        if type(keys) is not list or len(keys) > 64 or len(keys) != len(set(keys)):
            raise ValueError('Invalid trigger arm selection.')
        records = {r['id']: r['value'] for r in self.repository.list('trigger')}
        now = self.clock()
        following = {}
        for key in keys:
            value = records.get(key)
            if not value or not validate_trigger(value)['enabled']:
                raise ValueError('Only reviewed enabled triggers can be armed.')
            if value['kind'] == 'time':
                interval = value['schedule']['interval_seconds']
                following[key] = now + interval if interval else next_daily(value['schedule'], now)
        with self._lock:
            self.armed, self._next, self._last = set(keys), following, {}
        return dict(armed=sorted(keys), startup='disarmed; each action still requires its own review')

    def disarm(self):
        with self._lock:
            self.armed.clear()
            self._next.clear()
            self._events.clear()

    def queue_event(self, kind, source, event_id):
        if kind not in TRIGGERS or type(source) is not str or len(source) > 200 or type(event_id) is not str or len(event_id) > 200:
            raise ValueError('Invalid trusted source event.')
        with self._lock:
            if len(self._events) == self._events.maxlen:
                return False
            self._events.append((kind, source, event_id))
            return True

    def event(self, kind, source, event_id):
        if kind not in TRIGGERS or type(event_id) is not str or not 1 <= len(event_id) <= 200:
            raise ValueError('Invalid authenticated trigger event.')
        for record in self.repository.list('trigger'):
            value = record['value']
            if value['kind'] == kind and value['source'] == source:
                self._dispatch(record, event_id)

    def _dispatch(self, record, event_id):
        value, key, now = record['value'], record['id'], self.clock()
        with self._lock:
            if key not in self.armed or not value['enabled'] or now - self._last.get(key, -1e20) < value['cooldown']:
                return False
            if not self.allowed():
                self.disarm()
                return False
            digest = hashlib.sha256((value['kind'] + ':' + value['source'] + ':' + event_id).encode('utf-8')).hexdigest()
            # Claim before enqueue. A crash/busy queue can drop an event, never replay an uncertain effect.
            if not self.repository.claim_event(key, digest, now):
                return False
            def perform():
                with self._lock:
                    if key not in self.armed:
                        return
                latest = self.repository.get('trigger', key)
                if latest['revision'] != record['revision'] or not self.allowed():
                    return
                return self.run(value['workflow'], {})
            try:
                self.submit(perform, only_if_idle=True)
            except (queue.Full, RuntimeError):
                return False
            self._last[key] = now
            return True

    def tick(self):
        if not self.allowed():
            self.disarm()
            return
        now = self.clock()
        with self._lock:
            pending = self._events.popleft() if self._events else None
        if pending:
            self.event(*pending)
        with self._lock:
            due = dict(self._next)
        if not due:
            return
        records = {r['id']: r for r in self.repository.list('trigger')}
        for key, stamp in due.items():
            if now < stamp:
                continue
            record = records.get(key)
            if record is None:
                continue
            value = record['value']
            if now - stamp < 60 or value['missed'] == 'once':
                self._dispatch(record, f'time:{stamp:.3f}')
            interval = value['schedule']['interval_seconds']
            following = now + interval if interval else next_daily(value['schedule'], now)
            with self._lock:
                if key in self.armed:
                    self._next[key] = following

    def _loop(self):
        while not self._closed.wait(.5):
            try:
                self.tick()
            except Exception:
                self.disarm()

    def close(self):
        self.disarm()
        self._closed.set()

    def wait_closed(self):
        if self._thread:
            self._thread.join()
