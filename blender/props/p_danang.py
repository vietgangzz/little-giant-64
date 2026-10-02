"""Đà Nẵng – Hội An level, the Đà Nẵng half: golden_hand and golden_bridge_seg (Bà Nà's Golden
Bridge), cable_car and cable_tower, dragon_bridge_deck and dragon_bridge_pier (Cầu Rồng),
beach_umbrella and beach_chair (Mỹ Khê), stupa_tower (Ngũ Hành Sơn) and banh_mi_cart.

Blender axes: front = -Y (Godot +Z), up = +Z. Reported heights are the module constants below.
"""

import math
import os

from mathutils import Matrix, Vector

from lib import TAU, Part, bezier, lerp, look_matrix, mat4, rng, rounded_rect_points, text_part
from p_hoian import Kit

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "..", "..", "assets", "fonts", "Baloo2", "Baloo2-ExtraBold.ttf")

HAND_CRADLE = 8.6          # top of the heel pad and the four fingertips
BRIDGE_DECK = 0.30         # golden_bridge_seg plank top
CABLE_CAR_ROOF = 2.5
CABLE_CAR_GRIP = 4.4       # the cable runs along Y through the grip at this height
TOWER_SHEAVE_TOP = 14.2    # cable_tower: top of the sheave wheels (cable rests here)
DRAGON_GIRDER_LOW = -1.2   # dragon_bridge_deck: bottom of the side girders (road top is 0)

RY90 = Matrix.Rotation(math.radians(90), 4, "Y")     # local Z -> +X


# --------------------------------------------------------------------------------------------
def _surface_blob(part, centre, normal, rx, ry, h=0.08, subdiv=1):
    """A flattened lump sitting on a surface (moss, lichen)."""
    part.ico(1.0, look_matrix(Vector(centre), Vector(normal)), subdiv=subdiv, scale=(rx, ry, h))


def golden_hand(col):
    """One of Bà Nà's giant weathered stone hands: a forearm rising out of a mossy outcrop, the
    palm turned up with the fingers pointing +X and curling up, the thumb rising on the -Y side.
    The heel pad and the four fingertips all top out at 8.6 m: the bridge rests there."""
    k = Kit()
    stone = k("M_StoneHand", smooth=50)
    dark = k("M_StoneHandDark", smooth=45)
    moss = k("M_Moss", smooth=50)
    r = rng(5)
    # the outcrop it rises from
    base_c = Vector((-1.4, 0.0, 0.0))
    dark.lathe([(0.0, 0.0), (2.3, 0.0), (2.18, 0.35), (1.85, 0.8), (1.45, 1.2), (0.0, 1.35)], 18,
               Matrix.Translation(base_c), shape=lambda th, kk: 1.0 + 0.1 * math.sin(3 * th + kk) + 0.05 * math.sin(7 * th))
    # forearm: an elliptical tube, flared at the bottom
    ell = [(0.82 * math.cos(TAU * j / 14), math.sin(TAU * j / 14)) for j in range(14)]
    arm = [Vector((-1.4, 0, 0.6)), Vector((-1.45, 0, 2.2)), Vector((-1.55, 0, 4.3)), Vector((-1.55, 0, 6.2)),
           Vector((-1.35, 0, 7.7))]
    stone.tube(arm, [1.5, 1.18, 1.05, 1.0, 0.95], section=ell, caps=True)
    # palm and the heel pad that carries the bridge
    stone.rounded_box((1.45, 1.38, 0.5), 0.4, 5, Matrix.Translation((-0.5, 0.0, HAND_CRADLE - 0.51)))
    stone.rounded_box((0.45, 1.25, 0.3), 0.27, 4, Matrix.Translation((-1.7, 0.0, HAND_CRADLE - 0.3)))
    # fingers: y offset, radius, length factor
    fingers = ((-0.99, 0.34, 0.95), (-0.33, 0.35, 1.0), (0.33, 0.33, 0.96), (0.97, 0.29, 0.86))
    for y, rad, f in fingers:
        x_end = 0.6 + 2.05 * f
        rt = rad * 0.88
        zc = HAND_CRADLE - rad - 0.01
        pts = bezier((0.5, y, zc), (0.6 + 0.9 * f, y, zc), (x_end - 0.25, y, zc + 0.02), (x_end, y, HAND_CRADLE - rt), 10)
        stone.tube(pts, [rad * lerp(1.0, 0.88, j / 10) for j in range(11)], sides=10, caps=True)
        stone.sphere(rt, mat4(tuple(pts[-1])), segs=10, rings=6)
        # knuckle creases
        for t in (0.35, 0.68):
            i = int(t * 10)
            d = (pts[i + 1] - pts[i]).normalized()
            rr = rad * lerp(1.0, 0.88, t) + 0.01
            dark.lathe([(rr - 0.03, -0.03), (rr + 0.015, -0.015), (rr + 0.015, 0.015), (rr - 0.03, 0.03)], 10,
                       look_matrix(pts[i], d), closed=True)
    # thumb
    th = bezier((-0.95, -1.1, 7.9), (-0.3, -1.85, 8.0), (0.35, -2.05, 8.35), (0.55, -1.9, 9.05), 10)
    stone.tube(th, [lerp(0.44, 0.34, j / 10) for j in range(11)], sides=10, caps=True)
    stone.sphere(0.34, mat4(tuple(th[-1])), segs=10, rings=6)
    # cracks running up the forearm and across the palm
    for c in range(4):
        phi = r(0, TAU)
        path = []
        z = r(1.2, 2.5)
        for s in range(7):
            z += r(0.35, 0.7)
            phi += r(-0.12, 0.12)
            rad = 1.18 - 0.03 * z if z < 4.3 else 1.02
            path.append(Vector((-1.5 + 0.82 * rad * math.cos(phi), rad * math.sin(phi), z)))
        dark.tube(path, 0.045, sides=4, caps=True)
    dark.tube([Vector((-1.0, 1.39, 8.2)), Vector((-0.5, 1.4, 7.95)), Vector((0.0, 1.39, 8.15)), Vector((0.5, 1.38, 7.9))],
              0.035, sides=4, caps=True)
    # moss on the outcrop, the forearm and the back of the hand
    for i in range(14):
        phi = r(0, TAU)
        if i < 6:
            rr = r(1.6, 2.3)
            c = base_c + Vector((rr * math.cos(phi), rr * math.sin(phi), 0.95 - 0.35 * (rr - 1.6)))
            n = Vector((math.cos(phi) * 0.6, math.sin(phi) * 0.6, 1.0))
        else:
            z = r(0.9, 5.5)
            rad = 1.2 - 0.03 * z
            c = Vector((-1.5 + 0.82 * rad * math.cos(phi), rad * math.sin(phi), z))
            n = Vector((math.cos(phi), math.sin(phi), 0.2))
        _surface_blob(moss, c, n, r(0.35, 0.6), r(0.25, 0.45), 0.09)
    for p, n in (((-0.2, 0.0, 7.55), (0, 0, -1)), ((0.3, 1.36, 8.0), (0, 1, 0)), ((-1.0, -1.36, 8.05), (0, -1, 0))):
        _surface_blob(moss, p, n, 0.5, 0.3, 0.08)
    return [k.finish("golden_hand", col)]


# --------------------------------------------------------------------------------------------
def golden_bridge_seg(col):
    """A 2 m piece of the Golden Bridge walkway, running along Y: plank deck (top 0.30) on a gold
    girder, gold railings at x = ±1.15 with posts at y = -1 and 0 (so tiles post every metre), and
    pots of purple and yellow flowers along the railing feet."""
    k = Kit()
    gold = k("M_GoldBridge", smooth=40)
    gold.box((-1.25, -1.0, -0.2), (1.25, 1.0, BRIDGE_DECK - 0.08))
    for sx in (-1, 1):
        gold.box((sx * 1.25 - 0.04 if sx > 0 else -1.29, -1.0, -0.12), (1.29 if sx > 0 else -1.21, 1.0, 0.16))
        gold.box((sx * 1.25 - 0.06 if sx > 0 else -1.31, -1.0, 0.16), (1.31 if sx > 0 else -1.19, 1.0, 0.22))
    for i in range(8):
        y0 = -1.0 + 0.25 * i
        k("M_WoodLight" if i % 2 else "M_Wood", smooth=30).box((-1.18, y0 + 0.006, BRIDGE_DECK - 0.08),
                                                             (1.18, y0 + 0.244, BRIDGE_DECK))
    rail = k("M_Gold", smooth=45)
    top = BRIDGE_DECK + 1.0
    for sx in (-1, 1):
        x = sx * 1.15
        for y in (-1.0, 0.0):
            rail.box((x - 0.045, y - 0.045, BRIDGE_DECK), (x + 0.045, y + 0.045, top - 0.02))
            rail.sphere(0.065, mat4((x, y, top + 0.02)), segs=8, rings=5)
        for z, rr in ((top - 0.03, 0.035), (BRIDGE_DECK + 0.55, 0.022), (BRIDGE_DECK + 0.1, 0.022)):
            rail.tube([Vector((x, -1.0, z)), Vector((x, 1.0, z))], rr, sides=6, caps=True)
        for y in (-0.75, -0.5, -0.25, 0.25, 0.5, 0.75):
            rail.cylinder(0.014, top - BRIDGE_DECK - 0.03, 5, mat4((x, y, BRIDGE_DECK)))
        for j, y in enumerate((-0.75, -0.25, 0.25, 0.75)):
            px = sx * 0.95
            k("M_Terracotta", smooth=45).lathe([(0.0, 0.0), (0.07, 0.0), (0.095, 0.15), (0.085, 0.16), (0.0, 0.16)], 8,
                                              Matrix.Translation((px, y, BRIDGE_DECK)))
            k("M_LeafDark", smooth=50).ico(0.09, mat4((px, y, BRIDGE_DECK + 0.19)), subdiv=1, scale=(1, 1, 0.6))
            fl = k("M_Purple" if (j + (sx > 0)) % 2 else "M_Yellow", smooth=50)
            for a in range(3):
                ang = TAU * a / 3 + j
                fl.ico(0.045, mat4((px + 0.05 * math.cos(ang), y + 0.05 * math.sin(ang), BRIDGE_DECK + 0.25)), subdiv=1)
    return [k.finish("golden_bridge_seg", col)]


# --------------------------------------------------------------------------------------------
def cable_car(col):
    """Bà Nà gondola: a rounded red-and-white cabin with big windows and a flat red roof (walkable,
    top 2.5); the hanger rises from the back edge of the roof (y = +0.9) to the grip at 4.4, where
    the cable runs along Y."""
    k = Kit()
    k("M_White", smooth=45).rounded_box((1.2, 1.2, 1.15), 0.35, 5, Matrix.Translation((0, 0, 1.15)))
    k("M_CableRed", smooth=40).extrude_poly(rounded_rect_points(2.46, 2.46, 0.38, 4), 0.35, 0.95)
    k("M_CableRed", smooth=40).extrude_poly(rounded_rect_points(2.36, 2.36, 0.36, 4), 2.22, CABLE_CAR_ROOF)
    frame = k("M_Black", smooth=40)
    glass = k("M_Glass", smooth=30)
    for a in range(4):
        rot = Matrix.Rotation(TAU * a / 4, 4, "Z")
        frame.box((-0.8, -1.215, 1.02), (0.8, -1.17, 2.05), rot)
        glass.box((-0.72, -1.225, 1.1), (0.72, -1.18, 1.97), rot)
        frame.box((-0.025, -1.235, 1.1), (0.025, -1.2, 1.97), rot)
    # hanger arm and grip
    steel = k("M_Steel", smooth=45)
    steel.cylinder(0.09, 4.12 - CABLE_CAR_ROOF, 10, mat4((0, 0.9, CABLE_CAR_ROOF)))
    steel.tube([Vector((0, 0.9, 3.2)), Vector((0, 0.45, 4.25))], 0.05, sides=6)
    steel.box((-0.16, 0.4, CABLE_CAR_GRIP - 0.18), (0.16, 1.4, CABLE_CAR_GRIP + 0.14))
    for y in (0.6, 1.2):
        k("M_Black", smooth=45).lathe([(0.0, -0.06), (0.13, -0.06), (0.14, 0.0), (0.13, 0.06), (0.0, 0.06)], 12,
                                      Matrix.Translation((0, y, CABLE_CAR_GRIP + 0.12)) @ RY90)
    k("M_Yellow", smooth=40).box((-0.35, -1.25, 0.55), (0.35, -1.21, 0.75))     # number plate
    return [k.finish("cable_car", col)]


def cable_tower(col):
    """Steel lattice pylon, 14 m: four tapering legs with X bracing, a cross-arm along X and two
    sheave wheels at x = ±2.0 whose tops (14.2) carry the cables running along Y."""
    k = Kit()
    steel = k("M_Steel", smooth=30)
    lo, hi, H = 1.3, 0.45, 13.0
    corners = [(1, 1), (-1, 1), (-1, -1), (1, -1)]

    def leg(cx, cy, z):
        w = lerp(lo, hi, z / H)
        return Vector((cx * w, cy * w, z))

    for cx, cy in corners:
        steel.tube([leg(cx, cy, 0.0), leg(cx, cy, H + 0.4)], 0.1, sides=4, caps=True)
        k("M_Concrete", smooth=30).box((cx * lo - 0.3, cy * lo - 0.3, 0.0), (cx * lo + 0.3, cy * lo + 0.3, 0.35))
    tiers = [0.4, 3.0, 5.6, 8.0, 10.4, 12.6]
    for a in range(4):
        c0, c1 = corners[a], corners[(a + 1) % 4]
        for t in range(len(tiers) - 1):
            z0, z1 = tiers[t], tiers[t + 1]
            steel.tube([leg(*c0, z1), leg(*c1, z1)], 0.05, sides=4, caps=True)
            steel.tube([leg(*c0, z0), leg(*c1, z1)], 0.04, sides=4, caps=True)
            steel.tube([leg(*c1, z0), leg(*c0, z1)], 0.04, sides=4, caps=True)
    steel.box((-2.5, -0.25, H), (2.5, 0.25, H + 0.4))
    for sx in (-1, 1):
        steel.tube([leg(sx, 1, 10.4), Vector((sx * 2.3, 0.2, H))], 0.05, sides=4)
        steel.tube([leg(sx, -1, 10.4), Vector((sx * 2.3, -0.2, H))], 0.05, sides=4)
        steel.box((sx * 2.0 - 0.18, -0.08, H + 0.4), (sx * 2.0 + 0.18, 0.08, TOWER_SHEAVE_TOP - 0.4))
        k("M_Black", smooth=45).lathe([(0.0, -0.07), (0.36, -0.07), (0.4, -0.05), (0.36, 0.0), (0.4, 0.05), (0.36, 0.07),
                                       (0.0, 0.07)], 16, Matrix.Translation((sx * 2.0, 0, TOWER_SHEAVE_TOP - 0.4)) @ RY90)
    k("M_CableRed", smooth=50).sphere(0.16, mat4((0, 0, H + 0.55)), segs=10, rings=6)
    return [k.finish("cable_tower", col)]


# --------------------------------------------------------------------------------------------
def dragon_bridge_deck(col):
    """10 m of Cầu Rồng's road deck along Y. Origin at the road surface centre (road top 0.0):
    a 7 m asphalt road with lane markings, raised 1 m footways (top 0.15), steel railings, two
    street lamps a side, and light grey side girders reaching down to -1.2."""
    k = Kit()
    k("M_Asphalt", smooth=30).box((-3.5, -5.0, -0.35), (3.5, 5.0, 0.0))
    white = k("M_White", smooth=30)
    for x in (-1.75, 0.0, 1.75):
        for y0 in (-4.5, 0.5):
            white.box((x - 0.07, y0, -0.01), (x + 0.07, y0 + 2.0, 0.012))
    for x in (-3.3, 3.3):
        white.box((x - 0.06, -5.0, -0.01), (x + 0.06, 5.0, 0.012))
    walk = k("M_Concrete", smooth=30)
    girder = k("M_StoneLight", smooth=30)
    steel = k("M_Steel", smooth=45)
    for sx in (-1, 1):
        walk.box((min(sx * 3.5, sx * 4.5), -5.0, -0.35), (max(sx * 3.5, sx * 4.5), 5.0, 0.15))
        k("M_Stone", smooth=30).box((min(sx * 3.5, sx * 3.62), -5.0, 0.0), (max(sx * 3.5, sx * 3.62), 5.0, 0.17))
        girder.box((min(sx * 3.0, sx * 4.4), -5.0, DRAGON_GIRDER_LOW), (max(sx * 3.0, sx * 4.4), 5.0, -0.35))
        x = sx * 4.42
        for i in range(10):
            steel.box((x - 0.04, -4.5 + i - 0.04, 0.15), (x + 0.04, -4.5 + i + 0.04, 1.15))
        for z, rr in ((1.15, 0.045), (0.65, 0.03)):
            steel.tube([Vector((x, -5.0, z)), Vector((x, 5.0, z))], rr, sides=6, caps=True)
        for y in (-2.5, 2.5):
            px = sx * 4.2
            steel.lathe([(0.0, 0.15), (0.16, 0.15), (0.16, 0.45), (0.08, 0.6), (0.06, 6.0), (0.0, 6.05)], 8,
                        Matrix.Translation((px, y, 0)))
            arm = bezier((px, y, 5.9), (px, y, 6.35), (px - sx * 0.6, y, 6.4), (px - sx * 1.0, y, 6.25), 6)
            steel.tube(arm, 0.045, sides=5, caps=True)
            hx = px - sx * 1.0
            steel.box((hx - 0.28, y - 0.16, 6.08), (hx + 0.28, y + 0.16, 6.26))
            k("M_LampGlow", smooth=30).box((hx - 0.24, y - 0.12, 6.04), (hx + 0.24, y + 0.12, 6.09))
    k("M_StoneLight", smooth=30).box((-3.0, -0.4, -0.9), (3.0, 0.4, -0.35))
    return [k.finish("dragon_bridge_deck", col)]


def dragon_bridge_pier(col):
    """A concrete pier for the Dragon Bridge, sharing the deck's origin (road surface): the
    flared cap tops out at -1.2 under the girders, the column runs down to -6."""
    k = Kit()
    conc = k("M_Concrete", smooth=35)
    m = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))   # local XY -> world XZ
    cap = [(-4.5, -1.2), (-4.5, -1.6), (-1.6, -3.3), (1.6, -3.3), (4.5, -1.6), (4.5, -1.2)]
    conc.extrude_poly(cap, -1.6, 1.6, m)
    conc.rounded_box((1.5, 1.3, 1.4), 0.4, 4, Matrix.Translation((0, 0, -4.5)))
    conc.box((-1.5, -1.3, -6.0), (1.5, 1.3, -4.6))
    k("M_StoneDark", smooth=35).box((-1.53, -1.33, -6.0), (1.53, 1.33, -4.9))
    return [k.finish("dragon_bridge_pier", col)]


# --------------------------------------------------------------------------------------------
def beach_umbrella(col):
    """Mỹ Khê thatched beach umbrella: a 2.5 m pole under a two-layer straw canopy (Ø 2.8)."""
    k = Kit()
    k("M_Wood", smooth=45).cylinder(0.055, 2.75, 10)
    fringe = lambda th, kk: 1.0 + (0.05 * math.sin(17 * th) + 0.03 * math.sin(29 * th) if kk in (1, 2) else 0.0)
    k("M_Straw", smooth=40).lathe([(0.0, 2.38), (1.32, 1.92), (1.42, 1.88), (1.4, 1.98), (0.0, 2.78)], 48, shape=fringe)
    k("M_StrawDark", smooth=40).lathe([(0.0, 2.6), (0.82, 2.3), (0.9, 2.26), (0.88, 2.36), (0.0, 2.96)], 36, shape=fringe)
    k("M_WoodDark", smooth=45).lathe([(0.0, 2.9), (0.09, 2.9), (0.06, 3.05), (0.0, 3.1)], 8)
    return [k.finish("beach_umbrella", col)]


def beach_chair(col):
    """Wooden lounge chair: slatted seat, raised backrest at +Y, a blue towel."""
    k = Kit()
    frame = k("M_Wood", smooth=40)
    slats = k("M_WoodLight", smooth=30)
    for sx in (-1, 1):
        x = sx * 0.33
        frame.box((x - 0.04, -0.95, 0.27), (x + 0.04, 0.45, 0.35))
        for y in (-0.85, 0.35):
            frame.box((x - 0.04, y - 0.04, 0.0), (x + 0.04, y + 0.04, 0.3))
        back = [Vector((x, 0.42, 0.33)), Vector((x, 0.9, 1.0))]
        frame.tube(back, 0.04, sides=4, caps=True)
    for i in range(9):
        y = -0.92 + 0.15 * i
        slats.box((-0.36, y, 0.35), (0.36, y + 0.11, 0.39))
    d = Vector((0, 0.48, 0.67)).normalized()
    for i in range(5):
        c = Vector((0, 0.42, 0.37)) + d * (0.1 + 0.14 * i)
        slats.box((-0.36, -0.05, -0.02), (0.36, 0.05, 0.02), Matrix.Translation(c) @ Matrix.Rotation(math.atan2(0.67, 0.48), 4, "X"))
    k("M_BarrelBlue", smooth=40).box((-0.28, -0.6, 0.39), (0.28, 0.2, 0.42))
    k("M_White", smooth=40).box((-0.28, -0.35, 0.392), (0.28, -0.25, 0.425))
    return [k.finish("beach_chair", col)]


# --------------------------------------------------------------------------------------------
def _light_roof(tiles, trim, R, z_eave, rise, lift=0.16, flare=0.1, levels=3, thick=0.07, phase=0.0):
    """Hexagonal flared roof with upturned corners, lighter than p_halong._poly_roof (small
    tiers): 2 steps per side, 4-sided trim tubes and short corner hooks."""
    n, per = 6, 2
    M = n * per
    sector = TAU / n

    def pt(j, s, under):
        th = phase + TAU * j / M
        d = ((th - phase) % sector) - sector / 2
        Rp = R * math.cos(sector / 2) / math.cos(d)
        c = abs(d) / (sector / 2)
        rr = s * Rp * (1 + flare * c ** 4 * s ** 2)
        z = z_eave + rise * (1 - s) ** 1.7 + lift * c ** 4 * s ** 3 - (thick if under else 0.0)
        return Vector((rr * math.cos(th), rr * math.sin(th), z))

    ss = [k / levels for k in range(1, levels + 1)]
    rings = [[pt(0, 0.0, True)]] + [[pt(j, s, True) for j in range(M)] for s in ss]
    rings += [[pt(j, s, False) for j in range(M)] for s in reversed(ss)] + [[pt(0, 0.0, False)]]
    tiles.loft(rings, closed_rings=True)
    trim.tube([pt(j, 1.0, False) + Vector((0, 0, 0.015)) for j in range(M)], 0.045, sides=4, closed=True)
    for k in range(n):
        c = pt(k * per, 1.0, False)
        d = Vector((c.x, c.y, 0)).normalized()
        hook = [c + d * (0.12 * math.sin(a)) + Vector((0, 0, 0.13 * (1 - math.cos(a)))) for a in [i * 0.5 for i in range(6)]]
        trim.tube(hook, [0.06 * (1 - 0.6 * i / 5) for i in range(6)], sides=4, caps=True)


def stupa_tower(col):
    """Ngũ Hành Sơn stupa: five hexagonal marble tiers shrinking upwards, each under a flared
    terracotta roof with upturned corners, on a stone plinth, with a gold finial."""
    k = Kit()
    k("M_StoneLight", smooth=30).lathe([(0.0, 0.0), (1.25, 0.0), (1.25, 0.25), (1.12, 0.35), (0.0, 0.35)], 6)
    marble = k("M_Marble", smooth=30)
    niche = k("M_StoneDark", smooth=30)
    tiles = k("M_TileRoof", smooth=35)
    ridge = k("M_TileRoofDark", smooth=45)
    z = 0.35
    for t in range(5):
        r = 0.85 * 0.84 ** t
        h = 0.78 * 0.88 ** t
        marble.lathe([(0.0, z - 0.05), (r, z - 0.05), (r, z + h), (0.0, z + h)], 6)
        marble.lathe([(0.0, z - 0.05), (r * 1.1, z - 0.05), (r * 1.1, z + 0.07), (0.0, z + 0.07)], 6)
        for a in (math.radians(30), math.radians(150), math.radians(270)):
            c = Vector((r * math.cos(math.radians(30)) * math.cos(a), r * math.cos(math.radians(30)) * math.sin(a), z + h * 0.5))
            n = Vector((math.cos(a), math.sin(a), 0))
            q = r / 0.85
            arch = [(0.12 * q * math.cos(a2), 0.06 * q + 0.12 * q * math.sin(a2)) for a2 in [math.pi * i / 6 for i in range(7)]]
            niche.extrude_poly(arch + [(-0.12 * q, -0.2 * q), (0.12 * q, -0.2 * q)], -0.01, 0.03, look_matrix(c, n))
        z_eave = z + h + 0.02
        rise = 0.22 * 0.9 ** t
        _light_roof(tiles, ridge, r + 0.35, z_eave, rise, phase=math.radians(30))
        z = z_eave + rise * 0.55
    k("M_Gold", smooth=50).lathe([(0.0, z - 0.1), (0.14, z - 0.1), (0.16, z + 0.05), (0.08, z + 0.18), (0.11, z + 0.3),
                                  (0.06, z + 0.45), (0.03, z + 0.7), (0.0, z + 0.78)], 10)
    return [k.finish("stupa_tower", col)]


# --------------------------------------------------------------------------------------------
def banh_mi_cart(col):
    """A bánh mì street cart: blue painted body with red trim and a BÁNH MÌ sign, a glass-topped
    case of golden baguettes, a striped canopy on four posts, two bicycle wheels and a handle."""
    k = Kit()
    blue = k("M_BarrelBlue", smooth=40, bevel=(0.02, 1))
    red = k("M_Red", smooth=40)
    blue.box((-0.75, -0.4, 0.5), (0.75, 0.4, 1.0))
    red.box((-0.78, -0.43, 0.94), (0.78, 0.43, 1.02))
    red.box((-0.78, -0.43, 0.48), (0.78, 0.43, 0.54))
    try:
        text_part(k("M_Yellow", smooth=None), "BÁNH MÌ", 0.2, 0.03,
                  Matrix(((1, 0, 0, 0), (0, 0, -1, -0.405), (0, 1, 0, 0.73), (0, 0, 0, 1))),
                  font_path=FONT, resolution=2)
    except Exception as e:  # noqa: BLE001
        print("banh_mi_cart: sign skipped", e)
    # display case: white frame, a glass lid and back, open at the front
    wf = k("M_White", smooth=40)
    for x in (-0.7, 0.7):
        for y in (-0.35, 0.35):
            wf.box((x - 0.025, y - 0.025, 1.02), (x + 0.025, y + 0.025, 1.45))
    wf.box((-0.72, -0.37, 1.43), (0.72, 0.37, 1.47))
    glass = k("M_Glass", smooth=30)
    glass.box((-0.68, -0.33, 1.44), (0.68, 0.33, 1.465))
    glass.box((-0.68, 0.32, 1.03), (0.68, 0.34, 1.44))
    for x in (-0.7, 0.7):
        glass.box((x - 0.01, -0.33, 1.03), (x + 0.01, 0.33, 1.44))
    k("M_WoodLight", smooth=30).box((-0.66, -0.3, 1.02), (0.66, 0.3, 1.05))
    bread = k("M_Bread", smooth=55)
    slash = k("M_BambooDry", smooth=40)
    for i, (y, z) in enumerate(((-0.17, 1.1), (0.0, 1.1), (0.17, 1.1), (-0.08, 1.2), (0.09, 1.2))):
        x0 = -0.1 if i % 2 else 0.05
        bread.sphere(0.065, mat4((x0, y, z)), segs=12, rings=6, scale=(6.5, 1, 0.85))
        for s in (-0.22, 0.0, 0.22):
            slash.box((-0.035, -0.012, -0.01), (0.035, 0.012, 0.01),
                      Matrix.Translation((x0 + s, y, z + 0.052)) @ Matrix.Rotation(0.6, 4, "Z"))
    # canopy
    for x in (-0.7, 0.7):
        for y in (-0.35, 0.35):
            wf.cylinder(0.018, 0.5, 6, mat4((x, y, 1.47)))
    red.box((-0.85, -0.52, 1.95), (0.85, 0.52, 2.0))
    for i in range(10):
        x0 = -0.85 + 0.17 * i
        (red if i % 2 else wf).box((x0, -0.55, 1.83), (x0 + 0.17, -0.5, 1.98))
        (red if i % 2 else wf).box((x0, 0.5, 1.83), (x0 + 0.17, 0.55, 1.98))
    # bicycle wheels on both sides
    tire = k("M_Black", smooth=50)
    spoke = k("M_Steel", smooth=40)
    for sx in (-1, 1):
        c = Vector((sx * 0.85, 0.05, 0.34))
        m = Matrix.Translation(c) @ RY90
        tire.lathe([(0.3, -0.03), (0.34, -0.03), (0.34, 0.03), (0.3, 0.03)], 24, m, closed=True)
        spoke.cylinder(0.04, 0.12, 8, Matrix.Translation(c - Vector((0.06 * sx, 0, 0))) @ (RY90 if sx > 0 else Matrix.Rotation(-math.pi / 2, 4, "Y")))
        for a in range(8):
            ang = TAU * a / 8
            spoke.tube([c, c + Vector((0, 0.3 * math.cos(ang), 0.3 * math.sin(ang)))], 0.008, sides=3)
    spoke.tube([Vector((-0.85, 0.05, 0.34)), Vector((0.85, 0.05, 0.34))], 0.02, sides=5)
    k("M_Wood", smooth=40).box((-0.05, -0.38, 0.0), (0.05, -0.3, 0.5))           # front stand
    k("M_Wood", smooth=40).tube([Vector((-0.5, 0.4, 0.85)), Vector((-0.5, 0.7, 0.95)), Vector((0.5, 0.7, 0.95)),
                                 Vector((0.5, 0.4, 0.85))], 0.025, sides=5)
    return [k.finish("banh_mi_cart", col)]
