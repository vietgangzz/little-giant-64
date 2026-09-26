"""Hạ Long level, cave & collectible props: pearl (Dragon Pearl), stalactite, stalagmite,
crystal_cluster."""

import math

from mathutils import Matrix, Vector

from lib import TAU, Part, join_parts, lerp, mat4, rng


# --------------------------------------------------------------------------------------------
def pearl(col):
    """The Dragon Pearl (red-coin role): glowing pearly orb Ø 0.55 held by a gold lotus cradle
    with three flame swirls curling up around it. Origin at the cradle base."""
    orb = Part("M_Pearl", smooth=180)
    R, CZ = 0.275, 0.4
    orb.sphere(R, mat4((0, 0, CZ)), segs=24, rings=12)
    gold = Part("M_Gold", smooth=50)
    # lotus cup: scalloped petals
    gold.lathe([(0.0, 0.0), (0.1, 0.0), (0.12, 0.03), (0.09, 0.07), (0.13, 0.12), (0.2, 0.17), (0.215, 0.2),
                (0.17, 0.19), (0.0, 0.16)], 24, shape=lambda th, k: 1.0 + (0.12 if k >= 4 else 0.0) *
                abs(math.cos(4 * th)) ** 2)
    # three flame swirls
    for i in range(3):
        a0 = TAU * i / 3
        pts = []
        n = 12
        for k in range(n + 1):
            t = k / n
            a = a0 + 2.2 * t
            r = 0.2 + 0.13 * math.sin(math.pi * min(1.0, t * 1.1))
            z = 0.15 + 0.55 * t
            pts.append(Vector((r * math.cos(a), r * math.sin(a), z)))
        # curl the tip inward
        tip = pts[-1]
        d = Vector((-tip.x, -tip.y, 0)).normalized()
        pts += [tip + d * 0.05 + Vector((0, 0, 0.04)), tip + d * 0.09 + Vector((0, 0, 0.0))]
        radii = [0.045 * (1 - 0.55 * k / (len(pts) - 1)) for k in range(len(pts))]
        gold.tube(pts, radii, sides=6, caps=True)
    # a small flame crown on top
    gold.lathe([(0.0, 0.66), (0.05, 0.665), (0.035, 0.72), (0.0, 0.8)], 8)
    return [join_parts("pearl", [orb, gold], col)]


# --------------------------------------------------------------------------------------------
def _dripstone(part_a, part_b, height, r0, sign, seed, segs=14, band=0.62):
    """Lumpy cone with flowstone rings. sign=+1 grows up from z=0, -1 hangs down from z=0.
    part_a: upper (base) material, part_b: tip material from `band` of the height on."""
    r = rng(seed)
    ph = [r(0, TAU) for _ in range(3)]
    n = 12
    prof = []
    for k in range(n + 1):
        t = k / n
        rr = r0 * (1 - t) ** 0.85 * (1 + 0.1 * math.sin(t * 19 + ph[0]))
        if k == n:
            rr = 0.0
        prof.append((max(rr, 0.0), t * height))
    prof[-2] = (prof[-2][0] * 0.6 + 0.02, prof[-2][1])

    def shape(th, k):
        return 1.0 + 0.09 * math.sin(3 * th + ph[1] + k * 0.4) + 0.06 * math.sin(5 * th + ph[2])

    kb = int(band * n)
    for part, sub in ((part_a, prof[:kb + 1]), (part_b, prof[kb:])):
        rings = []
        for k, (rr, z) in enumerate(sub):
            kk = k + (0 if part is part_a else kb)
            if rr < 1e-6:
                rings.append([Vector((0, 0, sign * z))])
                continue
            rings.append([Vector((rr * shape(TAU * j / segs, kk) * math.cos(TAU * j / segs),
                                  rr * shape(TAU * j / segs, kk) * math.sin(TAU * j / segs), sign * z))
                          for j in range(segs)])
        if part is part_a:
            rings.insert(0, [Vector((0, 0, 0))])
        if sign < 0:
            rings.reverse()
        part.loft(rings, closed_rings=True)


def stalactite(col):
    """Hanging cave formation, ~2.5 m. Origin at the TOP centre (the ceiling contact)."""
    a = Part("M_Limestone", smooth=50)
    b = Part("M_Amber", smooth=50)
    _dripstone(a, b, 2.5, 0.5, -1, 3)
    for (x, y, h, rr, sd) in ((0.45, 0.2, 1.3, 0.25, 5), (-0.35, 0.35, 0.9, 0.2, 7), (0.05, -0.45, 1.6, 0.22, 9)):
        ta = Part("M_Limestone", smooth=50)
        tb = Part("M_Amber", smooth=50)
        _dripstone(ta, tb, h, rr, -1, sd)
        a.merge_part(ta, mat4((x, y, 0)))
        b.merge_part(tb, mat4((x, y, 0)))
    # ceiling pad
    a.lathe([(0.0, -0.12), (0.62, -0.1), (0.72, -0.04), (0.7, 0.0), (0.0, 0.0)], 16,
            shape=lambda th, k: 1.0 + 0.1 * math.sin(3 * th))
    return [join_parts("stalactite", [a, b], col)]


def stalagmite(col):
    """Cave floor formation, ~1.8 m, with two small satellites."""
    a = Part("M_Limestone", smooth=50)
    b = Part("M_Amber", smooth=50)
    _dripstone(a, b, 1.8, 0.55, 1, 11, band=0.55)
    for (x, y, h, rr, sd) in ((0.55, -0.2, 0.7, 0.22, 13), (-0.45, 0.3, 0.5, 0.18, 17)):
        ta = Part("M_Limestone", smooth=50)
        tb = Part("M_Amber", smooth=50)
        _dripstone(ta, tb, h, rr, 1, sd, band=0.5)
        a.merge_part(ta, mat4((x, y, 0)))
        b.merge_part(tb, mat4((x, y, 0)))
    # a round tip bead
    b.sphere(0.07, mat4((0, 0, 1.78)), segs=8, rings=4)
    return [join_parts("stalagmite", [a, b], col)]


def crystal_cluster(col):
    """Soft cyan glowing crystals (hexagonal, pointed) on a dark rock, ~0.8 m."""
    rock = Part("M_StoneDark", smooth=35)
    rock.ico(0.38, mat4((0, 0, 0.08)), subdiv=2, scale=(1.2, 1.0, 0.45))
    xtal = Part("M_Crystal", smooth=None)
    r = rng(23)
    spec = [((0, 0, 0.1), (0, 0, 1), 0.72, 0.1), ((0.18, 0.05, 0.08), (0.5, 0.1, 1), 0.5, 0.08),
            ((-0.16, 0.1, 0.08), (-0.55, 0.2, 1), 0.46, 0.075), ((0.05, -0.18, 0.08), (0.1, -0.6, 1), 0.4, 0.07),
            ((-0.1, -0.12, 0.06), (-0.4, -0.5, 1), 0.3, 0.06), ((0.2, -0.12, 0.05), (0.7, -0.4, 1), 0.28, 0.055),
            ((0.02, 0.2, 0.06), (0.0, 0.7, 1), 0.34, 0.06)]
    for base, d, L, rad in spec:
        d = Vector(d).normalized()
        m = Matrix.Translation(base) @ Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4() @ \
            Matrix.Rotation(r(0, 1), 4, "Z")
        xtal.lathe([(0.0, -0.05), (rad, -0.05), (rad, L * 0.78), (0.0, L)], 6, m)
    zmin = min(v.co.z for p in (rock, xtal) for v in p.bm.verts)
    for p in (rock, xtal):
        p.deform(lambda v: v - Vector((0, 0, zmin)))
    return [join_parts("crystal_cluster", [rock, xtal], col)]
