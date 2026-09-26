"""Blocks and drums: drum_block ("?"), used_block, brick_block, jelly_block (bánh chưng),
drum_spring, crusher, drum_big (finale stage)."""

import math
import os

from mathutils import Matrix, Vector

import motifs
from lib import (TAU, Part, densify, ellipse_points, face_frame, join_parts, mat4, profile_radius,
                 rng, rounded_rect_points, star_points, text_part)

ROUNDED_FONT = "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf"
SIDES = [Vector((0, -1, 0)), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((-1, 0, 0))]


def _font():
    return ROUNDED_FONT if os.path.exists(ROUNDED_FONT) else None


def _top_drum_face(star_part, ring_part, F, r_star=0.3, r_ring=(0.34, 0.4)):
    motifs.ring(ring_part, r_ring[0], r_ring[1], -0.01, 0.03, F, segs=32, round_top=False)
    star_part.faceted_star(14, r_star, 0.11, 0.05, 0.014, F, rot=90.0, back=False)


# --------------------------------------------------------------------------------------------
def drum_block(col):
    """The "?" block: bevelled bronze cube, drum sunburst + raised gold "?" on every side.
    The core is 0.9 wide so the relief stays inside the 1.0 m cube."""
    C, T = 0.45, 0.95
    core = Part("M_Bronze", smooth=40, bevel=(0.07, 3))
    core.box((-C, -C, 0.0), (C, C, T))
    gold = Part("M_Gold", smooth=40)
    burst = Part("M_BronzeLight", smooth=None)
    q = Part("M_GoldLight", smooth=35)
    for w in SIDES:
        F = face_frame(w, w * C + Vector((0, 0, T / 2)))
        motifs.ring(gold, 0.33, 0.39, -0.01, 0.03, F, segs=28, round_top=False)
        motifs.raised_star(burst, 14, 0.29, 0.19, -0.01, 0.022, F, inset=0.9)
        motifs.question_mark(q, F, h=0.5, width=0.105, depth=0.05)
    F = face_frame((0, 0, 1), (0, 0, T))
    _top_drum_face(gold, gold, F, r_ring=(0.33, 0.39))
    gold.sphere(0.05, F, segs=10, rings=5, scale=(1, 1, 0.9))
    return [join_parts("drum_block", [core, gold, burst, q], col)]


def used_block(col):
    """The emptied drum block: dark bronze, faint rings and four rivets per side."""
    C, T = 0.47, 0.97
    core = Part("M_BronzeDark", smooth=40, bevel=(0.07, 3))
    core.box((-C, -C, 0.0), (C, C, T))
    trim = Part("M_Bronze", smooth=40)
    for w in SIDES + [Vector((0, 0, 1))]:
        c = w * C + Vector((0, 0, T / 2)) if w.z < 0.5 else Vector((0, 0, T))
        F = face_frame(w, c)
        motifs.ring(trim, 0.33, 0.37, -0.01, 0.025, F, segs=28, round_top=False)
        for sx in (-1, 1):
            for sy in (-1, 1):
                trim.sphere(0.035, F @ mat4((sx * 0.36, sy * 0.36, 0)), segs=8, rings=4, scale=(1, 1, 0.6))
    return [join_parts("used_block", [core, trim], col)]


# --------------------------------------------------------------------------------------------
def brick_block(col):
    """Terracotta brick cube: chunky bevelled bricks in running bond over a mortar core."""
    mortar = Part("M_Mortar", smooth=30)
    mortar.cube(0.93, mat4((0, 0, 0.465)))
    b1 = Part("M_Terracotta", smooth=50, bevel=(0.022, 1))
    b2 = Part("M_TerracottaDark", smooth=50, bevel=(0.022, 1))
    r = rng(7)
    D, G = 0.12, 0.028          # brick depth, mortar gap
    top_t = D
    rows = 4
    row_h = (1.0 - top_t) / rows
    for fi, w in enumerate(SIDES):
        F = face_frame(w, w * 0.5)
        for ri in range(rows):
            z0 = ri * row_h + G / 2
            z1 = (ri + 1) * row_h - G / 2
            owns = (ri + fi) % 2 == 0      # which face's brick covers the corner on this row
            x_lo, x_hi = (-0.5, 0.5) if owns else (-0.5 + D + G, 0.5 - D - G)
            offset = 0.25 if ri % 2 else 0.0
            cuts = [x_lo] + [c for c in (-0.5 + offset + 0.5 * k for k in range(0, 4)) if x_lo + 0.1 < c < x_hi - 0.1] + [x_hi]
            for a, b in zip(cuts, cuts[1:]):
                part = b1 if r() > 0.3 else b2
                part.box((a + G / 2 if a > x_lo else a, z0, -D), (b - G / 2 if b < x_hi else b, z1, 0.0), F)
    # top course
    F = face_frame((0, 0, 1), (0, 0, 1.0))
    trows = 4
    th = 1.0 / trows
    for ri in range(trows):
        y0 = -0.5 + ri * th + (G / 2 if ri else 0)
        y1 = -0.5 + (ri + 1) * th - (G / 2 if ri < trows - 1 else 0)
        offset = 0.25 if ri % 2 else 0.0
        cuts = [-0.5] + [c for c in (-0.5 + offset + 0.5 * k for k in range(0, 4)) if -0.4 < c < 0.4] + [0.5]
        for a, b in zip(cuts, cuts[1:]):
            part = b1 if r() > 0.3 else b2
            part.box((a + (G / 2 if a > -0.5 else 0), y0, -D), (b - (G / 2 if b < 0.5 else 0), y1, 0.0), F)
    return [join_parts("brick_block", [mortar, b1, b2], col)]


# --------------------------------------------------------------------------------------------
def jelly_block(col):
    """Bánh chưng jelly cube: soft rounded green cube tied with bamboo strings (# pattern).
    Strings run over the top and down the sides, tucked under the rounded bottom edge."""
    H = 0.76
    body = Part("M_Jelly", smooth=180)
    body.rounded_box((H, H, H), 0.3, n=8, m=mat4((0, 0, H)))
    string = Part("M_String", smooth=50)
    rect = [(-0.05, -0.016), (0.05, -0.016), (0.05, 0.016), (-0.05, 0.016)]
    for c in (-0.3, 0.3):
        for axis in ("x", "y"):
            off = 0.014 if axis == "x" else 0.026
            pts2 = rounded_rect_points(2 * (H + off), 2 * (H + off), 0.3 + off, seg=5)
            # a U over the top: drop the bottom edge, keep half of each bottom corner
            thr = -(H + off) + 0.5 * (0.3 + off)
            kept = [p for p in pts2 if p[1] > thr]
            k = next(i for i, p in enumerate(kept) if p[0] > 0 and p[1] < 0)
            arc = kept[k:] + kept[:k]
            if axis == "x":   # U in the XZ plane at y = c
                path = [Vector((x, c, z + H)) for x, z in arc]
                up = (0, 1, 0)
            else:             # U in the YZ plane at x = c
                path = [Vector((c, y, z + H)) for y, z in arc]
                up = (1, 0, 0)
            string.tube(path, 1.0, section=rect, up=up, caps=True)
    knots = Part("M_String", smooth=50)
    for x in (-0.3, 0.3):
        for y in (-0.3, 0.3):
            knots.sphere(0.055, mat4((x, y, 2 * H + 0.035)), segs=10, rings=5, scale=(1, 1, 0.55))
    return [join_parts("jelly_block", [body, string, knots], col)]


# --------------------------------------------------------------------------------------------
def _band(part, prof, z, w, t, segs):
    r = profile_radius(prof, z)
    part.lathe([(r - 0.02, z - w / 2), (r + t * 0.7, z - w / 2), (r + t, z), (r + t * 0.7, z + w / 2),
                (r - 0.02, z + w / 2)], segs, closed=True)


def drum_spring(col):
    """A squat bronze drum bounce pad: star + rings on the membrane, four patina frogs."""
    body = Part("M_Bronze", smooth=40)
    Hd = 0.44
    base = [(0.0, 0.0), (0.6, 0.0), (0.65, 0.012), (0.665, 0.04), (0.62, 0.08), (0.575, 0.15),
            (0.57, 0.24), (0.6, 0.3), (0.655, 0.37), (0.68, 0.43), (0.7, 0.455), (0.7, 0.483),
            (0.686, 0.5)]
    prof = [(r, z * Hd / 0.5) for r, z in base]
    body.lathe(prof, 40, cap1=False)
    top = Part("M_BronzeLight", smooth=40)
    top.lathe([(0.686, Hd), (0.0, Hd)], 40)
    dark = Part("M_BronzeDark", smooth=45)
    _band(dark, prof, 0.18, 0.028, 0.02, 40)
    _band(dark, prof, 0.29, 0.028, 0.02, 40)
    gold = Part("M_Gold", smooth=None)
    F = Matrix.Translation((0, 0, Hd))
    gold.faceted_star(12, 0.33, 0.12, 0.05, 0.016, F, rot=90.0, back=False)
    rings = Part("M_Bronze", smooth=45)
    motifs.ring(rings, 0.37, 0.4, -0.01, 0.025, F, segs=40, round_top=False)
    motifs.ring(rings, 0.6, 0.64, -0.01, 0.025, F, segs=40, round_top=False)
    motifs.tick_ring(rings, 0.5, 28, 0.13, 0.022, 0.02, -0.005, F)
    frog_b = Part("M_Patina", smooth=60)
    frog_e = Part("M_Gold", smooth=60)
    for i in range(4):
        a = math.radians(45 + 90 * i)
        m = mat4((0.55 * math.cos(a), 0.55 * math.sin(a), Hd - 0.01), (0, 0, math.degrees(a) + 90))
        motifs.frog(frog_b, frog_e, m, s=0.1, lod=0)
    return [join_parts("drum_spring", [body, top, dark, gold, rings, frog_b, frog_e], col)]


# --------------------------------------------------------------------------------------------
def _wrap_front(part, R):
    """Map flat face coordinates (x along the arc, y up, z outward) onto the -Y side of a
    vertical cylinder of radius R."""
    def f(v):
        a = -math.pi / 2 + v.x / R
        r = R + v.z
        return Vector((r * math.cos(a), r * math.sin(a), v.y))
    part.deform(f)


def crusher(col):
    """Heavy bronze drum crusher (Thwomp role), flat side down, angry face on the front."""
    R, H = 0.84, 0.85
    body = Part("M_Bronze", smooth=40)
    prof = [(0.0, 0.0), (R - 0.1, 0.0), (R - 0.04, 0.01), (R - 0.007, 0.045), (R, 0.1), (R, H - 0.1),
            (R - 0.007, H - 0.045), (R - 0.04, H - 0.01), (R - 0.1, H), (0.0, H)]
    body.lathe(prof, 48)
    dark = Part("M_BronzeDark", smooth=45)
    bands = (0.085, H - 0.085)
    for z in bands:
        dark.lathe([(R - 0.02, z - 0.035), (R + 0.025, z - 0.035), (R + 0.035, z), (R + 0.025, z + 0.035),
                    (R - 0.02, z + 0.035)], 48, closed=True)
    studs = Part("M_Gold", smooth=50)
    for z in bands:
        for i in range(14):
            a = math.radians(-90 + 360 / 28) + TAU * i / 14
            studs.sphere(0.034, mat4(((R + 0.035) * math.cos(a), (R + 0.035) * math.sin(a), z),
                                     (0, 0, math.degrees(a))), segs=6, rings=4, scale=(0.7, 1, 1))
    # top: drum star and rings
    F = Matrix.Translation((0, 0, H))
    gold = Part("M_Gold", smooth=None)
    gold.faceted_star(14, 0.4, 0.15, 0.05, 0.016, F, rot=90.0, back=False)
    motifs.ring(dark, 0.48, 0.53, -0.01, 0.03, F, segs=40, round_top=False)
    motifs.ring(dark, 0.68, 0.73, -0.01, 0.03, F, segs=40, round_top=False)
    # ---- angry face (flat coordinates, then wrapped onto the front) ----
    white = Part("M_White", smooth=45)
    black = Part("M_Black", smooth=45)
    brow = Part("M_BronzeDark", smooth=40)
    for s in (-1, 1):
        # eye: ellipse clipped by the slanted brow line (inner end lower = angry)
        def line(x):
            t = (abs(x) - 0.08) / (0.42 - 0.08)
            return 0.49 + (0.6 - 0.49) * t
        eye = [(x, min(y, line(x) - 0.02)) for x, y in ellipse_points(s * 0.25, 0.47, 0.155, 0.13, 24)]
        white.extrude_poly(densify(eye, 0.04), -0.03, 0.035)
        pup = ellipse_points(s * 0.19, 0.43, 0.055, 0.06, 14)
        black.extrude_poly(pup, 0.0, 0.055)
        # brow: a thick slanted bar
        pts = [(s * 0.46, 0.63), (s * 0.06, 0.53), (s * 0.05, 0.6), (s * 0.45, 0.72)]
        brow.extrude_poly_tapered(densify(pts, 0.05), -0.03, 0.1, 0.9)
    # mouth: dark recess strips and gritted teeth
    for i in range(6):
        x0 = -0.3 + 0.1 * i
        black.box((x0, 0.19, -0.03), (x0 + 0.1, 0.33, 0.02))
    for i in range(5):
        x = -0.24 + 0.12 * i
        white.rounded_box((0.048, 0.055, 0.03), 0.018, n=3, m=mat4((x, 0.26, 0.02)))
    for p in (white, black, brow):
        _wrap_front(p, R)
    return [join_parts("crusher", [body, dark, studs, gold, white, black, brow], col)]


# --------------------------------------------------------------------------------------------
def _hemi(part, r, h, m, segs=8):
    part.lathe([(r, 0.0), (r * 0.72, h * 0.72), (0.0, h)], segs, m, cap0=False)


def drum_big(col):
    """Large Đông Sơn bronze drum (finale stage). Ø 4, 2.2 tall. Walkable top face with the
    14-point star, tick and dot bands, a ring of flying chim Lạc birds and four rain frogs."""
    R, H = 2.0, 2.2
    body = Part("M_Bronze", smooth=40)
    prof = motifs.drum_profile(R, H)
    body.lathe(prof[:-1], 56, cap1=False)
    top = Part("M_BronzeLight", smooth=40)
    top.lathe([(prof[-2][0], H), (0.0, H)], 56)
    F = Matrix.Translation((0, 0, H))
    gold = Part("M_Gold", smooth=None)
    gold.faceted_star(14, 0.68, 0.24, 0.1, 0.025, F, rot=90.0, back=False)
    relief = Part("M_Bronze", smooth=45)
    for r0, r1 in ((0.74, 0.79), (1.02, 1.07), (1.30, 1.35), (1.66, 1.71), (1.9, 1.95)):
        motifs.ring(relief, r0, r1, -0.01, 0.035, F, segs=48, round_top=False)
    motifs.tick_ring(relief, 0.905, 40, 0.19, 0.035, 0.025, -0.005, F)
    for i in range(32):
        a = TAU * i / 32
        _hemi(relief, 0.05, 0.035, F @ Matrix.Translation((1.185 * math.cos(a), 1.185 * math.sin(a), -0.005)))
    birds = Part("M_Gold", smooth=None)
    motifs.bird_ring(birds, 1.49, 8, 0.52, 0.04, -0.005, F, phase=0.1)
    motifs.tick_ring(relief, 1.805, 48, 0.15, 0.03, 0.025, -0.005, F)
    frog_b = Part("M_Patina", smooth=60)
    frog_e = Part("M_Gold", smooth=60)
    for i in range(4):
        a = math.radians(45 + 90 * i)
        m = mat4((1.78 * math.cos(a), 1.78 * math.sin(a), H), (0, 0, math.degrees(a) + 90))
        motifs.frog(frog_b, frog_e, m, s=0.42)
    # side: two raised bands on the shoulder with ticks between, and eight loop handles
    dark = Part("M_BronzeDark", smooth=45)
    _band(dark, prof, 1.45, 0.05, 0.03, 56)
    _band(dark, prof, 1.9, 0.05, 0.03, 56)
    # vertical double ribs split the waist into eight panels; shoulder gets a tick band
    for i in range(8):
        for da in (-0.035, 0.035):
            a = TAU * i / 8 + da
            d = Vector((math.cos(a), math.sin(a), 0))
            path = [d * (profile_radius(prof, z) + 0.005) + Vector((0, 0, z))
                    for z in (0.3, 0.55, 0.8, 1.05)]
            dark.tube(path, 0.03, sides=5, caps=True)
    for i in range(40):
        a = TAU * i / 40
        d = Vector((math.cos(a), math.sin(a), 0))
        z0, z1 = 1.52, 1.83
        path = [d * (profile_radius(prof, z) - 0.005) + Vector((0, 0, z)) for z in (z0, (z0 + z1) / 2, z1)]
        relief.tube(path, 0.022, sides=4, caps=False)
    _band(dark, prof, 0.3, 0.05, 0.03, 56)
    _band(dark, prof, 1.05, 0.05, 0.03, 56)
    for i in range(4):
        base = math.radians(90 * i + 45)
        for da in (-0.1, 0.1):
            a = base + da
            d = Vector((math.cos(a), math.sin(a), 0))
            z0, z1 = 1.12, 1.62
            r0, r1 = profile_radius(prof, z0), profile_radius(prof, z1)
            path = []
            for k in range(9):
                t = k / 8
                z = z0 + (z1 - z0) * t
                rr = r0 + (r1 - r0) * t + 0.22 * math.sin(math.pi * t) - 0.04
                path.append(d * rr + Vector((0, 0, z)))
            dark.tube(path, 0.045, sides=6, caps=True)
    return [join_parts("drum_big", [body, top, gold, relief, birds, frog_b, frog_e, dark], col)]
