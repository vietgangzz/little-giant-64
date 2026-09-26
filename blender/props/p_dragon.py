"""Friendly Lý-dynasty dragon (rồng) in chainable pieces: dragon_head, dragon_body, dragon_tail,
dragon_leg. Jade/emerald scales, gold-cream belly, gold crest flames.

Axis convention for head/body/tail: the spine runs along Blender Y at z = 0 (the origin), the
front faces -Y. body: origin at the segment centre, 1.6 m long (y -0.8..+0.8), Ø 1.3.
tail: origin at the joint (y = 0), extends 2 m towards +Y. head: origin at the neck joint,
extends 2.2 m towards -Y. A body cross-section is a circle whose top is cut flat at
z = SADDLE (the walkable saddle strip).
"""

import math

from mathutils import Matrix, Vector

from lib import TAU, Part, bezier, join_parts, lerp, mat4

R_BODY = 0.65
SADDLE_K = 0.86                 # flat top at 0.86 R
SADDLE = R_BODY * SADDLE_K      # 0.559 m above the axis
SEGS = 24
BELLY = (math.radians(222), math.radians(318))


def _ring(y, R, scallop, row_phase, flat=True):
    """Points P(θ) = (-R cos θ, y, R sin θ): θ = 90° is the top, 270° the belly.
    Anticlockwise around +Y, so lofting towards +Y gives outward faces."""
    pts = []
    for j in range(SEGS):
        th = TAU * j / SEGS
        m = 1.0 + scallop * abs(math.sin(5 * th + row_phase))
        x, z = -R * m * math.cos(th), R * m * math.sin(th)
        if flat:
            z = min(z, SADDLE)          # one absolute saddle height for every piece
        pts.append(Vector((x, y, z)))
    return pts


SADDLE_ARC = (math.radians(55), math.radians(125))


def _serpent(jade, belly, stations, flat=True, sides=None):
    """stations: list of (y, R, scallop, phase). Lofts three strips: the flat saddle/back
    (`jade`), the flanks (`sides`, dark jade under the scale plates) and the gold belly.
    Returns the ring list (for caps)."""
    sides = sides or jade
    rings = [_ring(y, R, sc, ph, flat) for y, R, sc, ph in stations]

    def idx(a0, a1):
        j0 = round(a0 / TAU * SEGS)
        j1 = round(a1 / TAU * SEGS)
        return [j % SEGS for j in range(j0, j1 + 1)]
    regions = ((jade, idx(*SADDLE_ARC)), (sides, idx(SADDLE_ARC[1], BELLY[0])), (belly, idx(*BELLY)),
               (sides, idx(BELLY[1], TAU + SADDLE_ARC[0])))
    for part, ids in regions:
        part.loft([[r[j] for j in ids] for r in rings], closed_rings=False)
    return rings


SCALE_SHAPE = [(-0.5, -0.5), (0.5, -0.5), (0.5, 0.15), (0.3, 0.42), (0.0, 0.5), (-0.3, 0.42), (-0.5, 0.15)]


def _scales(part, y0, y1, R_fn, row=0.2, per_ring=12, lift=9.0):
    """Staggered fish-scale plates on the flanks (not on the saddle strip or the belly); the
    rounded free edge points to the tail (+Y) and is lifted a little."""
    rows = max(1, round((y1 - y0) / row))
    step = (y1 - y0) / rows
    for k in range(rows):
        yc = y0 + (k + 0.5) * step
        R = R_fn(yc)
        for j in range(per_ring):
            th = TAU * (j + 0.5 * (k % 2)) / per_ring
            if SADDLE_ARC[0] - 0.05 < th < SADDLE_ARC[1] + 0.05 or BELLY[0] - 0.1 < th < BELLY[1] + 0.1:
                continue
            n = Vector((-math.cos(th), 0, math.sin(th)))
            t = Vector((math.sin(th), 0, math.cos(th)))
            m = Matrix((t, Vector((0, 1, 0)), n)).transposed().to_4x4()
            m.translation = n * R + Vector((0, yc, 0))
            m = m @ Matrix.Rotation(math.radians(lift), 4, "X")
            W = TAU * R / per_ring * 1.02
            pts = [(u * W, v * step * 1.35) for u, v in SCALE_SHAPE]
            part.extrude_poly_tapered(pts, -0.035, 0.035, 0.84, m)


def _scale_stations(y0, y1, R_fn, row=0.2, scallop=0.045):
    """Shingled scale rows from y0 to y1 (y1 > y0): each row grows towards its back edge."""
    st = []
    n = max(1, round((y1 - y0) / row))
    for k in range(n):
        a = y0 + (y1 - y0) * k / n
        b = y0 + (y1 - y0) * (k + 1) / n
        ph = (k % 2) * math.pi / 5
        st.append((a + (0.012 if k else 0.0), R_fn(a), 0.0, ph))
        st.append((b, R_fn(b) * 1.055, scallop, ph))
    return st


def _cap(part, ring, front):
    vs = [part._v(p) for p in ring]
    part.face(list(reversed(vs)) if front else vs)


def _spike_rows(gold, y0, y1, R_fn, n, h=0.18):
    """Two rows of small gold spikes along the saddle edges (the strip between stays flat)."""
    for k in range(n):
        y = lerp(y0, y1, (k + 0.5) / n)
        R = R_fn(y)
        if R <= SADDLE + 0.02:
            zt = R * SADDLE_K
        else:
            zt = SADDLE
        xz = math.sqrt(max(0.0, R * R - zt * zt))
        for s in (-1, 1):
            base = Vector((s * (xz + 0.02), y, zt - 0.04))
            d = Vector((s * 0.35, 0.55, 1.0)).normalized()
            m = Matrix.Translation(base) @ Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4()
            gold.lathe([(0.0, -0.02), (h * 0.36, -0.02), (h * 0.12, h * 0.7), (0.0, h)], 6, m)


# --------------------------------------------------------------------------------------------
def dragon_body(col):
    """One 1.6 m body segment (Ø 1.3), shingled scales, gold belly plates, flat saddle strip on
    top at z = +0.56 with a row of low gold spikes along each edge."""
    jade = Part("M_Jade", smooth=50)
    flank = Part("M_JadeDark", smooth=50)
    belly = Part("M_GoldLight", smooth=50)
    gold = Part("M_Gold", smooth=45)
    plates = Part("M_Jade", smooth=35)

    def R_fn(y):
        return R_BODY * (0.93 + 0.07 * math.cos(math.pi * y / 0.8))   # slight bulge mid-segment
    st = _scale_stations(-0.8, 0.8, R_fn, row=0.4, scallop=0.0)
    rings = _serpent(jade, belly, st, sides=flank)
    _scales(plates, -0.8, 0.8, R_fn, row=0.2)
    caps = Part("M_JadeDark", smooth=40)
    _cap(caps, rings[0], True)
    _cap(caps, rings[-1], False)
    _spike_rows(gold, -0.8, 0.8, R_fn, 4)
    return [join_parts("dragon_body", [jade, flank, belly, gold, plates, caps], col)]


def dragon_tail(col):
    """2 m tail: tapers from the body radius to a gold flame tuft. Origin at the joint end."""
    jade = Part("M_Jade", smooth=50)
    flank = Part("M_JadeDark", smooth=50)
    belly = Part("M_GoldLight", smooth=50)
    gold = Part("M_Gold", smooth=50)
    plates = Part("M_Jade", smooth=35)
    L = 1.75

    def R_fn(y):
        t = y / L
        return R_BODY * 0.93 * (1 - 0.8 * t ** 1.1)
    st = _scale_stations(0.0, L, R_fn, row=0.25, scallop=0.0)
    rings = _serpent(jade, belly, st, sides=flank)
    _scales(plates, 0.0, L * 0.85, R_fn, row=0.21, per_ring=10)
    caps = Part("M_JadeDark", smooth=40)
    _cap(caps, rings[0], True)
    _cap(caps, rings[-1], False)
    _spike_rows(gold, 0.0, L * 0.8, R_fn, 5, h=0.15)
    # flame tuft: tongues fanning back and curling up
    tip = Vector((0, L - 0.05, 0.0))
    for i, (sx, sz, ln) in enumerate(((0.0, 0.5, 0.55), (0.35, 0.25, 0.45), (-0.35, 0.25, 0.45),
                                      (0.22, -0.2, 0.38), (-0.22, -0.2, 0.38), (0.0, 0.95, 0.4))):
        d = Vector((sx, 1.0, sz)).normalized()
        p1 = tip + d * ln * 0.5
        p2 = tip + d * ln + Vector((0, 0, 0.12))
        p3 = p2 + Vector((0, -0.1, 0.12))
        pts = bezier(tip, p1, p2, p3, 7)
        gold.tube(pts, [0.12 * (1 - 0.85 * k / 7) for k in range(8)], sides=6, caps=True)
    return [join_parts("dragon_tail", [jade, flank, belly, gold, plates, caps], col)]


def dragon_head(col):
    """Friendly dragon head, ~2.2 m from the neck joint (origin) to the nose, facing -Y."""
    jade = Part("M_Jade", smooth=50)
    belly = Part("M_GoldLight", smooth=50)
    light = Part("M_JadeLight", smooth=55)
    gold = Part("M_Gold", smooth=50)
    white = Part("M_White", smooth=60)
    black = Part("M_Black", smooth=60)
    red = Part("M_Red", smooth=50)
    caps = Part("M_JadeDark", smooth=40)
    # neck: scale rows from the joint forward into the skull
    flank = Part("M_JadeDark", smooth=50)
    plates = Part("M_Jade", smooth=35)
    st = _scale_stations(-0.6, 0.0, lambda y: R_BODY * 0.93, row=0.3, scallop=0.0)
    rings = _serpent(jade, belly, st, sides=flank)
    _scales(plates, -0.45, 0.0, lambda y: R_BODY * 0.93, row=0.2)
    _cap(caps, rings[-1], False)
    # skull
    jade.sphere(0.66, mat4((0, -0.85, 0.2)), segs=20, rings=12, scale=(0.95, 1.05, 0.85))
    # snout (lathe along -Y), flattened
    snout_m = Matrix.Translation((0, -1.0, 0.02)) @ Matrix.Diagonal((1.0, 1.0, 0.78, 1.0)) @ \
        Matrix.Rotation(math.radians(90), 4, "X")
    jade.lathe([(0.0, 0.0), (0.46, 0.0), (0.45, 0.35), (0.4, 0.7), (0.33, 0.95), (0.18, 1.08), (0.0, 1.1)], 18,
               snout_m)
    # nose bulb + nostrils
    light.sphere(0.2, mat4((0, -1.98, 0.2)), segs=12, rings=6, scale=(1.3, 0.9, 0.8))
    for s in (-1, 1):
        black.sphere(0.045, mat4((s * 0.12, -2.13, 0.23)), segs=8, rings=4, scale=(1, 0.6, 0.8))
    # lower jaw, slightly open, and the mouth
    jaw_m = Matrix.Translation((0, -1.0, -0.28)) @ Matrix.Rotation(math.radians(-8), 4, "X") @ \
        Matrix.Diagonal((1.0, 1.0, 0.55, 1.0)) @ Matrix.Rotation(math.radians(90), 4, "X")
    belly.lathe([(0.0, 0.0), (0.38, 0.0), (0.36, 0.4), (0.3, 0.7), (0.18, 0.86), (0.0, 0.9)], 16, jaw_m)
    red.sphere(0.3, mat4((0, -1.45, -0.16)), segs=12, rings=6, scale=(1.05, 1.6, 0.35))
    for s in (-1, 1):
        white.lathe([(0.0, 0.0), (0.04, 0.0), (0.0, 0.09)], 6,
                    Matrix.Translation((s * 0.22, -1.78, -0.12)) @ Matrix.Rotation(math.pi, 4, "X"))
    # big friendly eyes with gold brows
    for s in (-1, 1):
        c = Vector((s * 0.38, -1.12, 0.5))
        white.sphere(0.2, mat4(tuple(c)), segs=16, rings=8)
        black.sphere(0.105, mat4(tuple(c + Vector((s * 0.02, -0.13, 0.0)))), segs=12, rings=6,
                     scale=(1, 0.6, 1.1))
        white.sphere(0.035, mat4(tuple(c + Vector((-s * 0.02, -0.2, 0.06)))), segs=6, rings=3)
        brow = [c + Vector((s * 0.2 * math.cos(a), -0.04, 0.2 * math.sin(a) + 0.05))
                for a in [math.radians(20 + 140 * k / 6) for k in range(7)]]
        gold.tube(brow, [0.035, 0.045, 0.05, 0.05, 0.045, 0.035, 0.025], sides=6, caps=True)
    # horns: antlers sweeping back and up, with one tine
    for s in (-1, 1):
        base = Vector((s * 0.26, -0.72, 0.66))
        pts = bezier(base, base + Vector((s * 0.05, 0.25, 0.3)), Vector((s * 0.35, 0.05, 1.2)),
                     Vector((s * 0.48, 0.22, 1.35)), 8)
        gold.tube(pts, [0.075 * (1 - 0.7 * k / 8) for k in range(9)], sides=6, caps=True)
        mid = pts[4]
        gold.tube([mid, mid + Vector((s * 0.12, -0.18, 0.12)), mid + Vector((s * 0.18, -0.22, 0.26))],
                  [0.045, 0.032, 0.018], sides=5, caps=True)
    # mane: gold flame tongues on the back of the skull and neck, curling back
    mane = [(-0.0, -0.55, 0.62, 0.0), (0.3, -0.45, 0.52, 0.5), (-0.3, -0.45, 0.52, -0.5),
            (0.45, -0.3, 0.3, 0.9), (-0.45, -0.3, 0.3, -0.9), (0.0, -0.2, 0.62, 0.0),
            (0.5, -0.65, 0.05, 1.2), (-0.5, -0.65, 0.05, -1.2)]
    for x, y, z, sx in mane:
        b = Vector((x, y, z))
        d = Vector((sx * 0.5, 1.0, 0.6 if abs(sx) < 1 else 0.1)).normalized()
        pts = bezier(b, b + d * 0.25, b + d * 0.55 + Vector((0, 0, 0.15)), b + d * 0.62 + Vector((0, -0.12, 0.3)), 6)
        gold.tube(pts, [0.1 * (1 - 0.85 * k / 6) for k in range(7)], sides=6, caps=True)
    # long whiskers from the snout, sweeping out and back
    for s in (-1, 1):
        b = Vector((s * 0.3, -1.85, 0.08))
        pts = bezier(b, b + Vector((s * 0.4, -0.1, -0.1)), Vector((s * 1.1, -1.2, 0.5)),
                     Vector((s * 1.25, -0.7, 0.75)), 10)
        gold.tube(pts, [0.035 * (1 - 0.7 * k / 10) for k in range(11)], sides=5, caps=True)
    # chin beard tuft
    b = Vector((0, -1.6, -0.42))
    gold.tube(bezier(b, b + Vector((0, 0.05, -0.15)), b + Vector((0, 0.25, -0.2)), b + Vector((0, 0.4, -0.12)), 5),
              [0.07, 0.065, 0.05, 0.035, 0.02, 0.01], sides=6, caps=True)
    return [join_parts("dragon_head", [jade, flank, plates, belly, light, gold, white, black, red, caps], col)]


def dragon_leg(col):
    """Small clawed leg to hang under the body every few segments. Origin at the hip (top);
    the leg reaches down and forward (-Y), gold claws and an elbow flame."""
    jade = Part("M_Jade", smooth=55)
    belly = Part("M_GoldLight", smooth=55)
    gold = Part("M_Gold", smooth=50)
    jade.sphere(0.22, mat4((0, 0, -0.12)), segs=12, rings=6, scale=(1, 1.1, 1))
    hip, knee, ankle = Vector((0, 0, -0.15)), Vector((0.05, 0.12, -0.5)), Vector((0.03, -0.12, -0.78))
    jade.tube([hip, (hip + knee) / 2, knee], [0.16, 0.13, 0.11], sides=10, caps=True)
    belly.tube([knee, (knee + ankle) / 2, ankle], [0.1, 0.085, 0.08], sides=10, caps=True)
    jade.sphere(0.12, mat4(tuple(ankle + Vector((0, -0.05, -0.02)))), segs=10, rings=5, scale=(1.1, 1.3, 0.7))
    for a, ln in ((-35, 0.2), (0, 0.23), (35, 0.2), (180, 0.14)):
        d = Vector((math.sin(math.radians(a)), -math.cos(math.radians(a)), 0))
        b = ankle + Vector((0, -0.05, -0.04)) + d * 0.08
        gold.tube([b, b + d * ln * 0.6 + Vector((0, 0, -0.02)), b + d * ln + Vector((0, 0, -0.1))],
                  [0.04, 0.03, 0.008], sides=5, caps=True)
    for sx in (-0.08, 0.08, 0.0):
        b = knee + Vector((sx, 0.06, 0.0))
        gold.tube(bezier(b, b + Vector((sx, 0.15, 0.02)), b + Vector((sx * 1.5, 0.3, 0.1)),
                         b + Vector((sx * 1.5, 0.36, 0.22)), 5), [0.06, 0.05, 0.04, 0.03, 0.015, 0.005],
                  sides=5, caps=True)
    return [join_parts("dragon_leg", [jade, belly, gold], col)]
