"""Minimal validated WebView facade to the existing Studio/Core services.

One owned collector consumes the legacy event channel. Native mode/approval
visibility and private transient state do not depend on browser timer execution.
"""
from dataclasses import asdict, replace
import copy
import json
import mimetypes
from pathlib import Path
import threading
import time

from clydex.core.contracts import canonical_json
from clydex.core.errors import PermissionDenied
from clydex.core.settings import read_settings, write_settings
from clydex.desktop.display import DisplayController
from clydex.desktop.notifications import NotificationCenter
from clydex.desktop.preferences import DesktopPreferences
from clydex.desktop.system_info import SystemInformation
from clydex.desktop.tray import SystemTray
from clydex.desktop.widget_service import WidgetService
from clydex.security.permissions import TOOL_SPECS

CONTRACT = json.loads(Path(__file__).with_name('hud_contract.json').read_text(encoding='utf-8'))


def validate_packet(group: str, name: str, values: dict) -> dict:
    schema = CONTRACT[group].get(name)
    if schema is None or not isinstance(values, dict) or set(values) - set(schema):
        raise ValueError('Unknown bridge operation or fields.')
    if len(canonical_json(values).encode('utf-8')) > 65536:
        raise ValueError('Bridge request exceeds its bound.')
    types = {'string': str, 'boolean': bool, 'integer': int, 'object': dict, 'array': list}
    for key, kind in schema.items():
        if key not in values:
            if kind.endswith('?'):
                continue
            raise ValueError('Missing bridge argument.')
        if type(values[key]) is not types[kind.rstrip('?')]:
            raise ValueError('Invalid bridge argument type.')
    return json.loads(canonical_json(values))


class HudService:
    def __init__(self, studio, *, display=None, widget=None, start=True):
        # Windows registry associations can classify .js as text/plain. ES modules
        # require a JavaScript MIME type in WebView2's local static-asset server.
        mimetypes.init()
        for suffix, mime in (('.js', 'text/javascript'), ('.mjs', 'text/javascript'),
                             ('.css', 'text/css'), ('.ttf', 'font/ttf'), ('.json', 'application/json')):
            mimetypes.add_type(mime, suffix)
        self.studio, self.core = studio, studio._core
        self.preferences = DesktopPreferences(self.core.paths)
        self.core.cloud.apply_theme = self.preferences.configure
        self.display = display or DisplayController(studio, self.core.paths)
        self.widget = widget or WidgetService()
        self.system = SystemInformation()
        self.notifications = NotificationCenter()
        if hasattr(self.core, 'operating'):
            self.system = self.core.operating.system
            self.core.operating.notify = self._notify
            self.core.operating.quiet = lambda: self.preferences.values.dnd or self.core.personality.config.mode in ('focus', 'gaming')
            self.core.operating.capture_indicator = self._capture_indicator
        self._lock, self._closed = threading.RLock(), threading.Event()
        self._thread = None
        self._chat, self._revision, self._last_busy = [], 0, False
        self._last_review, self._last_alert_count, self._greeted = None, 0, False
        self._playback = dict(frames_played=0, sample_rate=None, completed=None)
        self._frame = None
        self._started = time.monotonic()
        self._scope_path = self.core.paths.directory('settings') / 'desktop-permissions.json'
        self._apply_scopes(read_settings(self._scope_path).get('disabled_scopes', []))
        self.core.register_resource(self)
        studio._open_voice_window = self.show
        studio._activations.actions['open'] = self.show
        if start:
            self._thread = threading.Thread(target=self._run, name='clydex-hud-events', daemon=True)
            self._thread.start()

    def show(self):
        if self.display.window is not None:
            self.display.change('window')

    def _apply_scopes(self, scopes):
        known = {s.scope for s in TOOL_SPECS}
        if not isinstance(scopes, list) or any(type(s) is not str or s not in known for s in scopes):
            raise ValueError('Invalid disabled capability scopes.')
        # The startup policy is always an upper bound, including when preferences are edited.
        self.core.engine.executor._disabled_scopes = frozenset(self.core.config.disabled_scopes) | frozenset(scopes)

    def _notify(self, code):
        if self.core.voice.privacy.refresh():
            return
        self.notifications.add(code)
        preferences = self.preferences.values
        if preferences.native_notifications and not preferences.dnd and self.core.personality.config.mode not in ('focus', 'gaming'):
            self.native_notification()

    def native_notification(self) -> bool:
        if self.core.voice.privacy.refresh() or self.preferences.values.dnd:
            return False
        for service in self.studio._activations._services:
            if isinstance(service, SystemTray):
                return service.notify()
        return False

    def collect(self) -> None:
        frame = self.studio.snapshot()
        with self._lock:
            if frame['voice']['locked']:
                self.core.cloud.lock()
                self.core.operating.stop(clear=True)
                self._chat.clear()
                self.notifications.clear()
                frame.update(messages=[], intelligence_events=[], voice_events=[], level=0, bands=[], wave=[], review=None)
            else:
                for role, text in frame['messages']:
                    if role in ('user', 'bot', 'error', 'mic_info'):
                        self._chat.append(dict(role=role, text=text, id=f'{time.monotonic_ns()}-{len(self._chat)}'))
                self._chat = self._chat[-100:]
                for kind, value in frame['intelligence_events']:
                    if kind == 'intelligence_result':
                        self._revision += 1
                        if value.get('clear'):
                            self._chat.clear()
                        if 'transcript' in value:
                            self._chat = [dict(role='user' if x['role'] == 'user' else 'bot', text=x['content'],
                                               id=f'resumed-{i}') for i, x in enumerate(value['transcript'][-100:])]
                for kind, event in frame['voice_events']:
                    if kind == 'voice_event' and event['kind'] in ('warning', 'error'):
                        self._notify('voice.warning')
                    if kind == 'voice_event' and event['kind'] == 'playback_started':
                        self._playback = dict(frames_played=0, sample_rate=event['details']['sample_rate'], completed=None)
                    if kind == 'voice_event' and event['kind'] == 'playback_stopped':
                        self._playback.update(frames_played=event['details']['frames_played'], completed=event['details']['completed'])
                if self._last_busy and not frame['busy']:
                    state = frame['voice']['state']
                    self._notify('task.error' if state == 'error' else 'task.interrupted' if state == 'interrupted' else 'task.complete')
                review = frame['review']
                if review and review['id'] != self._last_review:
                    self._notify('approval.waiting')
                    self._last_review = review['id']
                count = len(self.widget.snapshot()['alerts'])
                if count > self._last_alert_count:
                    self._notify('timer.alert')
                self._last_alert_count = count
            self._last_busy = frame['busy']
            self._frame = frame
        if frame['review'] and self.display.window is not None:
            self.display.show_review()

    def _run(self):
        while not self._closed.wait(.1):
            try:
                self.collect()
            except Exception:
                # Fail closed on collector/native window failures; never leak exception text.
                self.core.voice.mute()

    def snapshot(self) -> dict:
        locked = self.core.voice.privacy.refresh()
        with self._lock:
            frame = copy.deepcopy(self._frame) if self._frame else dict(state='STARTING', busy=False, recording=False,
                voice=self.core.voice.snapshot(), review=None, level=0, bands=[], wave=[], voice_events=[])
            if locked:
                self._chat.clear()
                self.notifications.clear()
                return dict(version=1, locked=True, voice=self.core.voice.snapshot(), display=self.display.snapshot(),
                            preferences=asdict(self.preferences.values), messages=[], notifications=[], review=None)
            return dict(version=1, locked=False, state=frame['state'], busy=frame['busy'], recording=frame['recording'],
                voice=frame['voice'], review=frame['review'], level=frame['level'], bands=frame['bands'], wave=frame['wave'],
                voice_events=frame.get('voice_events', []), messages=copy.deepcopy(self._chat), revision=self._revision,
                playback=dict(self._playback),
                notifications=self.notifications.snapshot(), preferences=asdict(self.preferences.values),
                display=self.display.snapshot(), system=self.system.sample(), uptime_seconds=time.monotonic() - self._started,
                provider=copy.deepcopy(self.core.engine.intelligence.state) if self.core.engine.intelligence else {},
                session=dict(temporary=self.core.conversations.current.temporary, title=self.core.conversations.current.title),
                personality=self.core.personality.config.mode,
                operating_revision=self.core.operating.revision,
                language=self.core.voice.config.recognition_language,
                widget=self.widget.snapshot())

    def read(self, section: str, params: dict) -> dict | list | str:
        params = validate_packet('read', section, params)
        if self.core.voice.privacy.refresh():
            raise PermissionDenied('Desktop is locked.')
        functions = {'intelligence': self.studio.intelligence_settings, 'voice': self.studio.voice_settings,
                     'memories': self.studio.memories}
        if section in functions:
            return functions[section]()
        if section == 'bootstrap':
            with self.core.store.connect() as connection:
                schema_version = connection.execute('PRAGMA user_version').fetchone()[0]
            return dict(version=1, contract=CONTRACT, initialization=[
                dict(component='Core', status='ready', detail='Owned per-user Core and supervised queue'),
                dict(component='Configuration', status='ready', detail='Validated local settings loaded'),
                dict(component='Database', status='ready', detail=f'Schema {schema_version}'),
                dict(component='Voice', status='gated', detail='Local runtime ready; models and microphone need consent'),
                dict(component='Providers', status='unverified', detail='Configured locally; no network probe or inference')],
                identity=dict(logo='owner reference', avatar='owner reference image', rigged_model=False),
                preferences=asdict(self.preferences.values), display=self.display.snapshot())
        if section == 'conversations':
            return self.studio.conversations(params.get('query', ''))
        if section == 'export':
            return self.studio.export_conversation(params.get('id'))
        if section == 'preferences':
            return asdict(self.preferences.values)
        if section == 'permissions':
            return dict(scopes=[dict(scope=s, disabled=s in self.core.engine.executor._disabled_scopes,
                startup_disabled=s in self.core.config.disabled_scopes) for s in sorted({s.scope for s in TOOL_SPECS})],
                cloud_allowed=self.core.config.allow_cloud, privacy_ceiling=self.core.config.privacy_mode)
        if section == 'cloud':
            if self.core.queue.busy:
                return {'busy': True}
            return self.core.cloud.snapshot()
        if section == 'operating':
            return self.core.operating.snapshot()
        self.widget.start()
        return self.widget.snapshot()

    def command(self, action: str, values: dict) -> object:
        values = validate_packet('command', action, values)
        if action == 'voice.stop':
            return self.studio.stop()
        if action == 'voice.mute' and values['muted']:
            return self.studio.mute_microphone(True)
        if self.core.voice.privacy.refresh():
            raise PermissionDenied('Desktop is locked.')
        s = self.studio
        functions = {
            'chat.send': lambda: s.send(values['message']), 'chat.clear': self._clear_chat,
            'voice.capture': lambda: s.microphone(values.get('check', False)),
            'voice.mute': lambda: s.mute_microphone(values['muted']), 'voice.test': s.test_voice,
            'voice.arm': s.arm_voice_wake, 'voice.configure': lambda: s.configure_voice(values['values']),
            'voice.download': lambda: s.download_speech_model(values['model']),
            'personality.configure': lambda: s.configure_personality(values['values'], values.get('address')),
            'provider.configure': lambda: s.configure_provider(values['name'], values['values'], values.get('secret'), values.get('remove_key', False)),
            'provider.check': lambda: s.check_provider(values['name']),
            'routing.configure': lambda: s.configure_routing(values['values']),
            'conversation.manage': lambda: s.conversation_action(values['values']),
            'conversation.resume': lambda: s.resume_conversation(values['id']),
            'memory.manage': lambda: s.memory_action(values['values']),
            'memory.configure': lambda: s.configure_memory(values['values']),
            'approval.decide': lambda: s.decide(values['id'], values['approve']),
            'display.mode': lambda: self._mode(values['mode']),
            'display.monitor': lambda: self.display.select_monitor(values['index']),
            'preferences.configure': lambda: self._configure(values['values']),
            'permissions.configure': lambda: self._permissions(values['disabled_scopes']),
            'widget.action': lambda: self._widget_action(values),
            'notifications.clear': lambda: self.notifications.clear() or True,
            'notifications.native_test': lambda: self.native_notification() if self.preferences.values.native_notifications else False,
            'startup.greet': self._greet,
            'cloud.configure': lambda: s._intelligence_work(lambda: self.core.cloud.configure(values['values'])),
            'cloud.action': lambda: s._intelligence_work(lambda: self.core.cloud.execute(values['operation'], values['values'])),
            'knowledge.select': lambda: self._select_knowledge(values.get('folder', False)),
            'operating.action': lambda: s._intelligence_work(lambda: self.core.operating.execute(values['operation'], values['values'])),
            'operating.select': lambda: self._select_operating(values['kind']),
        }
        return functions[action]()

    def _capture_indicator(self, active):
        if self.display.window is None or not self.core.voice.privacy.visible or self.core.voice.privacy.refresh():
            return False
        self.display.window.set_title('CLYDEX · CAPTURE ACTIVE' if active else 'CLYDEX · Your Personal Digital Intelligence')
        return True

    def _select_operating(self, kind):
        if kind not in ('file', 'folder', 'script', 'plugin') or self.core.queue.busy or self.display.window is None:
            return False
        import webview
        paths = self.display.window.create_file_dialog(webview.FileDialog.FOLDER if kind in ('folder', 'plugin') else webview.FileDialog.OPEN,
                                                      allow_multiple=False)
        if not paths or self.core.voice.privacy.refresh():
            return False
        self.core.operating.selections.add(paths[0], kind)
        self.core.operating.revision += 1
        return True

    def _select_knowledge(self, folder):
        if self.core.queue.busy or self.display.window is None:
            return False
        import webview
        paths = self.display.window.create_file_dialog(webview.FileDialog.FOLDER if folder else webview.FileDialog.OPEN,
                                                      allow_multiple=not folder)
        if not paths:
            return False
        if self.core.voice.privacy.refresh():
            return False
        return self.core.cloud.selection(paths, folder=folder)

    def _clear_chat(self):
        if not self.studio.clear():
            return False
        with self._lock:
            self._chat.clear()
        return True

    def _mode(self, mode):
        if mode == 'widget':
            self.widget.start()
        return self.display.change(mode)

    def _configure(self, values):
        replace(self.preferences.values, **values)
        return self.studio._intelligence_work(lambda: self.core.engine.execute_tool('desktop.configure',
            'local presentation and notification preferences', {'values': values},
            lambda a: self.preferences.configure(a['values']),
            'Apply these presentation preferences? Optional startup speech/sounds remain local. No microphone or AI provider is enabled.'))

    def _permissions(self, scopes):
        known = {s.scope for s in TOOL_SPECS}
        if any(type(x) is not str or x not in known for x in scopes):
            raise ValueError('Invalid capability scope.')
        def apply(a):
            self._apply_scopes(a['disabled_scopes'])
            write_settings(self._scope_path, a)
            return a
        return self.studio._intelligence_work(lambda: self.core.engine.execute_tool('permissions.configure',
            'local disabled capabilities', {'disabled_scopes': scopes}, apply,
            'Change these runtime capability restrictions? Startup-disabled scopes remain disabled. No model can grant a scope.'))

    def _widget_action(self, values):
        op = values['operation']
        allowed = ('timer.set', 'timer.toggle', 'timer.reset', 'alarm.set', 'alarm.cancel', 'stopwatch.toggle',
                   'stopwatch.reset', 'stopwatch.lap', 'alert.dismiss', 'alarm.snooze', 'weather')
        if op not in allowed:
            raise ValueError('Unknown time-tool operation.')
        if op == 'timer.set' and not 1 <= values.get('seconds', 0) <= 86400:
            raise ValueError('Timer duration must be 1 second to 24 hours.')
        if op == 'alarm.set' and not (0 <= values.get('hour', -1) <= 23 and 0 <= values.get('minute', -1) <= 59):
            raise ValueError('Invalid local alarm time.')
        if op == 'weather' and (not values.get('city', '').strip() or len(values['city']) > 100):
            raise ValueError('Choose a city for the weather request.')
        return self.studio._intelligence_work(lambda: self.core.engine.execute_tool(
            'widget.weather' if op == 'weather' else 'widget.control', 'owned local time tools', {'values': values},
            lambda a: self.widget.action(a['values'], self.core.engine.cancel_token),
            'Weather transmits the displayed city to Open-Meteo. Other time tools run locally.'))

    def _greet(self):
        if self._greeted or not self.preferences.values.startup_greeting:
            return False
        self._greeted = True
        return self.studio._start('PREPARING SPEECH', lambda: self.core.engine.speak_with_audio_meter('Clydex is ready for your next request.'))

    def close(self):
        self._closed.set()
        self.display.close()
        self.widget.close()

    def wait_closed(self):
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join()
        self.widget.wait_closed()


class HudBridge:
    """The only object exposed to the new frontend. No general method dispatch."""
    def __init__(self, service: HudService):
        self._service = service

    def hud_snapshot(self) -> dict:
        return self._service.snapshot()

    def hud_read(self, section: str, params: dict | None = None) -> dict:
        try:
            return {'ok': True, 'data': self._service.read(section, {} if params is None else params)}
        except Exception:
            return {'ok': False, 'error': 'Read unavailable, locked, busy or invalid.'}

    def hud_command(self, action: str, payload: dict | None = None) -> dict:
        try:
            return {'ok': bool(self._service.command(action, {} if payload is None else payload))}
        except Exception:
            return {'ok': False, 'error': 'Request rejected. Check values, permissions and native availability.'}
