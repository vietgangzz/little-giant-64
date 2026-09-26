"""Nature props: bamboo_pipe, trees, bamboo, lotus, flowers, grass, mushroom, karst, cloud."""

import math

import bpy
from mathutils import Matrix, Vector

from lib import TAU, Part, bezier, join_parts, lerp, mat4, rng, smoothstep


# --------------------------------------------------------------------------------------------
def bamboo_pipe(col):
    """Warp pipe made of one fat bamboo culm: wide lip, two nodes, hollow dark throat."""
    body = Part("M_Bamboo", smooth=50)
    body.lathe([(0.0, 0.0), (0.55, 0.0), (0.575, 0.025), (0.58, 0.06), (0.58, 1.62)], 40, cap1=False)
    lip = Part("M_BambooLight", smooth=45)
    lip.lathe([(0.572, 1.58), (0.63, 1.605), (0.685, 1.64), (0.7, 1.69), (0.7, 1.93), (0.692, 1.972),
               (0.668, 1.994), (0.63, 2.0), (0.592, 1.992), (0.572, 1.968), (0.566, 1.9)], 40,
              cap0=False, cap1=False)
    throat = Part("M_BambooDark", smooth=50)
    throat.lathe([(0.566, 1.9), (0.566, 1.5), (0.0, 1.5)], 40, cap0=False)
    nodes = Part("M_BambooDark", smooth=45)
    for z in (0.55, 1.12):
        nodes.lathe([(0.57, z - 0.035), (0.6, z - 0.03), (0.612, z), (0.6, z + 0.03), (0.57, z + 0.035)],
                    40, closed=True)
    light = Part("M_BambooLight", smooth=45)
    for z in (0.55, 1.12):   # pale band under each node
        light.lathe([(0.57, z - 0.1), (0.585, z - 0.095), (0.585, z - 0.045), (0.57, z - 0.04)], 40, closed=True)
    # a little sprig out of the upper node, hugging the culm (stays inside the lip radius)
    twig = Part("M_BambooDark", smooth=50)
    a = math.radians(-60)
    out = Vector((math.cos(a), math.sin(a), 0))
    side = Vector((-math.sin(a), math.cos(a), 0))
    base = out * 0.6 + Vector((0, 0, 1.13))
    tip = out * 0.68 + side * 0.12 + Vector((0, 0, 1.36))
    twig.tube([base, (base + tip) / 2 + out * 0.02, tip], [0.026, 0.02, 0.014], sides=6)
    leaves = Part("M_Leaf", smooth=60)
    for d, L in (((side * 0.9 + Vector((0, 0, 0.5)) + out * 0.25), 0.3),
                 ((-side * 0.4 + Vector((0, 0, 1.0)) + out * 0.2), 0.26),
                 ((side * 0.5 + Vector((0, 0, -0.2)) + out * 0.3), 0.24)):
        leaves.leaf(tip, d, L, 0.09, droop=0.3, fold=0.25, steps=5, up=tuple(out))
    return [join_parts("bamboo_pipe", [body, lip, throat, nodes, light, twig, leaves], col)]


# --------------------------------------------------------------------------------------------
def tree_round(col):
    """Round toon tree: flared trunk with root buttresses, lumpy ball canopy in three greens."""
    trunk = Part("M_Wood", smooth=55)
    prof = [(0.0, 0.0), (0.34, 0.0), (0.3, 0.08), (0.21, 0.28), (0.17, 0.7), (0.15, 1.3), (0.13, 1.75),
            (0.0, 1.9)]
    trunk.lathe(prof, 10, shape=lambda th, k: 1.0 + (0.45 if k <= 2 else 0.1 if k == 3 else 0.0) *
                max(0.0, math.cos(5 * th)) ** 3)
    for a, L in ((0.6, 0.55), (2.9, 0.5)):
        d = Vector((math.cos(a), math.sin(a), 1.1)).normalized()
        trunk.tube([Vector((0, 0, 1.2)), Vector((0, 0, 1.2)) + d * L], [0.09, 0.05], sides=6)
    leaf = Part("M_Leaf", smooth=180)
    light = Part("M_LeafLight", smooth=180)
    dark = Part("M_LeafDark", smooth=180)
    leaf.ico(1.0, mat4((0, 0, 2.02)), subdiv=3, scale=(1.0, 1.0, 0.92))
    for c, rr, part, sd in (((-0.4, -0.5, 2.35), 0.5, light, 3), ((0.46, -0.42, 2.3), 0.45, light, 3),
                            ((0.0, -0.15, 2.7), 0.45, light, 3), ((0.66, 0.35, 1.85), 0.52, leaf, 2),
                            ((-0.7, 0.3, 1.9), 0.5, leaf, 2), ((0.05, 0.1, 1.28), 0.5, dark, 2)):
        part.ico(rr, mat4(c), subdiv=sd, scale=(1, 1, 0.85) if part is dark else (1, 1, 1))
    return [join_parts("tree_round", [trunk, leaf, light, dark], col)]


# --------------------------------------------------------------------------------------------
def tree_palm(col):
    """Coconut palm: curved ringed trunk, seven arching serrated fronds, coconuts."""
    path = bezier((0, 0, 0), (0.05, 0, 1.5), (0.35, 0, 2.7), (0.9, 0, 3.55), 24)
    radii = []
    for i in range(len(path)):
        t = i / (len(path) - 1)
        seg = (t * 8) % 1.0
        radii.append(lerp(0.27, 0.16, t) * (1.0 + 0.16 * seg ** 2) + (0.1 * (1 - t / 0.08) if t < 0.08 else 0))
    trunk = Part("M_WoodLight", smooth=48)
    trunk.tube(path, radii, sides=9, caps=True)
    top = path[-1]
    tan = (path[-1] - path[-2]).normalized()
    crown = Part("M_LeafDark", smooth=60)
    crown.sphere(0.26, mat4(tuple(top + tan * 0.05)), segs=10, rings=6, scale=(1, 1, 0.8))
    fr_a = Part("M_Leaf", smooth=55)
    fr_b = Part("M_LeafDark", smooth=55)
    r = rng(3)
    for i in range(7):
        a = TAU * i / 7 + r(-0.15, 0.15)
        d = Vector((math.cos(a), math.sin(a), 0))
        lift = r(0.25, 0.55)
        start = top + Vector((0, 0, 0.08))
        # arching frond: rises then droops
        (fr_a if i % 2 == 0 else fr_b).leaf(start, d + Vector((0, 0, lift)), r(1.8, 2.2), 0.95,
                                             droop=0.62, fold=0.28, steps=16, serrate=0.55,
                                             thick=0.02,
                                             width_fn=lambda t: math.sin(math.pi * min(1.0, 0.05 + t)) ** 0.6)
    nuts = Part("M_Coconut", smooth=60)
    for i in range(4):
        a = TAU * i / 4 + 0.4
        nuts.sphere(0.14, mat4(tuple(top + Vector((0.2 * math.cos(a), 0.2 * math.sin(a), -0.2)))),
                    segs=10, rings=6)
    return [join_parts("tree_palm", [trunk, crown, fr_a, fr_b, nuts], col)]


# --------------------------------------------------------------------------------------------
def _stalk(part, nodes_part, base, direction, height, r0, internode=0.62, segs=6):
    """A bamboo culm: straight stalk with swollen nodes; returns the node positions."""
    d = Vector(direction).normalized()
    m = Matrix.Translation(base) @ Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4()
    prof = [(0.0, 0.0), (r0 * 1.05, 0.0)]
    z = 0.0
    node_z = []
    while z + internode < height - 0.05:
        z += internode
        rr = r0 * (1 - 0.25 * z / height)
        prof += [(rr, z - 0.05), (rr * 1.13, z), (rr, z + 0.04)]
        node_z.append(z)
    rr = r0 * 0.7
    prof += [(rr, height - 0.02), (rr * 0.6, height), (0.0, height)]
    part.lathe(prof, segs, m)
    return [m @ Vector((0, 0, z)) for z in node_z], d


def bamboo_cluster(col):
    """Seven bamboo culms leaning out of one clump, sprigs of leaves on the upper nodes."""
    r = rng(11)
    st_a = Part("M_Bamboo", smooth=50)
    st_b = Part("M_BambooLight", smooth=50)
    nodes = Part("M_BambooDark", smooth=45)
    lv_a = Part("M_Leaf", smooth=60)
    lv_b = Part("M_LeafDark", smooth=60)
    n = 6
    for i in range(n):
        a = TAU * i / n + r(-0.3, 0.3)
        rad = 0.12 if i == 0 else r(0.22, 0.42)
        if i == 0:
            a = 0.0
        pos = Vector((rad * math.cos(a), rad * math.sin(a), 0.0)) if i else Vector((0, 0, 0))
        lean = Vector((math.cos(a) * r(0.05, 0.14), math.sin(a) * r(0.05, 0.14), 1.0))
        h = r(3.1, 3.9) if i else 3.95
        nodes_at, d = _stalk(st_a if i % 2 else st_b, nodes, pos, lean, h, r(0.07, 0.09))
        # leaves on the top nodes, drooping outward
        for k, npos in enumerate(nodes_at[-2:]):
            for j in range(2):
                la = a + (j - 0.5) * 1.6 + r(-0.3, 0.3) + k * 1.3
                ld = Vector((math.cos(la), math.sin(la), r(0.1, 0.5)))
                (lv_a if (j + k) % 2 else lv_b).leaf(npos, ld, r(0.55, 0.7), 0.13, droop=0.45, fold=0.3,
                                                     steps=4, thick=0.012)
        top = pos + d * h
        for j in range(3):
            la = a + j * 2.1
            ld = Vector((math.cos(la), math.sin(la), 0.9))
            lv_a.leaf(top - d * 0.05, ld, 0.55, 0.12, droop=0.45, fold=0.3, steps=4, thick=0.012)
    return [join_parts("bamboo_cluster", [st_a, st_b, lv_a, lv_b], col)]


# --------------------------------------------------------------------------------------------
def _lotus_leaf(part, R, notch_deg=16.0, na=40, nr=5, z0=0.0, seed=1):
    """A lotus pad: partial revolve of a lens section with a V notch towards +X, upturned wavy rim
    and radial vein ridges on top."""
    a0 = math.radians(notch_deg / 2)
    a1 = TAU - a0
    rings = []
    for k in range(na + 1):
        a = lerp(a0, a1, k / na)
        vein = 0.012 * R if (k % 4 == 0) else 0.0
        wave = 0.02 * R * math.sin(7 * a)
        loop = []
        # top from centre to rim (clockwise in (r,z): outward on top, down the rim, back below)
        for i in range(nr + 1):
            t = 0.04 + 0.96 * i / nr
            z = z0 + 0.075 * R + 0.07 * R * t ** 4 + wave * t ** 2 + vein * (1 - t) * (t > 0.1)
            loop.append((t * R, z))
        loop.append((R * 1.005, z0 + 0.05 * R + 0.07 * R + wave))
        for i in range(nr, -1, -1):
            t = 0.04 + 0.96 * i / nr
            z = z0 + 0.02 * R * t ** 2 + 0.05 * R * t ** 4 + wave * t ** 2
            loop.append((t * R, z))
        rings.append([Vector((rr * math.cos(a), rr * math.sin(a), zz)) for rr, zz in loop])
    part.loft(rings, closed_rings=True, cap0=True, cap1=True)


def lotus_pad(col):
    """Walkable lotus leaf, Ø 2.0, gently upturned rim with a notch."""
    pad = Part("M_Lotus", smooth=50)
    _lotus_leaf(pad, 1.0)
    nub = Part("M_LeafLight", smooth=60)
    nub.sphere(0.07, mat4((0, 0, 0.085)), segs=10, rings=5, scale=(1, 1, 0.5))
    return [join_parts("lotus_pad", [pad, nub], col)]


def _lotus_bloom(outer, inner, pod, stam, c, s=1.0):
    """Pink lotus bloom centred at c (base of the petals)."""
    c = Vector(c)
    layers = [(8, 0.3, 62, 0.0, outer), (8, 0.27, 40, math.pi / 8, outer), (6, 0.22, 18, 0.3, inner)]
    for n, L, tilt, ph, part in layers:
        for i in range(n):
            a = ph + TAU * i / n
            d = Vector((math.cos(a) * math.sin(math.radians(tilt)), math.sin(a) * math.sin(math.radians(tilt)),
                        math.cos(math.radians(tilt))))
            part.leaf(c + Vector((math.cos(a), math.sin(a), 0)) * 0.03 * s, d, L * s, 0.17 * s,
                      droop=-0.12, fold=-0.35, steps=5, thick=0.012 * s,
                      width_fn=lambda t: math.sin(math.pi * min(1.0, 0.1 + t * 0.95)) ** 0.6,
                      up=(0, 0, 1) if tilt < 5 else (-d.x, -d.y, 0.0))
    pod.lathe([(0.0, 0.0), (0.05 * s, 0.0), (0.085 * s, 0.1 * s), (0.08 * s, 0.12 * s), (0.0, 0.125 * s)], 12,
              Matrix.Translation(c + Vector((0, 0, 0.02 * s))))
    for i in range(14):
        a = TAU * i / 14
        stam.sphere(0.018 * s, mat4(tuple(c + Vector((0.095 * s * math.cos(a), 0.095 * s * math.sin(a),
                                                       0.09 * s)))), segs=6, rings=3)


def lotus_flower(col):
    """Pink lotus bloom on a short stem rising from a small pad (water-garden decor)."""
    pad = Part("M_Lotus", smooth=50)
    _lotus_leaf(pad, 0.5, notch_deg=20, na=28, nr=4)
    stem = Part("M_LeafDark", smooth=60)
    stem.tube([Vector((0.05, 0.02, 0.03)), Vector((0.06, 0.0, 0.2)), Vector((0.04, -0.02, 0.36))], 0.025,
              sides=6)
    outer = Part("M_Pink", smooth=55)
    inner = Part("M_PinkLight", smooth=55)
    pod = Part("M_Yellow", smooth=50)
    stam = Part("M_Orange", smooth=60)
    _lotus_bloom(outer, inner, pod, stam, (0.04, -0.02, 0.36), s=1.0)
    return [join_parts("lotus_flower", [pad, stem, outer, inner, pod, stam], col)]


# --------------------------------------------------------------------------------------------
def _small_flower(stem, leaves, petals, centre, base, height, lean, n_pet, pet_len, pet_w, pet_shape):
    top = Vector(base) + Vector((lean[0], lean[1], height))
    mid = Vector(base) + Vector((lean[0] * 0.3, lean[1] * 0.3, height * 0.55))
    stem.tube([Vector(base), mid, top], [0.018, 0.015, 0.012], sides=5)
    for a in (0.5, 2.8):
        leaves.leaf(Vector(base) + Vector((0, 0, 0.02)), (math.cos(a), math.sin(a), 0.7), 0.17, 0.07,
                    droop=0.4, fold=0.3, steps=4, thick=0.008)
    face = (Vector((lean[0], lean[1], 0.0)).normalized() * 0.35 + Vector((0, -0.25, 1.0))).normalized()
    q = Vector((0, 0, 1)).rotation_difference(face).to_matrix().to_4x4()
    m = Matrix.Translation(top) @ q
    for i in range(n_pet):
        a = TAU * i / n_pet
        d = Vector((math.cos(a), math.sin(a), 0.25))
        if pet_shape == "round":
            petals.sphere(pet_len * 0.5, m @ Matrix.Rotation(a, 4, "Z") @ mat4((pet_len * 0.55, 0, 0.0)),
                          segs=8, rings=4, scale=(1.0, pet_w / pet_len * 1.6, 0.35))
        else:
            dd = (m.to_3x3() @ d).normalized()
            petals.leaf(m @ Vector((0, 0, 0)), dd, pet_len, pet_w, droop=0.1, fold=-0.2, steps=4, thick=0.008,
                        up=tuple(m.to_3x3() @ Vector((0, 0, 1))))
    centre.sphere(pet_len * 0.42, m @ mat4((0, 0, 0.01)), segs=10, rings=5, scale=(1, 1, 0.65))


def _flower_cluster(name, col, petal_mat, centre_mat, n_pet, shape, pet_len, pet_w):
    stem = Part("M_LeafDark", smooth=60)
    leaves = Part("M_Leaf", smooth=60)
    petals = Part(petal_mat, smooth=60)
    centre = Part(centre_mat, smooth=60)
    for base, h, lean, s in (((0, 0, 0), 0.34, (0.02, -0.03), 1.0), ((0.12, 0.07, 0), 0.24, (0.06, 0.0), 0.85),
                             ((-0.1, 0.06, 0), 0.2, (-0.05, -0.02), 0.8)):
        _small_flower(stem, leaves, petals, centre, base, h, lean, n_pet, pet_len * s, pet_w * s, shape)
    return [join_parts(name, [stem, leaves, petals, centre], col)]


def flower_pink(col):
    """Three pink five-petal flowers with yellow hearts (scatter decor)."""
    return _flower_cluster("flower_pink", col, "M_Pink", "M_Yellow", 5, "round", 0.1, 0.075)


def flower_yellow(col):
    """Three yellow daisy-like flowers with orange hearts (scatter decor)."""
    return _flower_cluster("flower_yellow", col, "M_Yellow", "M_Orange", 8, "blade", 0.1, 0.045)


def grass_tuft(col):
    """A tuft of seven curved grass blades in two greens."""
    a_ = Part("M_Leaf", smooth=60)
    b_ = Part("M_LeafLight", smooth=60)
    r = rng(5)
    for i in range(8):
        a = TAU * i / 8 + r(-0.3, 0.3)
        out = r(0.15, 0.55)
        d = Vector((math.cos(a) * out, math.sin(a) * out, 1.0))
        base = Vector((math.cos(a) * 0.04, math.sin(a) * 0.04, 0.0))
        (a_ if i % 2 else b_).leaf(base, d, r(0.26, 0.42), 0.07, droop=r(0.15, 0.3), fold=0.2, steps=4,
                                   thick=0.008, width_fn=lambda t: 1.0 - t ** 1.5,
                                   up=(math.cos(a), math.sin(a), 0.0))
    return [join_parts("grass_tuft", [a_, b_], col)]


def mushroom(col):
    """Toon mushroom: plump white stem, red dome cap with white spots."""
    stem = Part("M_White", smooth=60)
    stem.lathe([(0.0, 0.0), (0.13, 0.0), (0.155, 0.03), (0.16, 0.1), (0.13, 0.22), (0.115, 0.3), (0.0, 0.3)], 16)
    cap = Part("M_Red", smooth=60)
    prof = [(0.0, 0.26), (0.2, 0.27), (0.29, 0.27), (0.32, 0.3), (0.31, 0.37), (0.27, 0.45), (0.19, 0.52),
            (0.1, 0.555), (0.0, 0.565)]
    cap.lathe(prof, 24)
    gills = Part("M_ShellLight", smooth=40)
    gills.lathe([(0.29, 0.268), (0.12, 0.262), (0.0, 0.26)], 24, cap0=False)
    spots = Part("M_White", smooth=60)
    for a, t in ((0.3, 0.55), (1.6, 0.35), (2.7, 0.62), (3.9, 0.4), (5.2, 0.6), (4.6, 0.12), (1.0, 0.1)):
        # point on the cap surface along the profile at parameter t
        i = t * (len(prof) - 2)
        k = int(i)
        f = i - k
        rr = lerp(prof[len(prof) - 1 - k][0], prof[len(prof) - 2 - k][0], f)
        zz = lerp(prof[len(prof) - 1 - k][1], prof[len(prof) - 2 - k][1], f)
        pos = Vector((rr * math.cos(a), rr * math.sin(a), zz))
        nrm = (Vector((pos.x, pos.y, 0)) * 0.9 + Vector((0, 0, 0.35 if rr > 0.2 else 1.0))).normalized()
        q = Vector((0, 0, 1)).rotation_difference(nrm).to_matrix().to_4x4()
        spots.sphere(0.055, Matrix.Translation(pos) @ q, segs=10, rings=4, scale=(1, 1, 0.35))
    return [join_parts("mushroom", [stem, cap, gills, spots], col)]


# --------------------------------------------------------------------------------------------
def rock_karst(col):
    """Hạ Long limestone tower: wave-cut notch at the waterline, bulging thumb-like body with
    vertical fluting, two side ledges with bushes and a thick green crown spilling over the top.
    3 x 3 x 8 m, origin at the base centre (waterline notch starts at z = 0)."""
    r = rng(21)
    NA = 48
    ph = [r(0, TAU) for _ in range(6)]
    # (z, base radius, ledge id)
    prof = [(0.0, 1.32, 0), (0.22, 1.16, 0), (0.5, 1.12, 0), (0.85, 1.34, 0), (1.6, 1.42, 0),
            (2.5, 1.34, 0), (3.2, 1.26, 0), (3.26, 1.1, 1), (4.0, 1.22, 0), (4.8, 1.42, 0), (5.6, 1.36, 0),
            (5.66, 1.14, 2), (6.2, 1.16, 0), (6.8, 1.1, 0), (7.15, 0.95, 0), (7.4, 0.68, 0)]
    ledge_dir = {1: 0.5, 2: 3.4}
    flute = [0.085, 0.03, -0.06, -0.02]
    lean = Vector((0.12, 0.05, 0))
    rings_lo, rings_hi = [], []
    for k, (z, base, ledge) in enumerate(prof):
        ring = []
        for j in range(NA):
            th = TAU * j / NA
            n = (0.08 * math.sin(2 * th + ph[0] + z * 0.3) + 0.06 * math.sin(3 * th + ph[1] - z * 0.22)
                 + 0.035 * math.sin(5 * th + ph[2] + z * 0.6))
            rr = base * (1 + n) + flute[(j + k // 3) % 4] * min(1.0, z / 0.6 + 0.3)
            if ledge:
                rr -= 0.3 * max(0.0, math.cos(th - ledge_dir[ledge])) ** 2 - 0.12
            off = lean * (z / 8.0) ** 2
            ring.append(Vector((rr * math.cos(th), rr * math.sin(th), z)) + off)
        (rings_lo if z <= 0.5 else rings_hi).append(ring)
    rings_hi.insert(0, rings_lo[-1])
    top_c = lean * (7.6 / 8.0) ** 2 + Vector((0, 0, 7.6))
    rings_hi.append([top_c])
    rings_lo.insert(0, [Vector((0, 0, 0.0))])
    stone = Part("M_Stone", smooth=38)
    stone.loft(rings_hi, closed_rings=True)
    wet = Part("M_StoneDark", smooth=38)
    wet.loft(rings_lo, closed_rings=True)
    # crown: bushes covering the dome and drooping over its rim
    g1 = Part("M_Leaf", smooth=180)
    g2 = Part("M_LeafDark", smooth=180)
    g3 = Part("M_LeafLight", smooth=180)
    tc = top_c
    crown = [((0.0, 0.0, -0.1), 0.78, g1, 3), ((0.62, -0.5, -0.4), 0.5, g3, 2),
             ((-0.66, -0.3, -0.42), 0.55, g2, 2), ((0.25, 0.7, -0.42), 0.52, g1, 2),
             ((-0.5, 0.55, -0.55), 0.45, g2, 2), ((0.86, 0.22, -0.6), 0.42, g1, 2),
             ((-0.1, -0.82, -0.65), 0.42, g2, 2), ((0.2, -0.3, 0.22), 0.45, g3, 2),
             ((-0.9, 0.0, -0.8), 0.34, g1, 2), ((0.55, 0.6, -0.85), 0.32, g3, 2)]
    for c, rad, g, sd in crown:
        g.ico(rad, mat4(tuple(tc + Vector(c))), subdiv=sd, scale=(1, 1, 0.78))
    for lk, la in ledge_dir.items():
        z = [p[0] for p in prof if p[2] == lk][0]
        off = lean * (z / 8.0) ** 2
        for da, rad, g, rr in ((-0.32, 0.36, g2, 1.2), (0.0, 0.46, g1, 1.22), (0.32, 0.34, g3, 1.18)):
            a = la + da
            g.ico(rad, mat4(tuple(off + Vector((rr * math.cos(a), rr * math.sin(a), z + 0.12)))), subdiv=2,
                  scale=(1, 1, 0.75))
    return [join_parts("rock_karst", [stone, wet, g1, g2, g3], col)]


# --------------------------------------------------------------------------------------------
def cloud(col):
    """Puffy cloud: overlapping spheres voxel-remeshed into one smooth shell, flattened underside."""
    part = Part("M_Cloud", smooth=180)
    puffs = [((0.0, 0.0, 1.0), 0.95), ((-0.95, 0.05, 0.78), 0.72), ((1.0, -0.05, 0.8), 0.75),
             ((-0.4, -0.35, 1.45), 0.62), ((0.5, 0.2, 1.5), 0.6), ((-1.6, 0.0, 0.62), 0.45),
             ((1.65, 0.1, 0.62), 0.45), ((0.15, 0.55, 0.9), 0.65), ((-0.2, -0.6, 0.8), 0.55)]
    for c, rad in puffs:
        part.ico(rad, mat4(c), subdiv=4)
    zmin = min(v.co.z for v in part.bm.verts)
    flat = 0.52

    def squash(v):
        if v.z < flat:
            v.z = flat + (v.z - flat) * 0.3
        return v
    part.deform(squash)
    part.mods += [("REMESH", {"mode": "VOXEL", "voxel_size": 0.07}),
                  ("SMOOTH", {"factor": 0.8, "iterations": 6}),
                  ("DECIMATE", {"ratio": 0.08})]
    # bottom to z = 0 is done after evaluation (see join): shift now using the squashed minimum
    zmin = min(v.co.z for v in part.bm.verts)
    part.deform(lambda v: v - Vector((0, 0, zmin)))
    return [join_parts("cloud", [part], col)]
