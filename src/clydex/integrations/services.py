"""Official API codecs with explicit resources and no implicit network/retries.

OAuth/bot credentials must be provisioned by the owner in Credential Manager.
This module does not impersonate browser sessions or implement account signup.
"""
from dataclasses import dataclass
import json
import re
from urllib.parse import quote, urlsplit

from clydex.core.contracts import canonical_json
from clydex.providers.transport import HTTPTransport
from clydex.security.schema import object_schema, validate

TEXT = {'type': 'string', 'minLength': 1, 'maxLength': 2000}
EMPTY = object_schema()
SEND = object_schema(text=TEXT)
OPERATIONS = {
    'microsoft': {'mail': EMPTY, 'calendar': EMPTY},
    'google': {'mail': EMPTY, 'calendar': EMPTY},
    'github': {'repository': EMPTY, 'issues': EMPTY, 'create_issue': object_schema(title={'type': 'string', 'minLength': 1, 'maxLength': 200}, body=TEXT)},
    'telegram': {'identity': EMPTY, 'send': SEND},
    'discord': {'messages': EMPTY, 'send': SEND},
    'whatsapp': {'send': SEND},
    'homeassistant': {'state': EMPTY, 'turn_on': EMPTY, 'turn_off': EMPTY},
    'azure': {'resources': EMPTY},
    'rest': {'get': EMPTY, 'post': {'type': 'object', 'additionalProperties': True}},
    'webhook': {'post': {'type': 'object', 'additionalProperties': True}},
    'mqtt': {'publish': SEND, 'receive': EMPTY},
}
SCOPES = {
    'microsoft': ['Mail.ReadBasic', 'Calendars.ReadBasic'],
    'google': ['https://www.googleapis.com/auth/gmail.metadata', 'https://www.googleapis.com/auth/calendar.events.readonly'],
    'github': ['metadata:read', 'issues:read', 'issues:write (create only)'],
    'telegram': ['selected bot and chat'], 'discord': ['bot, VIEW_CHANNEL, READ_MESSAGE_HISTORY, SEND_MESSAGES'],
    'whatsapp': ['whatsapp_business_messaging'], 'homeassistant': ['selected entity/service; token authority is account-wide'],
    'azure': ['Reader on selected resource group'], 'rest': ['owner-selected endpoint capability'],
    'mqtt': ['broker ACL for exact topic'], 'webhook': ['selected receiver capability'],
}


def endpoint(value):
    if type(value) is not str or len(value) > 2000:
        raise ValueError('Invalid endpoint.')
    parts = urlsplit(value)
    if (parts.scheme not in ('http', 'https') or not parts.hostname or parts.username or parts.password
            or parts.fragment or parts.query or (parts.scheme == 'http' and parts.hostname not in ('127.0.0.1', '::1'))):
        raise ValueError('Use verified HTTPS, or explicit literal loopback HTTP, without credentials/query/fragment.')
    _ = parts.port
    return value.rstrip('/')


def validate_profile(value):
    if (type(value) is not dict or set(value) != {'name', 'service', 'endpoint', 'resource', 'version', 'enabled'}
            or value['service'] not in OPERATIONS or type(value['enabled']) is not bool):
        raise ValueError('Invalid integration profile fields.')
    for key, maximum in (('name', 100), ('resource', 300), ('version', 40)):
        if type(value[key]) is not str or len(value[key]) > maximum or any(ord(c) < 32 for c in value[key]):
            raise ValueError('Invalid integration metadata.')
    endpoint(value['endpoint'])
    if value['service'] == 'whatsapp' and not re.fullmatch(r'v\d+\.\d+', value['version']):
        raise ValueError('Select an explicitly supported Meta Graph API version.')
    return value


@dataclass(frozen=True)
class PreparedRequest:
    method: str
    url: str
    headers: dict
    body: bytes | None


def prepare(profile, operation, data, secret):
    validate_profile(profile)
    service, resource = profile['service'], profile['resource']
    if operation not in OPERATIONS[service]:
        raise ValueError('Unknown integration operation.')
    validate(data, OPERATIONS[service][operation])
    headers = {'Accept': 'application/json', 'User-Agent': 'CLYDEX/2', 'Content-Type': 'application/json'}
    method, body, path = 'GET', None, ''
    bases = {'microsoft': 'https://graph.microsoft.com',
             'google': 'https://gmail.googleapis.com' if operation == 'mail' else 'https://www.googleapis.com',
             'github': 'https://api.github.com', 'telegram': 'https://api.telegram.org',
             'discord': 'https://discord.com', 'whatsapp': 'https://graph.facebook.com', 'azure': 'https://management.azure.com'}
    # Fixed official origins; loopback substitution is only explicit synthetic injection in tests.
    if service in bases and profile['endpoint'] != bases[service]:
        raise ValueError('This service requires its official API origin.')
    if secret:
        if any(ord(c) < 33 or ord(c) > 126 for c in secret):
            raise ValueError('Invalid API credential encoding.')
        headers['Authorization'] = ('Bot ' if service == 'discord' else 'Bearer ') + secret
    if service == 'microsoft':
        path = '/v1.0/me/messages?$top=12&$select=id,subject,receivedDateTime,isRead' if operation == 'mail' else '/v1.0/me/events?$top=12&$select=id,subject,start,end'
    elif service == 'google':
        path = '/gmail/v1/users/me/messages?maxResults=12' if operation == 'mail' else '/calendar/v3/calendars/' + quote(resource or 'primary', safe='') + '/events?maxResults=12'
    elif service == 'github':
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', resource):
            raise ValueError('Select owner/repository.')
        headers.update({'X-GitHub-Api-Version': '2026-03-10', 'Accept': 'application/vnd.github+json'})
        path = '/repos/' + resource + ('' if operation == 'repository' else '/issues')
        if operation == 'issues':
            path += '?per_page=12&state=open'
        elif operation == 'create_issue':
            method, body = 'POST', data
    elif service == 'telegram':
        if not secret or not re.fullmatch(r'[0-9]+:[A-Za-z0-9_-]+', secret):
            raise ValueError('Configure a legitimate bot token.')
        headers.pop('Authorization', None)
        path = '/bot' + secret + ('/getMe' if operation == 'identity' else '/sendMessage')
        if operation == 'send':
            if not re.fullmatch(r'-?\d{1,20}|@[A-Za-z0-9_]{5,64}', resource):
                raise ValueError('Configure a selected Telegram chat.')
            method, body = 'POST', {'chat_id': resource, 'text': data['text']}
    elif service == 'discord':
        if not resource.isdigit():
            raise ValueError('Select a Discord channel identifier.')
        path = '/api/v10/channels/' + resource + '/messages'
        if operation == 'messages':
            path += '?limit=12'
        else:
            method, body = 'POST', {'content': data['text'], 'allowed_mentions': {'parse': []}}
    elif service == 'whatsapp':
        pieces = resource.split(':')
        if len(pieces) != 2 or not all(p.isdigit() for p in pieces):
            raise ValueError('Select phone_number_id:recipient_digits.')
        path = '/' + profile['version'] + '/' + pieces[0] + '/messages'
        method, body = 'POST', dict(messaging_product='whatsapp', to=pieces[1], type='text', text={'body': data['text']})
    elif service == 'homeassistant':
        if not re.fullmatch(r'[a-z_]+\.[a-z0-9_]+', resource):
            raise ValueError('Select an exact Home Assistant entity.')
        if operation == 'state':
            path = '/api/states/' + resource
        else:
            path = '/api/services/' + resource.split('.')[0] + '/' + operation
            method, body = 'POST', {'entity_id': resource}
    elif service == 'azure':
        if not re.fullmatch(r'[0-9a-fA-F-]{36}/[A-Za-z0-9_.()-]{1,90}', resource):
            raise ValueError('Select subscription UUID/resource group.')
        subscription, group = resource.split('/')
        path = f'/subscriptions/{subscription}/resourceGroups/{group}/resources?api-version=2021-04-01&$top=30'
    elif service in ('rest', 'webhook'):
        if operation == 'post':
            method, body = 'POST', data
    else:
        raise ValueError('MQTT uses the separately bounded TLS adapter.')
    return PreparedRequest(method, profile['endpoint'] + path, headers,
                           canonical_json(body).encode('utf-8') if body is not None else None)


class IntegrationClient:
    def __init__(self, transport=None):
        self.transport = transport or HTTPTransport()

    def request(self, profile, operation, data, secret, token):
        packet = prepare(profile, operation, data, secret)
        response = self.transport.exchange(packet.method, packet.url, packet.headers, packet.body,
                                           token, 30, 65536, accepted={200, 201, 202, 204})
        token.check()
        result = json.loads(response.body) if response.body else {}
        if type(result) not in (dict, list):
            raise ValueError('Unexpected service response.')
        return dict(status=response.status, data=result, provenance=profile['service'], untrusted=True)
