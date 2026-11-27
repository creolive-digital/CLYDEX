"""One owned adapter to the existing Tk time tools, shared by every HUD view.

The standalone fallback remains independent; switching HUD modes never launches
it or restarts timers. Tk objects are created, used and disposed on their owner.
Weather uses the existing implementation only after an explicit reviewed request.
"""
from concurrent.futures import Future
from datetime import datetime
import gc
import queue
import threading
import time


class WidgetService:
    def __init__(self):
        self._closed = threading.Event()
        self._ready = threading.Event()
        self._lock = threading.RLock()
        self._queue = queue.Queue(maxsize=8)
        self._thread = None
        self._state = dict(status='not_started', alerts=[], weather='Not requested')

    def start(self) -> None:
        with self._lock:
            if self._closed.is_set():
                raise RuntimeError('Widget tools are closed.')
            if self._thread is None:
                self._thread = threading.Thread(target=self._run, name='clydex-time-tools', daemon=True)
                self._thread.start()

    def snapshot(self) -> dict:
        with self._lock:
            return dict(self._state, alerts=list(self._state['alerts']))

    def action(self, values: dict, cancel) -> dict:
        self.start()
        cancel.check()
        future = Future()
        self._queue.put_nowait((future, values, cancel))
        try:
            return future.result(30)  # Existing weather has two bounded native requests.
        except TimeoutError:
            future.cancel()
            raise RuntimeError('Time tools have not completed; native work remains owned.') from None

    def _run(self):
        widget = None
        try:
            from clydex.desktop.widget import ClydexWidget
            class AdaptedWidget(ClydexWidget):
                def request_weather(self):
                    pass  # No startup/periodic network; explicit adapter command only.

                def show_alert(self):
                    pass  # HUD displays the actual alert list, without a second window/bell.

                def update_clock(self):
                    pass  # The adapter's single pump owns ticking, not a hidden animation loop.

            widget = AdaptedWidget()
            widget.root.withdraw()
            self._ready.set()

            def publish():
                now = time.monotonic()
                widget.update_tools(now, datetime.now())
                elapsed = widget.stopwatch_elapsed + (now - widget.stopwatch_start if widget.stopwatch_start else 0)
                remaining = max(0, widget.timer_end - now) if widget.timer_end else widget.timer_remaining
                with self._lock:
                    self._state = dict(status='ready', timer_remaining=remaining,
                        timer_duration=widget.timer_duration, timer_running=widget.timer_end is not None,
                        alarm_at=widget.alarm_at.isoformat() if widget.alarm_at else None,
                        stopwatch_elapsed=elapsed, stopwatch_running=widget.stopwatch_start is not None,
                        lap_count=widget.lap_count, lap=widget.lap_text.get(), alerts=list(widget.alerts),
                        city=widget.city, weather=widget.condition.cget('text'), temperature=widget.temp.cget('text'),
                        weather_status=widget.status.cget('text'), weather_metrics=widget.metrics.cget('text'))

            def pump():
                if self._closed.is_set():
                    widget.root.destroy()
                    return
                try:
                    future, values, cancel = self._queue.get_nowait()
                except queue.Empty:
                    pass
                else:
                    try:
                        cancel.check()
                        if future.set_running_or_notify_cancel():
                            op = values['operation']
                            if op == 'timer.set':
                                widget.set_duration(values['seconds'])
                            elif op == 'alarm.set':
                                widget.alarm_hour.set(str(values['hour']))
                                widget.alarm_minute.set(str(values['minute']))
                                widget.set_alarm(None)
                                widget.toggle_alarm()
                            elif op == 'weather':
                                widget.city = values['city']
                                widget.fetch_weather(widget.city)
                                # Consume the same existing results path without scheduling another loop.
                            else:
                                functions = {'timer.toggle': widget.toggle_timer, 'timer.reset': widget.reset_timer,
                                    'alarm.cancel': lambda: widget.set_alarm(None), 'stopwatch.toggle': widget.toggle_stopwatch,
                                    'stopwatch.reset': widget.reset_stopwatch, 'stopwatch.lap': widget.mark_lap,
                                    'alert.dismiss': widget.dismiss_alert, 'alarm.snooze': widget.snooze}
                                functions[op]()
                            cancel.check()
                            publish()
                            future.set_result(self.snapshot())
                    except Exception as exc:
                        if not future.done():
                            future.set_exception(exc)
                publish()
                widget.root.after(100, pump)
            widget.root.after(0, pump)
            widget.root.mainloop()
        except Exception:
            with self._lock:
                self._state = dict(status='unavailable', alerts=[], weather='Unavailable')
            self._ready.set()
        finally:
            if widget:
                try:
                    widget.root.destroy()
                except Exception:
                    pass
            widget = None
            gc.collect()
            while not self._queue.empty():
                future, _, _ = self._queue.get_nowait()
                if not future.done():
                    future.set_exception(RuntimeError('Time tools stopped.'))

    def close(self) -> None:
        self._closed.set()

    def wait_closed(self) -> None:
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join()
