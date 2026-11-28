"""Existing deterministic parser and model response schemas."""
import re


def object_schema(**fields):
    return {'type': 'object', 'properties': fields, 'required': list(fields),
            'additionalProperties': False}


STRING = {'type': 'string'}
APP_ACTIONS = ('list_windows', 'manage_window', 'list_controls', 'press_control', 'append_text')
STEP = object_schema(action={'type': 'string', 'enum': [
    'operating_tool', 'open_app', 'browse', 'read_tab', 'read_inbox', 'draft_reply', 'windows_task', *APP_ACTIONS]},
    target=STRING, detail=STRING, control=STRING)
PLAN = object_schema(steps={'type': 'array', 'items': STEP}, message=STRING)

APP_NAMES = {
    'calculator': 'Calculator', 'notepad': 'Notepad', 'note pad': 'Notepad',
    'character map': 'Character Map', 'paint': 'Paint', 'file explorer': 'File Explorer',
    'chrome': 'Google Chrome', 'google chrome': 'Google Chrome',
    'edge': 'Microsoft Edge', 'microsoft edge': 'Microsoft Edge',
    'word': 'Word', 'microsoft word': 'Word', 'excel': 'Excel', 'powerpoint': 'PowerPoint',
}


def local_command(question):
    """Only route complete, unambiguous English commands without a model call."""
    text = ' '.join(question.casefold().split()).rstrip('.!?')
    text = re.sub(r'^(?:clydex[, ]+)?(?:(?:can|could|would) you |(?:please|kindly)[, ]+)*', '', text)
    text = re.sub(r'(?: for me|,? please)$', '', text)
    if text in ('which windows are open', 'what windows are open', 'list windows',
                'list open windows', 'list the open windows', 'show open windows'):
        return 'list_windows', '', ''
    match = re.fullmatch(r'(open|launch|start|switch to|focus|minimi[sz]e|maximi[sz]e|restore) '
                         r'(?:the )?(.+?)(?: window)?', text)
    if not match:
        return None
    verb, name = match.groups()
    target = APP_NAMES.get(name)
    if not target:
        if verb in ('open', 'launch', 'start') or not re.fullmatch(r'window [1-9]\d?', name):
            return None
        target = name
    if verb in ('open', 'launch', 'start'):
        return 'open_app', target, ''
    return 'manage_window', target, 'focus' if verb == 'switch to' else verb.replace('ise', 'ize')


