"""Optional Paho adapter: verified TLS, exact topic, owned synchronous loop."""
import time
from urllib.parse import urlsplit

from clydex.integrations.services import OPERATIONS, validate_profile
from clydex.security.schema import validate


def request(profile, operation, data, secret, token, *, factory=None):
    validate_profile(profile)
    if profile['service'] != 'mqtt' or operation not in ('publish', 'receive'):
        raise ValueError('Unsupported MQTT operation.')
    validate(data, OPERATIONS['mqtt'][operation])
    topic, parts = profile['resource'], urlsplit(profile['endpoint'])
    if parts.scheme != 'https' or parts.path not in ('', '/') or not topic or any(c in topic for c in ('#', '+', '\0')):
        raise ValueError('MQTT requires a verified TLS broker and exact topic.')
    if factory is None:
        import paho.mqtt.client as mqtt
        def factory():
            return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, reconnect_on_failure=False)
    client = factory()
    client.connect_timeout = 5.
    client.tls_set()
    if secret:
        client.username_pw_set(profile['version'], secret)
    connected, messages, errors = [], [], []
    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code != 0:
            errors.append(True)
        else:
            connected.append(True)
            if operation == 'receive':
                client.subscribe(topic, qos=0)
    def on_message(client, userdata, message):
        if message.topic == topic and len(messages) < 16 and len(message.payload) <= 4096:
            messages.append(message.payload.decode('utf-8', 'replace'))
    client.on_connect, client.on_message = on_connect, on_message
    deadline = time.monotonic() + 8
    try:
        token.check()
        client.connect(parts.hostname, parts.port or 8883, keepalive=15)
        while not connected:
            token.check()
            if time.monotonic() >= deadline or errors:
                raise ValueError('MQTT connection unavailable.')
            client.loop(timeout=.05)
        if operation == 'publish':
            pending = client.publish(topic, data['text'], qos=0, retain=False)
            while not pending.is_published():
                token.check()
                if time.monotonic() >= deadline:
                    raise ValueError('MQTT outcome uncertain; no automatic retry.')
                client.loop(timeout=.05)
            return dict(published=True, topic=topic, qos=0)
        while time.monotonic() < deadline and not messages:
            token.check()
            client.loop(timeout=.05)
        return dict(messages=messages, topic=topic, provenance='configured MQTT broker', untrusted=True)
    finally:
        client.disconnect()
