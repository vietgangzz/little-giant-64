"""Đông Sơn drum motifs shared by several props (star, rings, ticks, chim Lạc birds, frogs)."""

import math

from mathutils import Matrix, Vector

from lib import TAU, Part, mat4, star_points, circle_points


def raised_star(part, n, r_out, r_in, z0, h, m=Matrix(), rot=90.0, inset=0.82):
    """Flat drum-face star in low relief with a chamfered top (sharp readable points)."""
    pts = star_points(n, r_out, r_in, rot)
    part.extrude_poly_tapered(pts, z0, z0 + h, inset, m)


def faceted_star_relief(part, n, r_out, r_in, z0, h_edge, h_center, m=Matrix(), rot=90.0):
    """One-sided crystal star sitting on a surface at z0 (ridges from centre to each tip)."""
    part.faceted_star(n, r_out, r_in, h_center, h_edge, m @ Matrix.Translation((0, 0, z0)),
                      rot=rot, back=False)
    # push the underside down onto the surface
    return part


def ring(part, r_in, r_out, z0, h, m=Matrix(), segs=48, round_top=True):
    """Raised concentric ring (a low rounded bead) on a face whose normal is local +Z."""
    w = r_out - r_in
    if round_top:
        prof = [(r_out, z0), (r_out, z0 + h * 0.6), (r_out - w * 0.25, z0 + h), (r_in + w * 0.25, z0 + h),
                (r_in, z0 + h * 0.6), (r_in, z0)]
    else:
        prof = [(r_out, z0), (r_out, z0 + h), (r_in, z0 + h), (r_in, z0)]
    # anticlockwise in (r, z): outer wall up, top inward, inner wall down (outside on the right)
    part.lathe(prof, segs, m, cap0=False, cap1=False)


def tick_ring(part, r, n, length, width, h, z0, m=Matrix(), phase=0.0):
    """Ring of small radial bars (the tick bands of a drum face)."""
    for i in range(n):
        a = phase + TAU * i / n
        mm = m @ Matrix.Rotation(a, 4, "Z") @ Matrix.Translation((r, 0, z0 + h / 2))
        part.cube((length, width, h), mm)


def bump_ring(part, r, n, rad, z0, m=Matrix(), phase=0.0, segs=6, rings=3):
    """Ring of small hemispherical studs."""
    for i in range(n):
        a = phase + TAU * i / n
        mm = m @ Matrix.Translation((r * math.cos(a), r * math.sin(a), z0))
        part.sphere(rad, mm, segs=segs, rings=rings, scale=(1, 1, 0.7))


# Chim Lạc (the long-beaked Lạc bird of the Đông Sơn drums), side view, beak towards +X.
BIRD = [
    (1.00, 0.00), (0.62, 0.07), (0.55, 0.13), (0.52, 0.26), (0.46, 0.14), (0.40, 0.10),
    (0.30, 0.13), (0.14, 0.34), (0.02, 0.52), (-0.02, 0.40), (0.02, 0.22), (-0.08, 0.12),
    (-0.30, 0.20), (-0.52, 0.26), (-0.42, 0.10), (-0.56, 0.02), (-0.36, -0.03), (-0.10, -0.08),
    (0.20, -0.08), (0.42, -0.05), (0.60, -0.01),
]


def bird(part, m, length, h):
    """Extruded chim Lạc silhouette lying on a face (local XY), height h along +Z."""
    pts = [(x * length, y * length) for x, y in BIRD]
    part.extrude_poly_tapered(pts, 0.0, h, 0.94, m)


def bird_ring(part, r, n, length, h, z0, m=Matrix(), phase=0.0):
    """Birds flying anticlockwise around the centre (as on the Ngọc Lũ drum)."""
    for i in range(n):
        a = phase + TAU * i / n
        # tangent direction (anticlockwise) = a + 90deg; bird beak along local +X
        mm = m @ Matrix.Rotation(a, 4, "Z") @ Matrix.Translation((r, 0, z0)) @ Matrix.Rotation(
            math.pi / 2, 4, "Z") @ Matrix.Translation((0, -0.18 * length, 0))
        bird(part, mm, length, h)


def frog(body, eyes, m, s=1.0, lod=1):
    """A little bronze frog statuette (the rain frogs on drum rims). Faces local +X.
    lod 0 = tiny (bounce pad), 1 = hero (drum_big)."""
    bs, hs, ls = ((8, 4), (8, 4), (6, 3)) if lod == 0 else ((12, 6), (10, 5), (8, 4))
    body.sphere(0.5 * s, m @ mat4((0, 0, 0.32 * s)), segs=bs[0], rings=bs[1], scale=(1.25, 0.95, 0.62))
    body.sphere(0.32 * s, m @ mat4((0.42 * s, 0, 0.46 * s)), segs=hs[0], rings=hs[1], scale=(1.0, 1.1, 0.8))
    for side in (-1, 1):
        # haunches and front feet
        body.sphere(0.24 * s, m @ mat4((-0.32 * s, side * 0.42 * s, 0.2 * s)), segs=ls[0], rings=ls[1],
                    scale=(1.4, 0.8, 0.8))
        body.sphere(0.12 * s, m @ mat4((0.45 * s, side * 0.38 * s, 0.08 * s)), segs=ls[0], rings=ls[1],
                    scale=(1.3, 1.0, 0.6))
        eyes.sphere(0.12 * s, m @ mat4((0.5 * s, side * 0.2 * s, 0.66 * s)), segs=ls[0], rings=ls[1])


def question_mark(part, m, h=0.5, width=0.1, depth=0.045):
    """A chunky rounded "?" built from a flattened swept stroke + a dot (no font needed).
    Lies on a face whose normal is local +Z; spans about h tall centred on the origin."""
    k = h / 0.5
    pts = []
    for i in range(12):
        th = math.radians(165 - (165 + 55) * i / 11)
        pts.append(Vector((0.14 * k * math.cos(th), (0.1 + 0.135 * math.sin(th)) * k, 0)))
    pts += [Vector((0.035 * k, -0.045 * k, 0)), Vector((0.0, -0.085 * k, 0)), Vector((0.0, -0.11 * k, 0))]
    z = depth * 0.45
    pts = [m @ (p + Vector((0, 0, z))) for p in pts]
    normal = (m.to_3x3() @ Vector((0, 0, 1))).normalized()
    # section: x along the face normal (depth), y across the stroke (width)
    sec = [(depth / width * math.cos(a), math.sin(a)) for a in [math.tau * i / 8 for i in range(8)]]
    part.tube(pts, width / 2, section=sec, up=tuple(normal), caps=True)
    for p in (pts[0], pts[-1]):
        part.sphere(width / 2, Matrix.Translation(p) @ (m.to_3x3().to_4x4()), segs=8, rings=4,
                    scale=(1, 1, depth / width))
    dot = m @ Vector((0, -0.2 * k, z))
    part.sphere(width * 0.62, Matrix.Translation(dot) @ (m.to_3x3().to_4x4()), segs=10, rings=5,
                scale=(1, 1, depth / width * 0.9))


def drum_profile(r, h):
    """Đông Sơn drum silhouette as a lathe profile (bottom -> top), radius r, height h.
    Flared foot, straight waist, bulging shoulder, overhanging face."""
    pts = [
        (0.0, 0.0),
        (0.86, 0.0), (0.93, 0.015), (0.94, 0.05), (0.88, 0.1),   # flared foot with a lip
        (0.80, 0.25), (0.78, 0.45),                              # waist
        (0.80, 0.52), (0.88, 0.62), (0.94, 0.74),                # shoulder bulge
        (0.955, 0.86), (0.95, 0.92),
        (0.97, 0.94), (1.0, 0.955), (1.0, 0.985), (0.985, 1.0),  # overhanging face lip
        (0.0, 1.0),
    ]
    return [(x * r, z * h) for x, z in pts]
