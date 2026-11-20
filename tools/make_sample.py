#!/usr/bin/env python3
"""Generate three original, richly detailed Vice Panels scenes."""
from math import cos, sin, pi
from pathlib import Path
from random import Random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1] / 'app' / 'samples'
W, H = 2400, 1800
rng = Random(26)

def noise_field(w, h, seed, octaves=6):
    gen = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32); total = 0.0
    for octave in range(octaves):
        scale = 2 ** (octaves - octave - 1)
        gw, gh = max(2, w // (90 * scale)), max(2, h // (90 * scale))
        small = Image.fromarray(np.uint8(gen.random((gh, gw)) * 255)).resize((w, h), Image.Resampling.BICUBIC)
        weight = .58 ** octave
        out += np.asarray(small, dtype=np.float32) / 255 * weight; total += weight
    return out / total

def base_sky(top, horizon, sunx, suny, seed):
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    stops = np.array([top, horizon], np.float32)[None, :, :]
    t = np.clip(yy, 0, 1)
    grad = np.broadcast_to(stops[:, 0:1, :] * (1-t) + stops[:, 1:2, :] * t, (H, W, 3)).copy()
    n = noise_field(W, H, seed)
    cloud = np.maximum(0, (n - .49) * 2.1) ** 1.7
    yy2, xx = np.mgrid[0:H, 0:W]
    sun = np.exp(-(((xx-sunx)/(W*.28))**2 + ((yy2-suny)/(H*.21))**2))
    warm = np.stack([255*cloud, 174*cloud, 146*cloud], axis=2)
    cool = np.stack([65*cloud, 89*cloud, 147*cloud], axis=2)
    light = sun[:, :, None]
    grad = grad * (1-cloud[:, :, None]*.28) + warm * light + cool * (1-light) * cloud[:, :, None]
    return Image.fromarray(np.uint8(np.clip(grad, 0, 255)), 'RGB')

def draw_sun(im, box, color):
    glow = Image.new('RGBA', im.size, (0,0,0,0)); gd = ImageDraw.Draw(glow)
    cx=(box[0]+box[2])/2; cy=(box[1]+box[3])/2
    gd.ellipse((cx-380,cy-380,cx+380,cy+380),fill=(*color,105))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(110)))
    sun=Image.new('RGBA',(box[2]-box[0],box[3]-box[1]),(0,0,0,0)); sd=ImageDraw.Draw(sun)
    sd.ellipse((0,0,sun.width-1,sun.height-1),fill=(*color,255))
    for y in range(sun.height//2,sun.height,28): sd.rectangle((0,y,sun.width,y+5+(y-sun.height//2)//20),fill=(42,30,69,0))
    im.alpha_composite(sun,box[:2])

def skyline(im, horizon, seed, palette, layers=3):
    r=Random(seed); d=ImageDraw.Draw(im)
    for layer in range(layers):
        base=horizon+layer*70; x=-30
        while x<W:
            width=r.randrange(90,250)*(1+.18*layer); top=base-r.randrange(170,440)
            col=tuple(max(0,int(c*(.42+.22*layer))) for c in palette)
            d.rectangle((x,top,x+width,base),fill=(*col,255))
            d.polygon([(x,top+14),(x+width*.1,top-9),(x+width*.45,top+2),(x+width*.7,top-17),(x+width,top+8),(x+width,top+32),(x,top+32)],fill=(*col,255))
            if r.random()<.38:
                d.rectangle((x+width*.62,top-55,x+width*.66,top),fill=(*col,255)); d.ellipse((x+width*.60,top-59,x+width*.68,top-52),fill=(194,124,102,255))
            if r.random()<.48: d.line((x+width*.5,top-90,x+width*.5,top),fill=(*col,255),width=4)
            for wx in np.arange(x+17,x+width-12,23):
                for wy in range(int(top+35),base-18,32):
                    if r.random()<(.26+.12*layer):
                        c=r.choice([(255,198,123,220),(101,206,222,190),(247,125,160,205),(255,230,177,190)])
                        d.rounded_rectangle((wx,wy,wx+9,wy+14),radius=2,fill=c)
            x+=width+r.randrange(12,36)
    # softened distance veil
    haze=Image.new('RGBA',im.size,(0,0,0,0)); ImageDraw.Draw(haze).rectangle((0,horizon-110,W,horizon+180),fill=(*palette,58))
    im.alpha_composite(haze.filter(ImageFilter.GaussianBlur(48)))

def palm(im,x,ground,scale,seed):
    r=Random(seed); d=ImageDraw.Draw(im); cx=x+18*scale; cy=ground-300*scale
    trunk=[]
    for i in range(13):
        t=i/12; trunk.append((x+18*scale*sin(t*pi*.55),ground-300*scale*t))
    for i in range(12):
        d.line((trunk[i],trunk[i+1]),fill=(8,14,19,255),width=max(3,int(15*scale*(1-i/18))))
        if i%2==0:d.line((trunk[i][0]-6*scale,trunk[i][1],trunk[i+1][0]-5*scale,trunk[i+1][1]),fill=(172,106,82,150),width=max(1,int(2*scale)))
    for k in range(24):
        a=2*pi*k/24; length=(115+r.randrange(0,55))*scale
        pts=[]
        for j in range(17):
            t=j/16; px=cx+cos(a)*length*t; py=cy+sin(a)*length*t+42*scale*t*t
            pts.append((px,py))
        for j in range(16):
            width=max(1,int((7*(1-j/17)+1)*scale))
            d.line((pts[j],pts[j+1]),fill=(5,13,17,255),width=width)
            if j>2 and j%2==0:
                for side in (-1,1):
                    q=pts[j]; end=(q[0]+side*10*scale*cos(a+pi/2),q[1]+side*10*scale*sin(a+pi/2))
                    d.line((q,end),fill=(8,23,25,245),width=max(1,int(3*scale*(1-j/20))))
        # warm lit edge toward sun side
        if cos(a)>0: d.line(pts[:8],fill=(255,162,112,145),width=max(1,int(2*scale)))

def water(im, y0, color, sunx, seed, sea=False):
    r=Random(seed); d=ImageDraw.Draw(im); d.rectangle((0,y0,W,H),fill=(*color,255))
    for y in range(y0,H,7 if sea else 11):
        t=(y-y0)/(H-y0); spread=(22+250*t) if sea else (8+55*t)
        for _ in range(int(70+260*t)):
            x=max(0,min(W,r.gauss(sunx,spread*.42) if r.random()<.7 else r.randrange(W)))
            length=r.uniform(3,28)*(0.25+t); bright=max(.08,1-abs(x-sunx)/(spread*1.9))
            c=(255, int(190*bright+45), int(139*bright+70), int(90+145*bright))
            d.line((x,y,x+length,y+r.uniform(-1.4,1.4)),fill=c,width=r.choice([1,2,3]))
    # reflected sun smear
    smear=Image.new('RGBA',im.size,(0,0,0,0)); sd=ImageDraw.Draw(smear)
    for i in range(35):
        y=y0+i*max(3,(H-y0)//35); half=(8+i*5)*r.uniform(.65,1.4)
        sd.line((sunx-half,y,sunx+half,y),fill=(255,205,151,max(0,95-i*2)),width=r.randrange(2,9))
    im.alpha_composite(smear.filter(ImageFilter.GaussianBlur(18)))

def neon():
    im=base_sky((8,12,42),(194,49,127),1500,440,1).convert('RGBA'); draw_sun(im,(1410,320,1900,810),(255,185,123))
    skyline(im,1120,8,(67,43,91)); d=ImageDraw.Draw(im)
    d.rectangle((0,1120,W,H),fill=(8,12,24,255));d.polygon([(950,1120),(1450,1120),(W,H),(0,H)],fill=(22,19,34,255))
    water(im,1120,(14,19,34),1200,17)
    # lane and neon architecture accents
    d=ImageDraw.Draw(im)
    for x in (950,1450): d.line((x,1120,(x-950)*3 if x<1200 else W,H),fill=(235,54,164,255),width=7)
    for x in range(0,W,230):
        d.line((x,1160,x+140,1160),fill=(91,177,194,150),width=2)
    for args in [(130,1340,1.35,3),(2250,1330,1.25,4),(620,1150,.62,5),(1790,1160,.63,6)]: palm(im,*args)
    # car, chrome highlights, low headlight beams and underglow
    glow=Image.new('RGBA',im.size,(0,0,0,0)); gd=ImageDraw.Draw(glow)
    gd.polygon([(1160,1450),(1320,1350),(1690,1360),(1850,1450),(2030,1710),(1020,1710)],fill=(54,172,210,70))
    for x,y in [(1160,1460),(1845,1450)]: gd.polygon([(x,y),(x+25,y),(x+240,1790),(x-220,1790)],fill=(114,208,240,95))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(38)));d=ImageDraw.Draw(im)
    d.ellipse((1130,1550,1280,1710),fill=(2,4,9,255));d.ellipse((1770,1535,1920,1695),fill=(2,4,9,255))
    d.polygon([(1050,1480),(1250,1390),(1400,1300),(1660,1300),(1800,1385),(1930,1435),(1900,1585),(1240,1620),(1080,1560)],fill=(11,17,30,255))
    d.polygon([(1320,1390),(1430,1325),(1645,1325),(1745,1390)],fill=(48,67,91,255))
    d.line([(1060,1485),(1260,1450),(1410,1402),(1800,1415),(1920,1440)],fill=(244,128,194,255),width=8)
    d.line((1090,1540,1250,1510),fill=(235,255,255,255),width=13);d.line((1820,1490,1900,1470),fill=(235,255,255,255),width=12)
    d.line((1300,1590,1840,1550),fill=(131,184,205,255),width=4)
    return im.convert('RGB')

def coast():
    im=base_sky((45,104,148),(245,166,145),470,570,19).convert('RGBA');draw_sun(im,(340,500,610,770),(255,224,167))
    skyline(im,850,29,(77,103,131),2)
    water(im,850,(31,119,143),475,30,True);d=ImageDraw.Draw(im)
    d.polygon([(0,1390),(W,1080),(W,H),(0,H)],fill=(193,151,121,255))
    d.line([(0,1390),(700,1280),(W,1080)],fill=(246,227,199,255),width=22)
    # dune grasses, shells and wet sand reflections
    for i in range(260):
        x=rng.randrange(W);y=rng.randrange(1320,H);d.line((x,y,x+rng.randrange(-15,22),y-rng.randrange(4,22)),fill=(102,90,76,130),width=rng.randrange(1,4))
    d.polygon([(925,1015),(1100,1015),(1070,1045),(950,1045)],fill=(24,37,52,255));d.line((1008,825,1008,1018),fill=(34,43,59,255),width=7)
    d.polygon([(1000,845),(915,1005),(1000,1005)],fill=(250,223,183,255));d.polygon([(1017,865),(1017,1005),(1090,1005)],fill=(205,153,153,255))
    for args in [(180,1790,1.45,22),(2220,1490,.92,23),(530,1370,.56,24)]:palm(im,*args)
    return im.convert('RGB')

def motel():
    im=base_sky((72,43,104),(241,139,125),1480,400,36).convert('RGBA');draw_sun(im,(1390,290,1710,610),(255,188,140))
    skyline(im,820,37,(83,65,112),2);d=ImageDraw.Draw(im)
    d.rectangle((0,1310,W,H),fill=(26,32,48,255))
    # three depth rows of resort wings
    for layer,(x0,y0,scale) in enumerate([(180,680,.55),(420,740,.72),(470,800,1.0)]):
        width=int(1830*scale); height=int(570*scale)
        d.polygon([(x0,y0),(x0+width,y0+int(95*scale)),(x0+width,y0+height),(x0,y0+height-35)],fill=(102+layer*22,66+layer*19,87+layer*17,255))
        d.polygon([(x0,y0),(x0+width,y0+int(95*scale)),(x0+width+35,y0+int(64*scale)),(x0+30,y0-35)],fill=(232,174,151,255))
        for row in range(2):
            for i in range(13):
                x=x0+25+i*int(132*scale);y=y0+int((95+row*210)*scale)+i*int(6*scale)
                if x+55*scale<x0+width:
                    d.rectangle((x,y,x+int(67*scale),y+int(105*scale)),fill=(22,39,57,255))
                    d.rectangle((x+int(8*scale),y+int(10*scale),x+int(58*scale),y+int(69*scale)),fill=rng.choice([(255,187,114,255),(91,199,211,255),(241,125,151,255)]))
                    d.line((x+int(34*scale),y+int(10*scale),x+int(34*scale),y+int(69*scale)),fill=(58,54,69,255),width=max(1,int(3*scale)))
        # balcony rails and awnings
        for yy in range(int(y0+170*scale),int(y0+height-25),int(125*scale)):
            d.line((x0,yy,x0+width,yy+int(80*scale)),fill=(234,181,158,255),width=max(2,int(6*scale)))
            for xx in range(x0,x0+width,int(54*scale)):d.line((xx,yy,xx,yy+int(22*scale)),fill=(54,58,73,220),width=max(1,int(2*scale)))
    # pool, caustics and light strings
    d.polygon([(340,1500),(1590,1420),(2200,1800),(0,1800)],fill=(18,105,129,255))
    for i in range(1300):
        y=rng.randrange(1450,H);x=rng.randrange(W);length=rng.randrange(5,46)
        col=rng.choice([(95,217,213,145),(188,244,224,120),(31,143,167,180)])
        d.arc((x,y,x+length,y+rng.randrange(3,17)),0,180,fill=col,width=rng.randrange(1,4))
    for i in range(70):
        x=260+i*28;y=570+int(i*2.8);d.line((x,y,x+12,y+3),fill=(255,228,171,200),width=3)
        d.ellipse((x+6,y-7,x+19,y+8),fill=(255,229,166,255))
    # sign casing, layered neon bloom and geometric lettering
    glow=Image.new('RGBA',im.size,(0,0,0,0));gd=ImageDraw.Draw(glow)
    gd.rounded_rectangle((90,330,410,900),radius=42,outline=(64,246,236,220),width=18);gd.rectangle((145,430,355,790),fill=(250,91,157,175))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(34)));d=ImageDraw.Draw(im)
    d.rounded_rectangle((90,330,410,900),radius=42,fill=(26,52,68,255),outline=(94,244,232,255),width=11)
    d.polygon([(145,485),(290,485),(290,435),(365,535),(290,635),(290,585),(145,585)],fill=(255,191,130,255))
    for y in (680,725,770):d.line((145,y,355,y),fill=(92,242,229,255),width=14)
    # parked car with polished trim and light pool
    cg=Image.new('RGBA',im.size,(0,0,0,0));cgd=ImageDraw.Draw(cg);cgd.ellipse((1300,1440,2230,1690),fill=(70,204,222,110));im.alpha_composite(cg.filter(ImageFilter.GaussianBlur(48)))
    d=ImageDraw.Draw(im);d.ellipse((1330,1550,1475,1700),fill=(4,7,13,255));d.ellipse((1960,1530,2100,1685),fill=(4,7,13,255))
    d.polygon([(1260,1510),(1370,1430),(1580,1390),(1810,1395),(1960,1470),(2110,1505),(2090,1585),(1310,1610)],fill=(14,25,42,255))
    d.polygon([(1440,1450),(1595,1410),(1790,1415),(1910,1470)],fill=(88,115,132,255))
    d.line((1270,1518,1430,1490,1740,1485,2060,1520),fill=(255,218,175,255),width=8);d.line((1320,1570,2050,1555),fill=(111,220,226,255),width=5)
    return im.convert('RGB')

def save(scene,name):
    scene=scene.resize((1200,900),Image.Resampling.LANCZOS)
    scene=finish_print(scene)
    scene.save(ROOT/f'{name}.jpg','JPEG',quality=90,optimize=True)
    print(f'Wrote {ROOT/name}.jpg ({(ROOT/f"{name}.jpg").stat().st_size} bytes)')

def finish_print(scene):
    """Apply a reproducible photographic print treatment."""
    from PIL import ImageChops, ImageEnhance
    global rng
    rng = Random(2606)
    arr=np.asarray(scene.convert('RGB'),dtype=np.float32)
    h,w=arr.shape[:2]; yy,xx=np.mgrid[0:h,0:w]
    lum=arr[:,:,0]*.2126+arr[:,:,1]*.7152+arr[:,:,2]*.0722
    shadows=np.clip((150-lum)/150,0,1); highlights=np.clip((lum-95)/160,0,1)
    arr[:,:,0]+=18*highlights-8*shadows
    arr[:,:,1]+=7*highlights+4*shadows
    arr[:,:,2]-=5*highlights-17*shadows
    noise=np.fromiter((rng.gauss(0,2.8) for _ in range(w*h)),dtype=np.float32).reshape(h,w)
    arr+=noise[:,:,None]
    image=Image.fromarray(np.uint8(np.clip(arr,0,255)),'RGB')
    image=ImageEnhance.Contrast(image).enhance(1.08)
    image=image.filter(ImageFilter.UnsharpMask(radius=1.7,percent=145,threshold=3))
    arr=np.asarray(image,dtype=np.float32)
    nx=(xx-w/2)/(w*.64);ny=(yy-h/2)/(h*.64)
    vignette=np.clip(1-.34*(nx*nx+ny*ny),.58,1)
    arr*=vignette[:,:,None]
    # One-pixel RGB displacement is masked to high-contrast edges.
    gray=np.asarray(image.convert('L'),dtype=np.float32)
    edge=np.asarray(Image.fromarray(np.uint8(gray)).filter(ImageFilter.FIND_EDGES),dtype=np.float32)/255
    strength=np.clip((edge-.10)*1.8,0,.72)[:,:,None]
    red=np.asarray(image,dtype=np.float32)
    shifted_r=np.roll(red[:,:,0],1,axis=1);shifted_b=np.roll(red[:,:,2],-1,axis=1)
    arr[:,:,0]=arr[:,:,0]*(1-strength[:,:,0])+shifted_r*strength[:,:,0]
    arr[:,:,2]=arr[:,:,2]*(1-strength[:,:,0])+shifted_b*strength[:,:,0]
    return Image.fromarray(np.uint8(np.clip(arr,0,255)),'RGB')

ROOT.mkdir(parents=True,exist_ok=True)
save(neon(),'neon')
save(coast(),'coast')
save(motel(),'motel')
