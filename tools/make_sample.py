#!/usr/bin/env python3
"""Draw an original neon boulevard offline. No external assets or fonts."""
from math import cos, sin, pi
from pathlib import Path
from random import Random
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parents[1] / 'app' / 'samples' / 'neon.jpg'
W, H = 1200, 900
rng = Random(26)
im = Image.new('RGB', (W, H))
d = ImageDraw.Draw(im)
# Indigo zenith, violet middle, hot magenta horizon.
stops = [(0, (8, 10, 38)), (300, (48, 20, 87)), (565, (198, 45, 131)), (H, (9, 14, 29))]
for (ya, ca), (yb, cb) in zip(stops, stops[1:]):
    for y in range(ya, yb):
        t = (y-ya)/(yb-ya)
        d.line((0, y, W, y), fill=tuple(round(a+(b-a)*t) for a, b in zip(ca, cb)))
for _ in range(65):
    x, y = rng.randrange(W), rng.randrange(25, 340)
    c = rng.randrange(100, 200)
    d.ellipse((x, y, x+1, y+1), fill=(c, c, min(255, c+45)))
# Banded retro sun, composited through a circular mask.
sun = Image.new('RGB', (250, 250)); sd = ImageDraw.Draw(sun)
mask = Image.new('L', sun.size); ImageDraw.Draw(mask).ellipse((0, 0, 249, 249), fill=255)
for y in range(250):
    t = y/250
    sd.line((0, y, 250, y), fill=(255, round(205-140*t), round(105+52*t)))
md = ImageDraw.Draw(mask)
for y in range(110, 250, 22):
    md.rectangle((0, y, 250, y+int(3+(y-110)/20)), fill=0)
im.paste(sun, (705, 175), mask)
d = ImageDraw.Draw(im)
# Distant towers and foreground buildings with rooflines, antennas, windows.
for layer in range(2):
    x = -20
    while x < W:
        width = rng.randrange(45, 100) if not layer else rng.randrange(85, 150)
        top = rng.randrange(350, 490) if not layer else rng.randrange(290, 445)
        if 460 < x < 730:
            top += 110
        color = (38, 24, 65) if not layer else (12, 17, 35)
        d.rectangle((x, top, x+width, 592), fill=color)
        d.rectangle((x+width*.25, top-9, x+width*.75, top), fill=color)
        if rng.random() < .5:
            d.line((x+width*.5, top-29, x+width*.5, top), fill=color, width=3)
        for wx in range(x+10, x+width-8, 15):
            for wy in range(top+16, 586, 20):
                if rng.random() < .48:
                    d.rectangle((wx, wy, wx+4, wy+7), fill=rng.choice([(233, 167, 103), (58, 163, 193), (177, 72, 151)]))
        if layer and (x < 450 or x > 820):
            neon = rng.choice([(247, 55, 153), (47, 218, 231)])
            d.line((x+4, top+5, x+4, 580), fill=neon, width=3)
            d.line((x+6, top+5, x+width-4, top+5), fill=neon, width=2)
        x += width+rng.randrange(6, 18)
# Wet street and sidewalks converge toward the boulevard's vanishing point.
d.rectangle((0, 590, W, H), fill=(8, 12, 26))
d.polygon([(480, 590), (720, 590), (W, H), (0, H)], fill=(20, 18, 37))
d.line((480, 591, 0, H), fill=(45, 178, 198), width=3)
d.line((720, 591, W, H), fill=(221, 45, 134), width=3)
# Broken horizontal neon streaks and diffused pools of reflected light.
reflection = Image.new('RGB', (W, H)); rd = ImageDraw.Draw(reflection)
for anchor, color in [(190, (234, 36, 137)), (350, (36, 171, 212)), (830, (225, 56, 139)), (1030, (31, 185, 221))]:
    for _ in range(95):
        y = rng.randrange(602, H)
        t = (y-590)/310
        x = 600+(anchor-600)*(.2+t)+rng.gauss(0, 25*t)
        half = rng.uniform(3, 38)*t
        c = tuple(round(v*rng.uniform(.3, .9)) for v in color)
        rd.line((x-half, y, x+half, y), fill=c, width=rng.choice([1, 2, 3]))
from PIL import ImageChops
im = ImageChops.screen(im, reflection.filter(ImageFilter.GaussianBlur(7)))
im = ImageChops.screen(im, reflection); d = ImageDraw.Draw(im)
for y in [615, 644, 691, 768, 865]:
    t = (y-590)/310
    d.polygon([(598-5*t, y), (602+5*t, y), (604+7*t, y+9+15*t), (597-7*t, y+9+15*t)], fill=(188, 139, 132))
# Curved palms with tapered, feathered fronds.
def palm(x, ground, scale):
    crown = (x+20*scale, ground-285*scale)
    points = [(x, ground), (x+5*scale, ground-100*scale), crown]
    d.line(points, fill=(5, 10, 20), width=max(3, round(13*scale)))
    for k in range(9):
        angle = pi*(.07+k*.112)
        direction = -1 if k % 2 else 1
        length = (105+(k%3)*16)*scale
        frond = []
        for j in range(13):
            t = j/12
            fx = crown[0]+direction*length*t
            fy = crown[1]-sin(angle)*60*scale*sin(pi*t)+35*scale*t*t
            frond.append((fx, fy))
            if j > 1:
                d.line((fx, fy, fx-direction*14*scale, fy+17*scale), fill=(5, 10, 20), width=max(1, round(2*scale)))
        d.line(frond, fill=(5, 10, 20), width=max(2, round(5*scale)))
for args in [(104, 671, 1.25), (1088, 664, 1.2), (318, 611, .62), (875, 609, .58)]:
    palm(*args)
# Low sports car in three-quarter front view, with luminous headlights.
glow = Image.new('RGB', (W, H)); gd = ImageDraw.Draw(glow)
for x, y in [(664, 741), (923, 724)]:
    gd.ellipse((x-43, y-16, x+43, y+16), fill=(100, 191, 224))
    gd.polygon([(x-8, y+10), (x+8, y+10), (x+80, 896), (x-110, 896)], fill=(21, 45, 60))
im = ImageChops.screen(im, glow.filter(ImageFilter.GaussianBlur(19))); d = ImageDraw.Draw(im)
d.ellipse((625, 735, 710, 794), fill=(3, 6, 13)); d.ellipse((891, 716, 949, 774), fill=(3, 6, 13))
d.polygon([(606, 733), (668, 701), (722, 654), (840, 644), (901, 681), (955, 703), (948, 758), (659, 784), (614, 766)], fill=(8, 12, 24))
d.polygon([(692, 699), (733, 660), (833, 652), (873, 684)], fill=(26, 38, 63))
d.line((735, 660, 749, 693), fill=(92, 44, 108), width=3)
d.line((608, 734, 899, 706, 952, 705), fill=(211, 51, 151), width=3)
d.polygon([(628, 738), (706, 730), (702, 740), (631, 748)], fill=(177, 243, 251))
d.polygon([(901, 714), (940, 711), (938, 721), (900, 724)], fill=(204, 250, 255))
d.line((667, 767, 933, 744), fill=(56, 100, 127), width=2)
d.polygon([(724, 750), (856, 736), (856, 751), (728, 766)], fill=(2, 5, 12))
# A modest bloom keeps the drawing crisp while softening luminous edges.
im = Image.blend(im, im.filter(ImageFilter.GaussianBlur(5)), .08)
OUT.parent.mkdir(parents=True, exist_ok=True)
for quality in range(91, 59, -3):
    im.save(OUT, 'JPEG', quality=quality, optimize=True)
    if OUT.stat().st_size <= 130*1024:
        break
assert OUT.stat().st_size <= 130*1024, 'Sample exceeds size budget'
print(f'Wrote {OUT} ({W}x{H}, {OUT.stat().st_size} bytes)')

# Two additional original scenes let the five-panel Classic layout stay unique.
def save_scene(scene, name):
    path = OUT.with_name(f'{name}.jpg')
    scene.save(path, 'JPEG', quality=88, optimize=True)
    print(f'Wrote {path} ({path.stat().st_size} bytes)')

coast = Image.new('RGB', (W, H)); cd = ImageDraw.Draw(coast)
for y in range(H):
    if y < 420:
        t = y/420
        color = tuple(round(a+(b-a)*t) for a, b in zip((49, 105, 148), (244, 165, 148)))
    else:
        t = (y-420)/480
        color = tuple(round(a+(b-a)*t) for a, b in zip((34, 125, 149), (13, 57, 86)))
    cd.line((0, y, W, y), fill=color)
cd.ellipse((190, 250, 320, 380), fill=(255, 218, 159))
cd.polygon([(0, 720), (W, 550), (W, H), (0, H)], fill=(203, 159, 128))
cd.line([(0, 707), (410, 650), (800, 589), (W, 541)], fill=(209, 229, 211), width=12)
for i in range(100):
    x = rng.randrange(W); y = rng.randrange(440, 600)
    cd.line((x, y, x+rng.randrange(15, 75), y), fill=(83, 160, 172), width=1)
# A small sailboat and distant shore towers.
cd.polygon([(463, 522), (568, 522), (550, 537), (481, 537)], fill=(26, 38, 54))
cd.line((518, 414, 518, 524), fill=(42, 49, 65), width=3)
cd.polygon([(512, 426), (468, 512), (512, 512)], fill=(250, 219, 182))
cd.polygon([(524, 444), (524, 512), (562, 512)], fill=(206, 153, 154))
for x in range(860, 1200, 30):
    top = rng.randrange(365, 412)
    cd.rectangle((x, top, x+22, 427), fill=(91, 100, 128))
for x, y, scale in [(100, 895, 1.35), (1080, 765, .9)]:
    top = (x+35*scale, y-310*scale)
    cd.line([(x, y), (x+16*scale, y-150*scale), top], fill=(27, 43, 49), width=round(16*scale))
    for k in range(8):
        a = k*pi/4
        end = (top[0]+cos(a)*140*scale, top[1]+sin(a)*58*scale+25)
        cd.line([top, ((top[0]+end[0])/2, min(top[1], end[1])-30), end], fill=(24, 58, 58), width=round(9*scale))
save_scene(coast, 'coast')

motel = Image.new('RGB', (W, H)); md = ImageDraw.Draw(motel)
for y in range(H):
    t = y/H
    md.line((0, y, W, y), fill=tuple(round(a+(b-a)*t) for a, b in zip((71, 42, 103), (244, 136, 124))))
md.rectangle((0, 665, W, H), fill=(29, 35, 53))
md.polygon([(220, 302), (1180, 375), (1180, 715), (220, 650)], fill=(184, 119, 133))
md.polygon([(220, 302), (1180, 375), (1197, 357), (230, 278)], fill=(242, 191, 166))
for row in range(2):
    for i in range(8):
        x = 256+i*113; y = 342+row*155+i*8
        md.rectangle((x, y, x+57, y+100), fill=(38, 51, 72))
        md.rectangle((x+8, y+12, x+48, y+62), fill=(239, 184, 118))
        md.line((x+28, y+12, x+28, y+62), fill=(78, 62, 75), width=3)
        md.ellipse((x+44, y+77, x+48, y+81), fill=(251, 211, 142))
md.polygon([(210, 467), (1190, 538), (1190, 557), (210, 487)], fill=(238, 177, 151))
for x in range(225, 1200, 60):
    y = 435+(x-210)*.073
    md.line((x, y, x, y+40), fill=(63, 71, 90), width=4)
md.line((210, 435, 1190, 506), fill=(108, 207, 201), width=5)
# Tall geometric roadside sign and a turquoise pool in the foreground.
md.rectangle((123, 220, 138, 734), fill=(38, 46, 64))
md.rounded_rectangle((55, 143, 207, 407), radius=28, fill=(28, 67, 79), outline=(255, 151, 183), width=7)
# Simple original arrow motif instead of any brand lettering.
md.polygon([(90, 199), (151, 199), (151, 175), (185, 220), (151, 265), (151, 241), (90, 241)], fill=(253, 179, 126))
for y in range(292, 376, 25):
    md.line((85, y, 178, y), fill=(85, 223, 213), width=7)
md.polygon([(185, 766), (887, 729), (1125, 900), (0, 900)], fill=(233, 184, 161))
md.polygon([(220, 790), (867, 757), (1045, 885), (87, 885)], fill=(26, 135, 150))
for y in range(795, 887, 15):
    md.line((240-(y-795), y, 864+(y-795)*1.3, y-7), fill=(75, 184, 184), width=2)
save_scene(motel, 'motel')
