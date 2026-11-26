"""A folded light ribbon and a live frequency display for Clydex Studio."""
import math
import time
import tkinter as tk
from clydex.voice.spectrum import BANDS, HIGH_HZ, LOW_HZ
from clydex.desktop.theme import mix


class Hologram(tk.Canvas):
    surface = '#090b17'

    def __init__(self,parent):
        super().__init__(parent,bg=self.surface,highlightthickness=0,bd=0)
        self.phase = 0.
        self.last_frame = time.monotonic()
        self.angles = [math.tau*i/120 for i in range(121)]
        self.strands = []
        for i in range(42):
            k = i/41
            color = mix('#51cbbb','#a08af6',min(1,k*1.4))
            if k>.82:
                color = mix(color,'#ffc8a3',(k-.82)/.18)
            self.strands.append(self.create_line(0,0,1,1,fill=color,width=1))

    def draw(self,state,bands):
        w,h = self.winfo_width(),self.winfo_height()
        if min(w,h)<4:
            return
        now=time.monotonic()
        dt=min(.2,now-self.last_frame)
        self.last_frame=now
        self.phase += dt*(.64 if state=='THINKING' else .32)
        t=self.phase
        scale=min(w*.34,h*.42)
        # A twisted strip in perspective. Each section reacts to its own frequency band.
        for i,strand in enumerate(self.strands):
            depth=i/41-.5
            points=[]
            for j,a in enumerate(self.angles):
                amplitude=bands[min(j,120-j)*(BANDS-1)//60]
                twist=1.5*a+.42*math.sin(t)
                r=1+depth*.65*math.cos(twist)+amplitude*.12
                x=r*math.cos(a)
                y=.54*r*math.sin(a)+depth*.84*math.sin(twist)+.13*math.sin(2*a+t)
                points.extend((w*.5+scale*(x*.96-y*.26),h*.51+scale*(x*.26+y*.96)))
            self.coords(strand,*points)


class SpectrumMeter(tk.Canvas):
    def __init__(self,parent):
        super().__init__(parent,height=72,bg=Hologram.surface,highlightthickness=0,bd=0)
        self.bars=[0.]*BANDS
        self.peaks=[0.]*BANDS
        self.last_frame=time.monotonic()
        self.palette=[mix('#64dbcb','#a79bf3',i/(BANDS-1)) for i in range(BANDS)]

    def draw(self,values,active,upper_hz=HIGH_HZ):
        now=time.monotonic()
        dt=min(.2,now-self.last_frame)
        self.last_frame=now
        self.delete('all')
        width=self.winfo_width()
        if width<10:
            return
        left,right=2,width-3
        baseline,span=50,43
        step=(right-left)/BANDS
        for y in (7,28,50):
            self.create_line(left,y,right,y,fill='#29293b',dash=(2,4))
        for i,value in enumerate(values):
            self.bars[i]=max(float(value),self.bars[i]-dt*1.9) if active else 0.
            self.peaks[i]=max(self.bars[i],self.peaks[i]-dt*.72) if active else 0.
            x=left+i*step
            end=x+step*.73
            top=baseline-self.bars[i]*span
            self.create_rectangle(x,top-1,end,baseline,fill=self.palette[i] if self.bars[i] else '#3e4055',outline='')
            if self.peaks[i]>.02:
                y=baseline-self.peaks[i]*span-2
                self.create_line(x,y,end,y,fill='#efd0a8')
        for freq,anchor in ((LOW_HZ,'w'),(1000,'center'),(upper_hz,'e')):
            f=math.log(freq/LOW_HZ)/math.log(upper_hz/LOW_HZ)
            self.create_text(left+(right-left)*f,64,text=f'{freq:g} Hz' if freq<1000 else f'{freq/1000:g} kHz',
                             anchor=anchor,fill='#a9a8bd',font=('Consolas',-10))
