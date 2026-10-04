#!/usr/bin/env python3
"""Frames the Đà Nẵng – Hội An trailer in an iPhone Duo on an animated dusk backdrop, in 4K.

Reads the cut gameplay clip (the Duo's unfolded screen, ideally already 2220x1526), and for
every frame:
  - draws the backdrop: a dusk sky with stars, a setting retro sun behind Hội An's roofs, the
    Dragon Bridge and Marble Mountains on the left, Bà Nà's Golden Bridge on the right, silk
    lanterns drifting up and a lime perspective grid rolling towards the viewer
  - floats the phone in the middle with its reflection on the floor. The screen shape is the
    real iPhone Duo's, taken from the simulator (tools/iphone_duo_screen.png: big rounded top
    corners, small bottom ones, the front camera at the top left; no crease)
Everything that moves is placed with sub-pixel precision, so slow drifts don't step.

Writes a ProRes 422 HQ master (.mov, PCM sound) and, if a second path is given, an H.264
copy for upload. 3840x2160, 60 fps.

usage: frame_trailer.py GAME_CLIP MASTER.mov FFMPEG [UPLOAD.mp4]
"""
import math
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

CLIP, MASTER, FFMPEG = sys.argv[1], sys.argv[2], sys.argv[3]
UPLOAD = sys.argv[4] if len(sys.argv) > 4 else None
ROOT = Path(__file__).resolve().parent.parent
W, H, FPS = 3840, 2160, 60
K = W / 2560  # the layout is designed on a 2560x1440 canvas
HORIZON = round(1010 * K)
SCREEN_W, SCREEN_H = 2220, 1526  # the Duo's 2034x1398 screen at 4K
SCREEN_X, SCREEN_Y = (W - SCREEN_W) // 2, round(168 * K)
BEZEL, BAND = round(16 * K), round(11 * K)  # black glass border, then the metal band
LIME, ORANGE = (213, 246, 75), (255, 116, 71)
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


def shifted(img, fx, fy):
    """`img` moved right/down by a fraction of a pixel (0 ≤ fx, fy < 1), one pixel larger."""
    return img.transform((img.width + 1, img.height + 1), Image.AFFINE, (1, 0, -fx, 0, 1, -fy), Image.BICUBIC)


def paste(base, img, x, y):
    """Alpha-composites `img` at a fractional position."""
    ix, iy = math.floor(x), math.floor(y)
    base.alpha_composite(shifted(img, x - ix, y - iy), (ix, iy))


# ------------------------------------------------------------------ the static backdrop

def sky():
    top, mid, low = (10, 12, 38), (58, 28, 78), (255, 132, 84)
    y = np.linspace(0, 1, HORIZON)[:, None]
    t1 = np.clip(y / 0.62, 0, 1)
    t2 = np.clip((y - 0.62) / 0.38, 0, 1) ** 1.4
    c = np.zeros((HORIZON, W, 3), np.float32)
    for i in range(3):
        c[..., i] = top[i] + (mid[i] - top[i]) * t1 + (low[i] - mid[i]) * t2
    # a little noise keeps the long gradient from banding in 8-bit
    c += np.random.default_rng(3).uniform(-0.6, 0.6, c.shape)
    img = np.zeros((H, W, 3), np.uint8)
    img[:HORIZON] = np.clip(c, 0, 255).astype(np.uint8)
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
    for k in range(7):
        y0 = 0.56 + k * 0.064
        hgt = 0.008 + k * 0.006
        alpha[(v > y0) & (v < y0 + hgt)] = 0
    col[..., 3] = alpha * 255
    sun = np.array(Image.fromarray(col.astype(np.uint8), "RGBA").resize((r * 2, r * 2), Image.LANCZOS))
    cut = HORIZON - (cy - r)  # nothing of it below the horizon
    if 0 < cut < sun.shape[0]:
        sun[cut:, :, 3] = 0
    glow = radial(r * 5, (255, 150, 90), 2.2)
    base.alpha_composite(glow, (cx - glow.width // 2, cy - glow.height // 2))
    base.alpha_composite(Image.fromarray(sun, "RGBA"), (cx - r, cy - r))
    # its shimmer on the floor
    sh = Image.new("RGBA", (r * 2, round(140 * K)), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    for k in range(9):
        w = r * (1.6 - k * 0.15)
        y = (8 + k * 14) * K
        sd.rectangle([r - w / 2, y, r + w / 2, y + 4 * K], fill=ORANGE + (int(150 - k * 15),))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(2 * K)), (cx - r, HORIZON + round(4 * K)))


def skyline(base):
    """Silhouettes along the horizon, drawn in 2560-space at 2x for clean edges."""
    s = 2 * K
    layer = Image.new("RGBA", (round(2560 * s), round(1440 * s)), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    far, near, mid = (44, 24, 70, 255), (24, 14, 42, 255), (36, 20, 60, 255)
    hz = 1010 * s
    # far hills along the whole horizon
    pts = [(0, hz)]
    for x in range(0, 2600, 20):
        pts.append((x * s, hz - (40 + 30 * math.sin(x * 0.0021 * 2) + 22 * math.sin(x * 0.0057 * 2 + 1.0)) * s))
    pts.append((2560 * s, hz))
    d.polygon(pts, fill=far)
    # left: the Marble Mountains, steep peaks with a stupa on the tallest
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
    # Dragon Bridge: the deck and the arching dragon, catching the last of the sun
    deck_y = hz - 70 * s
    d.rectangle([0, deck_y, 520 * s, deck_y + 12 * s], fill=near)
    for px in range(20, 520, 46):
        d.rectangle([px * s, deck_y, (px + 10) * s, hz], fill=near)
    body = [(x * s, deck_y - (10 + 60 * max(0.0, math.sin((x - 10) / 470 * 3 * math.pi))) * s) for x in range(0, 470, 2)]
    gold = (196, 132, 44, 255)
    for i in range(len(body) - 1):
        d.line([body[i], body[i + 1]], fill=gold, width=round(16 * s))
    hx, hy = 470 * s, deck_y - 70 * s
    d.line([body[-1], (hx, hy)], fill=gold, width=round(16 * s))
    d.polygon([(hx - 10 * s, hy - 14 * s), (hx + 44 * s, hy - 6 * s), (hx + 38 * s, hy + 12 * s), (hx - 6 * s, hy + 14 * s)], fill=gold)
    d.polygon([(hx, hy - 12 * s), (hx - 14 * s, hy - 40 * s), (hx + 10 * s, hy - 14 * s)], fill=gold)
    for i in range(0, len(body) - 1, 3):
        d.line([body[i][0], body[i][1] - 6 * s, body[i + 1][0], body[i + 1][1] - 6 * s], fill=(255, 200, 90, 255), width=round(3 * s))
    # right: Bà Nà's peak with the Golden Bridge loop and the two hands
    bx = 2380 * s
    d.polygon([(2120 * s, hz), (bx - 120 * s, hz - 330 * s), (bx - 40 * s, hz - 380 * s), (bx + 60 * s, hz - 360 * s), (2560 * s, hz - 250 * s), (2560 * s, hz)], fill=far)
    by = hz - 300 * s
    for hxx in (bx - 70 * s, bx + 50 * s):
        d.rectangle([hxx - 9 * s, by, hxx + 9 * s, hz - 200 * s], fill=near)
    box = [bx - 120 * s, by - 34 * s, bx + 100 * s, by + 34 * s]
    d.arc(box, 200, 340, fill=(255, 205, 90, 255), width=round(7 * s))
    d.arc(box, 20, 160, fill=(255, 205, 90, 255), width=round(9 * s))
    # right: Hội An's roofs with curled eaves (the sun sets behind them)
    x = 2075
    while x < 2560:
        w = rng.choice([110, 130, 150])
        h = rng.choice([90, 120, 150])
        d.rectangle([x * s, hz - h * s, (x + w - 8) * s, hz], fill=near)
        d.polygon([((x - 16) * s, hz - h * s), ((x + w * 0.5) * s, hz - (h + 46) * s), ((x + w + 8) * s, hz - h * s)], fill=near)
        d.ellipse([(x - 24) * s, hz - (h + 10) * s, (x - 8) * s, hz - (h - 6) * s], fill=near)
        d.ellipse([(x + w) * s, hz - (h + 10) * s, (x + w + 16) * s, hz - (h - 6) * s], fill=near)
        x += w + 6
    base.alpha_composite(layer.resize((W, H), Image.LANCZOS))
    # warm windows and lights along the bridge
    lights = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lights)
    for px in range(14, 520, 26):
        ld.ellipse([(px - 3) * K, HORIZON - 76 * K, (px + 3) * K, HORIZON - 70 * K], fill=(255, 210, 120, 255))
    for i in range(46):
        wx = rng.randint(2080, 2550) * K
        wy = HORIZON - rng.randint(20, 120) * K
        ld.rectangle([wx, wy, wx + 7 * K, wy + 9 * K], fill=(255, rng.randint(170, 220), 110, 220))
    base.alpha_composite(lights.filter(ImageFilter.GaussianBlur(1.2 * K)))
    base.alpha_composite(lights)


def floor_glow(base):
    line = Image.new("RGBA", (W, round(60 * K)), (0, 0, 0, 0))
    ImageDraw.Draw(line).rectangle([0, 28 * K, W, 31 * K], fill=LIME + (255,))
    base.alpha_composite(line.filter(ImageFilter.GaussianBlur(9 * K)), (0, HORIZON - round(30 * K)))
    base.alpha_composite(line, (0, HORIZON - round(30 * K)))


def grid(phase):
    """The lime floor grid, rolling towards the viewer (phase 0..1 loops), drawn at 2x."""
    s = 2
    fh = H - HORIZON
    g = Image.new("RGBA", (W * s, fh * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    cx = W * s / 2
    for k in range(-26, 27):
        d.line([(cx + k * 46 * K * s, 0), (cx + k * 46 * 9 * K * s, fh * s * 1.4)], fill=LIME + (90,), width=round(2 * K * s))
    for i in range(16):
        z = (i + 1 - phase) / 16.0
        y = fh * s * (z ** 2.2)
        d.line([(0, y), (W * s, y)], fill=LIME + (int(40 + 150 * z),), width=round((2 if z > 0.4 else 1) * K * s))
    g = g.resize((W, fh), Image.LANCZOS)
    arr = np.array(g)
    arr[..., 3] = (arr[..., 3] * np.linspace(0.15, 1.0, fh)[:, None]).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


# ------------------------------------------------------------------ the phone

def grown(mask, d):
    """The mask grown outward by about `d` pixels, with soft edges (blur, then a threshold
    placed two sigmas out)."""
    a = np.array(mask.filter(ImageFilter.GaussianBlur(d / 2.0)), np.float32) / 255.0
    return Image.fromarray((np.clip((a - 0.0228) / 0.03, 0, 1) * 255).astype(np.uint8), "L")


def device_layers():
    """The unfolded iPhone Duo: the screen mask (the simulator's own), the bezel and band."""
    real = Image.open(ROOT / "tools/iphone_duo_screen.png").convert("L")
    screen_mask = real.resize((SCREEN_W, SCREEN_H), Image.LANCZOS)
    pad = BEZEL + BAND + 4
    ow, oh = SCREEN_W + 2 * pad, SCREEN_H + 2 * pad
    m = Image.new("L", (ow, oh), 0)
    m.paste(screen_mask, (pad, pad))
    glass = grown(m, BEZEL)
    body = grown(m, BEZEL + BAND)
    rim = grown(m, BEZEL + BAND - round(2.5 * K))
    frame = Image.new("RGBA", (ow, oh), (0, 0, 0, 0))
    frame.paste(Image.new("RGBA", (ow, oh), (62, 64, 70, 255)), (0, 0), body)  # the graphite band's lit edge
    frame.paste(Image.new("RGBA", (ow, oh), (34, 35, 40, 255)), (0, 0), rim)
    frame.paste(Image.new("RGBA", (ow, oh), (5, 5, 7, 255)), (0, 0), glass)
    # cut the screen out of the glass
    fa = np.array(frame)
    fa[..., 3] = np.minimum(fa[..., 3], 255 - np.array(m))
    frame = Image.fromarray(fa, "RGBA")
    # light catching the top of the band
    hl = np.zeros((oh, ow, 4), np.uint8)
    edge = np.array(body, np.int16) - np.array(rim, np.int16)
    hl[..., :3] = (205, 210, 220)
    hl[..., 3] = np.clip(edge * np.linspace(0.55, 0.05, oh)[:, None], 0, 255).astype(np.uint8)
    frame.alpha_composite(Image.fromarray(hl, "RGBA"))
    # buttons on the top edge
    bd = ImageDraw.Draw(frame)
    for x0, x1 in [(ow - 450, ow - 345), (ow - 315, ow - 210), (285, 435)]:
        bd.rounded_rectangle([x0, pad - BEZEL - BAND - round(4 * K), x1, pad - BEZEL - BAND + round(3 * K)], radius=round(4 * K), fill=(70, 72, 78, 255))
    # the front camera, where the simulator draws it (top left), and a faint glass sheen
    over = Image.new("RGBA", (SCREEN_W, SCREEN_H), (0, 0, 0, 0))
    od = ImageDraw.Draw(over)
    sc = SCREEN_W / real.width
    cam = np.array(real)[..., :3].max(axis=2) < 12
    ys, xs = np.where(cam[:400, :400] & (alpha[:400, :400] > 128))
    if len(xs):
        ccx, ccy, cr = (xs.min() + xs.max()) / 2 * sc, (ys.min() + ys.max()) / 2 * sc, (xs.max() - xs.min()) / 2 * sc
        od.ellipse([ccx - cr, ccy - cr, ccx + cr, ccy + cr], fill=(3, 3, 5, 255))
        od.ellipse([ccx - cr * 0.35, ccy - cr * 0.5, ccx + cr * 0.05, ccy - cr * 0.1], fill=(55, 65, 95, 200))
    sheen = np.zeros((SCREEN_H, SCREEN_W, 4), np.uint8)
    xx = np.arange(SCREEN_W)[None, :]
    yy = np.arange(SCREEN_H)[:, None]
    sheen[..., :3] = 255
    sheen[..., 3] = (np.exp(-(((xx * 0.55 + yy) - SCREEN_W * 0.42) / (120 * K)) ** 2) * 14).astype(np.uint8)
    over.alpha_composite(Image.fromarray(sheen, "RGBA"))
    return frame, over, screen_mask, pad


# ------------------------------------------------------------------ moving things

class Lantern:
    COLORS = [(224, 69, 43), (255, 196, 64), (255, 116, 71), (176, 92, 210), (236, 84, 120), (90, 160, 230)]

    def __init__(self, first=False):
        self.depth = rng.uniform(0.35, 1.0)
        self.x = rng.uniform(0, W)
        self.y = rng.uniform(80 * K, HORIZON + 300 * K) if first else HORIZON + rng.uniform(80, 260) * K
        self.speed = (22 + 40 * self.depth) * K
        self.phase = rng.uniform(0, math.tau)
        self.sprite = self._draw(rng.choice(self.COLORS), int((34 + 46 * self.depth) * K))

    @staticmethod
    def _draw(c, h):
        w = int(h * 0.72)
        pad = h
        img = Image.new("RGBA", (w + pad * 2, h * 2 + pad), (0, 0, 0, 0))
        glow = radial(int(h * 2.6), c, 2.4)
        img.alpha_composite(glow, ((img.width - glow.width) // 2, pad + h // 2 - glow.height // 2))
        # the lantern itself at 2x, scaled down for smooth edges
        s = 2
        body = Image.new("RGBA", (w * s + 8, int(h * 1.6) * s), (0, 0, 0, 0))
        d = ImageDraw.Draw(body)
        x0, y0 = 4, 6 * s
        d.ellipse([x0, y0, x0 + w * s, y0 + h * s], fill=c + (255,))
        d.ellipse([x0 + w * s * 0.3, y0 + 2, x0 + w * s * 0.7, y0 + h * s - 2], fill=lerp_color(c, (255, 240, 200), 0.45) + (255,))
        gold = (242, 190, 80, 255)
        d.rectangle([x0 + w * s * 0.25, y0 - 4 * s, x0 + w * s * 0.75, y0 + 5 * s], fill=gold)
        d.rectangle([x0 + w * s * 0.25, y0 + h * s - 5 * s, x0 + w * s * 0.75, y0 + h * s + 4 * s], fill=gold)
        d.line([(x0 + w * s / 2, y0 + h * s + 4 * s), (x0 + w * s / 2, y0 + h * s * 1.45)], fill=gold, width=max(2, h * s // 18))
        body = body.resize((body.width // s, body.height // s), Image.LANCZOS)
        img.alpha_composite(body, (pad - 2, pad - 6))
        return img

    def step(self, dt):
        self.y -= self.speed * dt
        if self.y < -140 * K:
            self.__init__()

    def draw(self, base, t):
        x = self.x + math.sin(t * 0.6 + self.phase) * 18 * self.depth * K
        paste(base, self.sprite, x - self.sprite.width / 2, self.y - self.sprite.height / 2)


class Sparkle:
    """A four-point star that swells and fades."""

    def __init__(self):
        self.reset(rng.uniform(0, 4))

    def reset(self, delay=0.0):
        left = rng.random() < 0.5
        self.x = rng.uniform(40 * K, SCREEN_X - 60 * K) if left else rng.uniform(SCREEN_X + SCREEN_W + 60 * K, W - 40 * K)
        self.y = rng.uniform(60 * K, HORIZON - 120 * K)
        self.t0 = delay
        self.life = rng.uniform(1.6, 2.6)
        self.size = int(rng.randint(30, 64) * K)
        self.color = rng.choice([(255, 186, 150), (230, 250, 170), (255, 255, 255)])
        s = self.size
        img = Image.new("RGBA", (s * 3, s * 3), (0, 0, 0, 0))
        img.alpha_composite(radial(s * 3, self.color, 3.0))
        star = Image.new("RGBA", (s * 6, s * 6), (0, 0, 0, 0))
        c = s * 3
        pts = [(c + math.cos(i * math.pi / 4 - math.pi / 2) * s * 2 * (0.55 if i % 2 == 0 else 0.12),
                c + math.sin(i * math.pi / 4 - math.pi / 2) * s * 2 * (0.55 if i % 2 == 0 else 0.12)) for i in range(8)]
        ImageDraw.Draw(star).polygon(pts, fill=self.color + (255,))
        img.alpha_composite(star.resize((s * 3, s * 3), Image.LANCZOS))
        self.sprite = img

    def draw(self, base, t):
        k = (t - self.t0) / self.life
        if k < 0:
            return
        if k > 1:
            self.reset(t + rng.uniform(0.2, 1.5))
            return
        a = math.sin(k * math.pi)
        size = max(2, int(self.sprite.width * (0.4 + 0.6 * a)))
        spr = np.array(self.sprite.resize((size, size), Image.BICUBIC))
        spr[..., 3] = (spr[..., 3] * a).astype(np.uint8)
        paste(base, Image.fromarray(spr, "RGBA"), self.x - size / 2, self.y - size / 2)


# ------------------------------------------------------------------ main loop

def main():
    total = probe_frames(CLIP)
    base = sky()
    stars = [(rng.uniform(0, W), rng.uniform(0, HORIZON * 0.7), rng.uniform(0.5, 1.6) * K, rng.uniform(0, math.tau)) for _ in range(300)]
    retro_sun(base, round(2290 * K), HORIZON - round(40 * K), round(250 * K))
    skyline(base)
    floor_glow(base)
    grids = [grid(i / 60.0) for i in range(60)]
    frame, over, mask, pad = device_layers()
    lanterns = sorted((Lantern(first=True) for _ in range(28)), key=lambda l: l.depth)
    sparkles = [Sparkle() for _ in range(8)]
    font = ImageFont.truetype(str(ROOT / "assets/fonts/Nunito/Nunito-Bold.ttf"), round(30 * K))
    halo = radial(round(1900 * K), (255, 140, 90), 2.0)
    shadow = Image.new("RGBA", (SCREEN_W + round(300 * K), round(200 * K)), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse([60 * K, 60 * K, SCREEN_W + 240 * K, 140 * K], fill=(0, 0, 0, 200))
    shadow = shadow.filter(ImageFilter.GaussianBlur(30 * K))
    refl_h = round(260 * K)
    fade = np.linspace(0.32, 0.0, refl_h)[:, None]

    dec = subprocess.Popen([FFMPEG, "-v", "error", "-i", CLIP, "-vf", f"scale={SCREEN_W}:{SCREEN_H}:flags=lanczos",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen([FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-i", CLIP, "-map", "0:v", "-map", "1:a",
                            "-c:v", "prores_ks", "-profile:v", "3", "-vendor", "apl0", "-pix_fmt", "yuv422p10le",
                            "-c:a", "pcm_s16le", "-shortest", MASTER], stdin=subprocess.PIPE)
    n = SCREEN_W * SCREEN_H * 3
    for f in range(total):
        raw = dec.stdout.read(n)
        if len(raw) < n:
            break
        t = f / FPS
        img = base.copy()
        sd = ImageDraw.Draw(img, "RGBA")  # RGBA drawing blends rather than overwriting alpha
        for (x, y, r, ph) in stars:
            sd.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, int(110 + 110 * math.sin(t * 2.0 + ph))))
        img.alpha_composite(grids[f % 60], (0, HORIZON))
        for l in lanterns:
            l.step(1 / FPS)
            l.draw(img, t)
        for s in sparkles:
            s.draw(img, t)
        bob = math.sin(t * 0.9) * 7 * K
        sy = SCREEN_Y + bob
        img.alpha_composite(halo, (W // 2 - halo.width // 2, round(sy + SCREEN_H / 2 - halo.height / 2)))
        img.alpha_composite(shadow, (SCREEN_X - round(150 * K), SCREEN_Y + SCREEN_H + round(40 * K)))
        screen = Image.frombytes("RGB", (SCREEN_W, SCREEN_H), raw).convert("RGBA")
        screen.alpha_composite(over)
        screen.putalpha(mask)
        device = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        device.alpha_composite(screen, (pad, pad))
        device.alpha_composite(frame)
        # the reflection on the floor, then the phone, both at their exact sub-pixel height
        refl = np.array(device.transpose(Image.FLIP_TOP_BOTTOM).crop((0, pad, device.width, pad + refl_h)))
        refl[..., 3] = (refl[..., 3] * fade).astype(np.uint8)
        dx, dy = SCREEN_X - pad, sy - pad
        paste(img, Image.fromarray(refl, "RGBA"), dx, dy + device.height - pad + 6 * K)
        paste(img, device, dx, dy)
        sd = ImageDraw.Draw(img, "RGBA")
        sd.text((W // 2, H - round(44 * K)), "vgang.studio", font=font, fill=(213, 246, 75, 120), anchor="mm")
        enc.stdin.write(img.convert("RGB").tobytes())
        if f % 300 == 0:
            print(f"frame {f}/{total}", flush=True)
    enc.stdin.close()
    enc.wait()
    dec.wait()
    print("wrote", MASTER)
    if UPLOAD:
        # a high-quality H.264 copy for social upload (they re-encode anyway)
        subprocess.run([FFMPEG, "-y", "-v", "error", "-i", MASTER, "-c:v", "libx264", "-preset", "slow", "-crf", "12",
                        "-profile:v", "high", "-level", "5.2", "-pix_fmt", "yuv420p", "-g", "60",
                        "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", UPLOAD], check=True)
        print("wrote", UPLOAD)


if __name__ == "__main__":
    main()
