#!/usr/bin/env python3
"""Frames the Đà Nẵng – Hội An trailer in an iPhone Duo on an animated dusk backdrop.

Reads the cut gameplay clip (2034x1398, the Duo's unfolded screen), and for every frame:
  - draws the backdrop: a dusk sky with stars, a setting retro sun behind Hội An's roofs, the
    Dragon Bridge and Marble Mountains on the left, Bà Nà's Golden Bridge on the right, silk
    lanterns drifting up and a lime perspective grid rolling towards the viewer
  - floats the phone in the middle, its screen showing the game, with its reflection on the floor
and pipes the frames to ffmpeg with the clip's sound. Output: H.264 2560x1440 60 fps + AAC.

usage: frame_trailer.py GAME_CLIP.mp4 OUT.mp4 FFMPEG
"""
import math
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

CLIP, OUT, FFMPEG = sys.argv[1], sys.argv[2], sys.argv[3]
ROOT = Path(__file__).resolve().parent.parent
W, H, FPS = 2560, 1440, 60
HORIZON = 1010
SCREEN_W, SCREEN_H = 1480, 1017  # the Duo's 2034x1398 screen, scaled
SCREEN_X, SCREEN_Y = (W - SCREEN_W) // 2, 168
SCREEN_R = 58  # screen corner radius
BEZEL, BAND = 16, 11  # black glass border, then the metal band
LIME, ORANGE, FOREST = (213, 246, 75), (255, 116, 71), (35, 77, 55)
rng = random.Random(64)


def probe_frames(path):
    ffprobe = str(Path(FFMPEG).with_name("ffprobe"))
    out = subprocess.run([ffprobe, "-v", "error", "-count_packets", "-select_streams", "v:0",
                          "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout
    return int(out.strip().split(",")[0])


def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def radial(size, color, power=2.0):
    """A soft round glow sprite."""
    yy, xx = np.mgrid[0:size, 0:size]
    d = np.sqrt((xx - size / 2 + 0.5) ** 2 + (yy - size / 2 + 0.5) ** 2) / (size / 2)
    a = np.clip(1.0 - d, 0, 1) ** power
    img = np.zeros((size, size, 4), np.uint8)
    img[..., 0], img[..., 1], img[..., 2] = color
    img[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


# ------------------------------------------------------------------ the static backdrop

def sky():
    top, mid, low = (10, 12, 38), (58, 28, 78), (255, 132, 84)
    y = np.linspace(0, 1, HORIZON)[:, None]
    t1 = np.clip(y / 0.62, 0, 1)
    t2 = np.clip((y - 0.62) / 0.38, 0, 1) ** 1.4
    c = np.zeros((HORIZON, W, 3), np.float32)
    for i in range(3):
        c[..., i] = top[i] + (mid[i] - top[i]) * t1 + (low[i] - mid[i]) * t2
    img = np.zeros((H, W, 3), np.uint8)
    img[:HORIZON] = c.astype(np.uint8)
    img[HORIZON:] = (8, 8, 22)
    return Image.fromarray(img, "RGB").convert("RGBA")


def retro_sun(base, cx, cy, r):
    """The setting sun: lime at the top to brand orange, cut by widening stripes."""
    s = 2
    size = r * 2 * s
    yy, xx = np.mgrid[0:size, 0:size]
    d = np.sqrt((xx - size / 2) ** 2 + (yy - size / 2) ** 2) / (size / 2)
    v = yy / size
    col = np.zeros((size, size, 4), np.float32)
    for i in range(3):
        col[..., i] = LIME[i] + (ORANGE[i] - LIME[i]) * np.clip(v * 1.15, 0, 1)
    alpha = (d <= 1.0).astype(np.float32)
    # stripes widen towards the bottom, like a synthwave sun
    for k in range(7):
        y0 = 0.56 + k * 0.064
        hgt = 0.008 + k * 0.006
        alpha[(v > y0) & (v < y0 + hgt)] = 0
    col[..., 3] = alpha * 255
    sun = Image.fromarray(col.astype(np.uint8), "RGBA").resize((r * 2, r * 2), Image.LANCZOS)
    # the sun sets: nothing of it below the horizon, only a shimmer on the floor
    sa = np.array(sun)
    cut = HORIZON - (cy - r)
    if 0 < cut < sa.shape[0]:
        sa[cut:, :, 3] = 0
    sun = Image.fromarray(sa, "RGBA")
    glow = radial(r * 5, (255, 150, 90), 2.2)
    base.alpha_composite(glow, (cx - glow.width // 2, cy - glow.height // 2))
    base.alpha_composite(sun, (cx - r, cy - r))
    shimmer = Image.new("RGBA", (r * 2, 140), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shimmer)
    for k in range(9):
        w = r * (1.6 - k * 0.15)
        sd.rectangle([r - w / 2, 8 + k * 14, r + w / 2, 12 + k * 14], fill=ORANGE + (int(150 - k * 15),))
    base.alpha_composite(shimmer.filter(ImageFilter.GaussianBlur(2)), (cx - r, HORIZON + 4))


def skyline(base):
    """Silhouettes along the horizon, drawn at 2x for clean edges."""
    s = 2
    layer = Image.new("RGBA", (W * s, H * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    far, near = (44, 24, 70, 255), (24, 14, 42, 255)
    hz = HORIZON * s
    # far hills along the whole horizon
    pts = [(0, hz)]
    for x in range(0, W * s + 40, 40):
        pts.append((x, hz - (40 + 30 * math.sin(x * 0.0021) + 22 * math.sin(x * 0.0057 + 1.0)) * s))
    pts.append((W * s, hz))
    d.polygon(pts, fill=far)
    # left: the Marble Mountains, steep peaks with a stupa on the tallest
    mid = (36, 20, 60, 255)
    for cx, top, rad in [(70, 250, 95), (230, 400, 120), (390, 230, 85)]:
        peak = []
        for k in range(13):
            u = k / 12
            x = cx - rad + 2 * rad * u
            bump = math.sin(u * math.pi) ** 0.6
            jag = 0.06 * math.sin(k * 2.3 + cx)
            peak.append((x * s, hz - (top * (bump + jag)) * s))
        d.polygon([((cx - rad * 1.15) * s, hz)] + peak + [((cx + rad * 1.15) * s, hz)], fill=mid)
    sx, st = 230 * s, hz - 395 * s
    for i in range(5):
        w = (34 - i * 5) * s
        d.polygon([(sx - w, st - i * 26 * s), (sx + w, st - i * 26 * s), (sx, st - (i * 26 + 20) * s)], fill=mid)
        d.rectangle([sx - w * 0.6, st - (i * 26 + 18) * s, sx + w * 0.6, st - i * 26 * s], fill=mid)
    # Dragon Bridge: the deck and the arching dragon, its head raised towards the device
    deck_y = hz - 70 * s
    d.rectangle([0, deck_y, 520 * s, deck_y + 12 * s], fill=near)
    for px in range(20, 520, 46):
        d.rectangle([px * s, deck_y, (px + 10) * s, hz], fill=near)
    body = []
    for x in range(0, 470, 4):
        y = deck_y - (10 + 60 * max(0.0, math.sin((x - 10) / 470 * 3 * math.pi))) * s
        body.append((x * s, y))
    gold = (196, 132, 44, 255)  # the dragon catches the last of the sun
    for i in range(len(body) - 1):
        d.line([body[i], body[i + 1]], fill=gold, width=16 * s)
    hx, hy = 470 * s, deck_y - 70 * s
    d.line([body[-1], (hx, hy)], fill=gold, width=16 * s)
    d.polygon([(hx - 10 * s, hy - 14 * s), (hx + 44 * s, hy - 6 * s), (hx + 38 * s, hy + 12 * s), (hx - 6 * s, hy + 14 * s)], fill=gold)
    d.polygon([(hx, hy - 12 * s), (hx - 14 * s, hy - 40 * s), (hx + 10 * s, hy - 14 * s)], fill=gold)  # a horn
    for i in range(0, len(body) - 1, 3):  # a bright ridge along the back
        d.line([body[i][0], body[i][1] - 6 * s, body[i + 1][0], body[i + 1][1] - 6 * s], fill=(255, 200, 90, 255), width=3 * s)
    # right: Bà Nà's peak with the Golden Bridge loop and the two hands
    bx = 2380 * s
    d.polygon([(2120 * s, hz), (bx - 120 * s, hz - 330 * s), (bx - 40 * s, hz - 380 * s), (bx + 60 * s, hz - 360 * s), (W * s, hz - 250 * s), (W * s, hz)], fill=far)
    by = hz - 300 * s
    for hxx in (bx - 70 * s, bx + 50 * s):
        d.rectangle([hxx - 9 * s, by, hxx + 9 * s, hz - 200 * s], fill=near)
    d.arc([bx - 120 * s, by - 34 * s, bx + 100 * s, by + 34 * s], 200, 340, fill=(255, 205, 90, 255), width=7 * s)
    d.arc([bx - 120 * s, by - 34 * s, bx + 100 * s, by + 34 * s], 20, 160, fill=(255, 205, 90, 255), width=9 * s)
    # right: Hội An's roofs with curled eaves (the sun sets behind them)
    x = 2075
    while x < W:
        w = rng.choice([110, 130, 150])
        h = rng.choice([90, 120, 150])
        base_y = hz
        d.rectangle([x * s, base_y - h * s, (x + w - 8) * s, base_y], fill=near)
        roof = [((x - 16) * s, base_y - h * s), ((x + w * 0.5) * s, base_y - (h + 46) * s), ((x + w + 8) * s, base_y - h * s)]
        d.polygon(roof, fill=near)
        d.ellipse([(x - 24) * s, base_y - (h + 10) * s, (x - 8) * s, base_y - (h - 6) * s], fill=near)
        d.ellipse([(x + w) * s, base_y - (h + 10) * s, (x + w + 16) * s, base_y - (h - 6) * s], fill=near)
        x += w + 6
    layer = layer.resize((W, H), Image.LANCZOS)
    base.alpha_composite(layer)
    # warm windows and lights along the bridge
    lights = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lights)
    for px in range(14, 520, 26):
        ld.ellipse([px - 3, HORIZON - 76, px + 3, HORIZON - 70], fill=(255, 210, 120, 255))
    for i in range(46):
        wx = rng.randint(2080, W - 10)
        wy = HORIZON - rng.randint(20, 120)
        ld.rectangle([wx, wy, wx + 7, wy + 9], fill=(255, rng.randint(170, 220), 110, 220))
    base.alpha_composite(lights.filter(ImageFilter.GaussianBlur(1.2)))
    base.alpha_composite(lights)


def floor_glow(base):
    # the horizon line glows lime
    line = Image.new("RGBA", (W, 60), (0, 0, 0, 0))
    ld = ImageDraw.Draw(line)
    ld.rectangle([0, 28, W, 31], fill=LIME + (255,))
    base.alpha_composite(line.filter(ImageFilter.GaussianBlur(9)), (0, HORIZON - 30))
    base.alpha_composite(line, (0, HORIZON - 30))


def grid(phase):
    """The lime floor grid, rolling towards the viewer (phase 0..1 loops)."""
    g = Image.new("RGBA", (W, H - HORIZON), (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    fh = H - HORIZON
    cx = W / 2
    for k in range(-26, 27):
        x_far = cx + k * 46
        x_near = cx + k * 46 * 9
        d.line([(x_far, 0), (x_near, fh * 1.4)], fill=LIME + (90,), width=2)
    for i in range(16):
        z = (i + 1 - phase) / 16.0
        y = fh * (z ** 2.2)
        a = int(40 + 150 * z)
        d.line([(0, y), (W, y)], fill=LIME + (a,), width=2 if z > 0.4 else 1)
    fade = np.linspace(0.15, 1.0, fh)[:, None]
    arr = np.array(g)
    arr[..., 3] = (arr[..., 3] * fade).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


# ------------------------------------------------------------------ the phone

def device_layers():
    """The iPhone Duo, unfolded: the frame overlay and the rounded screen mask."""
    s = 2
    ow, oh = SCREEN_W + 2 * (BEZEL + BAND), SCREEN_H + 2 * (BEZEL + BAND)
    frame = Image.new("RGBA", (ow * s, oh * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(frame)
    r_out = (SCREEN_R + BEZEL + BAND) * s
    # metal band: graphite with a lighter rim
    d.rounded_rectangle([0, 0, ow * s - 1, oh * s - 1], radius=r_out, fill=(58, 60, 66, 255))
    d.rounded_rectangle([3 * s, 3 * s, ow * s - 1 - 3 * s, oh * s - 1 - 3 * s], radius=r_out - 3 * s, fill=(34, 35, 40, 255))
    d.rounded_rectangle([BAND * s, BAND * s, (ow - BAND) * s - 1, (oh - BAND) * s - 1], radius=(SCREEN_R + BEZEL) * s, fill=(6, 6, 8, 255))
    # the screen hole
    d.rounded_rectangle([(BAND + BEZEL) * s, (BAND + BEZEL) * s, (ow - BAND - BEZEL) * s - 1, (oh - BAND - BEZEL) * s - 1],
                        radius=SCREEN_R * s, fill=(0, 0, 0, 0))
    # buttons on the top edge
    for x0, x1 in [(ow - 300, ow - 230), (ow - 210, ow - 140), (190, 290)]:
        d.rounded_rectangle([x0 * s, -2 * s, x1 * s, 5 * s], radius=3 * s, fill=(70, 72, 78, 255))
    frame = frame.resize((ow, oh), Image.LANCZOS)
    # a soft highlight along the top of the band
    hl = Image.new("RGBA", (ow, oh), (0, 0, 0, 0))
    ImageDraw.Draw(hl).rounded_rectangle([2, 2, ow - 3, oh - 3], radius=r_out // s - 2, outline=(200, 205, 215, 90), width=2)
    mask_top = np.linspace(1.0, 0.15, oh)[:, None]
    a = np.array(hl)
    a[..., 3] = (a[..., 3] * mask_top).astype(np.uint8)
    frame.alpha_composite(Image.fromarray(a, "RGBA"))
    # the screen's own details: hinge crease and a punch-hole camera on the right panel
    over = Image.new("RGBA", (SCREEN_W, SCREEN_H), (0, 0, 0, 0))
    od = ImageDraw.Draw(over)
    cx = SCREEN_W // 2
    od.rectangle([cx - 1, 0, cx + 1, SCREEN_H], fill=(255, 255, 255, 14))
    od.rectangle([cx + 2, 0, cx + 5, SCREEN_H], fill=(0, 0, 0, 22))
    cam = (cx + SCREEN_W // 4, 26)
    od.ellipse([cam[0] - 11, cam[1] - 11, cam[0] + 11, cam[1] + 11], fill=(4, 4, 6, 255))
    od.ellipse([cam[0] - 4, cam[1] - 6, cam[0] + 1, cam[1] - 1], fill=(60, 70, 100, 200))
    # a faint glass sheen
    sheen = np.zeros((SCREEN_H, SCREEN_W, 4), np.uint8)
    xx = np.arange(SCREEN_W)[None, :]
    yy = np.arange(SCREEN_H)[:, None]
    band = np.exp(-(((xx * 0.55 + yy) - SCREEN_W * 0.42) / 120.0) ** 2)
    sheen[..., :3] = 255
    sheen[..., 3] = (band * 16).astype(np.uint8)
    over.alpha_composite(Image.fromarray(sheen, "RGBA"))
    mask = Image.new("L", (SCREEN_W * s, SCREEN_H * s), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, SCREEN_W * s - 1, SCREEN_H * s - 1], radius=SCREEN_R * s, fill=255)
    mask = mask.resize((SCREEN_W, SCREEN_H), Image.LANCZOS)
    return frame, over, mask


# ------------------------------------------------------------------ moving things

class Lantern:
    COLORS = [(224, 69, 43), (255, 196, 64), (255, 116, 71), (176, 92, 210), (236, 84, 120), (90, 160, 230)]

    def __init__(self, first=False):
        self.depth = rng.uniform(0.35, 1.0)
        self.x = rng.uniform(0, W)
        self.y = rng.uniform(80, HORIZON + 300) if first else HORIZON + rng.uniform(80, 260)
        self.speed = 22 + 40 * self.depth
        self.phase = rng.uniform(0, math.tau)
        c = rng.choice(self.COLORS)
        self.sprite = self._draw(c, int(34 + 46 * self.depth))

    @staticmethod
    def _draw(c, h):
        w = int(h * 0.72)
        pad = h
        img = Image.new("RGBA", (w + pad * 2, h * 2 + pad), (0, 0, 0, 0))
        glow = radial(int(h * 2.6), c, 2.4)
        img.alpha_composite(glow, ((img.width - glow.width) // 2, pad + h // 2 - glow.height // 2))
        d = ImageDraw.Draw(img)
        x0, y0 = pad, pad
        d.ellipse([x0, y0, x0 + w, y0 + h], fill=c + (255,))
        light = lerp_color(c, (255, 240, 200), 0.45)
        d.ellipse([x0 + w * 0.3, y0 + 2, x0 + w * 0.7, y0 + h - 2], fill=light + (255,))
        gold = (242, 190, 80, 255)
        d.rectangle([x0 + w * 0.25, y0 - 4, x0 + w * 0.75, y0 + 5], fill=gold)
        d.rectangle([x0 + w * 0.25, y0 + h - 5, x0 + w * 0.75, y0 + h + 4], fill=gold)
        d.line([(x0 + w / 2, y0 + h + 4), (x0 + w / 2, y0 + h + h * 0.45)], fill=gold, width=max(2, h // 18))
        return img

    def step(self, dt, t):
        self.y -= self.speed * dt
        if self.y < -140:
            self.__init__()

    def draw(self, base, t):
        x = self.x + math.sin(t * 0.6 + self.phase) * 18 * self.depth
        base.alpha_composite(self.sprite, (int(x - self.sprite.width / 2), int(self.y - self.sprite.height / 2)))


class Sparkle:
    """A four-point star that swells and fades."""

    def __init__(self):
        self.reset(rng.uniform(0, 4))

    def reset(self, delay=0.0):
        side = rng.random() < 0.5
        self.x = rng.uniform(40, SCREEN_X - 60) if side else rng.uniform(SCREEN_X + SCREEN_W + 60, W - 40)
        self.y = rng.uniform(60, HORIZON - 120)
        self.t0 = delay
        self.life = rng.uniform(1.6, 2.6)
        self.size = rng.randint(30, 64)
        self.color = rng.choice([(255, 186, 150), (230, 250, 170), (255, 255, 255)])
        self.sprite = self._draw()

    def _draw(self):
        s = self.size
        img = Image.new("RGBA", (s * 3, s * 3), (0, 0, 0, 0))
        img.alpha_composite(radial(s * 3, self.color, 3.0))
        d = ImageDraw.Draw(img)
        c = s * 1.5
        pts = []
        for i in range(8):
            a = i * math.pi / 4 - math.pi / 2
            r = s * (0.55 if i % 2 == 0 else 0.12)
            pts.append((c + math.cos(a) * r, c + math.sin(a) * r))
        d.polygon(pts, fill=self.color + (255,))
        return img

    def draw(self, base, t):
        k = (t - self.t0) / self.life
        if k < 0:
            return
        if k > 1:
            self.reset(t + rng.uniform(0.2, 1.5))
            return
        a = math.sin(k * math.pi)
        spr = self.sprite.resize((max(2, int(self.sprite.width * (0.4 + 0.6 * a))),) * 2, Image.BILINEAR)
        arr = np.array(spr)
        arr[..., 3] = (arr[..., 3] * a).astype(np.uint8)
        base.alpha_composite(Image.fromarray(arr, "RGBA"), (int(self.x - spr.width / 2), int(self.y - spr.height / 2)))


def star_field():
    pts = [(rng.uniform(0, W), rng.uniform(0, HORIZON * 0.7), rng.uniform(0.5, 1.6), rng.uniform(0, math.tau)) for _ in range(260)]
    return pts


# ------------------------------------------------------------------ main loop

def main():
    total = probe_frames(CLIP)
    base = sky()
    stars = star_field()
    retro_sun(base, 2290, HORIZON - 40, 250)
    skyline(base)
    floor_glow(base)
    grids = [grid(i / 60.0) for i in range(60)]
    frame, over, mask = device_layers()
    lanterns = [Lantern(first=True) for _ in range(26)]
    lanterns.sort(key=lambda l: l.depth)
    sparkles = [Sparkle() for _ in range(7)]
    font = ImageFont.truetype(str(ROOT / "assets/fonts/Nunito/Nunito-Bold.ttf"), 30)
    halo = radial(1900, (255, 140, 90), 2.0)
    shadow = Image.new("RGBA", (SCREEN_W + 300, 200), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse([60, 60, SCREEN_W + 240, 140], fill=(0, 0, 0, 200))
    shadow = shadow.filter(ImageFilter.GaussianBlur(30))
    fade = np.linspace(0.32, 0.0, 260)[:, None]

    dec = subprocess.Popen([FFMPEG, "-v", "error", "-i", CLIP, "-vf", f"scale={SCREEN_W}:{SCREEN_H}:flags=lanczos",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen([FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-i", CLIP, "-map", "0:v", "-map", "1:a",
                            "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-profile:v", "high", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    n = SCREEN_W * SCREEN_H * 3
    for f in range(total):
        raw = dec.stdout.read(n)
        if len(raw) < n:
            break
        t = f / FPS
        img = base.copy()
        # twinkling stars (an RGBA draw blends instead of overwriting the alpha)
        sd = ImageDraw.Draw(img, "RGBA")
        for (x, y, r, ph) in stars:
            a = int(110 + 110 * math.sin(t * 2.0 + ph))
            sd.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, a))
        img.alpha_composite(grids[f % 60], (0, HORIZON))
        for l in lanterns:
            l.step(1 / FPS, t)
            l.draw(img, t)
        for s in sparkles:
            s.draw(img, t)
        bob = int(round(math.sin(t * 0.9) * 7))
        sx, sy = SCREEN_X, SCREEN_Y + bob
        img.alpha_composite(halo, (W // 2 - halo.width // 2, sy + SCREEN_H // 2 - halo.height // 2))
        img.alpha_composite(shadow, (sx - 150, SCREEN_Y + SCREEN_H + 40))
        screen = Image.frombytes("RGB", (SCREEN_W, SCREEN_H), raw).convert("RGBA")
        screen.alpha_composite(over)
        screen.putalpha(mask)
        device = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        device.alpha_composite(screen, (BEZEL + BAND, BEZEL + BAND))
        device.alpha_composite(frame)
        # the reflection on the floor
        refl = device.transpose(Image.FLIP_TOP_BOTTOM).crop((0, 0, device.width, 260))
        ra = np.array(refl)
        ra[..., 3] = (ra[..., 3] * fade).astype(np.uint8)
        dx, dy = sx - BEZEL - BAND, sy - BEZEL - BAND
        img.alpha_composite(Image.fromarray(ra, "RGBA"), (dx, dy + device.height + 6))
        img.alpha_composite(device, (dx, dy))
        sd = ImageDraw.Draw(img, "RGBA")
        sd.text((W // 2, H - 44), "vgang.studio", font=font, fill=(213, 246, 75, 120), anchor="mm")
        enc.stdin.write(img.convert("RGB").tobytes())
        if f % 300 == 0:
            print(f"frame {f}/{total}", flush=True)
    enc.stdin.close()
    enc.wait()
    dec.wait()
    print("wrote", OUT)


if __name__ == "__main__":
    main()
