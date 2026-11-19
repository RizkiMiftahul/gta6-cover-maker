#!/usr/bin/env python3
"""Generate an original, offline neon boulevard sample for Vice Panels."""
from math import exp
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parents[1] / 'app' / 'samples' / 'neon.jpg'
W, H = 1200, 900
im = Image.new('RGB', (W, H))
p = im.load()
# Dusk sky fades from deep indigo into a hot pink horizon.
for y in range(H):
    t = min(1, y / 610)
    if t < .58:
        q = t / .58
        top, mid = (17, 24, 66), (108, 42, 104)
        rgb = tuple(int(a*(1-q)+b*q) for a,b in zip(top,mid))
    else:
        q=(t-.58)/.42
        mid, low=(108,42,104),(250,112,101)
        rgb=tuple(int(a*(1-q)+b*q) for a,b in zip(mid,low))
    for x in range(W):
        glow=exp(-(((x-W*.73)/(W*.33))**2+((y-H*.57)/(H*.2))**2)*2)*.18
        p[x,y]=tuple(min(255,int(c+(255-c)*glow)) for c in rgb)
d=ImageDraw.Draw(im,'RGBA')
# Sun disc and distant skyline.
d.ellipse((760,240,975,455),fill=(255,207,153,235))
d.ellipse((784,264,951,431),fill=(255,151,143,255))
d.rectangle((0,460,W,620),fill=(21,25,54,255))
# Layered block silhouettes, lit windows.
blocks=[(-20,350,130,640),(95,410,235,610),(205,325,340,630),(320,385,475,615),(446,292,580,630),(550,390,700,605),(660,337,805,630),(970,370,1110,620),(1080,435,1220,620)]
for i,(x1,y1,x2,y2) in enumerate(blocks):
    d.rectangle((x1,y1,x2,y2),fill=(20+i%3*5,23,48,255))
    if i in (2,4,6): d.polygon([(x1,y1),(x1+20,y1-23),(x1+20,y1)],fill=(30,28,54,255))
    for wx in range(x1+12,x2-6,19):
        for wy in range(y1+18,y2-12,26):
            if (wx*3+wy+i)%5<2:d.rectangle((wx,wy,wx+5,wy+9),fill=(255,191,111,170))
# Palm silhouettes.
def palm(x,y,scale=1):
    d.line((x,y,x+8*scale, y-190*scale),fill=(17,20,37,255),width=max(5,int(12*scale)))
    for k in range(7):
        xx=x+8*scale; yy=y-190*scale
        endx=xx+(-1 if k%2 else 1)*(45+13*(k%3))*scale
        endy=yy-(20+(k%4)*12)*scale
        d.line((xx,yy,endx,endy),fill=(17,20,37,255),width=max(3,int(7*scale)))
        d.line((endx,endy,endx+(-1 if endx<xx else 1)*35*scale,endy+14*scale),fill=(17,20,37,255),width=max(2,int(4*scale)))
palm(110,595,.85);palm(1050,602,1.0)
# Wet boulevard foreground with converging edges and long colored reflections.
d.polygon([(0,594),(W,594),(W,900),(0,900)],fill=(16,19,35,255))
d.polygon([(445,595),(755,595),(1200,900),(0,900)],fill=(30,28,50,255))
for x,color,width in [(220,(255,91,159,120),15),(370,(255,159,118,100),12),(860,(53,216,235,140),17),(1010,(246,83,174,125),13),(600,(255,196,135,90),9)]:
    d.line((600+(x-600)*.08,610,x,895),fill=color,width=width)
# Soft reflected neon bloom, then road markings and a little texture.
bloom=im.filter(ImageFilter.GaussianBlur(22)); im=Image.blend(im,bloom,.22);d=ImageDraw.Draw(im,'RGBA')
d.polygon([(585,630),(615,630),(685,900),(640,900)],fill=(255,255,225,130))
d.line((600,640,596,900),fill=(255,233,194,190),width=5)
for y in range(665,900,57):
    half=4+(y-650)*.045
    d.polygon([(600-half,y),(600+half,y),(600+half*1.2,y+22),(600-half*1.2,y+22)],fill=(255,223,183,175))
# Tiny glints sell the damp road surface.
for i in range(270):
    x=(i*173+41)%W;y=620+(i*97)%280
    alpha=30+(i*13)%75
    d.line((x,y,x+8+(i%27),y+(i%4)),fill=(255,196,208,alpha),width=1)
OUT.parent.mkdir(parents=True,exist_ok=True)
im.save(OUT,'JPEG',quality=91,optimize=True)
print(f'Wrote {OUT} ({W}x{H})')
