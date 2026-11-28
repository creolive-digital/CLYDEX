"""Editable routines are ordinary disabled workflow definitions, not another engine."""
import uuid

ROUTINES = ('morning', 'work', 'focus', 'meeting', 'evening', 'night', 'custom')


def template(kind):
    if kind not in ROUTINES:
        raise ValueError('Unknown routine template.')
    feeds = {'morning': ['weather', 'calendar', 'tasks'], 'work': ['github', 'tasks'],
             'focus': ['system'], 'meeting': ['calendar'], 'evening': ['tasks'],
             'night': ['system'], 'custom': []}[kind]
    nodes, edges = [], []
    for index, feed in enumerate(feeds):
        key = 'feed_' + str(index)
        nodes.append(dict(id=key, kind='tool', config={'tool': 'feeds.read', 'arguments': {'feed': feed}}, x=60 + index * 220, y=80))
        if index:
            edges.append({'from': 'feed_' + str(index - 1), 'to': key, 'port': 'next'})
    if not nodes:
        nodes = [dict(id='start', kind='note', config={'text': 'Add reviewed tools to your custom routine.'}, x=60, y=80)]
    return dict(contract_version=2, id=str(uuid.uuid4()), name=kind.title() + ' routine',
                inputs={'type': 'object', 'properties': {}, 'required': [], 'additionalProperties': False},
                nodes=nodes, edges=edges, timeout=120)
