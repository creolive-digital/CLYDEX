"""Bounded, deliberately small JSON Schema subset for executable contracts.

Unsupported keywords fail closed. No references, executable expressions, regular
expressions or remote schema resolution are accepted.
"""
import json
import math

from clydex.core.contracts import canonical_json

TYPES = {'object': dict, 'array': list, 'string': str, 'integer': int,
         'number': (int, float), 'boolean': bool, 'null': type(None)}
KEYS = {'type', 'properties', 'required', 'additionalProperties', 'items', 'enum',
        'minimum', 'maximum', 'minLength', 'maxLength', 'minItems', 'maxItems',
        'description', 'title', '$schema', 'x-mcp-header'}


def check_schema(schema: dict, depth: int = 0) -> None:
    if (depth > 12 or type(schema) is not dict or set(schema) - KEYS
            or schema.get('type') not in TYPES):
        raise ValueError('Unsupported or excessively nested schema.')
    if depth == 0 and len(canonical_json(schema).encode('utf-8')) > 32768:
        raise ValueError('Schema too large.')
    kind = schema['type']
    for key in ('minimum', 'maximum', 'minLength', 'maxLength', 'minItems', 'maxItems'):
        if key in schema and (type(schema[key]) not in (int, float) or not math.isfinite(schema[key])):
            raise ValueError('Invalid schema bound.')
    if 'enum' in schema and (type(schema['enum']) is not list or not 1 <= len(schema['enum']) <= 128):
        raise ValueError('Invalid enumeration.')
    if kind == 'object':
        props = schema.get('properties', {})
        required = schema.get('required', [])
        if (type(props) is not dict or len(props) > 64 or type(required) is not list
                or any(type(k) is not str or len(k) > 128 for k in props)
                or any(type(k) is not str or k not in props for k in required)
                or len(required) != len(set(required))
                or type(schema.get('additionalProperties', False)) is not bool):
            raise ValueError('Invalid object schema.')
        for child in props.values():
            check_schema(child, depth + 1)
    elif kind == 'array':
        check_schema(schema.get('items'), depth + 1)


def validate(value, schema: dict, *, depth: int = 0) -> None:
    if depth == 0:
        check_schema(schema)
        if len(canonical_json(value).encode('utf-8')) > 262144:
            raise ValueError('Value exceeds its bound.')
    if depth > 16:
        raise ValueError('Value nesting exceeds its bound.')
    kind = schema['type']
    expected = TYPES[kind]
    if not (type(value) in expected if isinstance(expected, tuple) else type(value) is expected):
        raise ValueError('Schema type mismatch.')
    if 'enum' in schema and canonical_json(value) not in [canonical_json(x) for x in schema['enum']]:
        raise ValueError('Unsupported enumeration value.')
    if kind == 'object':
        props = schema.get('properties', {})
        if (set(schema.get('required', [])) - set(value)
                or (not schema.get('additionalProperties', False) and set(value) - set(props))):
            raise ValueError('Unexpected or missing fields.')
        for key, child in value.items():
            if key in props:
                validate(child, props[key], depth=depth + 1)
    elif kind == 'array':
        if not schema.get('minItems', 0) <= len(value) <= min(1024, schema.get('maxItems', 1024)):
            raise ValueError('Array length exceeds bounds.')
        for item in value:
            validate(item, schema['items'], depth=depth + 1)
    elif kind == 'string':
        if not schema.get('minLength', 0) <= len(value) <= min(65536, schema.get('maxLength', 65536)):
            raise ValueError('String length exceeds bounds.')
    elif kind in ('integer', 'number'):
        if not math.isfinite(value) or value < schema.get('minimum', -math.inf) or value > schema.get('maximum', math.inf):
            raise ValueError('Numeric value exceeds bounds.')


def object_schema(**fields) -> dict:
    return {'type': 'object', 'properties': fields, 'required': list(fields), 'additionalProperties': False}


def detached(value):
    return json.loads(canonical_json(value))
