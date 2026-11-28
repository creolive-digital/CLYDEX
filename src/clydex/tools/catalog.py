"""Installed tool definitions. Neither models nor plugins assign this policy."""
import platform

from clydex.core.contracts import Risk, ToolSpec, canonical_json
from clydex.security.schema import object_schema

STRING = {'type': 'string', 'maxLength': 4096}
ID = {'type': 'string', 'minLength': 36, 'maxLength': 36}
OBJECT = {'type': 'object', 'additionalProperties': True}


def spec(name, scope, fields, *, read=False, timeout=60, destinations=(), platforms=('Windows', 'Linux', 'Darwin')):
    return ToolSpec(name, scope, Risk.SENSITIVE if read else Risk.HIGH, timeout,
                    tuple((k, {'string': str, 'object': dict, 'integer': int, 'boolean': bool}[v['type']])
                          for k, v in fields.items()), (dict,),
                    description=name.replace('.', ' ').replace('_', ' '),
                    argument_schema_json=canonical_json(object_schema(**fields)),
                    result_schema_json=canonical_json(OBJECT), platforms=platforms,
                    read_only=read, destinations=destinations, idempotent=read, approval_required=True)


OPERATING_SPECS = (
    spec('operating.configure', 'operating.settings', {'operation': STRING, 'data': OBJECT}),
    spec('workflow.checkpoint', 'automation.approval', {'workflow': ID, 'node': STRING, 'message': STRING}),
    spec('files.inspect', 'files.selected.read', {'selection': ID, 'operation': {'type': 'string', 'enum': ['read', 'list', 'metadata']}, 'relative': STRING}, read=True),
    spec('files.modify', 'files.selected.write', {'selection': ID, 'operation': {'type': 'string', 'enum': ['write', 'mkdir', 'delete']},
         'relative': STRING, 'text': STRING, 'expected_sha256': STRING}),
    spec('developer.git_read', 'developer.git.read', {'selection': ID, 'operation': {'type': 'string', 'enum': ['status', 'history', 'diff', 'branches']}}, read=True),
    spec('developer.git_branch', 'developer.git.write', {'selection': ID, 'operation': {'type': 'string', 'enum': ['create', 'switch']}, 'branch': STRING}),
    spec('developer.script', 'developer.script', {'selection': ID, 'sha256': STRING}, timeout=120, platforms=('Windows',)),
    spec('developer.diagnostic', 'developer.diagnostics', {'profile': ID, 'operation': STRING}, read=True, timeout=60),
    spec('developer.docker_manage', 'developer.docker.write', {'profile': ID,
         'operation': {'type': 'string', 'enum': ['start', 'stop', 'restart']}, 'container': STRING}),
    spec('developer.ssh_service', 'developer.ssh.write', {'profile': ID,
         'operation': {'type': 'string', 'enum': ['restart']}, 'service': STRING}),
    spec('developer.sql_read', 'developer.sql.read', {'profile': ID, 'query': STRING}, read=True, timeout=40),
    spec('developer.sql_write', 'developer.sql.write', {'profile': ID, 'query': STRING}, timeout=40),
    spec('developer.sql_schema', 'developer.sql.schema', {'profile': ID, 'query': STRING}, timeout=40),
    spec('integration.request', 'integrations.external', {'profile': ID, 'operation': STRING, 'data': OBJECT}, destinations=('reviewed configured service',)),
    spec('mcp.request', 'integrations.mcp', {'server': ID, 'operation': STRING, 'tool': STRING, 'arguments': OBJECT}, destinations=('reviewed MCP endpoint',)),
    spec('plugins.invoke', 'plugins.execute', {'plugin': ID, 'tool': STRING, 'arguments': OBJECT}),
    spec('monitoring.sample', 'monitoring.local', {}, read=True),
    spec('monitoring.gpu', 'monitoring.local', {}, read=True, timeout=15),
    spec('feeds.read', 'feeds.local', {'feed': STRING}, read=True),
    spec('capture.once', 'capture.visible', {'kind': {'type': 'string', 'enum': ['screen', 'camera']},
         'device': {'type': 'integer', 'minimum': 0, 'maximum': 15}}, platforms=('Windows',)),
    spec('media.control', 'media.local', {'operation': {'type': 'string', 'enum': ['play_pause', 'volume_up', 'volume_down', 'mute']}}, platforms=('Windows',)),
)


class TrustedRegistry:
    def __init__(self, engine):
        self.engine = engine
        self.specs = {s.name: s for s in OPERATING_SPECS}
        self.handlers = {}
        self.describe = lambda name, arguments: name

    def bind(self, name, handler):
        if name not in self.specs or name in self.handlers:
            raise ValueError('Unknown or duplicate installed tool binding.')
        self.handlers[name] = handler

    def invoke(self, name, arguments, token=None):
        definition = self.specs.get(name)
        if definition is None or name not in self.handlers:
            raise ValueError('Unknown or unavailable installed tool.')
        definition.validate(arguments)
        if platform.system() not in definition.platforms:
            raise ValueError('Tool unavailable on this platform.')
        active = token or self.engine.cancel_token
        active.check()
        target = self.describe(name, arguments)
        def perform(a):
            if self.describe(name, a) != target:
                raise ValueError('Configured target changed during approval; review again.')
            active.check()
            return self.handlers[name](a, active)
        return self.engine.execute_tool(name, target, arguments, perform,
            'Review the exact arguments and configured destination. Prior effects cannot be undone; no automatic retry.')

    def inventory(self):
        return [dict(**s.inventory(), available=s.name in self.handlers) for s in self.specs.values()]
