"""Portable workflow v2. Contracts contain data, never authority or code."""
import re
import uuid

from clydex.core.contracts import canonical_json
from clydex.security.schema import check_schema, detached, validate

KINDS = ('input', 'note', 'tool', 'condition', 'delay', 'approval', 'loop', 'output')
NAME = re.compile(r'^[A-Za-z][A-Za-z0-9_-]{0,63}$')


def text(value, maximum=120):
    if type(value) is not str or not value.strip() or len(value) > maximum:
        raise ValueError('Invalid workflow text.')
    return value


def exact(value, fields):
    if type(value) is not dict or set(value) != set(fields):
        raise ValueError('Unexpected or missing contract fields.')


def identifier(value):
    if type(value) is not str or str(uuid.UUID(value)) != value:
        raise ValueError('Canonical UUID required.')
    return value


def references(value, depth=0):
    if depth > 12:
        raise ValueError('Expression nesting limit exceeded.')
    if type(value) is dict:
        if '$ref' in value:
            exact(value, ('$ref',))
            ref = value['$ref']
            if (type(ref) is not str or len(ref) > 200 or
                    any(not NAME.fullmatch(part) for part in ref.split('.'))):
                raise ValueError('Invalid output reference.')
            return {ref.split('.')[0]}
        result = set()
        for item in value.values():
            result |= references(item, depth + 1)
        return result
    if type(value) is list:
        result = set()
        for item in value:
            result |= references(item, depth + 1)
        return result
    return set()


def validate_workflow(value: dict, specs=None) -> dict:
    exact(value, ('contract_version', 'id', 'name', 'inputs', 'nodes', 'edges', 'timeout'))
    if value['contract_version'] != 2 or type(value['contract_version']) is not int:
        raise ValueError('Unsupported workflow version.')
    identifier(value['id'])
    text(value['name'])
    if type(value['timeout']) is not int or not 1 <= value['timeout'] <= 300:
        raise ValueError('Workflow timeout must be 1–300 seconds.')
    check_schema(value['inputs'])
    if value['inputs']['type'] != 'object' or value['inputs'].get('additionalProperties', False):
        raise ValueError('Workflow inputs must be an explicit object schema.')
    if (type(value['nodes']) is not list or not 1 <= len(value['nodes']) <= 64
            or type(value['edges']) is not list or len(value['edges']) > 128
            or len(canonical_json(value).encode('utf-8')) > 65536):
        raise ValueError('Workflow graph exceeds its limits.')
    nodes, effects, refs = {}, 0, {}
    fields = {'input': (), 'note': ('text',), 'tool': ('tool', 'arguments'),
              'condition': ('left', 'operator', 'right'), 'delay': ('seconds',),
              'approval': ('message',), 'loop': ('count', 'tool', 'arguments'), 'output': ('value',)}
    for node in value['nodes']:
        exact(node, ('id', 'kind', 'config', 'x', 'y'))
        key, kind, config = node['id'], node['kind'], node['config']
        if type(key) is not str or not NAME.fullmatch(key) or key in ('inputs', 'iteration') or key in nodes or kind not in KINDS:
            raise ValueError('Invalid or duplicate workflow node.')
        if any(type(node[p]) not in (int, float) or not -10000 <= node[p] <= 10000 for p in ('x', 'y')):
            raise ValueError('Invalid node position.')
        exact(config, fields[kind])
        if kind in ('note', 'approval'):
            text(config['text' if kind == 'note' else 'message'], 2000)
        if kind == 'delay' and (type(config['seconds']) not in (int, float) or not 0 <= config['seconds'] <= 60):
            raise ValueError('Delay must be bounded to 60 seconds.')
        if kind == 'condition' and config['operator'] not in ('eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'contains', 'exists'):
            raise ValueError('Unsupported condition operator.')
        if kind in ('tool', 'loop'):
            text(config['tool'], 100)
            if type(config['arguments']) is not dict:
                raise ValueError('Tool arguments must be an object.')
            count = config['count'] if kind == 'loop' else 1
            if type(count) is not int or not 1 <= count <= 10:
                raise ValueError('Loops require an explicit count of 1–10.')
            effects += count
            if specs is not None:
                spec = specs.get(config['tool'])
                if spec is None:
                    raise ValueError('Unknown or unavailable workflow tool.')
                if not references(config['arguments']):
                    spec.validate(config['arguments'])
        refs[key] = references(config)
        if kind != 'loop' and 'iteration' in refs[key]:
            raise ValueError('Iteration references are confined to loop actions.')
        nodes[key] = node
    if effects > 64:
        raise ValueError('Workflow effect budget exceeded.')
    incoming, outgoing, seen = {k: [] for k in nodes}, {k: [] for k in nodes}, set()
    for edge in value['edges']:
        exact(edge, ('from', 'to', 'port'))
        a, b, port = edge['from'], edge['to'], edge['port']
        if a not in nodes or b not in nodes or a == b or type(port) is not str:
            raise ValueError('Invalid graph edge.')
        if port not in (('true', 'false') if nodes[a]['kind'] == 'condition' else ('next',)):
            raise ValueError('Invalid edge port.')
        edge_key = (a, b, port)
        if edge_key in seen:
            raise ValueError('Duplicate graph edge.')
        seen.add(edge_key)
        incoming[b].append(a)
        outgoing[a].append(b)
    pending, ordered = set(nodes), []
    ancestors = {}
    while pending:
        ready = sorted(k for k in pending if all(a in ordered for a in incoming[k]))
        if not ready:
            raise ValueError('Cycles require a bounded loop node; cyclic graphs are rejected.')
        for key in ready:
            ancestors[key] = set(incoming[key])
            for parent in incoming[key]:
                ancestors[key] |= ancestors[parent]
            if refs[key] - ancestors[key] - {'inputs', 'iteration'}:
                raise ValueError('Output references must name an upstream dependency.')
            ordered.append(key)
            pending.remove(key)
    return detached(value)


def migrate_v1(value: dict) -> dict:
    """Only inert legacy contracts migrate. Importing never enables execution."""
    from clydex.synchronization.contracts import validate_payload
    value = validate_payload('workflows', value)
    if value['contract_version'] != 1:
        raise ValueError('Expected inert v1 workflow.')
    keys = {n['id']: f'node_{i}' for i, n in enumerate(value['nodes'])}
    return validate_workflow(dict(contract_version=2, id=str(uuid.uuid4()), name=value['name'],
        inputs={'type': 'object', 'properties': {}, 'required': [], 'additionalProperties': False}, timeout=120,
        nodes=[dict(id=keys[n['id']], kind='note', config={'text': n['text'] or 'Imported inert node'},
                    x=60 + i * 180, y=80) for i, n in enumerate(value['nodes'])],
        edges=[{'from': keys[e['from']], 'to': keys[e['to']], 'port': 'next'} for e in value['edges']]))


def validate_inputs(workflow, inputs):
    validate(inputs, workflow['inputs'])
