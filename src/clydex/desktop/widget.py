"""CLYDEX Mini — a desktop flip clock, timer, alarm and stopwatch.
Python 3 standard library only. Run: python scripts/windows/clydex_widget.pyw
Right-click for settings; drag anywhere on the header to move.
"""
import json
import subprocess
import sys
from pathlib import Path
import math
import queue
import threading
import time
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from clydex.desktop.theme import StudioSkin
from datetime import datetime, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen

RESOURCE_ROOT = (Path(sys._MEIPASS) if getattr(sys, 'frozen', False)
                 else Path(__file__).resolve().parents[3])
ASSETS = RESOURCE_ROOT / 'frontend' / 'legacy'
BG = '#171d1e'
PANEL = '#252b2d'
CYAN = '#4cd7f6'
LIGHT = '#dee3e6'
MUTED = '#bcc9cd'
OUTLINE = '#3d494c'
TOP = '#252b2d'
BOTTOM = '#1b2122'
AMBER = '#ffc788'

WEATHER_CODES = {
 0:'CLEAR',1:'MOSTLY CLEAR',2:'PARTLY CLOUDY',3:'OVERCAST',45:'FOG',48:'FOG',
 51:'DRIZZLE',53:'DRIZZLE',55:'DRIZZLE',56:'FREEZING RAIN',57:'FREEZING RAIN',
 61:'LIGHT RAIN',63:'RAIN',65:'HEAVY RAIN',66:'FREEZING RAIN',67:'FREEZING RAIN',
 71:'LIGHT SNOW',73:'SNOW',75:'HEAVY SNOW',77:'SNOW',80:'RAIN SHOWERS',81:'RAIN SHOWERS',
 82:'HEAVY SHOWERS',85:'SNOW SHOWERS',86:'SNOW SHOWERS',95:'THUNDERSTORM',
 96:'THUNDERSTORM',99:'THUNDERSTORM'
}

def blend(a,b,t):
    x=[int(a[i:i+2],16) for i in (1,3,5)]
    y=[int(b[i:i+2],16) for i in (1,3,5)]
    return '#%02x%02x%02x'%tuple(round(p*(1-t)+q*t) for p,q in zip(x,y))

class SplitPair(tk.Frame):
    """A printed pair of numerals on two clipped leaves with a shared hinge."""
    def __init__(self, parent, width, height, type_size, ink):
        super().__init__(parent, width=width, height=height, bg='#090f11', bd=0)
        self.width = width
        self.half_height = height // 2
        self.ink = ink
        self.typeface = ('Space Grotesk', -type_size, 'bold')
        self.value = '00'
        self.job = None
        self.top = self.leaf(TOP, self.half_height)
        self.bottom = self.leaf(BOTTOM, 0)
        self.top.place(x=0, y=0, width=width, height=self.half_height-1)
        self.bottom.place(x=0, y=self.half_height, width=width, height=self.half_height)
        self.fold = self.leaf(TOP, self.half_height)

    def leaf(self, color, center):
        pane = tk.Canvas(self, bg=color, highlightthickness=0, bd=0)
        pane.create_text(self.width/2, center, tags='number', text=self.value,
                         fill=self.ink, font=self.typeface)
        return pane

    def set(self, value, animated):
        if self.value == value and animated:
            return
        if self.job is not None:
            self.after_cancel(self.job)
            self.job = None
        previous, self.value = self.value, value
        self.top.itemconfigure('number', text=value)
        self.bottom.itemconfigure('number', text=previous if animated else value)
        if animated:
            self.animate(previous, 0)
        else:
            self.fold.place_forget()

    def animate(self, previous, frame):
        progress = frame / 10
        if frame == 10:
            self.bottom.itemconfigure('number', text=self.value)
            self.fold.place_forget()
            self.job = None
            return
        rising = progress < .5
        projection = abs(math.cos(math.pi * progress))
        height = max(1, round((self.half_height-1)*projection))
        self.fold.configure(bg=blend('#090f11', TOP, projection))
        self.fold.itemconfigure('number', text=previous if rising else self.value,
                                fill=blend('#394147', self.ink, projection))
        self.fold.coords('number', self.width/2, height if rising else 0)
        self.fold.place(x=0, y=self.half_height-height-1 if rising else self.half_height,
                        width=self.width, height=height)
        self.job = self.after(20, self.animate, previous, frame+1)


class ClydexWidget:
    def __init__(self):
        if sys.platform == 'win32':
            # Make the Studio fonts available to this widget process.
            import ctypes
            for filename in ('grotesk.ttf', 'ubuntu.ttf'):
                ctypes.windll.gdi32.AddFontResourceExW(str(ASSETS/filename), 0x10, None)
        self.root=tk.Tk()
        self.icons = {name:tk.PhotoImage(file=str(ASSETS/f'mini-{name}.png'))
                      for name in ('neurology', 'graphic_eq', 'settings', 'cloud', 'calendar_month')}
        style = ttk.Style(self.root)
        style.theme_use('clam')
        self.skin = StudioSkin(self.root,style)
        self.agent_style = self.skin.button('MiniAgent',BG,CYAN,'#003640')
        self.settings_style = self.skin.button('MiniSettings',BG,PANEL,MUTED)
        style.configure(self.agent_style,font=('Space Grotesk',-11,'bold'),padding=(4,0))
        style.configure(self.settings_style,padding=0)
        self.selected_preset_style = 'Selected.' + self.settings_style
        style.configure(self.selected_preset_style, foreground=CYAN)
        self.root.title('CLYDEX // DESKTOP WIDGET')
        self.root.geometry('+70+70')
        self.root.resizable(False,False)
        self.root.configure(bg=BG)
        self.root.overrideredirect(True)
        self.root.attributes('-topmost',True)
        self.on_top=True
        self.mode24=True
        self.last=None
        self.city='Colombo'
        self.dataq=queue.Queue()
        self.loading=False
        self.drag_origin=None
        self.compact = True
        self.page = 'Clock'
        self.timer_duration = 25 * 60
        self.timer_remaining = self.timer_duration
        self.timer_end = None
        self.alarm_at = None
        self.stopwatch_start = None
        self.stopwatch_elapsed = 0
        self.lap_count = 0
        self.alerts = []
        self.shell = tk.Frame(self.root, bg=BG, highlightthickness=1, highlightbackground=OUTLINE)
        self.shell.pack(fill='both', expand=True)
        self.header(self.shell).pack(fill='x', padx=12, pady=(8, 7))
        tk.Frame(self.shell, bg=OUTLINE, height=1).pack(fill='x')
        self.content = tk.Frame(self.shell, bg=BG)
        self.content.pack(fill='both', expand=True)
        self.make_ui()
        self.make_watch()
        self.make_tools()
        self.make_navigation()
        self.show_page('Clock')
        self.make_menu()
        self.update_clock()
        self.request_weather()
        self.check_results()
        self.root.bind('<Escape>', self.escape)
        self.root.bind('<Button-3>',self.show_menu)

    def header(self, parent):
        bar = tk.Frame(parent, bg=BG)
        badge = tk.Label(bar, image=self.icons['neurology'], bg=PANEL,
                         highlightthickness=1, highlightbackground=OUTLINE, padx=3, pady=2)
        badge.pack(side='left')
        brand = tk.Label(bar, text='CLYDEX', bg=BG, fg=LIGHT, font=('Space Grotesk',-13,'bold'))
        brand.pack(side='left', padx=(5,0))
        mini = tk.Label(bar, text='MINI', bg=BG, fg=MUTED, font=('Ubuntu',-10))
        mini.pack(side='left', padx=(2,0))
        for item in (bar,badge,brand,mini):
            self.bind_drag(item)
        settings = ttk.Button(bar, image=self.icons['settings'], text='Clock settings',
                              compound='none', style=self.settings_style, cursor='hand2')
        settings.configure(command=lambda:self.menu.tk_popup(
            settings.winfo_rootx(),settings.winfo_rooty()+settings.winfo_height()))
        settings.pack(side='right')
        ttk.Button(bar, text='Agent', image=self.icons['graphic_eq'], compound='left',
                   style=self.agent_style, cursor='hand2', command=self.launch_agent
                   ).pack(side='right', padx=(0,5))
        return bar

    def bind_drag(self, widget):
        widget.bind('<ButtonPress-1>',self.drag_start)
        widget.bind('<B1-Motion>',self.drag_motion)

    def make_ui(self):
        main = self.full_face = tk.Frame(self.content,bg=BG)
        clock = tk.Frame(main,bg=BG)
        clock.pack(pady=(9,4))
        self.full_pairs = []
        for column,(label,ink) in enumerate((('HOURS',LIGHT),('MINUTES',LIGHT),('SECONDS',CYAN))):
            pair = SplitPair(clock,117,77,84,ink)
            pair.grid(row=0,column=column,padx=3)
            self.full_pairs.append(pair)
            tk.Label(clock,text=label,bg=BG,fg=MUTED,font=('Space Grotesk',-10)
                     ).grid(row=1,column=column,pady=(3,0))
        tk.Frame(main,bg=OUTLINE,height=1).pack(fill='x',padx=16,pady=(2,7))
        weather=tk.Frame(main,bg=BG)
        weather.pack(fill='x',padx=16)
        tk.Label(weather,image=self.icons['cloud'],bg=BG).pack(side='left',padx=(0,5))
        self.temp=tk.Label(weather,text='—',bg=BG,fg=CYAN,font=('Space Grotesk',-30,'bold'))
        self.temp.pack(side='left',padx=(0,12))
        details=tk.Frame(weather,bg=BG)
        details.pack(side='left')
        self.condition=tk.Label(details,text='Updating weather',bg=BG,fg=LIGHT,font=('Ubuntu',-13))
        self.condition.pack(anchor='w')
        self.metrics=tk.Label(details,text='',bg=BG,fg=MUTED,font=('Ubuntu',-11))
        self.metrics.pack(anchor='w')
        self.status=tk.Label(weather,text='',bg=PANEL,fg=CYAN,font=('Space Grotesk',-10),padx=5)
        self.status.pack(side='right')
        footer=tk.Frame(main,bg=BG)
        footer.pack(fill='x',side='bottom',padx=16,pady=8)
        self.city_label=tk.Label(footer,text=self.city.upper(),bg=BG,fg=MUTED,font=('Ubuntu',-12))
        self.city_label.pack(side='left')
        self.date_label=tk.Label(footer,bg=BG,fg=LIGHT,font=('Space Grotesk',-12))
        self.date_label.pack(side='right')
        calendar=tk.Label(footer,image=self.icons['calendar_month'],bg=BG)
        calendar.pack(side='right',padx=(0,4))
        for item in (footer,calendar,self.date_label,self.city_label):
            self.bind_drag(item)

    def make_watch(self):
        face = self.watch = tk.Frame(self.content, bg=BG)
        summary = tk.Frame(face, bg=BG)
        summary.pack(fill='x', padx=16, pady=(10, 6))
        self.watch_date = tk.Label(summary, bg=BG, fg=MUTED, font=('Ubuntu', -12))
        self.watch_date.pack(side='left')
        self.watch_period = tk.Label(summary, bg=BG, fg=MUTED, font=('Space Grotesk', -11))
        self.watch_period.pack(side='right')
        clock = tk.Frame(face, bg=BG)
        clock.pack()
        self.watch_pairs = []
        for col, (width, ink) in enumerate(((99, LIGHT), (99, LIGHT), (74, CYAN))):
            if col:
                tk.Label(clock, text=':', bg=BG, fg=MUTED, font=('Space Grotesk', -19)).pack(side='left')
            pair = SplitPair(clock, width, 56, 58 if col < 2 else 46, ink)
            pair.pack(side='left')
            self.watch_pairs.append(pair)
            for item in (pair,pair.top,pair.bottom,pair.fold):
                self.bind_drag(item)
        weather = tk.Frame(face, bg=BG)
        weather.pack(fill='x', padx=17, pady=(8,0))
        tk.Label(weather, image=self.icons['cloud'], bg=BG).pack(side='left')
        self.watch_weather = tk.Label(weather, bg=BG, fg=LIGHT, font=('Ubuntu', -12))
        self.watch_weather.pack(side='left', padx=4)
        self.watch_condition = tk.Label(weather, bg=BG, fg=MUTED, font=('Ubuntu', -11))
        self.watch_condition.pack(side='right')
        self.bind_drag(face)

    def toggle_size(self):
        self.compact = not self.compact
        self.show_page(self.page)

    def draw_watch_time(self, now):
        self.watch_period.configure(text='24h' if self.mode24 else now.strftime('%p'))
        self.watch_date.configure(text=f"{now:%a, %d %b}")
        city = self.city if len(self.city) <= 15 else self.city[:14] + '…'
        self.watch_weather.configure(text=f"{city}  {self.temp.cget('text')}")
        self.watch_condition.configure(text=self.condition.cget('text').capitalize().rstrip('.'))

    def make_navigation(self):
        tk.Frame(self.shell, bg=OUTLINE, height=1).pack(fill='x')
        nav = tk.Frame(self.shell, bg=BG)
        nav.pack(fill='x', padx=6, pady=(0, 4))
        self.tabs = {}
        for col, name in enumerate(('Clock', 'Timer', 'Alarm', 'Stopwatch')):
            nav.columnconfigure(col, weight=1, uniform='tabs')
            cell = tk.Frame(nav, bg=BG)
            cell.grid(row=0, column=col, sticky='ew')
            indicator = tk.Frame(cell, bg=BG, height=2)
            indicator.pack(fill='x', padx=8)
            button = tk.Button(cell, text=name, command=lambda n=name:self.show_page(n),
                               bg=BG, fg=MUTED, activebackground=PANEL, activeforeground=LIGHT,
                               bd=0, relief='flat', cursor='hand2', highlightthickness=1,
                               highlightbackground=BG, highlightcolor=CYAN, pady=5,
                               font=('Ubuntu', -12))
            button.pack(fill='x')
            self.tabs[name] = button, indicator

    def show_page(self, name):
        self.page = name
        for child in self.content.winfo_children():
            child.pack_forget()
        face = self.watch if self.compact else self.full_face
        if self.alerts:
            face = self.alert_face
        elif name != 'Clock':
            face = self.tools[name]
        face.pack(fill='both' if name == 'Clock' and not self.alerts else 'none', expand=True)
        for label, (button, indicator) in self.tabs.items():
            selected = label == name and not self.alerts
            indicator.configure(bg=CYAN if selected else BG)
            button.configure(fg=CYAN if selected else MUTED, state='disabled' if self.alerts else 'normal')
        self.root.geometry('336x220' if self.compact else '466x296')
        self.last = None

    def tool_button(self, parent, text, command, primary=False):
        button = ttk.Button(parent, text=text, command=command, cursor='hand2',
                            style=self.agent_style if primary else self.settings_style)
        button.pack(side='left', padx=3, ipadx=7)
        return button

    @staticmethod
    def duration_text(seconds):
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        return f'{hours}:{minutes:02}:{seconds:02}' if hours else f'{minutes:02}:{seconds:02}'

    def make_tools(self):
        self.tools = {name: tk.Frame(self.content, bg=BG) for name in ('Timer', 'Alarm', 'Stopwatch')}
        timer = self.tools['Timer']
        self.timer_text = tk.StringVar(value=self.duration_text(self.timer_duration))
        tk.Label(timer, textvariable=self.timer_text, bg=BG, fg=LIGHT,
                 font=('Space Grotesk', -39, 'bold')).pack(pady=(4,0))
        self.timer_rail = tk.Canvas(timer, width=168, height=3, bg=OUTLINE, bd=0, highlightthickness=0)
        self.timer_rail.pack(pady=(0, 5))
        self.timer_fill = self.timer_rail.create_rectangle(0, 0, 168, 3, fill=CYAN, outline='')
        presets = tk.Frame(timer, bg=BG)
        presets.pack()
        self.preset_buttons = []
        for minutes in (5, 15, 25):
            self.preset_buttons.append(self.tool_button(
                presets, f'{minutes} min', lambda m=minutes:self.set_duration(m * 60)))
        self.preset_buttons.append(self.tool_button(presets, 'Custom…', self.custom_timer))
        self.preset_buttons[2].configure(style=self.selected_preset_style)
        actions = tk.Frame(timer, bg=BG)
        actions.pack(pady=(8,0))
        self.timer_button = self.tool_button(actions, 'Start timer', self.toggle_timer, True)
        self.tool_button(actions, 'Reset', self.reset_timer)

        alarm = self.tools['Alarm']
        self.alarm_note = tk.StringVar(value='Alarm time · 24-hour local time')
        tk.Label(alarm, textvariable=self.alarm_note, bg=BG, fg=MUTED,
                 font=('Ubuntu', -12)).pack(pady=(8,4))
        fields = self.alarm_editor = tk.Frame(alarm, bg=BG)
        fields.pack()
        next_hour = datetime.now() + timedelta(hours=1)
        self.alarm_hour = tk.StringVar(value=f'{next_hour.hour:02}')
        self.alarm_minute = tk.StringVar(value='00')
        for index, (variable, limit) in enumerate(((self.alarm_hour, 23), (self.alarm_minute, 59))):
            if index:
                tk.Label(fields, text=':', bg=BG, fg=AMBER, font=('Space Grotesk', -25)).pack(side='left')
            field = tk.Spinbox(fields, from_=0, to=limit, format='%02.0f', textvariable=variable,
                               width=3, wrap=True, justify='center', relief='flat', bd=0,
                               bg=PANEL, fg=LIGHT,
                               buttonbackground=PANEL, insertbackground=CYAN, highlightthickness=1,
                               highlightbackground=OUTLINE, highlightcolor=CYAN,
                               font=('Space Grotesk', -29, 'bold'))
            field.pack(side='left', ipady=3)
            field.bind('<Return>', lambda e:self.toggle_alarm())
        self.armed_time = tk.Label(alarm, bg=BG, fg=AMBER, font=('Space Grotesk', -36, 'bold'))
        alarm_actions = self.alarm_actions = tk.Frame(alarm, bg=BG)
        alarm_actions.pack(pady=(9,0))
        self.alarm_button = self.tool_button(alarm_actions, 'Set alarm', self.toggle_alarm, True)

        stopwatch = self.tools['Stopwatch']
        self.stopwatch_text = tk.StringVar(value='00:00.0')
        tk.Label(stopwatch, textvariable=self.stopwatch_text, bg=BG, fg=LIGHT,
                 font=('Space Grotesk', -39, 'bold')).pack(pady=(5,0))
        self.lap_text = tk.StringVar()
        tk.Label(stopwatch, textvariable=self.lap_text, bg=BG, fg=MUTED,
                 font=('Ubuntu', -12)).pack()
        watch_actions = tk.Frame(stopwatch, bg=BG)
        watch_actions.pack(pady=(7,0))
        self.stopwatch_button = self.tool_button(watch_actions, 'Start', self.toggle_stopwatch, True)
        self.lap_button = self.tool_button(watch_actions, 'Lap', self.mark_lap)
        self.lap_button.state(['disabled'])
        self.tool_button(watch_actions, 'Reset', self.reset_stopwatch)

        self.alert_face = tk.Frame(self.content, bg=BG)
        self.alert_title = tk.Label(self.alert_face, bg=BG, fg=AMBER, font=('Space Grotesk', -28, 'bold'))
        self.alert_title.pack(pady=(12,1))
        self.alert_detail = tk.Label(self.alert_face, bg=BG, fg=LIGHT, font=('Ubuntu', -13))
        self.alert_detail.pack()
        alert_actions = tk.Frame(self.alert_face, bg=BG)
        alert_actions.pack(pady=9)
        self.dismiss_button = self.tool_button(alert_actions, 'Dismiss', self.dismiss_alert, True)
        self.snooze_button = self.tool_button(alert_actions, 'Snooze 5 min', self.snooze)

    def set_duration(self, seconds):
        self.timer_duration = seconds
        presets = (300, 900, 1500)
        selected = presets.index(seconds) if seconds in presets else 3
        for index, button in enumerate(self.preset_buttons):
            button.configure(style=self.selected_preset_style if index == selected else self.settings_style)
        self.reset_timer()

    def custom_timer(self):
        minutes, seconds = divmod(self.timer_duration, 60)
        value = simpledialog.askstring('Custom timer', 'Duration in minutes or mm:ss',
                                       initialvalue=f'{minutes}:{seconds:02}',
                                       parent=self.root)
        if value is None:
            return
        parts = value.strip().split(':')
        if len(parts) in (1, 2) and all(part.isascii() and part.isdigit() and len(part) <= 4 for part in parts):
            minutes = int(parts[0])
            seconds = int(parts[1]) if len(parts) == 2 else 0
            duration = 60 * minutes + seconds
            if seconds < 60 and 0 < duration <= 24 * 3600:
                self.set_duration(duration)
                return
        messagebox.showerror('Custom timer', 'Enter 1 second to 24 hours, for example 0:30 or 25.', parent=self.root)

    def reset_timer(self):
        self.timer_end = None
        self.timer_remaining = self.timer_duration
        self.timer_text.set(self.duration_text(self.timer_duration))
        self.timer_rail.coords(self.timer_fill, 0, 0, 168, 3)
        self.timer_button.configure(text='Start timer')
        self.tabs['Timer'][0].configure(text='Timer')
        for button in self.preset_buttons:
            button.state(['!disabled'])

    def toggle_timer(self):
        now = time.monotonic()
        if self.timer_end is None:
            self.timer_end = now + (self.timer_remaining or self.timer_duration)
            self.timer_button.configure(text='Pause')
            self.tabs['Timer'][0].configure(text='Timer •')
            for button in self.preset_buttons:
                button.state(['disabled'])
        elif now >= self.timer_end:
            self.update_tools(now, datetime.now())
        else:
            self.timer_remaining = self.timer_end - now
            self.timer_end = None
            self.timer_button.configure(text='Resume')
            self.tabs['Timer'][0].configure(text='Timer')
            for button in self.preset_buttons:
                button.state(['!disabled'])

    def toggle_alarm(self):
        if self.alarm_at is not None:
            self.set_alarm(None)
            return
        try:
            now = datetime.now()
            target = now.replace(hour=int(self.alarm_hour.get()), minute=int(self.alarm_minute.get()),
                                 second=0, microsecond=0)
        except ValueError:
            self.alarm_note.set('Use hours 00–23 and minutes 00–59')
            return
        self.set_alarm(target if target > now else target + timedelta(days=1))

    def set_alarm(self, target):
        self.alarm_at = target
        if target:
            self.alarm_hour.set(f'{target.hour:02}')
            self.alarm_minute.set(f'{target.minute:02}')
            self.armed_time.configure(text=f'{target:%H:%M}')
            self.alarm_editor.pack_forget()
            self.armed_time.pack(before=self.alarm_actions)
        else:
            self.armed_time.pack_forget()
            self.alarm_editor.pack(before=self.alarm_actions)
        self.alarm_note.set(f'Alarm set · {target:%a, %d %b}' if target else 'Alarm time · 24-hour local time')
        self.alarm_button.configure(text='Cancel alarm' if target else 'Set alarm')
        self.tabs['Alarm'][0].configure(text='Alarm •' if target else 'Alarm')

    def stopwatch_value(self, now):
        elapsed = self.stopwatch_elapsed
        if self.stopwatch_start is not None:
            elapsed += now - self.stopwatch_start
        return f'{self.duration_text(elapsed)}.{int(elapsed * 10) % 10}'

    def toggle_stopwatch(self):
        now = time.monotonic()
        if self.stopwatch_start is None:
            self.stopwatch_start = now
            self.stopwatch_button.configure(text='Pause')
            self.lap_button.state(['!disabled'])
            self.tabs['Stopwatch'][0].configure(text='Stopwatch •')
        else:
            self.stopwatch_elapsed += now - self.stopwatch_start
            self.stopwatch_start = None
            self.stopwatch_text.set(self.stopwatch_value(now))
            self.stopwatch_button.configure(text='Resume')
            self.lap_button.state(['disabled'])
            self.tabs['Stopwatch'][0].configure(text='Stopwatch')

    def mark_lap(self):
        if self.stopwatch_start is not None:
            self.lap_count += 1
            self.lap_text.set(f'Lap {self.lap_count}  ·  {self.stopwatch_value(time.monotonic())}')

    def reset_stopwatch(self):
        self.stopwatch_elapsed = 0
        self.stopwatch_start = None
        self.lap_count = 0
        self.lap_text.set('')
        self.stopwatch_text.set('00:00.0')
        self.stopwatch_button.configure(text='Start')
        self.lap_button.state(['disabled'])
        self.tabs['Stopwatch'][0].configure(text='Stopwatch')

    def update_tools(self, monotonic_now, now):
        if self.timer_end is not None:
            remaining = max(0, math.ceil(self.timer_end - monotonic_now))
            if remaining != self.timer_remaining:
                self.timer_remaining = remaining
                self.timer_text.set(self.duration_text(remaining))
                self.timer_rail.coords(self.timer_fill, 0, 0, 168 * remaining / self.timer_duration, 3)
            if remaining == 0:
                self.reset_timer()
                self.raise_alert('Timer', f'{self.duration_text(self.timer_duration)} countdown finished')
        if self.alarm_at is not None and now >= self.alarm_at:
            scheduled = self.alarm_at
            self.set_alarm(None)
            self.raise_alert('Alarm', f'Scheduled for {scheduled:%H:%M}')
        if self.stopwatch_start is not None and self.page == 'Stopwatch':
            self.stopwatch_text.set(self.stopwatch_value(monotonic_now))

    def raise_alert(self, kind, detail):
        self.alerts.append((kind, detail))
        if len(self.alerts) == 1:
            self.show_alert()

    def show_alert(self):
        kind, detail = self.alerts[0]
        self.alert_title.configure(text='Time’s up' if kind == 'Timer' else 'Alarm')
        self.alert_detail.configure(text=detail)
        if kind == 'Alarm':
            self.snooze_button.pack(side='left', padx=3, ipadx=7)
        else:
            self.snooze_button.pack_forget()
        self.show_page(self.page)
        self.root.attributes('-topmost', True)
        self.root.lift()
        self.dismiss_button.focus_set()
        self.root.bell()

    def dismiss_alert(self):
        if self.alerts:
            self.alerts.pop(0)
        if self.alerts:
            self.show_alert()
        else:
            self.root.attributes('-topmost', self.on_top)
            self.show_page(self.page)

    def snooze(self):
        if self.alerts and self.alerts[0][0] == 'Alarm':
            self.set_alarm(datetime.now() + timedelta(minutes=5))
            self.dismiss_alert()

    def escape(self, event):
        if self.alerts:
            self.dismiss_alert()
        elif self.page != 'Clock':
            self.show_page('Clock')
        else:
            self.root.destroy()

    def launch_agent(self):
        if getattr(sys, 'frozen', False):
            # Installed layout: widget\ and agent\ sit side-by-side under the app root.
            agent_exe = Path(sys.executable).parent.parent / 'agent' / 'clydex_voice_agent.exe'
            if agent_exe.is_file():
                subprocess.Popen([str(agent_exe)], cwd=str(agent_exe.parent))
                return
            from tkinter import messagebox
            messagebox.showerror('CLYDEX AI', 'Voice agent not found. Please reinstall CLYDEX.')
            return
        # Development: both .pyw files live in the same directory.
        base = RESOURCE_ROOT
        agent_pyw = base / 'scripts' / 'windows' / 'clydex_voice_agent.pyw'
        if not agent_pyw.is_file():
            from tkinter import messagebox
            messagebox.showerror('CLYDEX AI', 'The CLYDEX agent launcher is missing from scripts/windows. Restore the installation.')
            return
        python_exe = sys.executable
        if python_exe.lower().endswith('python.exe'):
            maybe = Path(python_exe).with_name('pythonw.exe')
            if maybe.exists():
                python_exe = str(maybe)
        subprocess.Popen([python_exe, str(agent_pyw)], cwd=str(agent_pyw.parent))

    def make_menu(self):
        self.menu=tk.Menu(self.root,tearoff=False,bg=PANEL,fg=LIGHT,activebackground='#1e4d58',activeforeground=LIGHT,font=('Ubuntu',-13))
        self.menu.add_command(label='Open CLYDEX voice assistant',command=self.launch_agent)
        self.menu.add_command(label='Change weather city...',command=self.change_city)
        self.menu.add_command(label='Refresh weather',command=self.request_weather)
        self.menu.add_command(label='Switch 12 / 24 hour',command=self.switch_format)
        self.menu.add_command(label='Disable always on top',command=self.toggle_topmost)
        self.menu.add_command(label='Switch compact / full watch',command=self.toggle_size)
        self.menu.add_separator()
        self.menu.add_command(label='Close widget',command=self.root.destroy)

    def show_menu(self,event):
        self.menu.tk_popup(event.x_root,event.y_root)
        self.menu.grab_release()

    def drag_start(self,event):
        self.drag_origin=(event.x_root-self.root.winfo_x(),event.y_root-self.root.winfo_y())

    def drag_motion(self,event):
        if self.drag_origin:
            ox,oy=self.drag_origin
            self.root.geometry(f'+{event.x_root-ox}+{event.y_root-oy}')

    def switch_format(self):
        self.mode24=not self.mode24
        self.last=None

    def toggle_topmost(self):
        self.on_top=not self.on_top
        self.root.attributes('-topmost',self.on_top)
        self.menu.entryconfigure(4,label=('Disable' if self.on_top else 'Enable')+' always on top')

    def update_clock(self):
        now=datetime.now()
        self.update_tools(time.monotonic(), now)
        value=now.strftime('%H%M%S' if self.mode24 else '%I%M%S')
        if value!=self.last and self.page == 'Clock' and not self.alerts:
            if self.compact:
                self.draw_watch_time(now)
            pairs = self.watch_pairs if self.compact else self.full_pairs
            for index, pair in enumerate(pairs):
                pair.set(value[2*index:2*index+2], animated=self.last is not None)
            self.last=value
        self.date_label.configure(text=now.strftime('%d %b %Y' if self.mode24 else '%p  ·  %d %b %Y').upper())
        self.root.after(85,self.update_clock)

    def change_city(self):
        city=simpledialog.askstring('Weather location','Enter city name:',initialvalue=self.city,parent=self.root)
        if city and city.strip():
            self.city=city.strip()
            self.city_label.configure(text=self.city.upper()[:23])
            self.temp.configure(text='—')
            self.metrics.configure(text='')
            self.loading=False
            self.request_weather()

    def request_weather(self):
        if self.loading:return
        self.loading=True
        self.status.configure(text='SYNCING',fg='#ffb873')
        self.condition.configure(text='UPDATING WEATHER...')
        threading.Thread(target=self.fetch_weather,args=(self.city,),daemon=True).start()

    @staticmethod
    def get_json(url):
        req=Request(url,headers={'User-Agent':'CLYDEXWidget/1.0'})
        with urlopen(req,timeout=9) as response:
            return json.loads(response.read().decode('utf-8'))

    def fetch_weather(self,city):
        try:
            geo=self.get_json('https://geocoding-api.open-meteo.com/v1/search?'+urlencode({'name':city,'count':1,'language':'en','format':'json'}))
            places=geo.get('results') or []
            if not places:raise ValueError('City not found')
            p=places[0]
            url='https://api.open-meteo.com/v1/forecast?'+urlencode({'latitude':p['latitude'],'longitude':p['longitude'],
                'current':'temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m',
                'timezone':'auto'})
            current=self.get_json(url)['current']
            self.dataq.put(('ok',city,p,current))
        except Exception as ex:
            self.dataq.put(('error',city,str(ex)))

    def check_results(self):
        try:
            while True:
                entry=self.dataq.get_nowait()
                status,city,*payload=entry
                if city!=self.city:continue
                self.loading=False
                if status=='ok':
                    place,w=payload
                    self.temp.configure(text=f"{w['temperature_2m']:.0f}°C")
                    self.condition.configure(text=WEATHER_CODES.get(w['weather_code'],'CURRENT CONDITIONS')[:21])
                    self.metrics.configure(text=f"HUM {w['relative_humidity_2m']}%  |  WIND {w['wind_speed_10m']:.0f} km/h")
                    location=f"{place['name']}, {place.get('country_code','')}"
                    self.city_label.configure(text=location.upper()[:23])
                    self.status.configure(text='LIVE',fg=CYAN)
                else:
                    self.condition.configure(text='WEATHER UNAVAILABLE')
                    self.status.configure(text='OFFLINE',fg='#ffb873')
        except queue.Empty:
            pass
        self.root.after(250,self.check_results)

    def run(self):
        self.root.after(15*60*1000,self.periodic_refresh)
        self.root.mainloop()

    def periodic_refresh(self):
        self.request_weather()
        self.root.after(15*60*1000,self.periodic_refresh)

