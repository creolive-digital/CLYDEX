"""One strict sync payload policy reused by desktop and cloud."""
import json
import uuid

from clydex.core.contracts import canonical_json
from clydex.security.content import validate_private_text

CATEGORIES = ('knowledge', 'memory', 'history', 'preferences', 'workflows', 'devices', 'themes')


def identifier(value: str) -> str:
    if not isinstance(value, str) or str(uuid.UUID(value)) != value:
        raise ValueError('Canonical UUID required.')
    return value


def validate_payload(category: str, value: dict, *, deleted=False) -> dict:
    if category not in CATEGORIES or not isinstance(value, dict) or type(deleted) is not bool:
        raise ValueError('Invalid sync category or payload.')
    if len(canonical_json(value).encode()) > 65536:
        raise ValueError('Sync entity exceeds its bound.')
    if deleted:
        if value:
            raise ValueError('Deletion payloads contain no private data.')
        return {}
    if category == 'memory':
        allowed = {'category', 'value', 'local_only', 'confirmed', 'origin', 'source_kind'}
        if (set(value) != allowed or value['local_only'] is not False or value['confirmed'] is not True
                or value['category'] not in ('preferences', 'profile', 'projects', 'routines', 'work', 'facts')
                or value['origin'] not in ('explicit', 'inferred')
                or value['source_kind'] not in ('manual_ui', 'user_prompt', 'cloud_sync')):
            raise ValueError('Local-only, unconfirmed or external-source memories cannot synchronize.')
        validate_private_text(value['value'], 2000)
    elif category == 'history':
        if (set(value) != {'title', 'messages', 'temporary', 'local_only', 'sensitive'}
                or any(value[x] is not False for x in ('temporary', 'local_only', 'sensitive'))
                or not isinstance(value['messages'], list) or len(value['messages']) > 100):
            raise ValueError('Only explicitly saved safe history can synchronize.')
        validate_private_text(value['title'], 120)
        for message in value['messages']:
            if not isinstance(message, dict) or set(message) != {'role', 'content', 'provider', 'model', 'created_at'}:
                raise ValueError('Unexpected history fields.')
            if message['role'] not in ('user', 'assistant'):
                raise ValueError('Tool/system messages cannot synchronize.')
            validate_private_text(message['content'], 16000)
            for key in ('provider', 'model', 'created_at'):
                if not isinstance(message[key], str) or len(message[key]) > 160:
                    raise ValueError('Invalid history metadata.')
    elif category == 'preferences':
        if set(value) - {'recognition_mode', 'speak_replies'}:
            raise ValueError('Activation, credentials and permission preferences never synchronize.')
        if 'recognition_mode' in value and value['recognition_mode'] not in ('en', 'en-accurate', 'auto'):
            raise ValueError('Unsupported recognition mode.')
        if 'speak_replies' in value and type(value['speak_replies']) is not bool:
            raise ValueError('Invalid preference flag.')
    elif category == 'themes':
        from clydex.desktop.preferences import PresentationPreferences
        if set(value) - {'theme', 'accent', 'reduced_motion', 'animations', 'resource_saving', 'fps', 'particles', 'detail'}:
            raise ValueError('Only appearance/resource preferences synchronize as themes.')
        PresentationPreferences(**value)
    elif category == 'knowledge':
        if set(value) != {'title'}:
            raise ValueError('Knowledge sync changes metadata only; uploads use reviewed document transfers.')
        validate_private_text(value['title'], 120)
    elif category == 'devices':
        if set(value) != {'display_name', 'platform'}:
            raise ValueError('Device credentials, scopes and revocation cannot synchronize as metadata.')
        validate_private_text(value['display_name'], 80)
        validate_private_text(value['platform'], 40)
    elif category == 'workflows':
        if value.get('contract_version') == 2:
            from clydex.automation.workflows.schema import validate_workflow
            value = validate_workflow(value)
            def safe_constants(item):
                if type(item) is dict:
                    if any(k.casefold() in ('password', 'secret', 'token', 'api_key', 'authorization', 'permissions', 'approval') for k in item):
                        raise ValueError('Credentials and authority cannot synchronize in workflows.')
                    for child in item.values():
                        safe_constants(child)
                elif type(item) is list:
                    for child in item:
                        safe_constants(child)
                elif type(item) is str and item.strip():
                    validate_private_text(item, 65536)
            safe_constants(value)
            return json.loads(canonical_json(value))
        if (set(value) != {'contract_version', 'name', 'nodes', 'edges'} or value['contract_version'] != 1
                or not isinstance(value['nodes'], list) or not isinstance(value['edges'], list)
                or len(value['nodes']) > 64 or len(value['edges']) > 128):
            raise ValueError('Only version 1 inert workflow contracts can synchronize.')
        validate_private_text(value['name'], 120)
        node_ids = set()
        for node in value['nodes']:
            if not isinstance(node, dict) or set(node) != {'id', 'kind', 'text'} or node['kind'] not in ('input', 'note', 'output'):
                raise ValueError('Executable workflow nodes are outside Phase 05.')
            key = identifier(node['id'])
            if key in node_ids:
                raise ValueError('Duplicate graph node.')
            node_ids.add(key)
            validate_private_text(node['text'], 1000)
        for edge in value['edges']:
            if not isinstance(edge, dict) or set(edge) != {'from', 'to'} or edge['from'] not in node_ids or edge['to'] not in node_ids:
                raise ValueError('Invalid contract edge.')
    return json.loads(canonical_json(value))
