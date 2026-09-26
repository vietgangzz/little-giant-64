"""Built props: checkpoint flag, One Pillar Pagoda, sampan, Hội An lantern, bamboo fence,
bridge plank segment and the cổng làng village gate."""

import json
import math
import os

import bpy
from mathutils import Matrix, Vector

import motifs
from lib import (TAU, Part, bezier, densify, join_parts, lerp, mat4, rng, rounded_rect_points,
                 simplify_points, svg_path_points)
from p_nature import _lotus_leaf

HERE = os.path.dirname(os.path.abspath(__file__))
ARTWORK = os.path.join(HERE, "..", "common", "mascot_artwork.json")


# --------------------------------------------------------------------------------------------
# shared: curved hip roof with upturned "dragon-tail" corners
# --------------------------------------------------------------------------------------------
def hip_roof(tiles, ridge_part, curl_part, z_eave, ax, ay, rx, rise, thick=0.12, n=18, lift=0.42,
             flare=0.14, tile_rows=True, curls=True):
    """Hip roof over a rectangle (half sizes ax, ay), ridge along X of half length rx.
    Concave slopes, corners lifted and pushed out, alternating tile ridges, eave rim, hip ridges
    and curled corner tails. Returns the ridge endpoints."""
    top = []
    bot = []

    def surf(u, v, under):
        x0, y0 = u * ax, v * ay
        fx = max(0.0, (abs(x0) - rx) / (ax - rx))
        fy = abs(y0) / ay
        f = min(1.0, max(fx, fy))
        c = min(abs(u), abs(v))
        h = z_eave + rise * (1 - f) ** 1.7
        h += lift * (c ** 4) * (f ** 3)
        push = 1.0 + flare * c ** 4
        x, y = x0 * push, y0 * push
        if tile_rows and not under and 0.02 < f < 0.985:
            # tile rows run down-slope: corrugate across the slope
            if fy >= fx:
                k = round((u + 1) * n / 2)
            else:
                k = round((v + 1) * n / 2)
            if k % 2 == 1:
                h += 0.045
        if under:
            h -= thick
        return Vector((x, y, h))

    grid_t = [[surf(-1 + 2 * i / n, -1 + 2 * j / n, False) for j in range(n + 1)] for i in range(n + 1)]
    grid_b = [[surf(-1 + 2 * i / n, -1 + 2 * j / n, True) for j in range(n + 1)] for i in range(n + 1)]
    vt = [[tiles._v(p) for p in row] for row in grid_t]
    vb = [[tiles._v(p) for p in row] for row in grid_b]
    for i in range(n):
        for j in range(n):
            tiles.face([vt[i][j], vt[i + 1][j], vt[i + 1][j + 1], vt[i][j + 1]])
            tiles.face([vb[i][j], vb[i][j + 1], vb[i + 1][j + 1], vb[i + 1][j]])
    # border band (eave edge)
    border = [(i, 0) for i in range(n)] + [(n, j) for j in range(n)] + [(i, n) for i in range(n, 0, -1)] + \
             [(0, j) for j in range(n, 0, -1)]
    for k in range(len(border)):
        i0, j0 = border[k]
        i1, j1 = border[(k + 1) % len(border)]
        tiles.face([vt[i0][j0], vb[i0][j0], vb[i1][j1], vt[i1][j1]])
    # eave rim (a rounded lip along the border) and hip ridges
    rim = [grid_t[i][j] + Vector((0, 0, 0.02)) for i, j in border]
    ridge_part.tube(rim, 0.055, sides=6, closed=True)
    ends = [surf(-rx / ax, 0, False) + Vector((0, 0, 0.05)), surf(rx / ax, 0, False) + Vector((0, 0, 0.05))]
    ridge_part.tube([ends[0], ends[1]], 0.09, sides=8, caps=True)
    for sx in (-1, 1):
        for sy in (-1, 1):
            hip = [surf(sx * lerp(rx / ax, 1.0, t), sy * t, False) + Vector((0, 0, 0.05)) for t in
                   [k / 10 for k in range(11)]]
            ridge_part.tube(hip, 0.06, sides=6, caps=True)
            if curls:
                c = hip[-1]
                d = Vector((sx, sy, 0)).normalized()
                # a short dragon-tail hook: out, up and curling back over the corner
                pts = [c - d * 0.05 + d * (0.17 * math.sin(a)) + Vector((0, 0, 0.17 * (1 - math.cos(a))))
                       for a in [k * 0.36 for k in range(9)]]
                curl_part.tube(pts, [0.085 * (1 - 0.7 * k / 8) for k in range(9)], sides=6, caps=True)
                curl_part.sphere(0.035, mat4(tuple(pts[-1])), segs=6, rings=3)
    return ends


# --------------------------------------------------------------------------------------------
def checkpoint(col):
    """Bamboo flagpole on a drum pedestal with a gold ball; the lime VGANG flag with the two
    brand 'gang eyes' is a separate mesh object named "Flag" (origin at the pole edge, top) so
    Godot can wave it in a vertex shader (weight = local X / 1.0 or UV.x)."""
    base = Part("M_Bronze", smooth=45)
    base.lathe([(0.0, 0.0), (0.32, 0.0), (0.345, 0.02), (0.345, 0.1), (0.32, 0.13), (0.3, 0.15), (0.0, 0.15)], 28)
    trim = Part("M_Gold", smooth=45)
    motifs.ring(trim, 0.2, 0.24, 0.14, 0.03, segs=28, round_top=False)
    trim.faceted_star(12, 0.17, 0.06, 0.035, 0.01, Matrix.Translation((0, 0, 0.15)), back=False)
    pole = Part("M_BambooDry", smooth=50)
    prof = [(0.0, 0.14), (0.05, 0.14)]
    for z in (0.7, 1.3, 1.9):
        prof += [(0.045, z - 0.03), (0.055, z), (0.045, z + 0.03)]
    prof += [(0.042, 2.44), (0.0, 2.44)]
    pole.lathe(prof, 10)
    trim.sphere(0.1, mat4((0, 0, 2.5)), segs=16, rings=8)
    trim.cylinder(0.05, 0.05, 10, mat4((0, 0, 2.39)))
    pole_obj = join_parts("checkpoint", [base, trim, pole], col)

    # ---- the flag cloth ----
    W, H, NX, NZ = 1.0, 0.64, 16, 10
    cloth = Part("M_Lime", smooth=180)
    t = 0.008
    for side in (-1, 1):
        rows = []
        for i in range(NX + 1):
            x = W * i / NX
            rows.append([cloth._v(Vector((x, side * t, -H * j / NZ))) for j in range(NZ + 1)])
        for i in range(NX):
            for j in range(NZ):
                q = [rows[i][j], rows[i + 1][j], rows[i + 1][j + 1], rows[i][j + 1]]
                cloth.face(q if side < 0 else list(reversed(q)))
        if side < 0:
            front = rows
        else:
            back = rows
    # close the edges
    edges = [(i, 0) for i in range(NX)] + [(NX, j) for j in range(NZ)] + \
            [(i, NZ) for i in range(NX, 0, -1)] + [(0, j) for j in range(NZ, 0, -1)]
    for k in range(len(edges)):
        i0, j0 = edges[k]
        i1, j1 = edges[(k + 1) % len(edges)]
        cloth.face([front[i0][j0], back[i0][j0], back[i1][j1], front[i1][j1]])
    cloth.flip()  # the grid above is wound inward; flip the whole closed shell
    eyes = Part("M_EyeGreen", smooth=None)
    art = json.load(open(ARTWORK))
    polys = [simplify_points(svg_path_points(d, samples=4), 4.0) for d in art["eyes"]]
    allp = [p for poly in polys for p in poly]
    cx = (min(p[0] for p in allp) + max(p[0] for p in allp)) / 2
    cy = (min(p[1] for p in allp) + max(p[1] for p in allp)) / 2
    span = max(p[0] for p in allp) - min(p[0] for p in allp)
    sc = 0.5 / span
    for poly in polys:
        pts = [((x - cx) * sc + W * 0.52, (y - cy) * sc - H * 0.5) for x, y in poly]
        pts = densify(pts, 0.03)
        # local XY -> flag XZ plane, extruded along -Y (front); the back print is mirrored in X
        front_m = Matrix(((1, 0, 0, 0), (0, 0, -1, -t), (0, 1, 0, 0), (0, 0, 0, 1)))
        back_m = Matrix(((-1, 0, 0, 0), (0, 0, 1, t), (0, 1, 0, 0), (0, 0, 0, 1)))
        eyes.extrude_poly(pts, 0.0, 0.006, front_m)
        eyes.extrude_poly([(-x, y) for x, y in pts], 0.0, 0.006, back_m)
    flag = join_parts("Flag", [cloth, eyes], col)
    # UVs: u = distance from the pole (0..1), v = down the flag
    me = flag.data
    uv = me.uv_layers.new(name="UVMap")
    for loop in me.loops:
        co = me.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (max(0.0, min(1.0, co.x / W)), max(0.0, min(1.0, -co.z / H)))
    flag.parent = pole_obj
    flag.location = (0.05, 0.0, 2.36)
    return [pole_obj]


# --------------------------------------------------------------------------------------------
def pagoda(col):
    """Chùa Một Cột (One Pillar Pagoda): square lacquered pavilion with a curved tiled roof and
    upturned dragon-tail eaves on a single stone pillar in a square lotus pond, with its stair."""
    stone = Part("M_StoneLight", smooth=40, bevel=(0.03, 2))
    stone_d = Part("M_Stone", smooth=40)
    water = Part("M_Water", smooth=40)
    # pond: four walls + coping, water inside
    P, T, HW = 2.3, 0.28, 0.5
    for sx, sy, w, d in ((0, -1, 2 * P, T), (0, 1, 2 * P, T), (-1, 0, T, 2 * P - 2 * T), (1, 0, T, 2 * P - 2 * T)):
        c = Vector((sx * (P - T / 2), sy * (P - T / 2), HW / 2))
        stone.cube((w, d, HW), mat4(tuple(c)))
    water.box((-P + T, -P + T, 0.0), (P - T, P - T, 0.32))
    lp = Part("M_Lotus", smooth=50)
    for x, y, r in ((1.2, -1.2, 0.34), (-1.3, 0.9, 0.3), (1.35, 1.1, 0.26), (-0.9, -1.45, 0.28)):
        tmp = Part("M_Lotus")
        _lotus_leaf(tmp, r, na=16, nr=3, z0=0.3)
        lp.merge_part(tmp, mat4((x, y, 0), (0, 0, x * 90)))
    pink = Part("M_Pink", smooth=55)
    for x, y in ((1.25, -1.1), (-1.25, 0.95)):
        pink.sphere(0.1, mat4((x, y, 0.45)), segs=8, rings=5, scale=(1, 1, 1.3))
    # the single pillar
    stone_d.lathe([(0.0, 0.3), (0.55, 0.3), (0.55, 0.42), (0.46, 0.5), (0.43, 0.6), (0.42, 2.55),
                   (0.46, 2.65), (0.52, 2.72), (0.0, 2.72)], 20)
    # wooden bracket frame (the "lotus" struts) from the pillar head to the platform
    wood = Part("M_WoodDark", smooth=40, bevel=(0.02, 1))
    for i in range(8):
        a = TAU * i / 8
        d = Vector((math.cos(a), math.sin(a), 0))
        reach = 1.35 / max(abs(math.cos(a)), abs(math.sin(a)))
        wood.tube([d * 0.42 + Vector((0, 0, 2.35)), d * reach * 0.92 + Vector((0, 0, 3.0))], 0.07, sides=6)
    wood.box((-0.55, -0.55, 2.72), (0.55, 0.55, 2.86))
    for s in (-1, 1):
        wood.box((-1.45, s * 0.5 - 0.07, 2.86), (1.45, s * 0.5 + 0.07, 3.0))
        wood.box((s * 0.5 - 0.07, -1.45, 2.86), (s * 0.5 + 0.07, 1.45, 3.0))
    floor = Part("M_Wood", smooth=40, bevel=(0.03, 2))
    floor.box((-1.5, -1.5, 3.0), (1.5, 1.5, 3.14))
    # railing around the balcony
    red = Part("M_Red", smooth=40)
    for i in range(9):
        for s in (-1, 1):
            t = -1.4 + 2.8 * i / 8
            if abs(t) < 0.35 and s == -1:
                continue  # opening for the stair
            red.box((t - 0.035, s * 1.4 - 0.035, 3.14), (t + 0.035, s * 1.4 + 0.035, 3.52))
            red.box((s * 1.4 - 0.035, t - 0.035, 3.14), (s * 1.4 + 0.035, t + 0.035, 3.52))
    for s in (-1, 1):
        red.box((s * 1.4 - 0.045, -1.445, 3.5), (s * 1.4 + 0.045, 1.445, 3.56))
        red.box((0.35 if s > 0 else -1.445, 1.4 * -1 - 0.045, 3.5), (1.445 if s > 0 else -0.35, -1.4 + 0.045, 3.56))
    red.box((-1.445, 1.4 - 0.045, 3.5), (1.445, 1.4 + 0.045, 3.56))
    # the room: red columns, light wooden walls, door and lattice windows
    walls = Part("M_WoodLight", smooth=40)
    R0 = 1.05
    walls.box((-R0, -R0, 3.14), (R0, R0, 4.3))
    for sx in (-1, 1):
        for sy in (-1, 1):
            red.cylinder(0.09, 1.3, 10, mat4((sx * (R0 + 0.02), sy * (R0 + 0.02), 3.14)))
    dark = Part("M_WoodDark", smooth=40)
    dark.box((-0.36, -R0 - 0.03, 3.14), (0.36, -R0 + 0.01, 4.0))           # door recess
    gold = Part("M_Gold", smooth=45)
    gold.box((-0.03, -R0 - 0.05, 3.14), (0.03, -R0 - 0.01, 4.0))           # door split
    for face in range(1, 4):
        a = face * math.pi / 2
        m = Matrix.Rotation(a, 4, "Z")
        dark.box((-0.45, -R0 - 0.03, 3.45), (0.45, -R0 + 0.01, 3.95), m)
        for k in range(5):
            x = -0.36 + 0.18 * k
            red.box((x - 0.018, -R0 - 0.06, 3.45), (x + 0.018, -R0 - 0.02, 3.95), m)
        red.box((-0.45, -R0 - 0.06, 3.68), (0.45, -R0 - 0.02, 3.72), m)
    # the roof
    tiles = Part("M_Roof", smooth=35)
    ridge = Part("M_RoofDark", smooth=45)
    curl_tails = Part("M_RoofDark", smooth=45)
    ends = hip_roof(tiles, ridge, curl_tails, z_eave=4.18, ax=1.95, ay=1.95, rx=0.45, rise=1.05, n=12)
    curl = Part("M_Gold", smooth=45)
    # ridge ornament: two little dragons rising toward a golden pearl
    for s in (-1, 1):
        e = ends[0] if s < 0 else ends[1]
        pts = bezier(e, e + Vector((0, 0, 0.35)), Vector((s * 0.22, 0, e.z + 0.05)),
                     Vector((s * 0.12, 0, e.z + 0.32)), 10)
        curl.tube(pts, [0.075 - 0.045 * k / 10 for k in range(11)], sides=6, caps=True)
        curl.sphere(0.05, mat4(tuple(pts[1] + Vector((s * 0.03, 0, 0.02)))), segs=8, rings=4)
    top = (ends[0] + ends[1]) / 2
    curl.sphere(0.12, mat4(tuple(top + Vector((0, 0, 0.38)))), segs=12, rings=6)
    curl.lathe([(0.0, 0.0), (0.09, 0.02), (0.05, 0.12), (0.0, 0.2)], 8, Matrix.Translation(top + Vector((0, 0, 0.04))))
    # stair from outside the pond up to the balcony (front, -Y)
    stair = Part("M_Wood", smooth=40, bevel=(0.015, 1))
    n = 13
    y0, y1, z1 = -3.25, -1.5, 3.14
    for k in range(n):
        t = (k + 1) / n
        y = lerp(y0, y1, t)
        z = z1 * t
        stair.box((-0.4, y - 0.09, z - 0.06), (0.4, y + 0.09, z))
    for s in (-1, 1):
        red.tube([Vector((s * 0.43, y0 - 0.02, 0.05)), Vector((s * 0.43, y1, z1))], 0.05, sides=6)
        red.tube([Vector((s * 0.43, y0 - 0.02, 0.75)), Vector((s * 0.43, y1, z1 + 0.42))], 0.035, sides=6)
        red.cylinder(0.05, 0.8, 8, mat4((s * 0.43, y0 - 0.02, 0.0)))
    return [join_parts("pagoda", [stone, stone_d, water, lp, pink, wood, floor, red, walls, dark, gold, tiles,
                                  ridge, curl, curl_tails, stair], col)]


# --------------------------------------------------------------------------------------------
def sampan(col):
    """Vietnamese sampan (moving platform): rising bow and stern, painted bow eyes, red gunwale
    stripe, plank deck and a woven bamboo arched canopy. 1.4 x 3.5 m, bow towards -Y."""
    L, B = 3.24, 1.4
    N = 26
    hull = Part("M_WoodDark", smooth=40)
    stations = []
    for k in range(N + 1):
        t = lerp(0.006, 0.994, k / N)
        y = lerp(-L / 2, L / 2, t)
        e = abs(2 * t - 1)
        w = (B / 2) * math.sin(math.pi * t) ** 0.75
        sheer = 0.55 + 0.42 * e ** 3.0
        keel = 0.5 * e ** 3.2
        stations.append((y, w, sheer, keel))
    rings = []
    for y, w, sheer, keel in stations:
        outer = []
        for i in range(9):
            a = math.pi * i / 8              # 0 = left gunwale ... pi = right gunwale
            x = -w * math.cos(a)
            depth = math.sin(a) ** 0.6
            z = lerp(sheer, keel, depth ** 1.0) if i not in (0, 8) else sheer
            outer.append(Vector((x * (0.85 + 0.15 * (1 - depth)), y, z)))
        th = 0.06
        inner = [Vector((p.x * max(0.0, (w - th)) / max(w, 1e-4), p.y, max(p.z, keel + th) if 0 < i < 8 else sheer))
                 for i, p in enumerate(outer)]
        ring = outer + list(reversed(inner))
        rings.append(ring)
    # outer goes left gunwale -> keel -> right gunwale; with increasing y this winds outward
    hull.loft(rings, closed_rings=True, cap0=True, cap1=True)
    hull.flip()
    # bow and stern posts
    wood = Part("M_Wood", smooth=45)
    for s, (y, w, sheer, keel) in ((-1, stations[0]), (1, stations[-1])):
        wood.tube([Vector((0, y + s * 0.02, keel + 0.02)), Vector((0, y + s * 0.12, sheer + 0.05)),
                   Vector((0, y + s * 0.1, sheer + 0.2))], [0.07, 0.06, 0.045], sides=6)
    # deck
    deck = Part("M_WoodLight", smooth=40)
    pts_l, pts_r = [], []
    for y, w, sheer, keel in stations[3:-3]:
        pts_r.append((w - 0.1, y))
        pts_l.append((-(w - 0.1), y))
    deck.extrude_poly(pts_r + list(reversed(pts_l)), 0.26, 0.3)
    for k in range(1, 7):
        y = -1.2 + 0.4 * k
        wood.box((-0.55, y - 0.012, 0.3), (0.55, y + 0.012, 0.31))
    # red stripe along each gunwale
    red = Part("M_Red", smooth=50)
    for s in (-1, 1):
        path = [Vector((s * w * 1.0, y, sheer - 0.07)) for y, w, sheer, keel in stations]
        red.tube(path, 0.035, sides=5, caps=True)
    # painted bow eyes (mắt thuyền)
    white = Part("M_White", smooth=None)
    black = Part("M_Black", smooth=None)
    y, w, sheer, keel = stations[4]
    for s in (-1, 1):
        n = Vector((s, -0.35, 0)).normalized()
        up = Vector((0, 0, 1))
        right = up.cross(n)
        m = Matrix((right, up, n)).transposed().to_4x4()
        m.translation = Vector((s * (w * 0.93), y, sheer - 0.2))
        eye = [(0.13 * math.cos(a), 0.065 * math.sin(a) * (1.0 if math.sin(a) > 0 else 0.8))
               for a in [TAU * i / 16 for i in range(16)]]
        white.extrude_poly(eye, -0.02, 0.015, m)
        black.extrude_poly([(0.045 * math.cos(a) - s * 0.0, 0.045 * math.sin(a)) for a in
                            [TAU * i / 10 for i in range(10)]], 0.0, 0.025, m)
    # woven bamboo canopy (mui): arched shell with ribs
    shell = Part("M_BambooDry", smooth=50)
    ribs = Part("M_Wood", smooth=45)
    RA, Z0 = 0.58, 0.46
    y0, y1 = -0.55, 0.75
    rings = []
    for k in range(9):
        y = lerp(y0, y1, k / 8)
        o = [Vector((RA * math.cos(a), y, Z0 + RA * math.sin(a) * 1.05)) for a in
             [math.pi * i / 10 for i in range(11)]]
        i_ = [Vector((0.94 * p.x, y, Z0 + (p.z - Z0) * 0.94)) for p in reversed(o)]
        rings.append(o + i_)
    shell.loft(rings, closed_rings=True, cap0=True, cap1=True)
    shell.flip()
    for k in range(7):
        y = lerp(y0 + 0.02, y1 - 0.02, k / 6)
        path = [Vector(((RA + 0.02) * math.cos(a), y, Z0 + (RA + 0.02) * math.sin(a) * 1.05)) for a in
                [math.pi * i / 10 for i in range(11)]]
        ribs.tube(path, 0.022, sides=5, caps=True)
    for a in (math.radians(40), math.radians(90), math.radians(140)):
        ribs.tube([Vector(((RA + 0.025) * math.cos(a), y0, Z0 + (RA + 0.025) * math.sin(a) * 1.05)),
                   Vector(((RA + 0.025) * math.cos(a), y1, Z0 + (RA + 0.025) * math.sin(a) * 1.05))],
                  0.018, sides=5)
    # a long oar lying on the deck beside the canopy
    wood.tube([Vector((0.3, -1.1, 0.34)), Vector((0.32, 0.9, 0.34))], 0.028, sides=6)
    wood.box((-0.08, -0.22, -0.018), (0.08, 0.0, 0.018), mat4((0.3, -1.1, 0.34)))
    parts = [hull, wood, deck, red, white, black, shell, ribs]
    zmin = min(v.co.z for p in parts for v in p.bm.verts)
    for p in parts:
        p.deform(lambda v: v - Vector((0, 0, zmin)))
    return [join_parts("sampan", parts, col)]


# --------------------------------------------------------------------------------------------
def lantern(col):
    """Hội An silk lantern: ribbed onion body, gold caps, red trim ribs and tassel, top hook.
    0.6 m tall, origin at the tassel tip."""
    silk = Part("M_Orange", smooth=55)
    prof = [(0.07, 0.14), (0.13, 0.18), (0.185, 0.24), (0.205, 0.3), (0.19, 0.36), (0.15, 0.41), (0.08, 0.45)]
    silk.lathe(prof, 32, shape=lambda th, k: 1.0 - 0.07 * (1 - abs(math.sin(4 * th))) ** 3, cap0=False,
               cap1=False, phase=math.pi / 8)
    ribs = Part("M_RedDark", smooth=45)
    for i in range(8):
        a = TAU * i / 8
        path = [Vector((r * 0.94 * math.cos(a), r * 0.94 * math.sin(a), z)) for r, z in prof]
        ribs.tube(path, 0.009, sides=4, caps=True)
    gold = Part("M_Gold", smooth=45)
    gold.lathe([(0.0, 0.1), (0.07, 0.1), (0.09, 0.12), (0.085, 0.145), (0.0, 0.15)], 16)
    gold.lathe([(0.0, 0.44), (0.09, 0.44), (0.1, 0.455), (0.075, 0.49), (0.03, 0.5), (0.0, 0.5)], 16)
    hook = [Vector((0.035 * math.cos(a), 0.0, 0.555 + 0.035 * math.sin(a))) for a in
            [math.radians(-90 + 360 * i / 10) for i in range(11)]]
    gold.tube(hook, 0.01, sides=5, caps=False)
    gold.cylinder(0.012, 0.03, 6, mat4((0, 0, 0.495)))
    red = Part("M_Red", smooth=45)
    red.cylinder(0.015, 0.03, 6, mat4((0, 0, 0.07)))
    red.lathe([(0.0, 0.0), (0.04, 0.0), (0.035, 0.03), (0.02, 0.06), (0.0, 0.075)], 10,
              shape=lambda th, k: 1.0 + 0.15 * math.cos(6 * th))
    return [join_parts("lantern", [silk, ribs, gold, red], col)]


# --------------------------------------------------------------------------------------------
def _bamboo_pole(part, a, b, r, nodes=3, segs=8):
    a, b = Vector(a), Vector(b)
    L = (b - a).length
    m = Matrix.Translation(a) @ Vector((0, 0, 1)).rotation_difference(b - a).to_matrix().to_4x4()
    prof = [(0.0, 0.0), (r * 0.9, 0.0), (r, 0.02)]
    for k in range(1, nodes + 1):
        z = L * k / (nodes + 1)
        prof += [(r, z - 0.02), (r * 1.12, z), (r, z + 0.02)]
    prof += [(r, L - 0.02), (r * 0.9, L), (0.0, L)]
    part.lathe(prof, segs, m)


def fence_bamboo(col):
    """2 m bamboo railing segment along X: two posts (left end + middle) so segments tile,
    two rails lashed with string."""
    posts = Part("M_Bamboo", smooth=50)
    rails = Part("M_BambooLight", smooth=50)
    ties = Part("M_String", smooth=50)
    cap = Part("M_BambooDark", smooth=45)
    for x in (-0.95, 0.05):
        _bamboo_pole(posts, (x, 0, 0), (x, 0, 0.84), 0.06, nodes=2)
        cap.lathe([(0.0, 0.84), (0.062, 0.84), (0.066, 0.86), (0.0, 0.86)], 8)
    for z in (0.36, 0.68):
        _bamboo_pole(rails, (-1.0, -0.075, z), (1.0, -0.075, z), 0.042, nodes=2, segs=7)
        for x in (-0.95, 0.05):
            ring = [Vector((x + 0.075 * math.cos(a), -0.035 + 0.06 * math.sin(a), z)) for a in
                    [TAU * i / 8 for i in range(8)]]
            ties.tube(ring, 0.014, sides=4, closed=True)
            ties.tube([Vector((x + 0.07, -0.02, z - 0.07)), Vector((x - 0.07, -0.08, z + 0.07))], 0.012,
                      sides=4)
    return [join_parts("fence_bamboo", [posts, rails, ties, cap], col)]


def bridge_plank(col):
    """One segment of a plank bridge: 1.0 m wide (X) x 1.0 m long (Y, the walking direction),
    three planks on two stringers with rope lashings. Segments tile along Y."""
    r = rng(9)
    beams = Part("M_WoodDark", smooth=40, bevel=(0.015, 1))
    for x in (-0.36, 0.36):
        beams.box((x - 0.06, -0.5, 0.0), (x + 0.06, 0.5, 0.11))
    planks_a = Part("M_Wood", smooth=45, bevel=(0.02, 2))
    planks_b = Part("M_WoodLight", smooth=45, bevel=(0.02, 2))
    ropes = Part("M_String", smooth=50)
    for k in range(3):
        y = -0.5 + 0.1667 + k * 0.3333
        half = r(0.47, 0.5)
        xoff = r(-0.015, 0.015)
        m = Matrix.Translation((xoff, y, 0)) @ Matrix.Rotation(math.radians(r(-2.0, 2.0)), 4, "Z")
        (planks_a if k % 2 == 0 else planks_b).box((-half, -0.15, 0.11), (half, 0.15, 0.19), m)
        for x in (-0.36, 0.36):
            # a lashing wrapped round stringer + plank: flat strap over the plank top
            loop = rounded_rect_points(0.16, 0.2, 0.035, seg=2)
            ring = [Vector((x + px, y, 0.1 + pz)) for px, pz in loop]
            ropes.tube(ring, 0.015, sides=5, closed=True, up=(0, 1, 0))
    return [join_parts("bridge_plank", [beams, planks_a, planks_b, ropes], col)]


# --------------------------------------------------------------------------------------------
def cong_lang(col):
    """Cổng làng (village gate): lime-washed arch wall between two square pillars, small tiled
    hip roof with curled corners, red signboard with a gold drum star. ~4.4 x 1.2 x 4.7 m."""
    wall = Part("M_Mortar", smooth=35, bevel=(0.03, 2))
    trim = Part("M_StoneLight", smooth=35, bevel=(0.025, 2))
    # arch wall: U-shaped polygon extruded along Y (local y -> world z)
    rx, spring = 1.05, 2.25
    arch = [(-1.55, 0.0), (-rx, 0.0), (-rx, spring)]
    for i in range(1, 12):
        a = math.pi - math.pi * i / 12
        arch.append((rx * math.cos(a), spring + rx * 0.8 * math.sin(a)))
    arch += [(rx, spring), (rx, 0.0), (1.55, 0.0), (1.55, 3.5), (-1.55, 3.5)]
    M = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))  # (x, y, z) -> (x, -z, y)
    wall.extrude_poly(arch, -0.3, 0.3, M)
    # pillars with plinths, caps and lotus-bud finials
    for s in (-1, 1):
        x = s * 1.85
        trim.box((x - 0.4, -0.45, 0.0), (x + 0.4, 0.45, 0.35))
        wall.box((x - 0.32, -0.37, 0.35), (x + 0.32, 0.37, 3.7))
        trim.box((x - 0.4, -0.45, 3.7), (x + 0.4, 0.45, 3.86))
    bud = Part("M_Stone", smooth=50)
    for s in (-1, 1):
        bud.lathe([(0.0, 3.86), (0.2, 3.86), (0.22, 3.95), (0.16, 4.1), (0.19, 4.2), (0.14, 4.38), (0.05, 4.52),
                   (0.0, 4.58)], 12, Matrix.Translation((s * 1.85, 0, 0)))
    # arch rim moulding
    rim_path = [Vector((x, -0.31, y)) for x, y in arch[2:15]]
    trim.tube(rim_path, 0.06, sides=6, caps=True)
    # roof over the arch
    tiles = Part("M_Roof", smooth=35)
    ridge = Part("M_RoofDark", smooth=45)
    curl = Part("M_RoofDark", smooth=45)
    hip_roof(tiles, ridge, curl, z_eave=3.48, ax=1.75, ay=0.72, rx=1.1, rise=0.55, n=10, lift=0.28,
             flare=0.12)
    # signboard
    board = Part("M_Red", smooth=40, bevel=(0.02, 2))
    board.box((-0.75, -0.38, 2.7), (0.75, -0.3, 3.2))
    frame = Part("M_Gold", smooth=45)
    for (a, b) in (((-0.8, -0.4, 2.66), (0.8, -0.35, 2.7)), ((-0.8, -0.4, 3.2), (0.8, -0.35, 3.24)),
                   ((-0.8, -0.4, 2.66), (-0.75, -0.35, 3.24)), ((0.75, -0.4, 2.66), (0.8, -0.35, 3.24))):
        frame.box(a, b)
    m = Matrix(((1, 0, 0, 0), (0, 0, -1, -0.38), (0, 1, 0, 2.95), (0, 0, 0, 1)))
    frame.faceted_star(12, 0.19, 0.07, 0.035, 0.01, m, back=False)
    return [join_parts("cong_lang", [wall, trim, bud, tiles, ridge, curl, board, frame], col)]
