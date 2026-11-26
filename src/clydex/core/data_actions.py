"""Exact-action local data operations; only current user/UI input reaches these methods."""
import re

from clydex.core.errors import PermissionDenied
from clydex.memory.models import CATEGORIES
from clydex.security.content import validate_private_text


class OwnedDataActions:
    def __init__(self, engine, conversations, memory):
        self.engine, self.conversations, self.memory = engine, conversations, memory

    def reset_context(self):
        self.engine.history.clear()
        self.engine.history_local_only = False
        self.engine.apps.clear()
        self.engine.inbox.messages.clear()

    def conversation(self, values: dict) -> dict:
        args = dict(operation='', id='', title='', persistent=False, days=0)
        if not isinstance(values, dict) or set(values) - set(args):
            raise ValueError('Invalid conversation action.')
        args.update(values)
        operation = args['operation']
        if operation not in ('new', 'rename', 'archive', 'unarchive', 'delete', 'retention'):
            raise ValueError('Invalid conversation operation.')
        if operation in ('new', 'rename'):
            validate_private_text(args['title'], 120)
        if operation not in ('new', 'retention'):
            self.conversations.repository.get(args['id'])

        def perform(a):
            repo = self.conversations.repository
            if a['operation'] == 'new':
                result = self.conversations.new(a['title'], a['persistent'], consent=True)
                self.reset_context()
                return result
            if a['operation'] == 'retention':
                previous = self.conversations.current.id
                repo.set_retention(a['days'] or None)
                self.conversations.purge_expired()
                if previous != self.conversations.current.id:
                    self.reset_context()
                return {'retention_days': a['days'] or None}
            if a['operation'] == 'rename':
                repo.update(a['id'], title=a['title'])
            else:
                status = {'archive': 'archived', 'unarchive': 'active', 'delete': 'deleted'}[a['operation']]
                repo.update(a['id'], status=status)
            if a['id'] == self.conversations.current.id:
                if a['operation'] == 'delete':
                    self.conversations.new('Temporary conversation', False)
                    self.reset_context()
                else:
                    self.conversations.current = repo.get(a['id'])
            return {'operation': a['operation'], 'id': a['id']}
        return self.engine.execute_tool('conversation.manage', args['id'] or 'owned local history', args,
                                       perform, 'Apply this local conversation change? Persistent text is encrypted.')

    def memory_action(self, values: dict) -> dict:
        args = dict(operation='', id='', category='facts', value='', local_only=True, revision=0,
                    origin='explicit', source_id='', source_kind='manual_ui')
        if not isinstance(values, dict) or set(values) - set(args):
            raise ValueError('Invalid memory action.')
        args.update(values)
        if args['operation'] not in ('add', 'update', 'delete', 'accept', 'dismiss'):
            raise ValueError('Invalid memory operation.')
        if args['operation'] in ('add', 'update'):
            validate_private_text(args['value'], 2000)
        if args['operation'] in ('update', 'delete'):
            current = self.memory.repository.get(args['id'])
            args.update(category=current['category'], origin=current['origin'], source_id=current['source_id'],
                        source_kind=current['source_kind'])
            if args['operation'] == 'delete':
                args.update(value=current['value'], revision=current['revision'], local_only=current['local_only'])
        if args['operation'] in ('accept', 'dismiss'):
            proposal = self.memory.pending.get(args['id'])
            if proposal is None:
                raise PermissionDenied('Memory proposal is unavailable.')
            args.update(category=proposal['category'], value=proposal['value'], origin='inferred',
                        source_id=proposal['source_id'], source_kind='user_prompt')

        def perform(a):
            if a['operation'] == 'add':
                return self.memory.remember(a['category'], a['value'], consent=True, local_only=a['local_only'],
                                            source_kind=a['source_kind'], source_id=a['source_id'])
            if a['operation'] == 'update':
                return self.memory.repository.update(a['id'], a['value'], local_only=a['local_only'],
                                                      revision=a['revision'])
            if a['operation'] == 'delete':
                current = self.memory.repository.get(a['id'])
                if current['revision'] != a['revision']:
                    raise PermissionDenied('Memory changed after review.')
                self.memory.repository.delete(a['id'], a['revision'])
                return {'deleted': a['id']}
            proposal = self.memory.pending.get(a['id'])
            if proposal is None or proposal['value'] != a['value'] or proposal['source_id'] != a['source_id']:
                raise PermissionDenied('Memory proposal changed after review.')
            if a['operation'] == 'dismiss':
                self.memory.pending.pop(a['id'])
                return {'dismissed': a['id']}
            return self.memory.accept(a['id'], consent=True, local_only=a['local_only'])
        return self.engine.execute_tool('memory.manage', args['id'] or 'new ' + args['category'] + ' memory',
                                       args, perform, 'Apply this exact local memory change?')

    def configure_memory(self, values: dict) -> dict:
        if not isinstance(values, dict) or set(values) != {'enabled', 'automatic', 'categories'}:
            raise ValueError('Invalid memory policy.')
        def perform(a):
            self.memory.configure(a['enabled'], a['automatic'], a['categories'], consent=True)
            return self.memory.policy()
        return self.engine.execute_tool('memory.configure', 'owned local memory policy', values, perform,
            'Change memory policy? Automatic suggestions use only literal current-user statements, '
            'and each proposed memory still requires review before saving.')

    def command(self, question: str) -> str | None:
        text = question.strip().rstrip('.?!')
        if text.casefold() in ('what do you remember about me', 'what do you remember', 'show my memories'):
            self.engine.turn_sensitive = True
            self.engine.history_local_only = True
            records = self.memory.repository.list()
            return ('No saved memories.' if not records else '\n'.join(
                f"{r['id']} [{r['category']}, {'local only' if r['local_only'] else 'cloud review required'}]: {r['value']}"
                for r in records[:30]))
        match = re.fullmatch(r'remember this\s*:\s*(.+)', text, re.IGNORECASE)
        if match:
            self.engine.history_local_only = True
            value = match[1]
            category, separator, body = value.partition(':')
            if not separator or category.strip().casefold() not in CATEGORIES:
                category, body = 'facts', value
            saved = self.memory_action(dict(operation='add', category=category.strip().casefold(), value=body.strip(),
                                             source_id=self.engine._request_context.request_id, source_kind='user_prompt'))
            return 'Saved local-only memory ' + saved['id'] + '. You can review or forget it in Memory.'
        match = re.fullmatch(r'update this memory\s+([a-f0-9-]{36})\s*:\s*(.+)', text, re.IGNORECASE)
        if match:
            self.engine.history_local_only = True
            current = self.memory.repository.get(match[1])
            self.memory_action(dict(operation='update', id=match[1], value=match[2],
                                    revision=current['revision'], local_only=current['local_only']))
            return 'Updated that memory.'
        match = re.fullmatch(r'forget this information\s+([a-f0-9-]{36})', text, re.IGNORECASE)
        if match:
            self.memory_action(dict(operation='delete', id=match[1]))
            return 'Forgot that memory.'
        if text.casefold() in ('remember this', 'update this memory', 'forget this information'):
            return 'Give the information after “Remember this:”, or use a memory ID from Memory to update or forget it.'
        return None
