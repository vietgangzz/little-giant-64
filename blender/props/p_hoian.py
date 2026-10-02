"""Đà Nẵng – Hội An level, the Hội An half: chua_cau (Japanese Covered Bridge), hoian_house,
hoian_house_small, hoa_dang (floating flower lantern), basket_boat (thúng chai), nipa_palm,
lantern_boat and silk_lantern_string. Shared helpers (Kit, gable_roof, silk_lantern) are used by
p_danang too.

Blender axes: front = -Y (Godot +Z), up = +Z. Reported heights are the module constants below.
"""

import math

import bmesh
from mathutils import Matrix, Vector

from lib import TAU, Part, ellipse_points, join_parts, lerp, look_matrix, mat4, rng

CHUA_CAU_DECK_END = 1.0      # deck top where the steps arrive (|y| = 4.5)
CHUA_CAU_DECK_MID = 1.6      # deck top at the middle of the arch
CHUA_CAU_EAVE = 3.8
CHUA_CAU_RIDGE = 5.6
HOUSE_EAVE, HOUSE_RIDGE = 4.2, 5.6
SMALL_EAVE, SMALL_RIDGE = 2.6, 3.8
BASKET_RIM, BASKET_FLOOR = 0.70, 0.25
LANTERN_BOAT_DECK = 0.55


# --------------------------------------------------------------------------------------------
# shared helpers
# --------------------------------------------------------------------------------------------
class Kit:
    """One Part per material, created on first use. finish() fixes normals and joins them."""

    def __init__(self):
        self.parts = {}

    def __call__(self, mat, smooth=40.0, bevel=None):
        if mat not in self.parts:
            self.parts[mat] = Part(mat, smooth=smooth, bevel=bevel, name=mat)
        return self.parts[mat]

    def finish(self, name, col):
        for p in self.parts.values():
            if p.bm.faces:
                bmesh.ops.recalc_face_normals(p.bm, faces=p.bm.faces[:])
        return join_parts(name, list(self.parts.values()), col)


def gable_roof(kit, x0, x1, w, z_eave, z_ridge, m=Matrix(), thick=0.14, pitch=0.34, sag=0.1, amp=0.05,
               tile="M_TileRoof", dark="M_TileRoofDark", caps=True, curls=False, sides=(-1, 1), nv=5,
               ridge_r=0.1):
    """Yin-yang tiled gable roof in roof space (ridge along local X from x0 to x1 at local y = 0,
    slopes falling to local y = ±w), then placed by `m`. The tile surface is exactly z_ridge at
    the ridge and z_eave at the eave (the raised tile rows add `amp`). Closed slabs."""
    tiles = kit(tile, smooth=50)
    trim = kit(dark, smooth=45)
    nu = max(2, int(round((x1 - x0) / (pitch / 2))))
    nu += nu % 2
    rise = z_ridge - z_eave

    for s in sides:
        def P(i, j, under, s=s):
            t = j / nv
            x = lerp(x0, x1, i / nu)
            z = z_ridge - rise * t - sag * math.sin(math.pi * t)
            if not under and i % 2 == 1:
                z += amp
            if under:
                z -= thick
            return m @ Vector((x, s * (0.003 + w * t), z))

        top = [[tiles._v(P(i, j, False)) for j in range(nv + 1)] for i in range(nu + 1)]
        bot = [[tiles._v(P(i, j, True)) for j in range(nv + 1)] for i in range(nu + 1)]
        for i in range(nu):
            for j in range(nv):
                tiles.face([top[i][j], top[i + 1][j], top[i + 1][j + 1], top[i][j + 1]])
                tiles.face([bot[i][j], bot[i][j + 1], bot[i + 1][j + 1], bot[i + 1][j]])
        border = [(i, 0) for i in range(nu)] + [(nu, j) for j in range(nv)] + \
                 [(i, nv) for i in range(nu, 0, -1)] + [(0, j) for j in range(nv, 0, -1)]
        for k in range(len(border)):
            i0, j0 = border[k]
            i1, j1 = border[(k + 1) % len(border)]
            tiles.face([top[i0][j0], bot[i0][j0], bot[i1][j1], top[i1][j1]])
        # bargeboards up the gable edges
        for i in (0, nu):
            trim.tube([P(i, j, False) + (m.to_3x3() @ Vector((0, 0, 0.04))) for j in range(nv + 1)], 0.06,
                      sides=5, caps=True)
        # round end caps on the raised tile rows along the eave
        if caps:
            for i in range(1, nu, 2):
                e = P(i, nv, False)
                d = (e - P(i, nv - 1, False)).normalized()
                trim.cylinder(0.07, 0.05, 6, look_matrix(e - d * 0.03 - (m.to_3x3() @ Vector((0, 0, 0.02))), d))
    a = m @ Vector((x0 - 0.06, 0, z_ridge + 0.04))
    b = m @ Vector((x1 + 0.06, 0, z_ridge + 0.04))
    trim.tube([a, b], ridge_r, sides=8, caps=True)
    if curls:
        up = m.to_3x3() @ Vector((0, 0, 1))
        for end, sgn in ((a, -1), (b, 1)):
            d = (m.to_3x3() @ Vector((sgn, 0, 0))).normalized()
            pts = [end + d * (0.32 * math.sin(t)) + up * (0.32 * (1 - math.cos(t))) for t in
                   [k * 0.38 for k in range(9)]]
            trim.tube(pts, [ridge_r * (1 - 0.6 * k / 8) for k in range(9)], sides=6, caps=True)
            trim.sphere(ridge_r * 0.55, mat4(tuple(pts[-1])), segs=6, rings=4)


def roof_under(y, w, z_eave, z_ridge, sag=0.1, thick=0.14):
    """Underside height of a gable_roof slope at horizontal distance |y| from the ridge."""
    t = min(1.0, abs(y) / w)
    return z_ridge - (z_ridge - z_eave) * t - sag * math.sin(math.pi * t) - thick


def gable_wall(part, x, w, z0, z_eave, z_ridge, m=Matrix(), thickness=0.12, n=8):
    """Triangular gable-end wall at local x (between local y = ±w, from z0 up to just under the
    roof), extruded along X."""
    pts = [(-w, z0), (w, z0)]
    for k in range(n + 1):
        y = w - 2 * w * k / n
        pts.append((y, max(z0 + 0.01, roof_under(y, w + 0.4, z_eave, z_ridge) - 0.02)))
    # local XY -> world YZ, local Z -> world X
    mm = m @ Matrix(((0, 0, 1, x - thickness / 2), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    part.extrude_poly(pts, 0.0, thickness, mm)


def silk_lantern(kit, top, s=1.0, mat="M_SilkRed", segs=12, trim_mat="M_Gold"):
    """A Hội An silk lantern hanging from the hook point `top`; s = 1 is 0.56 m long."""
    m = Matrix.Translation(Vector(top) - Vector((0, 0, 0.56 * s))) @ Matrix.Scale(s, 4)
    prof = [(0.07, 0.14), (0.13, 0.18), (0.185, 0.24), (0.205, 0.3), (0.19, 0.36), (0.15, 0.41), (0.08, 0.45)]
    kit(mat, smooth=55).lathe(prof, segs, m, shape=lambda th, k: 1.0 - 0.08 * (1 - abs(math.cos(segs / 4 * th))) ** 2)
    g = kit(trim_mat, smooth=45)
    g.lathe([(0.0, 0.1), (0.07, 0.1), (0.09, 0.12), (0.085, 0.145), (0.0, 0.15)], 8, m)
    g.lathe([(0.0, 0.44), (0.09, 0.44), (0.1, 0.455), (0.075, 0.49), (0.03, 0.5), (0.0, 0.5)], 8, m)
    g.cylinder(0.012, 0.07, 5, m @ Matrix.Translation((0, 0, 0.495)))
    t = kit("M_RedDark", smooth=45)
    t.cylinder(0.015, 0.04, 5, m @ Matrix.Translation((0, 0, 0.065)))
    t.lathe([(0.0, 0.0), (0.04, 0.0), (0.035, 0.03), (0.02, 0.065), (0.0, 0.075)], 6, m)


def _patch(part, centre, normal, rx, ry, seed, thick=0.015):
    """A flat irregular blotch stuck onto a wall (weathering, moss)."""
    r = rng(seed)
    pts = [(rx * (0.75 + 0.25 * r()) * math.cos(a), ry * (0.75 + 0.25 * r()) * math.sin(a)) for a in
           [TAU * i / 10 for i in range(10)]]
    part.extrude_poly(pts, -0.01, thick, look_matrix(centre, normal))


def _shutter_window(kit, c, normal, w=0.8, h=0.8, open_=True):
    """Window on a wall face: dark recess, frame, and two teal shutters folded open."""
    n = Vector(normal).normalized()
    up = Vector((0, 0, 1))
    side = up.cross(n).normalized()       # right as seen from outside
    c = Vector(c)
    fr = kit("M_WoodDark", smooth=40)
    sh = kit("M_Shutter", smooth=40)

    def slab(part, centre, half_side, half_up, depth0, depth1):
        corners = []
        for a, b, d in ((-1, -1, depth0), (1, -1, depth0), (1, 1, depth0), (-1, 1, depth0),
                        (-1, -1, depth1), (1, -1, depth1), (1, 1, depth1), (-1, 1, depth1)):
            corners.append(centre + side * a * half_side + up * b * half_up + n * d)
        v = [part._v(p) for p in corners]
        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            part.face([v[i] for i in f])

    slab(fr, c, w / 2 + 0.07, h / 2 + 0.07, -0.02, 0.04)
    slab(kit("M_Black", smooth=40), c, w / 2, h / 2, -0.02, 0.05)
    # mullion
    slab(fr, c, 0.03, h / 2, 0.0, 0.07)
    if open_:
        for sgn in (-1, 1):
            slab(sh, c + side * sgn * (w / 2 + 0.07 + w / 4), w / 4, h / 2 + 0.02, 0.04, 0.08)
    else:
        slab(sh, c, w / 2, h / 2, 0.04, 0.08)


# --------------------------------------------------------------------------------------------
def chua_cau(col):
    """Chùa Cầu, Hội An's Japanese Covered Bridge: an arched plank deck between stone abutments
    with steps at both ends, dark wooden pillars, red lacquered beams, a yin-yang tiled gable roof
    (ridge along Y) with curled ridge ends, and the little temple room on the +X side."""
    k = Kit()
    L2 = 4.5

    def deck_z(y):
        return CHUA_CAU_DECK_MID - (CHUA_CAU_DECK_MID - CHUA_CAU_DECK_END) * (y / L2) ** 2

    # plank deck: strips across the bridge, alternating tones
    W = 1.6
    n = 18
    for i in range(n):
        y0, y1 = -L2 + 2 * L2 * i / n, -L2 + 2 * L2 * (i + 1) / n
        part = k("M_WoodLight" if i % 2 else "M_Wood", smooth=30)
        rings = []
        for y in (y0 + 0.01, y1 - 0.01):
            z = deck_z(y)
            rings.append([Vector((-W, y, z - 0.28)), Vector((W, y, z - 0.28)), Vector((W, y, z)), Vector((-W, y, z))])
        part.loft(rings, closed_rings=True, cap0=True, cap1=True)
    # fascia boards along both sides of the deck (red lacquer)
    red = k("M_Red", smooth=40)
    for sx in (-1, 1):
        rings = []
        for i in range(n + 1):
            y = -L2 + 2 * L2 * i / n
            z = deck_z(y)
            rings.append([Vector((sx * W - 0.06, y, z - 0.32)), Vector((sx * W + 0.06, y, z - 0.32)),
                          Vector((sx * W + 0.06, y, z + 0.02)), Vector((sx * W - 0.06, y, z + 0.02))])
        red.loft(rings, closed_rings=True, cap0=True, cap1=True)
    # stone abutments, a middle pier and the steps
    stone = k("M_StoneLight", smooth=30)
    for e in (-1, 1):
        y_in, y_out = e * 3.7, e * 4.6
        stone.box((-1.85, min(y_in, y_out), 0.0), (1.85, max(y_in, y_out), deck_z(4.15) - 0.27))
        for s, h in enumerate((0.75, 0.5, 0.25)):
            ya, yb = e * (4.5 + 0.5 * s), e * (5.0 + 0.5 * s)
            stone.box((-1.4, min(ya, yb), 0.0), (1.4, max(ya, yb), h))
    for y in (-1.6, 1.6):
        stone.box((-1.7, y - 0.35, 0.0), (1.7, y + 0.35, deck_z(y) - 0.27))
    # pillars on stone drums, red beams, balustrade
    pil = k("M_RoofDark", smooth=40)
    drum = k("M_Stone", smooth=40)
    beam_z = 3.45
    ys = [-4.4, -2.95, -1.5, 0.0, 1.5, 2.95, 4.4]
    for sx in (-1, 1):
        for y in ys:
            z = deck_z(y)
            drum.lathe([(0.0, z - 0.02), (0.17, z - 0.02), (0.15, z + 0.16), (0.0, z + 0.16)], 6,
                       Matrix.Translation((sx * 1.55, y, 0)))
            pil.cylinder(0.11, beam_z - z, 10, mat4((sx * 1.55, y, z)))
        red.box((sx * 1.55 - 0.1, -4.75, beam_z), (sx * 1.55 + 0.1, 4.75, beam_z + 0.2))
        # balustrade: rail following the arch with short balusters
        rail = k("M_RedDark", smooth=40)
        path = [Vector((sx * 1.52, y, deck_z(y) + 0.72)) for y in [-4.4 + 8.8 * i / 16 for i in range(17)]]
        rail.tube(path, 0.045, sides=6, caps=True)
        path = [Vector((sx * 1.52, y, deck_z(y) + 0.32)) for y in [-4.4 + 8.8 * i / 16 for i in range(17)]]
        rail.tube(path, 0.03, sides=5, caps=True)
        for i in range(30):
            y = -4.3 + 8.6 * (i + 0.5) / 30
            if min(abs(y - yy) for yy in ys) < 0.15:
                continue
            z = deck_z(y)
            rail.box((sx * 1.52 - 0.025, y - 0.025, z), (sx * 1.52 + 0.025, y + 0.025, z + 0.72))
    for y in ys:
        red.box((-1.7, y - 0.08, beam_z), (1.7, y + 0.08, beam_z + 0.16))
    # main roof: ridge along Y (roof space X -> world Y)
    rz = Matrix.Rotation(math.radians(90), 4, "Z")
    gable_roof(k, -6.35, 6.35, 2.35, CHUA_CAU_EAVE, CHUA_CAU_RIDGE, rz, curls=True, ridge_r=0.12, pitch=0.5, nv=4)
    # gable boards at both ends above the beam, with a red name plaque
    wood = k("M_WoodDark", smooth=40)
    for e in (-1, 1):
        pts = [(-1.7, beam_z + 0.2), (1.7, beam_z + 0.2)]
        for i in range(9):
            x = 1.7 - 3.4 * i / 8
            pts.append((x, max(beam_z + 0.21, roof_under(x, 2.35, CHUA_CAU_EAVE, CHUA_CAU_RIDGE) - 0.03)))
        # local XY -> world XZ, local Z -> world -Y
        mm = Matrix(((1, 0, 0, 0), (0, 0, -1, e * 4.6), (0, 1, 0, 0), (0, 0, 0, 1)))
        wood.extrude_poly(pts, -0.06, 0.06, mm)
        red.box((-0.6, e * 4.6 - 0.1 if e < 0 else e * 4.6 - 0.02, beam_z + 0.35),
                (0.6, e * 4.6 + 0.02 if e < 0 else e * 4.6 + 0.1, beam_z + 0.8))
        k("M_Gold", smooth=40).box((-0.5, e * 4.6 - 0.13 if e < 0 else e * 4.6 + 0.08, beam_z + 0.42),
                                   (0.5, e * 4.6 - 0.09 if e < 0 else e * 4.6 + 0.12, beam_z + 0.46))
    # ridge ornament: a small gold disc on the middle of the ridge
    k("M_Gold", smooth=50).lathe([(0.0, -0.04), (0.28, -0.04), (0.3, 0.0), (0.28, 0.04), (0.0, 0.04)], 16,
                                 Matrix.Translation((0, 0, CHUA_CAU_RIDGE + 0.42)) @ Matrix.Rotation(math.radians(90), 4, "Y"))
    k("M_TileRoofDark").box((-0.12, -0.12, CHUA_CAU_RIDGE + 0.1), (0.12, 0.12, CHUA_CAU_RIDGE + 0.16))
    # the temple room on +X
    stone.box((1.7, -1.4, 0.0), (3.75, 1.4, 1.45))
    room = k("M_WoodDark", smooth=40)
    room.box((1.75, -1.3, 1.45), (3.7, 1.3, 3.25))
    red.box((3.7, -0.55, 1.5), (3.76, 0.55, 2.9))                          # doors
    k("M_Gold", smooth=40).box((3.74, -0.04, 1.55), (3.78, 0.04, 2.85))
    for y in (-1.3, 1.3):
        red.box((3.62, y - 0.1, 1.45), (3.82, y + 0.1, 3.25))            # corner posts
    for y in (-1, 1):
        _shutter_window(k, (2.75, y * 1.31, 2.4), (0, y, 0), w=0.7, h=0.6, open_=False)
    gable_roof(k, 1.55, 4.1, 1.75, 3.1, 4.25, curls=True, ridge_r=0.09, pitch=0.45, nv=3)
    gable_wall(room, 3.68, 1.3, 3.25, 3.1, 4.25, thickness=0.1)
    # guardian statues at the entrances (monkeys one end, dogs the other)
    st = k("M_Stone", smooth=60)
    for e in (-1, 1):
        for sx in (-1, 1):
            base = Vector((sx * 1.65, e * 5.6, 0))
            stone.box((base.x - 0.25, base.y - 0.25, 0.0), (base.x + 0.25, base.y + 0.25, 0.75))
            st.sphere(0.2, mat4(tuple(base + Vector((0, 0, 0.95)))), segs=10, rings=6, scale=(1, 0.9, 1.15))
            st.sphere(0.14, mat4(tuple(base + Vector((0, -e * 0.05, 1.27)))), segs=10, rings=6)
            for ex in (-1, 1):
                st.sphere(0.06, mat4(tuple(base + Vector((ex * 0.11, -e * 0.03, 1.38 if e < 0 else 1.33)))),
                          segs=6, rings=4, scale=(1, 0.6, 1.3 if e > 0 else 1.0))
    return [k.finish("chua_cau", col)]


# --------------------------------------------------------------------------------------------
def _house_common(k, W, D, eave, ridge, front_h, seed):
    """Ochre walls on a stone plinth, roof, gable walls and weathering. Returns (walls, wood)."""
    walls = k("M_Ochre", smooth=30)
    k("M_Concrete", smooth=30).box((-W / 2 - 0.05, -D / 2 - 0.05, 0.0), (W / 2 + 0.05, D / 2 + 0.05, 0.2))
    walls.box((-W / 2, -D / 2, 0.2), (W / 2, D / 2, eave))
    overhang = 0.4
    gable_roof(k, -W / 2 - 0.25, W / 2 + 0.25, D / 2 + overhang, eave, ridge)
    for sx in (-1, 1):
        gable_wall(walls, sx * (W / 2 - 0.06), D / 2, eave - 0.01, eave, ridge, thickness=0.12)
    # weathered patches on the walls
    r = rng(seed)
    dark = k("M_OchreDark", smooth=None)
    for i in range(7):
        side = i % 3
        if side == 0:
            c, nrm = Vector((W / 2 + 0.005, r(-D / 2 + 0.6, D / 2 - 0.6), r(0.5, eave - 0.6))), (1, 0, 0)
        elif side == 1:
            c, nrm = Vector((-W / 2 - 0.005, r(-D / 2 + 0.6, D / 2 - 0.6), r(0.5, eave - 0.6))), (-1, 0, 0)
        else:
            c, nrm = Vector((r(-W / 2 + 0.5, W / 2 - 0.5), D / 2 + 0.005, r(0.5, eave - 0.6))), (0, 1, 0)
        _patch(dark, c, nrm, r(0.25, 0.5), r(0.15, 0.35), seed * 10 + i)
    # moss line along the plinth
    _patch(k("M_Moss", smooth=None), Vector((W / 2 * 0.3, -D / 2 - 0.006, 0.32)), (0, -1, 0), 0.45, 0.1, seed + 3)
    return walls


def hoian_house(col):
    """Two-storey Hội An shophouse: ochre walls, a dark wooden shopfront with folding doors, a
    tiled awning over the shop, a wooden balcony rail and teal shutters upstairs, the main yin-yang
    tiled gable roof (ridge along X) and two red silk lanterns at the door. Front -Y."""
    k = Kit()
    W, D = 5.0, 6.0
    _house_common(k, W, D, HOUSE_EAVE, HOUSE_RIDGE, 2.5, 4)
    wood = k("M_WoodDark", smooth=40)
    light = k("M_Wood", smooth=40)
    # shopfront: dark frame, six folding door panels
    wood.box((-2.3, -3.06, 0.2), (2.3, -2.98, 2.55))
    for i in range(6):
        x0 = -2.1 + 0.7 * i
        light.box((x0 + 0.03, -3.11, 0.3), (x0 + 0.67, -3.04, 2.3))
        wood.box((x0 + 0.12, -3.14, 1.2), (x0 + 0.58, -3.09, 2.15))     # upper lattice panel
    wood.box((-2.3, -3.12, 2.3), (2.3, -3.02, 2.45))                     # lintel
    # awning over the shop (one slope down to the street) on two posts
    gable_roof(k, -2.65, 2.65, 0.95, 2.55, 3.0, Matrix.Translation((0, -3.0, 0)), sides=(-1,), thick=0.1,
               sag=0.04, nv=3)
    for sx in (-1, 1):
        wood.cylinder(0.08, 2.5, 8, mat4((sx * 2.35, -3.75, 0.2)))
        k("M_Stone", smooth=40).cylinder(0.13, 0.18, 8, mat4((sx * 2.35, -3.75, 0.0)))
    # upstairs: balcony rail and shuttered windows
    for x in (-1.25, 1.25):
        _shutter_window(k, (x, -3.0, 3.55), (0, -1, 0), w=0.7, h=0.62)
    wood.box((-2.35, -3.32, 3.02), (2.35, -3.0, 3.08))                   # balcony floor edge
    wood.tube([Vector((-2.35, -3.28, 3.45)), Vector((2.35, -3.28, 3.45))], 0.04, sides=6)
    for i in range(17):
        x = -2.3 + 4.6 * i / 16
        wood.box((x - 0.025, -3.3, 3.06), (x + 0.025, -3.26, 3.45))
    # side and back windows
    for y in (-1.2, 1.4):
        _shutter_window(k, (2.5, y, 1.6), (1, 0, 0), w=0.65, h=0.75)
        _shutter_window(k, (-2.5, y, 1.6), (-1, 0, 0), w=0.65, h=0.75, open_=False)
    _shutter_window(k, (0.0, 3.0, 3.4), (0, 1, 0), w=0.7, h=0.6, open_=False)
    # lanterns at the door, hanging from the awning
    for x, mat in ((-1.45, "M_SilkRed"), (1.45, "M_SilkRed")):
        k("M_Black", smooth=40).cylinder(0.01, 0.12, 4, mat4((x, -3.6, 2.42)))
        silk_lantern(k, (x, -3.6, 2.44), 0.8, mat)
    # a name board over the door
    k("M_Black", smooth=40).box((-0.9, -3.17, 2.47), (0.9, -3.1, 2.75))
    k("M_Gold", smooth=40).box((-0.8, -3.19, 2.55), (0.8, -3.16, 2.67))
    return [k.finish("hoian_house", col)]


def hoian_house_small(col):
    """Single-storey Hội An house: weathered ochre walls, a wooden front with a door and shutters,
    tiled gable roof (ridge along X), a lantern and a potted plant. Front -Y."""
    k = Kit()
    W, D = 4.0, 5.0
    _house_common(k, W, D, SMALL_EAVE, SMALL_RIDGE, 2.2, 9)
    wood = k("M_WoodDark", smooth=40)
    light = k("M_Wood", smooth=40)
    wood.box((-1.85, -2.56, 0.2), (1.85, -2.48, 2.45))
    light.box((-0.55, -2.62, 0.2), (0.55, -2.54, 2.15))                 # door
    wood.box((-0.03, -2.65, 0.25), (0.03, -2.6, 2.1))
    for x in (-1.25, 1.25):
        _shutter_window(k, (x, -2.52, 1.45), (0, -1, 0), w=0.55, h=0.7)
    for y in (-0.8, 0.9):
        _shutter_window(k, (2.0, y, 1.4), (1, 0, 0), w=0.6, h=0.7)
        _shutter_window(k, (-2.0, y, 1.4), (-1, 0, 0), w=0.6, h=0.7, open_=False)
    k("M_Black", smooth=40).cylinder(0.01, 0.14, 4, mat4((0.9, -2.85, 2.25)))
    k("M_Black", smooth=40).box((0.87, -2.9, 2.36), (0.93, -2.5, 2.4))
    silk_lantern(k, (0.9, -2.85, 2.27), 0.7, "M_SilkYellow")
    # potted plant by the door
    k("M_Terracotta", smooth=45).lathe([(0.0, 0.0), (0.2, 0.0), (0.26, 0.38), (0.22, 0.42), (0.0, 0.42)], 12,
                                      Matrix.Translation((-0.95, -2.95, 0.0)))
    leaf = k("M_LeafDark", smooth=55)
    for i in range(7):
        a = TAU * i / 7
        leaf.leaf(Vector((-0.95, -2.95, 0.4)), Vector((math.cos(a), math.sin(a), 1.4)), 0.55, 0.2,
                  droop=0.5, fold=0.2, steps=5)
    return [k.finish("hoian_house_small", col)]


# --------------------------------------------------------------------------------------------
def hoa_dang(col):
    """Hoa đăng: a paper lotus lantern that floats on the river, three rings of petals around a
    candle with a glowing flame. Origin at the base (the waterline)."""
    k = Kit()
    k("M_Paper", smooth=30).extrude_poly([(0.17 * math.cos(a), 0.17 * math.sin(a)) for a in
                                         [TAU * i / 4 + TAU / 8 for i in range(4)]], 0.0, 0.05)
    green = k("M_Leaf", smooth=50)
    for i in range(4):
        a = TAU * i / 4
        green.leaf(Vector((0.1 * math.cos(a), 0.1 * math.sin(a), 0.03)), Vector((math.cos(a), math.sin(a), 0.15)),
                   0.22, 0.17, droop=0.05, fold=-0.25, steps=4, thick=0.008)
    rings = (("M_PaperRed", 8, 0.08, 0.6, 0.27, 0.15, 0.0),
             ("M_PaperPink", 8, 0.06, 1.3, 0.27, 0.13, 0.5),
             ("M_PaperYellow", 6, 0.035, 2.6, 0.22, 0.1, 0.0))
    for mat, n, r0, lift, length, width, ph in rings:
        part = k(mat, smooth=50)
        for i in range(n):
            a = TAU * (i + ph) / n
            d = Vector((math.cos(a), math.sin(a), lift))
            part.leaf(Vector((r0 * math.cos(a), r0 * math.sin(a), 0.05)), d, length, width,
                      droop=-0.25, fold=-0.35, steps=5, thick=0.008)
    k("M_White", smooth=50).cylinder(0.035, 0.13, 10, mat4((0, 0, 0.05)))
    k("M_Flame", smooth=60).lathe([(0.0, 0.18), (0.03, 0.2), (0.032, 0.23), (0.018, 0.27), (0.0, 0.31)], 8)
    return [k.finish("hoa_dang", col)]


# --------------------------------------------------------------------------------------------
def basket_boat(col):
    """Thúng chai: a round woven bamboo boat, tarred below, basket weave up the side, a thick
    bamboo rim and a paddle on the floor. Rim top 0.70, walkable floor 0.25."""
    k = Kit()
    # a thin tarred outer shell, lined inside with weave (the floor top is the walkable 0.25)
    k("M_Tar", smooth=50).lathe([(0.0, 0.0), (0.55, 0.01), (0.9, 0.12), (1.05, 0.3), (1.085, 0.4), (1.06, 0.4),
                                 (1.025, 0.3), (0.88, 0.14), (0.55, 0.04), (0.0, 0.03)], 48)
    k("M_Woven", smooth=40).lathe([(0.0, 0.04), (0.55, 0.05), (0.88, 0.15), (1.02, 0.3), (1.055, 0.4), (1.02, 0.4),
                                   (0.97, 0.32), (0.86, BASKET_FLOOR), (0.0, BASKET_FLOOR)], 48)
    wall = [(1.02, 0.4), (1.085, 0.4), (1.09, 0.45), (1.095, 0.5), (1.1, 0.55), (1.1, 0.6), (1.1, 0.65),
            (1.03, 0.65), (1.02, 0.5)]
    cells = 32

    def weave(th, kk):
        if 1 <= kk <= 6:
            return 1.0 + 0.012 * ((int(th / (TAU / cells)) + kk) % 2)
        return 1.0

    k("M_Woven", smooth=40).lathe(wall, 96, shape=weave, closed=True)
    dark = k("M_WovenDark", smooth=50)
    for r in (0.3, 0.55, 0.76):
        dark.lathe([(r - 0.02, BASKET_FLOOR - 0.01), (r + 0.02, BASKET_FLOOR - 0.01), (r + 0.02, BASKET_FLOOR + 0.012),
                    (r - 0.02, BASKET_FLOOR + 0.012)], 40, closed=True)
    for i in range(8):                                                   # ribs up the inside
        a = TAU * i / 8
        path = [Vector((r * math.cos(a), r * math.sin(a), z)) for r, z in ((0.86, 0.26), (0.97, 0.33), (1.01, 0.45), (1.02, 0.62))]
        dark.tube(path, 0.022, sides=5, caps=True)
    rim_z = BASKET_RIM - 0.05
    k("M_BambooDry", smooth=50).lathe([(1.03, rim_z - 0.05), (1.08, rim_z - 0.05), (1.13, rim_z), (1.08, rim_z + 0.05),
                                       (1.03, rim_z + 0.05), (1.0, rim_z)], 48, closed=True)
    lash = k("M_WovenDark", smooth=40)
    for i in range(12):
        a = TAU * i / 12 + 0.13
        lash.lathe([(0.0, -0.05), (0.07, -0.05), (0.075, 0.0), (0.07, 0.05), (0.0, 0.05)], 6,
                   Matrix.Translation((1.075 * math.cos(a), 1.075 * math.sin(a), rim_z)) @
                   Matrix.Rotation(a, 4, "Z") @ Matrix.Rotation(math.radians(90), 4, "X"))
    oar = k("M_Wood", smooth=45)
    a, b = Vector((-0.6, 0.32, BASKET_FLOOR + 0.04)), Vector((0.35, -0.1, BASKET_FLOOR + 0.04))
    oar.tube([a, b], 0.03, sides=6)
    d = (b - a).normalized()
    oar.box((-0.11, 0.0, -0.015), (0.11, 0.34, 0.015), look_matrix(b, Vector((0, 0, 1))) @ Matrix.Rotation(
        math.atan2(d.y, d.x) - math.pi / 2, 4, "Z"))
    return [k.finish("basket_boat", col)]


# --------------------------------------------------------------------------------------------
def nipa_palm(col):
    """Dừa nước: a trunkless clump of long feathery fronds rising from the water and arching out."""
    k = Kit()
    k("M_WoodDark", smooth=50).lathe([(0.0, 0.0), (0.4, 0.0), (0.42, 0.15), (0.3, 0.38), (0.0, 0.48)], 10)
    r = rng(17)
    fr = [k("M_Leaf", smooth=55), k("M_LeafDark", smooth=55), k("M_LeafLight", smooth=55)]
    rib = k("M_BambooDry", smooth=50)
    n = 11
    for i in range(n):
        a = TAU * i / n + r(-0.2, 0.2)
        tilt = r(0.2, 0.55) if i % 3 else r(0.08, 0.2)
        d = Vector((math.cos(a) * tilt, math.sin(a) * tilt, 1.0))
        base = Vector((0.12 * math.cos(a), 0.12 * math.sin(a), 0.3))
        length = r(4.3, 5.0) if i % 3 else r(3.2, 3.8)
        pts = fr[i % 3].leaf(base, d, length, r(0.7, 0.85), droop=r(0.28, 0.42), fold=0.25, steps=30,
                             serrate=0.45, thick=0.02,
                             width_fn=lambda t: math.sin(math.pi * min(1.0, 0.04 + t * 0.98)) ** 0.5 * (0.25 if t < 0.12 else 1.0))
        rib.tube(pts[:-1], [0.05 * (1 - 0.8 * j / (len(pts) - 2)) for j in range(len(pts) - 1)], sides=5)
    return [k.finish("nipa_palm", col)]


# --------------------------------------------------------------------------------------------
def lantern_boat(col):
    """Hội An river boat: dark painted hull with bow eyes and stripes, a plank deck (0.55) and a
    light arched canopy frame hung with colourful silk lanterns. 4 m long, bow towards -Y."""
    k = Kit()
    L, B = 4.0, 1.5
    N = 26
    st = []
    for i in range(N + 1):
        t = lerp(0.006, 0.994, i / N)
        y = lerp(-L / 2, L / 2, t)
        e = abs(2 * t - 1)
        w = (B / 2) * math.sin(math.pi * t) ** 0.7
        st.append((y, w, 0.82 + 0.45 * e ** 3.0, 0.4 * e ** 3.2))
    rings = []
    for y, w, sheer, keel in st:
        outer = []
        for i in range(9):
            a = math.pi * i / 8
            depth = math.sin(a) ** 0.6
            z = lerp(sheer, keel, depth) if i not in (0, 8) else sheer
            outer.append(Vector((-w * math.cos(a) * (0.85 + 0.15 * (1 - depth)), y, z)))
        inner = [Vector((p.x * max(0.0, w - 0.06) / max(w, 1e-4), p.y, max(p.z, keel + 0.06) if 0 < i < 8 else sheer))
                 for i, p in enumerate(outer)]
        rings.append(outer + list(reversed(inner)))
    hull = k("M_WoodDark", smooth=40)
    hull.loft(rings, closed_rings=True, cap0=True, cap1=True)
    pts = [(w - 0.1, y) for y, w, s, kk in st[3:-3]]
    k("M_WoodLight", smooth=40).extrude_poly(pts + [(-x, y) for x, y in reversed(pts)], LANTERN_BOAT_DECK - 0.05,
                                             LANTERN_BOAT_DECK)
    for mat, dz in (("M_Red", 0.07), ("M_Shutter", 0.2)):
        for s in (-1, 1):
            k(mat, smooth=50).tube([Vector((s * w * (1.0 if dz < 0.1 else 0.97), y, sheer - dz)) for y, w, sheer, kk in st[1:-1]],
                                   0.035, sides=5, caps=True)
    y, w, sheer, keel = st[4]
    for s in (-1, 1):
        n = Vector((s, -0.35, 0)).normalized()
        m = look_matrix(Vector((s * w * 0.93, y, sheer - 0.25)), n)
        k("M_White", smooth=None).extrude_poly(ellipse_points(0, 0, 0.065, 0.13, 14), -0.02, 0.015,
                                               m @ Matrix.Rotation(math.radians(90), 4, "Z"))
        k("M_Black", smooth=None).extrude_poly(ellipse_points(0, 0, 0.045, 0.045, 10), 0.0, 0.025, m)
    # canopy frame
    frame = k("M_WoodLight", smooth=45)
    arch_y = (-1.0, -0.3, 0.4, 1.1)
    top_z = 2.0
    for ay in arch_y:
        path = [Vector((0.62 * math.cos(a), ay, LANTERN_BOAT_DECK + (top_z - LANTERN_BOAT_DECK) * math.sin(a)))
                for a in [math.pi * i / 10 for i in range(11)]]
        frame.tube(path, 0.03, sides=5, caps=True)
    frame.tube([Vector((0, arch_y[0], top_z)), Vector((0, arch_y[-1], top_z))], 0.03, sides=5)
    side_z = LANTERN_BOAT_DECK + (top_z - LANTERN_BOAT_DECK) * math.sin(math.radians(54))
    side_x = 0.62 * math.cos(math.radians(54))
    for s in (-1, 1):
        frame.tube([Vector((s * side_x, arch_y[0], side_z)), Vector((s * side_x, arch_y[-1], side_z))], 0.025, sides=5)
    mats = ["M_SilkRed", "M_SilkYellow", "M_SilkPurple", "M_SilkBlue", "M_SilkGreen", "M_SilkOrange", "M_SilkPink"]
    i = 0
    for ay in (-0.65, 0.05, 0.75):
        silk_lantern(k, (0, ay, top_z - 0.03), 0.55, mats[i % 7], segs=10)
        i += 1
    for s in (-1, 1):
        for ay in (-0.75, 0.05, 0.85):
            silk_lantern(k, (s * side_x, ay, side_z - 0.02), 0.45, mats[i % 7], segs=10)
            i += 1
    return [k.finish("lantern_boat", col)]


# --------------------------------------------------------------------------------------------
def silk_lantern_string(col):
    """A 6 m sagging string of seven silk lanterns in mixed colours, hooked at x = ±3, z = 0."""
    k = Kit()
    sag = 0.8
    path = [Vector((x, 0, -sag * (1 - (x / 3.0) ** 2))) for x in [-3 + 6 * i / 24 for i in range(25)]]
    k("M_Black", smooth=40).tube(path, 0.012, sides=4, caps=True)
    mats = ["M_SilkRed", "M_SilkYellow", "M_SilkPurple", "M_SilkBlue", "M_SilkGreen", "M_SilkOrange", "M_SilkPink"]
    for i, mat in enumerate(mats):
        x = -2.25 + 4.5 * i / 6
        z = -sag * (1 - (x / 3.0) ** 2)
        silk_lantern(k, (x, 0, z), 0.6, mat, segs=10)
    return [k.finish("silk_lantern_string", col)]
