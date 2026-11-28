"""Explicit sources and transient observed results, without default polling."""
import time

from clydex.automation.workflows.schema import exact, identifier, text

FEEDS = ('weather', 'news', 'technology', 'email', 'calendar', 'system', 'github', 'network', 'server', 'tasks', 'custom')


def validate_feed(value):
    exact(value, ('name', 'kind', 'enabled', 'profile', 'operation', 'interval', 'threshold', 'cooldown'))
    text(value['name'])
    if (value['kind'] not in FEEDS or type(value['enabled']) is not bool
            or type(value['interval']) is not int or not 60 <= value['interval'] <= 86400
            or type(value['cooldown']) is not int or not 60 <= value['cooldown'] <= 86400
            or type(value['threshold']) is not int or not 1 <= value['threshold'] <= 100
            or type(value['operation']) is not str or len(value['operation']) > 100):
        raise ValueError('Invalid feed configuration.')
    if value['kind'] not in ('system', 'tasks'):
        identifier(value['profile'])
    elif value['profile']:
        raise ValueError('Local feeds do not use an external profile.')
    return value


class FeedService:
    def __init__(self, repository, refresh, notify=lambda code: None, clock=time.time):
        self.repository, self._refresh, self.notify, self.clock = repository, refresh, notify, clock
        self.results, self.last_alert, self.polling = {}, {}, False

    def refresh(self, key):
        record = self.repository.get('feed', key)
        value = validate_feed(record['value'])
        if not value['enabled']:
            raise ValueError('Feed is disabled.')
        now = self.clock()
        try:
            result = self._refresh(value)
            self.results[key] = dict(status='observed', updated_at=now, provenance=value['profile'] or 'local Core', data=result)
            if value['kind'] == 'system' and any(type(result.get(field)) in (int, float) and result[field] >= value['threshold']
                    for field in ('cpu_percent', 'memory_percent', 'disk_percent')):
                if now - self.last_alert.get(key, -1e20) >= value['cooldown']:
                    self.notify('resource.alert')
                    self.last_alert[key] = now
        except Exception:
            self.results[key] = dict(status='failed', updated_at=now, provenance=value['profile'] or 'local Core',
                                     data={}, error='Source unavailable, denied or interrupted; no automatic action retry.')
            raise
        return self.results[key]

    def read(self, kind):
        candidates = [r for r in self.repository.list('feed') if r['value']['kind'] == kind]
        return dict(kind=kind, sources=[dict(id=r['id'], name=r['value']['name'], enabled=r['value']['enabled'],
            **self.result(r)) for r in candidates], status='configured' if candidates else 'unconfigured')

    def result(self, record):
        result = dict(self.results.get(record['id'], dict(status='not_refreshed', updated_at=None,
                                                       provenance=record['value']['profile'] or 'local Core', data={})))
        result['stale'] = result['updated_at'] is None or self.clock() - result['updated_at'] > record['value']['interval']
        return result

    def due(self):
        if not self.polling:
            return None
        for record in self.repository.list('feed'):
            if record['value']['enabled'] and self.result(record)['stale']:
                return record['id']
        return None

    def clear(self):
        self.polling = False
        self.results.clear()
