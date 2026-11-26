"""Rounded skins for native ttk controls. Tk retains focus and keyboard handling."""
import math
import tkinter as tk


def mix(a, b, ratio):
    channels = (round(int(a[i:i+2], 16)*(1-ratio)+int(b[i:i+2], 16)*ratio)
                for i in (1, 3, 5))
    return '#%02x%02x%02x' % tuple(channels)


class StudioSkin:
    def __init__(self, root, style):
        self.root = root
        self.style = style
        self.images = []

    def capsule(self, outside, inside, rim, radius):
        # Nine-slice borders keep the corners circular as a label or DPI changes.
        middle = 32
        diameter = radius*2+middle
        image = tk.PhotoImage(master=self.root, width=diameter, height=diameter)
        pixels = []
        for y in range(diameter):
            row = []
            for x in range(diameter):
                dx = max(radius-x,0,x-(diameter-radius-1))
                dy = max(radius-y,0,y-(diameter-radius-1))
                d = math.hypot(dx,dy)
                coverage = min(1,max(0,radius+.5-d))
                interior = min(1,max(0,radius-.5-d))
                if interior == 1:
                    row.append(inside)
                elif coverage == 0:
                    row.append(outside)
                else:
                    row.append(mix(mix(outside,rim,coverage),inside,interior))
            pixels.append('{'+' '.join(row)+'}')
        image.put(' '.join(pixels))
        self.images.append(image)
        return image

    def button(self, name, outside, inside, text):
        radius = 12
        normal = self.capsule(outside,inside,mix(inside,text,.22),radius)
        hover = self.capsule(outside,mix(inside,text,.12),mix(inside,text,.45),radius)
        focus = self.capsule(outside,inside,text,radius)
        pressed = self.capsule(outside,mix(inside,'#161522',.25),text,radius)
        disabled = self.capsule(outside,'#26273a','#34354a',radius)
        self.style.element_create(name,'image',normal,('disabled',disabled),('pressed',pressed),
                                  ('focus',focus),('active',hover),border=radius,padding=0,width=26,height=26,
                                  sticky='nsew')
        key = name+'.TButton'
        self.style.layout(key,[(name,{'sticky':'nsew','children':[
            ('Button.padding',{'sticky':'nsew','children':[('Button.label',{'sticky':''})]})]})])
        self.style.configure(key,foreground=text,font=('Segoe UI',9),padding=(10,3),
                             anchor='center',width=0)
        self.style.map(key,foreground=[('disabled','#9393a3')])
        return key

    def container(self, name, outside, inside, rim):
        image = self.capsule(outside,inside,rim,12)
        self.style.element_create(name,'image',image,border=12,sticky='nsew')
        key = name+'.TFrame'
        self.style.layout(key,[(name,{'sticky':'nsew'})])
        return key
