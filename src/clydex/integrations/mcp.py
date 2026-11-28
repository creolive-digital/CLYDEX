"""Reviewed MCP 2026-07-28 Streamable HTTP client, not a server launcher.

No sampling, roots, elicitation, subscriptions or remote code installation.
Discovery is untrusted inventory; each exact tool/schema needs owner review.
"""
import base64
import codecs
import hashlib
import json
import re
import uuid

from clydex.core.contracts import canonical_json
from clydex.integrations.services import endpoint
from clydex.providers.transport import HTTPTransport
from clydex.security.schema import check_schema, detached, validate

VERSION = '2026-07-28'
HEADER_NAME = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")


def header_value(value):
    if type(value) is bool:
        value = 'true' if value else 'false'
    elif type(value) is int and abs(value) <= 2 ** 53 - 1:
        value = str(value)
    elif type(value) is not str:
        raise ValueError('Invalid MCP header value.')
    if (value != value.strip(' \t') or any(ord(c) < 32 and c != '\t' or ord(c) > 126 for c in value)
            or value.startswith('=?base64?')):
        return '=?base64?' + base64.b64encode(value.encode('utf-8')).decode('ascii') + '?='
    return value


def parameter_headers(schema, arguments):
    result, used = {}, set()
    def walk(part, value, properties_only=True):
        annotation = part.get('x-mcp-header')
        if annotation is not None:
            if (not properties_only or type(annotation) is not str or not HEADER_NAME.fullmatch(annotation)
                    or annotation.lower() in used or part['type'] not in ('string', 'integer', 'boolean')):
                raise ValueError('Unsupported MCP header annotation.')
            used.add(annotation.lower())
            if value is not None:
                result['Mcp-Param-' + annotation] = header_value(value)
        for key, child in part.get('properties', {}).items():
            walk(child, value.get(key) if type(value) is dict else None, properties_only)
        if 'items' in part:
            walk(part['items'], None, False)
    walk(schema, arguments)
    return result


def reviewed_tool(tool):
    if (type(tool) is not dict or type(tool.get('name')) is not str or not 1 <= len(tool['name']) <= 128
            or type(tool.get('description', '')) is not str or len(tool.get('description', '')) > 4000):
        raise ValueError('Invalid MCP tool inventory.')
    check_schema(tool.get('inputSchema'))
    if tool['inputSchema']['type'] != 'object':
        raise ValueError('MCP tool input must be an object.')
    parameter_headers(tool['inputSchema'], {})
    output = tool.get('outputSchema')
    if output is not None:
        check_schema(output)
    safe = dict(name=tool['name'], description=tool.get('description', ''), inputSchema=tool['inputSchema'])
    if output is not None:
        safe['outputSchema'] = output
    safe['digest'] = hashlib.sha256(canonical_json(safe).encode('utf-8')).hexdigest()
    return detached(safe)


class ResponseStream:
    def __init__(self, request_id):
        self.request_id, self.result = request_id, None
        self.decoder = codecs.getincrementaldecoder('utf-8')('strict')
        self.text, self.data, self.raw = '', [], bytearray()

    def receive(self, chunk):
        self.raw.extend(chunk)
        self.text += self.decoder.decode(chunk)
        if len(self.raw) > 131072:
            raise ValueError('MCP response exceeds its bound.')
        while '\n' in self.text:
            line, self.text = self.text.split('\n', 1)
            line = line.rstrip('\r')
            if not line:
                if self.data:
                    packet = json.loads('\n'.join(self.data))
                    self.accept(packet)
                    self.data = []
            elif line.startswith('data:'):
                self.data.append(line[5:].removeprefix(' '))

    def accept(self, packet):
        if type(packet) is not dict or packet.get('jsonrpc') != '2.0':
            raise ValueError('Invalid MCP JSON-RPC response.')
        if 'method' in packet:
            if 'id' in packet or packet['method'] not in ('notifications/progress', 'notifications/message'):
                raise ValueError('Unsolicited MCP request/notification is not authorized.')
            return
        if packet.get('id') != self.request_id or ('result' in packet) == ('error' in packet):
            raise ValueError('MCP response identity mismatch.')
        self.result = packet


class MCPClient:
    def __init__(self, transport=None):
        self.transport = transport or HTTPTransport()

    def rpc(self, profile, method, params, secret, token, tool=None):
        destination = endpoint(profile['endpoint'])
        if profile.get('protocol_version') != VERSION:
            raise ValueError('Only explicitly configured MCP 2026-07-28 is supported; no silent legacy downgrade.')
        key = str(uuid.uuid4())
        parameters = detached(params)
        parameters['_meta'] = {'io.modelcontextprotocol/protocolVersion': VERSION,
            'io.modelcontextprotocol/clientInfo': {'name': 'CLYDEX', 'version': '2.0.0.dev1'},
            'io.modelcontextprotocol/clientCapabilities': {}}
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream',
                   'MCP-Protocol-Version': VERSION, 'Mcp-Method': method}
        if 'name' in params:
            headers['Mcp-Name'] = header_value(params['name'])
        if tool:
            headers.update(parameter_headers(tool['inputSchema'], params['arguments']))
        if secret:
            if any(ord(c) < 33 or ord(c) > 126 for c in secret):
                raise ValueError('Invalid MCP credential encoding.')
            headers['Authorization'] = 'Bearer ' + secret
        stream = ResponseStream(key)
        response = self.transport.exchange('POST', destination, headers,
            canonical_json({'jsonrpc': '2.0', 'id': key, 'method': method, 'params': parameters}).encode('utf-8'),
            token, 45, 131072, receive=stream.receive, accepted=None, stop_receiving=lambda: stream.result is not None)
        token.check()
        content_type = dict((k.lower(), v) for k, v in response.headers).get('content-type', '').split(';')[0].strip()
        if content_type == 'application/json':
            stream.accept(json.loads(bytes(stream.raw)))
        elif content_type != 'text/event-stream':
            raise ValueError('Unsupported MCP response content type.')
        packet = stream.result
        if response.status != 200 or not packet or 'error' in packet:
            raise ValueError('MCP request failed or protocol/schema changed; no automatic retry.')
        value = packet['result']
        if type(value) is not dict or value.get('resultType') != 'complete':
            raise ValueError('MCP requested unsupported additional input; no authority granted.')
        return value

    def discover(self, profile, secret, token):
        identity = self.rpc(profile, 'server/discover', {}, secret, token)
        if not isinstance(identity.get('capabilities'), dict) or 'tools' not in identity['capabilities']:
            return dict(identity=identity, tools=[])
        tools, cursor = [], None
        for _ in range(4):
            value = self.rpc(profile, 'tools/list', {'cursor': cursor} if cursor else {}, secret, token)
            if type(value.get('tools')) is not list or len(value['tools']) > 64:
                raise ValueError('MCP tool inventory exceeds bounds.')
            for item in value['tools']:
                try:
                    tool = reviewed_tool(item)
                except ValueError:
                    continue  # Explicitly unsupported schemas are not executable.
                if any(x['name'] == tool['name'] for x in tools):
                    raise ValueError('Duplicate MCP tool identity.')
                tools.append(tool)
                if len(tools) > 64:
                    raise ValueError('MCP inventory exceeds bounds.')
            cursor = value.get('nextCursor')
            if not cursor:
                return dict(identity=identity, tools=tools)
            if type(cursor) is not str or len(cursor) > 2000:
                raise ValueError('Invalid MCP pagination.')
        raise ValueError('MCP inventory requires too many pages.')

    def call(self, profile, tool, arguments, secret, token):
        validate(arguments, tool['inputSchema'])
        result = self.rpc(profile, 'tools/call', {'name': tool['name'], 'arguments': arguments}, secret, token, tool)
        if 'outputSchema' in tool and not result.get('isError', False):
            validate(result.get('structuredContent'), tool['outputSchema'])
        if type(result.get('content')) is not list or len(result['content']) > 32:
            raise ValueError('Invalid MCP tool result.')
        # Only text is presented; no remote resources, images, links or instructions are followed.
        content = [dict(type='text', text=x['text'][:16000]) for x in result['content']
                   if type(x) is dict and x.get('type') == 'text' and type(x.get('text')) is str]
        return dict(content=content, isError=bool(result.get('isError', False)), untrusted=True)
