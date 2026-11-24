"""CLYDEX Mini Plus — compact, draggable Windows weather flip clock.
Python 3 standard library only. Run: python clydex_widget.py
Right-click for settings; drag anywhere on the header to move.
"""
import json
import subprocess
import sys
from pathlib import Path
import math
import queue
import threading
import tkinter as tk
from tkinter import font as tkfont, simpledialog, ttk
from clydex_theme import StudioSkin
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ASSETS = (Path(sys.executable).parent if getattr(sys, 'frozen', False)
          else Path(__file__).resolve().parent) / 'studio_ui'
BG = '#171d1e'
PANEL = '#252b2d'
CYAN = '#4cd7f6'
LIGHT = '#dee3e6'
MUTED = '#bcc9cd'
OUTLINE = '#3d494c'
TOP = '#252b2d'
BOTTOM = '#1b2122'

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
        self.root.title('CLYDEX // DESKTOP WIDGET')
        self.root.geometry('466x270+70+70')
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
        self.make_ui()
        self.make_watch()
        self.compact = False
        self.toggle_size()
        self.make_menu()
        self.update_clock()
        self.request_weather()
        self.check_results()
        self.root.bind('<Escape>',lambda e:self.root.destroy())
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
        main = self.full_face = tk.Frame(self.root,bg=BG,highlightthickness=1,highlightbackground=OUTLINE)
        self.header(main).pack(fill='x',padx=16,pady=(10,7))
        tk.Frame(main,bg=OUTLINE,height=1).pack(fill='x')
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
        face = self.watch = tk.Canvas(self.root,bg=BG,bd=0,highlightthickness=0)
        face.create_rectangle(0,0,247,107,outline=OUTLINE)
        face.create_window(7,3,anchor='nw',width=234,height=26,window=self.header(face))
        face.create_rectangle(6,32,241,82,fill=BOTTOM,outline='#090f11')
        face.create_rectangle(7,33,240,56,fill=TOP,outline='')
        face.create_line(7,57,240,57,fill='#090f11')
        self.watch_pairs = []
        for x,width,size,ink in ((9,78,54,LIGHT),(97,78,54,LIGHT),(183,54,38,CYAN)):
            pair=SplitPair(face,width,48,size,ink)
            face.create_window(x,33,anchor='nw',window=pair)
            self.watch_pairs.append(pair)
            for item in (pair,pair.top,pair.bottom,pair.fold):
                self.bind_drag(item)
        for y in (49,62):
            face.create_rectangle(90,y,92,y+2,fill=MUTED,outline='')
        face.create_line(179,37,179,77,fill=OUTLINE)
        face.create_image(7,95,anchor='w',image=self.icons['calendar_month'])
        face.create_text(27,95,anchor='w',tags='date',fill=LIGHT,font=('Ubuntu',-11))
        face.create_text(117,95,anchor='e',tags='period',fill=MUTED,font=('Space Grotesk',-10))
        face.create_line(122,90,122,100,fill=OUTLINE)
        face.create_image(129,95,anchor='w',image=self.icons['cloud'])
        self.weather_font = tkfont.Font(root=self.root, family='Ubuntu', size=-11)
        face.create_text(151,95,anchor='w',tags='city',fill=MUTED,font=self.weather_font)
        face.create_text(240,95,anchor='e',tags='weather',fill=LIGHT,font=self.weather_font)
        self.bind_drag(face)

    def toggle_size(self):
        self.compact = not self.compact
        if self.compact:
            self.full_face.pack_forget()
            self.watch.pack(fill='both', expand=True)
            self.root.geometry('248x108')
        else:
            self.watch.pack_forget()
            self.full_face.pack(fill='both', expand=True)
            self.root.geometry('466x270')
        self.last = None

    def draw_watch_time(self, now):
        self.watch.itemconfigure('period', text='' if self.mode24 else now.strftime('%p'))
        self.watch.itemconfigure('date', text=now.strftime('%a, %d %b'))
        temperature = self.temp.cget('text')
        self.watch.itemconfigure('weather', text=temperature)
        available = 240 - 151 - 6 - self.weather_font.measure(temperature)
        city = self.city
        if self.weather_font.measure(city) > available:
            city = city[:max(0, available)]
            while city and self.weather_font.measure(city + '…') > available:
                city = city[:-1]
            city += '…'
        self.watch.itemconfigure('city', text=city)

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
        base = Path(__file__).resolve().parent
        agent_pyw = base / 'clydex_voice_agent.pyw'
        if not agent_pyw.is_file():
            from tkinter import messagebox
            messagebox.showerror('CLYDEX AI', 'Place clydex_voice_agent.pyw in the same folder as the widget.')
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
        value=now.strftime('%H%M%S' if self.mode24 else '%I%M%S')
        if value!=self.last:
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

if __name__=='__main__':
    ClydexWidget().run()
