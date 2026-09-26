"""Collectibles: coin (đồng xu), coin_red (red paper lantern), star (Đông Sơn star)."""

import math

from mathutils import Matrix, Vector

import motifs
from lib import TAU, Part, join_parts, lerp, mat4

UPRIGHT = Matrix.Rotation(math.radians(90), 4, "X")  # local +Z (front) -> -Y, local +Y -> +Z


def _square_blend(th, b):
    sq = 1.0 / max(abs(math.cos(th)), abs(math.sin(th)))
    return lerp(1.0, sq, b)


def coin(col):
    """Vietnamese cash coin: square hole, raised rims, four embossed strokes. < 600 tris."""
    R = 0.275
    # closed cross-section, anticlockwise in (r, z); z>0 is the front face (-> -Y)
    loop = [  # (r, z, squareness)
        (0.085, 0.030, 1.0), (0.085, -0.030, 1.0),
        (0.130, -0.014, 0.65), (0.200, -0.014, 0.0),
        (0.214, -0.040, 0.0), (0.262, -0.040, 0.0), (R, 0.0, 0.0),
        (0.262, 0.040, 0.0), (0.214, 0.040, 0.0),
        (0.200, 0.014, 0.0), (0.130, 0.014, 0.65),
    ]
    g = Part("M_Gold", smooth=38)
    prof = [(r, z) for r, z, _ in loop]
    g.lathe(prof, 24, Matrix(), shape=lambda th, k: _square_blend(th, loop[k][2]), closed=True,
            phase=0.0)
    # embossed strokes (triangular ridges) above/below/left/right of the hole, both faces
    for zs in (1, -1):
        for i in range(4):
            a = i * math.pi / 2
            c = Vector((0.166 * math.cos(a), 0.166 * math.sin(a), 0))
            t = Vector((-math.sin(a), math.cos(a), 0))  # tangential
            rad = Vector((math.cos(a), math.sin(a), 0))
            L, W, H = 0.036, 0.016, 0.014
            z0 = zs * 0.012
            p = [c - t * L + rad * W, c + t * L + rad * W, c + t * L - rad * W, c - t * L - rad * W]
            base = [g._v(Vector((q.x, q.y, z0))) for q in p]
            top = [g._v(Vector((q.x, q.y, z0 + zs * H))) for q in (c - t * L * 0.8, c + t * L * 0.8)]
            if zs > 0:
                g.face([base[0], base[1], top[1], top[0]])
                g.face([base[2], base[3], top[0], top[1]])
                g.face([base[3], base[0], top[0]])
                g.face([base[1], base[2], top[1]])
            else:
                g.face([top[0], top[1], base[1], base[0]])
                g.face([top[1], top[0], base[3], base[2]])
                g.face([top[0], base[0], base[3]])
                g.face([top[1], base[2], base[1]])
    g.deform(lambda v: UPRIGHT @ v + Vector((0, 0, R)))
    return [join_parts("coin", [g], col)]


def coin_red(col):
    """Red paper lantern (đèn lồng) with gold caps, a hanging loop and a gold tassel. ~0.6 m."""
    red = Part("M_Red", smooth=65)
    gold = Part("M_Gold", smooth=40)
    # ribbed paper body
    body = [(0.075, 0.13), (0.14, 0.15), (0.19, 0.19), (0.215, 0.25), (0.222, 0.30), (0.215, 0.35),
            (0.19, 0.41), (0.14, 0.45), (0.075, 0.47)]
    red.lathe(body, 48, shape=lambda th, k: 1.0 + 0.04 * abs(math.cos(6 * th)) ** 0.5, cap0=False, cap1=False)
    # gold caps (bottom and top)
    gold.lathe([(0.0, 0.10), (0.085, 0.10), (0.105, 0.115), (0.105, 0.135), (0.09, 0.15), (0.0, 0.15)], 20)
    gold.lathe([(0.0, 0.45), (0.09, 0.45), (0.105, 0.465), (0.105, 0.485), (0.085, 0.50), (0.0, 0.50)], 20)
    # gold band around the waist
    gold.lathe([(0.19, 0.283), (0.238, 0.283), (0.244, 0.30), (0.238, 0.317), (0.19, 0.317)], 36,
               closed=True)
    # hanging loop
    loop = [(0.05 * math.cos(a), 0.0, 0.55 + 0.05 * math.sin(a)) for a in
            [math.radians(-90 + 360 * i / 12) for i in range(13)]]
    gold.tube(loop, 0.014, sides=6, caps=False)
    gold.cylinder(0.02, 0.05, 8, mat4((0, 0, 0.495)))
    # tassel: knot + flared strands
    gold.cylinder(0.018, 0.04, 8, mat4((0, 0, 0.07)))
    gold.sphere(0.03, mat4((0, 0, 0.075)), segs=10, rings=5)
    gold.lathe([(0.0, 0.0), (0.05, 0.0), (0.045, 0.02), (0.03, 0.05), (0.02, 0.07), (0.0, 0.07)], 16,
               shape=lambda th, k: 1.0 + 0.12 * math.cos(8 * th))
    return [join_parts("coin_red", [red, gold], col)]


def star(col):
    """Bronze-gold Đông Sơn star: faceted 14-point star, bronze ring, raised centre boss.
    Upright, faces -Y, Ø 1.0, 0.25 thick, origin at the bottom tip."""
    R, RI = 0.5, 0.335
    gold = Part("M_Gold", smooth=None)          # faceted crystal star
    boss = Part("M_GoldLight", smooth=40)
    bronze = Part("M_Bronze", smooth=50)
    gold.faceted_star(14, R, RI, 0.105, 0.045, rot=90.0)
    # centre boss: a domed disc with an embossed ring, same on the back
    prof = [(0.0, 0.0), (0.17, 0.0), (0.172, 0.085), (0.16, 0.103), (0.135, 0.108), (0.118, 0.1),
            (0.1, 0.108), (0.08, 0.118), (0.045, 0.124), (0.0, 0.126)]
    full = [(r, -z) for r, z in reversed(prof[1:])] + prof[2:]
    boss.lathe(full, 24)
    # bronze ring bridging the valleys: rounded, chunky
    ring_prof = [(0.395, -0.03), (0.395, 0.03), (0.382, 0.058), (0.36, 0.068), (0.338, 0.058),
                 (0.325, 0.03), (0.325, -0.03), (0.338, -0.058), (0.36, -0.068), (0.382, -0.058)]
    bronze.lathe(ring_prof, 36, closed=True)
    # a thin gold bead ring around the boss
    bead = [(0.215 + 0.018 * math.cos(a), 0.0 + 0.018 * math.sin(a)) for a in
            [TAU * i / 5 for i in range(5)]]
    for zs in (1, -1):
        bronze.lathe([(r, z * 0.6 + zs * 0.082) for r, z in bead], 28, closed=True)
    parts = [gold, boss, bronze]
    for p in parts:
        p.deform(lambda v: UPRIGHT @ v + Vector((0, 0, R)))
    return [join_parts("star", parts, col)]
