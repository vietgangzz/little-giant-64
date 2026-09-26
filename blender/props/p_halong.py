"""Vịnh Hạ Long level props: junk_boat, raft_house, raft_platform, fish_cage_ring, kayak,
pavilion_titop, buoy, seagull, net_rack, vietnam_flag.

Reported heights (metres above the prop origin) are the module constants below; the build
prints them too.
"""

import math

import bmesh
from mathutils import Matrix, Vector

from lib import (TAU, Part, bezier, densify, join_parts, lerp, mat4, rng, rounded_rect_points,
                 star_points)

JUNK_DECK = 1.55          # top of the junk's main deck planks
JUNK_CABIN_ROOF = 3.62    # top of the stern cabin sun deck
RAFT_HOUSE_DECK = 0.80
RAFT_HOUSE_RIDGE = 4.20   # roof ridge top (the ridge cap)
RAFT_PLATFORM_DECK = 0.50
PAVILION_FLOOR = 0.50

RY90 = Matrix.Rotation(math.radians(90), 4, "Y")     # local Z -> +X
RXm90 = Matrix.Rotation(math.radians(-90), 4, "X")   # local Z -> +Y
RX90 = Matrix.Rotation(math.radians(90), 4, "X")     # local Z -> -Y


# --------------------------------------------------------------------------------------------
# shared bits
# --------------------------------------------------------------------------------------------
def _barrel(part, band, c, r, L, axis_m=RY90, segs=10):
    """Blue plastic float barrel lying on its side (axis along X by default), two rib bands."""
    m = Matrix.Translation(c) @ axis_m
    h = L / 2
    part.lathe([(0.0, -h), (r * 0.8, -h), (r * 0.97, -h + 0.05), (r, -h + 0.14), (r, h - 0.14),
                (r * 0.97, h - 0.05), (r * 0.8, h), (0.0, h)], segs, m)
    for z in (-h * 0.45, h * 0.45):
        band.lathe([(r * 0.98, z - 0.035), (r * 1.05, z - 0.025), (r * 1.05, z + 0.025), (r * 0.98, z + 0.035)],
                   segs, m, closed=True)


def _raft(planks_a, planks_b, beams, barrels, bands, W, D, deck_top, barrel_r, grid, barrel_len, seed=1):
    """Square plank raft on blue barrels. Planks run along X; perimeter beams below them."""
    r = rng(seed)
    plank_t = 0.08
    beam_top = deck_top - plank_t
    for sx in (-1, 1):
        beams.box((sx * W / 2 - 0.14, -D / 2, beam_top - 0.16), (sx * W / 2, D / 2, beam_top))
        beams.box((-W / 2, sx * D / 2 - 0.14 if sx > 0 else -D / 2, beam_top - 0.16),
                  (W / 2, sx * D / 2 if sx > 0 else -D / 2 + 0.14, beam_top))
    beams.box((-0.07, -D / 2, beam_top - 0.16), (0.07, D / 2, beam_top))
    n = max(2, round(D / 0.32))
    pw = D / n
    for k in range(n):
        y0 = -D / 2 + k * pw + 0.015
        y1 = y0 + pw - 0.03
        part = planks_a if r() > 0.35 else planks_b
        ext = r(-0.04, 0.04)
        part.box((-W / 2 - 0.03 + ext, y0, beam_top), (W / 2 + 0.03 + ext, y1, deck_top))
    nx, ny = grid
    for i in range(nx):
        for j in range(ny):
            x = lerp(-W / 2 + barrel_len / 2 + 0.1, W / 2 - barrel_len / 2 - 0.1, i / max(1, nx - 1))
            y = lerp(-D / 2 + barrel_r + 0.15, D / 2 - barrel_r - 0.15, j / max(1, ny - 1))
            _barrel(barrels, bands, (x, y, barrel_r), barrel_r, barrel_len)


def _bamboo_pole(part, a, b, r, segs=7, nodes=2):
    a, b = Vector(a), Vector(b)
    L = (b - a).length
    m = Matrix.Translation(a) @ Vector((0, 0, 1)).rotation_difference(b - a).to_matrix().to_4x4()
    prof = [(0.0, 0.0), (r, 0.0)]
    for k in range(1, nodes + 1):
        z = L * k / (nodes + 1)
        prof += [(r, z - 0.02), (r * 1.12, z), (r, z + 0.02)]
    prof += [(r, L), (0.0, L)]
    part.lathe(prof, segs, m)


def _corrugated(part, p0, u, v, nu, amp=0.035, thick=0.05):
    """Corrugated sheet: spans p0 + u (along the ridge) and + v (down the slope); ridges run
    down the slope. Closed slab; normals fixed with recalc afterwards."""
    p0, u, v = Vector(p0), Vector(u), Vector(v)
    n = u.cross(v).normalized()
    if n.z < 0:
        n = -n
    top, bot = [], []
    for i in range(nu + 1):
        off = n * (amp if i % 2 else 0.0)
        top.append([part._v(p0 + u * (i / nu) + v * j + off) for j in (0, 1)])
        bot.append([part._v(p0 + u * (i / nu) + v * j - n * thick) for j in (0, 1)])
    for i in range(nu):
        part.face([top[i][0], top[i + 1][0], top[i + 1][1], top[i][1]])
        part.face([bot[i][0], bot[i][1], bot[i + 1][1], bot[i + 1][0]])
        part.face([top[i][0], bot[i][0], bot[i + 1][0], top[i + 1][0]])
        part.face([top[i][1], top[i + 1][1], bot[i + 1][1], bot[i][1]])
    part.face([top[0][0], top[0][1], bot[0][1], bot[0][0]])
    part.face([top[nu][0], bot[nu][0], bot[nu][1], top[nu][1]])


def _fix_normals(part):
    bmesh.ops.recalc_face_normals(part.bm, faces=part.bm.faces[:])


def _vn_star(part, cx, cy, R, m, z0, z1):
    part.extrude_poly(star_points(5, R, R * 0.382, 90.0), z0, z1, m @ Matrix.Translation((cx, cy, 0)))


def _cloth_flag(col, name, W, H, NX, NZ, cloth_mat, emblem_mat, emblem_pts, parent, loc):
    """Waving flag cloth as its own object: origin at the pole edge / top, local +X = away from the
    pole (0..W), hangs down to -H. Emblem polygon (flag-local XZ coords) printed on both sides."""
    cloth = Part(cloth_mat, smooth=180)
    t = 0.008
    grids = {}
    for side in (-1, 1):
        rows = []
        for i in range(NX + 1):
            x = W * i / NX
            rows.append([cloth._v(Vector((x, side * t, -H * j / NZ))) for j in range(NZ + 1)])
        for i in range(NX):
            for j in range(NZ):
                q = [rows[i][j], rows[i + 1][j], rows[i + 1][j + 1], rows[i][j + 1]]
                cloth.face(q if side < 0 else list(reversed(q)))
        grids[side] = rows
    edges = [(i, 0) for i in range(NX)] + [(NX, j) for j in range(NZ)] + \
            [(i, NZ) for i in range(NX, 0, -1)] + [(0, j) for j in range(NZ, 0, -1)]
    for k in range(len(edges)):
        i0, j0 = edges[k]
        i1, j1 = edges[(k + 1) % len(edges)]
        cloth.face([grids[-1][i0][j0], grids[1][i0][j0], grids[1][i1][j1], grids[-1][i1][j1]])
    cloth.flip()
    emb = Part(emblem_mat, smooth=None)
    pts = densify(emblem_pts, 0.04)
    front_m = Matrix(((1, 0, 0, 0), (0, 0, -1, -t), (0, 1, 0, 0), (0, 0, 0, 1)))
    back_m = Matrix(((-1, 0, 0, 0), (0, 0, 1, t), (0, 1, 0, 0), (0, 0, 0, 1)))
    emb.extrude_poly(pts, 0.0, 0.006, front_m)
    emb.extrude_poly([(-x, y) for x, y in pts], 0.0, 0.006, back_m)
    flag = join_parts(name, [cloth, emb], col)
    me = flag.data
    uv = me.uv_layers.new(name="UVMap")
    for loop in me.loops:
        co = me.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (max(0.0, min(1.0, co.x / W)), max(0.0, min(1.0, -co.z / H)))
    flag.parent = parent
    flag.location = loc
    return flag


# --------------------------------------------------------------------------------------------
def junk_boat(col):
    """Hạ Long tourist junk: 10 m wooden hull with a flat walkable main deck, raised stern cabin
    with a railed sun deck, three masts with ribbed orange batwing sails, carved dragon-head prow
    and a small Vietnam flag at the stern. Bow towards -Y."""
    L, B = 10.0, 3.2
    D = JUNK_DECK - 0.05                  # hull deck line (planks sit on it)
    hull = Part("M_WoodDark", smooth=40)
    N = 30
    st = []
    for k in range(N + 1):
        y = lerp(-L / 2 + 0.05, L / 2, k / N)
        if y < -2.0:
            w = (B / 2) * math.sin(0.5 * math.pi * (y + L / 2) / (L / 2 - 2.0)) ** 0.75
        elif y > 2.5:
            w = (B / 2) * (1 - 0.3 * ((y - 2.5) / 2.5) ** 2)
        else:
            w = B / 2
        w = max(w, 0.05)
        sheer = D + 0.55 + (1.1 * ((-2.0 - y) / 3.0) ** 2 if y < -2.0 else 0) + \
            (0.7 * ((y - 2.0) / 3.0) ** 2 if y > 2.0 else 0)
        keel = (1.15 * ((-2.2 - y) / 2.8) ** 2 if y < -2.2 else 0) + (0.5 * ((y - 3.0) / 2.0) ** 2 if y > 3.0 else 0)
        st.append((y, w, sheer, keel))
    rings = []
    for y, w, sheer, keel in st:
        outer = []
        for i in range(9):
            a = math.pi * i / 8
            depth = math.sin(a) ** 0.5
            x = -w * math.cos(a) * (0.9 + 0.1 * (1 - depth))
            z = sheer if i in (0, 8) else lerp(sheer, keel, depth)
            outer.append(Vector((x, y, z)))
        wi = max(0.02, w - 0.14)
        dz = max(D, keel + 0.15)
        inner = [Vector((wi, y, sheer)), Vector((wi, y, dz)), Vector((wi * 0.33, y, dz)),
                 Vector((-wi * 0.33, y, dz)), Vector((-wi, y, dz)), Vector((-wi, y, sheer))]
        rings.append(outer + inner)
    hull.loft(rings, closed_rings=True, cap0=True, cap1=True)
    hull.flip()
    # light rub-rails along the sheer and a hull band
    trim = Part("M_WoodLight", smooth=45)
    for s in (-1, 1):
        trim.tube([Vector((s * (w + 0.01), y, sheer + 0.02)) for y, w, sheer, keel in st], 0.06, sides=5)
        trim.tube([Vector((s * (w * 0.97 + 0.01), y, sheer - 0.45)) for y, w, sheer, keel in st[4:]], 0.05, sides=5)
    # main deck planks (flat, walkable)
    deck = Part("M_WoodLight", smooth=40)
    pts_r = [(max(0.05, w - 0.16), y) for y, w, sheer, keel in st if -4.0 <= y <= 4.7]
    deck.extrude_poly(pts_r + [(-x, y) for x, y in reversed(pts_r)], D - 0.02, JUNK_DECK)
    seams = Part("M_Wood", smooth=40)
    for x in (-0.9, -0.3, 0.3, 0.9):
        seams.box((x - 0.012, -3.6, JUNK_DECK - 0.01), (x + 0.012, 1.4, JUNK_DECK + 0.004))
    # stern cabin with a railed sun deck
    cab = Part("M_WoodLight", smooth=40, bevel=(0.03, 1))
    y0, y1, cw, top = 1.7, 4.4, 1.25, JUNK_CABIN_ROOF - 0.1
    cab.box((-cw, y0, JUNK_DECK), (cw, y1, top - 0.1))
    roof = Part("M_Wood", smooth=40, bevel=(0.03, 1))
    roof.box((-cw - 0.15, y0 - 0.2, top - 0.1), (cw + 0.15, y1 + 0.15, JUNK_CABIN_ROOF))
    red = Part("M_Red", smooth=45)
    dark = Part("M_WoodDark", smooth=40)
    for sx in (-1, 1):
        for y in (y0, y1):
            red.cylinder(0.08, top - JUNK_DECK - 0.1, 8, mat4((sx * cw, y, JUNK_DECK)))
        for y in (2.3, 3.2, 3.95):   # side windows
            dark.box((sx * cw - 0.03 if sx > 0 else -cw - 0.02, y - 0.25, 2.3),
                     (sx * cw + 0.02 if sx > 0 else -cw + 0.03, y + 0.25, 2.95))
    dark.box((-0.42, y0 - 0.03, JUNK_DECK), (0.42, y0 + 0.02, 3.0))            # cabin door
    for x in (-0.85, 0.85):
        dark.box((x - 0.25, y0 - 0.03, 2.3), (x + 0.25, y0 + 0.02, 2.95))       # front windows
    rail = Part("M_Wood", smooth=40)
    ry = [y0 - 0.15, y1 + 0.1]
    for sx in (-1, 1):
        for k in range(6):
            y = lerp(ry[0], ry[1], k / 5)
            rail.cylinder(0.035, 0.55, 6, mat4((sx * (cw + 0.08), y, JUNK_CABIN_ROOF)))
        rail.tube([Vector((sx * (cw + 0.08), ry[0], JUNK_CABIN_ROOF + 0.55)),
                   Vector((sx * (cw + 0.08), ry[1], JUNK_CABIN_ROOF + 0.55))], 0.04, sides=5)
    for y in ry:
        rail.tube([Vector((-(cw + 0.08), y, JUNK_CABIN_ROOF + 0.55)), Vector((cw + 0.08, y, JUNK_CABIN_ROOF + 0.55))],
                  0.04, sides=5)
    # little red lanterns under the cabin eave
    for x in (-0.95, 0.95):
        red.sphere(0.12, mat4((x, y0 - 0.12, top - 0.35)), segs=10, rings=6, scale=(1, 1, 1.2))
    # a life ring on the cabin front
    white = Part("M_White", smooth=50)
    white.lathe([(0.2, -0.03), (0.28, -0.03), (0.3, 0.0), (0.28, 0.03), (0.2, 0.03), (0.18, 0.0)], 16,
                Matrix.Translation((0.0, y0 - 0.06, 3.15)) @ RX90, closed=True)
    # masts, battened batwing sails
    mast = Part("M_Wood", smooth=45)
    sail = Part("M_Sail", smooth=None)
    batt = Part("M_WoodDark", smooth=45)
    sail_m = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))  # (u,v,w)->(w,u,v)
    for my, base_z, h, span, sh, off in ((-2.7, JUNK_DECK, 7.2, 3.0, 4.6, -0.2), (0.3, JUNK_DECK, 8.6, 3.6, 5.6, 0.2),
                                         (3.0, JUNK_CABIN_ROOF, 5.0, 2.0, 3.2, -0.2)):
        mast.lathe([(0.0, 0.0), (0.12, 0.0), (0.1, h), (0.06, h + 0.12), (0.0, h + 0.18)], 8,
                   Matrix.Translation((0, my, base_z)))
        # batwing outline in (u = along the boat from the mast, v = up)
        z0 = base_z + 0.9
        nb = 6
        lead = []
        leech = []
        for k in range(nb + 1):
            t = k / nb
            v = z0 + sh * t
            fwd = -0.35 * span * (1 - t) - 0.1
            aft = span * (0.55 + 0.45 * math.sin(math.pi * (0.25 + 0.75 * t)) ** 0.8)
            lead.append((my + fwd, v))
            leech.append((my + aft, v))
        outline = list(lead)
        top_v = z0 + sh
        outline.append((my + (lead[-1][0] - my + leech[-1][0] - my) / 2, top_v + 0.45))
        for k in range(nb, -1, -1):
            u, v = leech[k]
            outline.append((u, v))
            if k > 0:   # scallop between battens
                u2, v2 = leech[k - 1]
                outline.append(((u + u2) / 2 + 0.28, (v + v2) / 2))
        # mirror the order so the polygon is simple: lead up, then leech down
        poly = outline
        sail.extrude_poly([(u, v) for u, v in poly], off - 0.02, off + 0.02, sail_m)
        bx = off + (0.04 if off > 0 else -0.04)
        for k in range(nb + 1):
            a, b = lead[k], leech[k]
            batt.tube([Vector((bx, a[0], a[1])), Vector((bx, b[0], b[1]))], 0.035, sides=4)
        # gaff to the peak
        batt.tube([Vector((bx, lead[-1][0], top_v)), Vector((bx, outline[nb + 1][0], top_v + 0.45))], 0.05, sides=5)
    # dragon-head prow
    gold = Part("M_Gold", smooth=50)
    bow_y, bow_w, bow_sheer, bow_keel = st[0]
    neck0 = Vector((0, bow_y + 0.15, bow_sheer - 0.3))
    pts = bezier(neck0, neck0 + Vector((0, -0.45, 0.35)), neck0 + Vector((0, -0.4, 0.95)),
                 neck0 + Vector((0, -0.75, 1.05)), 8)
    gold.tube(pts, [0.26, 0.24, 0.22, 0.2, 0.19, 0.19, 0.2, 0.21, 0.22], sides=10, caps=True)
    hd = pts[-1]
    gold.sphere(0.3, mat4(tuple(hd + Vector((0, -0.05, 0.05)))), segs=12, rings=6, scale=(0.85, 1.1, 0.9))
    gold.lathe([(0.0, 0.0), (0.2, 0.0), (0.17, 0.25), (0.1, 0.42), (0.0, 0.45)], 10,
               Matrix.Translation(hd + Vector((0, -0.2, 0.0))) @ RX90 @ Matrix.Diagonal((1, 0.75, 1, 1)))
    for s in (-1, 1):
        red.sphere(0.07, mat4(tuple(hd + Vector((s * 0.2, -0.12, 0.14)))), segs=8, rings=4)
        hb = hd + Vector((s * 0.12, 0.08, 0.2))
        gold.tube([hb, hb + Vector((s * 0.1, 0.25, 0.25)), hb + Vector((s * 0.15, 0.45, 0.3))],
                  [0.06, 0.04, 0.015], sides=5, caps=True)
    for k in range(4):   # red mane flames down the neck
        p = pts[3 + k]
        red.tube(bezier(p, p + Vector((0, 0.25, 0.1)), p + Vector((0, 0.45, 0.05)), p + Vector((0, 0.55, 0.2)), 4),
                 [0.08, 0.06, 0.045, 0.025, 0.008], sides=5, caps=True)
    # stern flag (static): pole + red cloth + yellow star
    flag_x, flag_y = 0.0, y1 + 0.05
    mast.cylinder(0.03, 1.6, 6, mat4((flag_x, flag_y, JUNK_CABIN_ROOF)))
    fr = Part("M_FlagRed", smooth=40)
    fy = Part("M_FlagYellow", smooth=None)
    fz = JUNK_CABIN_ROOF + 1.55
    fr.box((-0.012, flag_y, fz - 0.6), (0.012, flag_y + 0.9, fz))
    for s in (-1, 1):
        m = Matrix.Translation((s * 0.012, flag_y + 0.45, fz - 0.3)) @ Matrix.Rotation(math.radians(s * 90), 4, "Z") @ \
            Matrix.Rotation(math.radians(90), 4, "X")
        # local x across the flag, y up, z outward
        fy.extrude_poly(star_points(5, 0.17, 0.065, 90.0), 0.0, 0.006, m)
    parts = [hull, trim, deck, seams, cab, roof, red, dark, rail, white, mast, sail, batt, gold, fr, fy]
    return [join_parts("junk_boat", parts, col)]


# --------------------------------------------------------------------------------------------
def raft_platform(col):
    """Plain 4 x 4 m plank raft on blue barrels; deck top at 0.50 m."""
    pa = Part("M_Wood", smooth=40, bevel=(0.015, 1))
    pb = Part("M_WoodLight", smooth=40, bevel=(0.015, 1))
    beams = Part("M_WoodDark", smooth=40)
    barrels = Part("M_BarrelBlue", smooth=50)
    bands = Part("M_BarrelBlue", smooth=45)
    _raft(pa, pb, beams, barrels, bands, 4.0, 4.0, RAFT_PLATFORM_DECK, 0.22, (2, 3), 1.5, seed=4)
    ropes = Part("M_String", smooth=50)
    for sx in (-1, 1):
        for sy in (-1, 1):
            ropes.lathe([(0.05, 0.0), (0.08, 0.0), (0.08, 0.14), (0.05, 0.14)], 8,
                        Matrix.Translation((sx * 1.85, sy * 1.85, RAFT_PLATFORM_DECK)), closed=True)
            beams.cylinder(0.06, 0.25, 8, mat4((sx * 1.85, sy * 1.85, RAFT_PLATFORM_DECK)))
    return [join_parts("raft_platform", [pa, pb, beams, barrels, bands, ropes], col)]


def raft_house(col):
    """Nhà bè: 6 x 6 m plank raft on blue barrels with a 4 x 4 m wooden house (blue corrugated
    gable roof), front porch with railing, potted plant, hanging lantern, clothesline and a
    thúng chai basket boat."""
    pa = Part("M_Wood", smooth=40, bevel=(0.015, 1))
    pb = Part("M_WoodLight", smooth=40, bevel=(0.015, 1))
    beams = Part("M_WoodDark", smooth=40)
    barrels = Part("M_BarrelBlue", smooth=50)
    bands = Part("M_BarrelBlue", smooth=45)
    DK = RAFT_HOUSE_DECK
    _raft(pa, pb, beams, barrels, bands, 6.0, 6.0, DK, 0.3, (3, 3), 1.6, seed=6)
    # house body
    x0, x1, y0, y1 = -2.0, 2.0, -1.2, 2.8
    wt = DK + 2.4
    walls = Part("M_WoodLight", smooth=40)
    walls.box((x0, y0, DK), (x1, y1, wt))
    strips = Part("M_Wood", smooth=40)
    for k in range(1, 10):     # vertical board battens on the side walls
        y = lerp(y0, y1, k / 10)
        for sx in (-1, 1):
            strips.box((sx * 2.0 - 0.03, y - 0.025, DK), (sx * 2.0 + 0.03, y + 0.025, wt))
    for k in range(1, 10):
        x = lerp(x0, x1, k / 10)
        if abs(x) < 0.55:
            continue
        for y in (y0, y1):
            strips.box((x - 0.025, y - 0.03, DK), (x + 0.025, y + 0.03, wt))
    bamboo = Part("M_Bamboo", smooth=50)
    for x in (x0, x1):
        for y in (y0, y1):
            _bamboo_pole(bamboo, (x, y, DK), (x, y, wt + 0.05), 0.08, nodes=3)
    blue = Part("M_RoofBlue", smooth=40)
    dark = Part("M_WoodDark", smooth=40)
    dark.box((-0.55, y0 - 0.05, DK), (0.55, y0 + 0.02, DK + 2.05))          # door frame
    blue.box((-0.45, y0 - 0.07, DK), (0.45, y0 + 0.0, DK + 1.95))           # blue door
    for sx in (-1, 1):
        for y in (0.0, 1.7):
            dark.box((sx * 2.0 - 0.05, y - 0.4, DK + 1.0), (sx * 2.0 + 0.05, y + 0.4, DK + 1.8))
            for so in (-1, 1):   # open shutters
                blue.box((sx * 2.0 - 0.04 + sx * 0.04, y + so * 0.4 + (0.02 if so > 0 else -0.42), DK + 1.0),
                         (sx * 2.0 + 0.04 + sx * 0.04, y + so * 0.4 + (0.42 if so > 0 else -0.02), DK + 1.8))
    for sx in (-1, 1):   # front windows
        dark.box((sx * 1.3 - 0.35, y0 - 0.05, DK + 1.0), (sx * 1.3 + 0.35, y0 + 0.02, DK + 1.7))
    # gables + corrugated roof (ridge along Y)
    ridge_z = RAFT_HOUSE_RIDGE - 0.08
    half = 2.4
    eave = ridge_z - 1.05
    gable = Part("M_WoodLight", smooth=40)
    for y in (y0, y1):
        gable.extrude_poly([(-2.0, wt), (2.0, wt), (0.0, ridge_z - 0.05)], -y - 0.05, -y + 0.05,
                           Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1))))
    roof = Part("M_RoofBlue", smooth=None)
    ry0, ry1 = y0 - 0.45, y1 + 0.4
    for s in (-1, 1):
        p0 = Vector((0.0, ry0, ridge_z))
        _corrugated(roof, p0, Vector((0, ry1 - ry0, 0)), Vector((s * half, 0, eave - ridge_z)), 28)
    _fix_normals(roof)
    cap = Part("M_Metal", smooth=45)
    cap.tube([Vector((0, ry0 - 0.02, ridge_z + 0.02)), Vector((0, ry1 + 0.02, ridge_z + 0.02))], 0.09, sides=6)
    # porch railing (front and the front halves of the sides), gap for boarding
    rails = Part("M_Bamboo", smooth=50)
    ph = DK + 0.85
    for x in (-2.9, -2.1, -1.3, 1.3, 2.1, 2.9):
        rails.cylinder(0.045, 0.85, 6, mat4((x, -2.9, DK)))
    for sx in (-1, 1):
        rails.tube([Vector((sx * 2.9, -2.9, ph)), Vector((sx * 1.3, -2.9, ph))], 0.04, sides=5)
        for y in (-2.1, -1.3):
            rails.cylinder(0.045, 0.85, 6, mat4((sx * 2.9, y, DK)))
        rails.tube([Vector((sx * 2.9, -2.9, ph)), Vector((sx * 2.9, -1.3, ph))], 0.04, sides=5)
    # potted plant
    pot = Part("M_Terracotta", smooth=45)
    pot.lathe([(0.0, 0.0), (0.16, 0.0), (0.22, 0.3), (0.25, 0.32), (0.25, 0.36), (0.0, 0.36)], 12,
              Matrix.Translation((-1.4, -1.7, DK)))
    leaf = Part("M_Leaf", smooth=60)
    leaf_d = Part("M_LeafDark", smooth=60)
    for dx, dy, dz, rr, p in ((0, 0, 0.62, 0.3, leaf), (0.18, -0.1, 0.5, 0.2, leaf_d), (-0.17, 0.08, 0.52, 0.2, leaf_d)):
        p.ico(rr, mat4((-1.4 + dx, -1.7 + dy, DK + dz)), subdiv=2)
    # hanging lantern at the front eave
    lant = Part("M_Red", smooth=60)
    lg = Part("M_Gold", smooth=45)
    lx, ly = 1.3, ry0 + 0.15
    lz = eave + (ridge_z - eave) * (1 - 1.3 / half) - 0.5
    lg.cylinder(0.01, 0.4, 4, mat4((lx, ly, lz + 0.18)))
    lant.sphere(0.16, mat4((lx, ly, lz)), segs=12, rings=6, scale=(1, 1, 1.15))
    lg.cylinder(0.07, 0.04, 8, mat4((lx, ly, lz + 0.16)))
    lg.cylinder(0.06, 0.04, 8, mat4((lx, ly, lz - 0.2)))
    # clothesline on the right side of the house
    for y in (-0.8, 2.4):
        _bamboo_pole(bamboo, (2.6, y, DK), (2.6, y, DK + 2.0), 0.05, nodes=2)
    line = Part("M_String", smooth=50)
    line.tube([Vector((2.6, -0.8, DK + 1.92)), Vector((2.6, 0.8, DK + 1.84)), Vector((2.6, 2.4, DK + 1.92))], 0.012,
              sides=4)
    clothes = []
    for y, mname, h in ((-0.2, "M_Red", 0.6), (0.6, "M_Yellow", 0.5), (1.4, "M_RoofBlue", 0.65)):
        c = Part(mname, smooth=40)
        c.box((2.585, y - 0.24, DK + 1.86 - h), (2.615, y + 0.24, DK + 1.87))
        clothes.append(c)
    # thúng chai (round basket boat) leaning on the back-left corner
    basket = Part("M_BambooDry", smooth=50)
    basket.lathe([(0.0, 0.0), (0.45, 0.02), (0.72, 0.18), (0.8, 0.38), (0.84, 0.4), (0.8, 0.44), (0.74, 0.3),
                  (0.66, 0.2), (0.42, 0.1), (0.0, 0.08)], 16,
                 Matrix.Translation((-2.45, 2.3, DK + 0.75)) @ Matrix.Rotation(math.radians(70), 4, "Y"))
    parts = [pa, pb, beams, barrels, bands, walls, strips, bamboo, blue, dark, gable, roof, cap, rails, pot, leaf,
             leaf_d, lant, lg, line, basket] + clothes
    return [join_parts("raft_house", parts, col)]


# --------------------------------------------------------------------------------------------
def fish_cage_ring(col):
    """Round fish-farm cage (decor): two yellow float pipes Ø 3.5, stanchions, a top rail and
    a net lattice, with a fish leaping in the middle. Origin at the float bottom."""
    fl = Part("M_Float", smooth=50)
    for R in (1.65, 1.4):
        ring = [Vector((R * math.cos(a), R * math.sin(a), 0.1)) for a in [TAU * k / 40 for k in range(40)]]
        fl.tube(ring, 0.1, sides=8, closed=True)
    metal = Part("M_Metal", smooth=45)
    for k in range(12):
        a = TAU * k / 12
        c = Vector((math.cos(a), math.sin(a), 0))
        metal.box((-0.05, -0.16, 0.12), (0.05, 0.16, 0.22),
                  Matrix.Translation(c * 1.525) @ Matrix.Rotation(a + math.pi / 2, 4, "Z"))
        metal.cylinder(0.03, 0.85, 6, mat4(tuple(c * 1.525 + Vector((0, 0, 0.2)))))
    rail = [Vector((1.525 * math.cos(a), 1.525 * math.sin(a), 1.05)) for a in [TAU * k / 36 for k in range(36)]]
    metal.tube(rail, 0.04, sides=5, closed=True)
    net = Part("M_Net", smooth=40)
    NR = 1.36
    for k in range(28):
        a = TAU * k / 28
        c = Vector((NR * math.cos(a), NR * math.sin(a), 0))
        net.tube([c + Vector((0, 0, 1.02)), c * 0.97 + Vector((0, 0, 0.55)), c + Vector((0, 0, 0.12))], 0.014,
                 sides=3)
    for z in (0.35, 0.6, 0.85):
        ring = [Vector((NR * math.cos(a), NR * math.sin(a), z)) for a in [TAU * k / 28 for k in range(28)]]
        net.tube(ring, 0.014, sides=3, closed=True)
    water = Part("M_Water", smooth=40)
    water.cylinder(1.36, 0.02, 24, mat4((0, 0, 0.14)))
    fish = Part("M_Orange", smooth=50)
    fish.sphere(0.13, mat4((0.2, 0.1, 0.62), (0, -35, 20)), segs=10, rings=6, scale=(1.6, 0.6, 0.8))
    fish.lathe([(0.0, 0.0), (0.09, 0.0), (0.0, 0.12)], 4,
               Matrix.Translation((0.44, 0.19, 0.78)) @ Matrix.Rotation(math.radians(-60), 4, "Y") @
               Matrix.Diagonal((1.0, 0.3, 1.0, 1.0)))
    return [join_parts("fish_cage_ring", [fl, metal, net, water, fish], col)]


# --------------------------------------------------------------------------------------------
def kayak(col):
    """Bright sea kayak (3.8 m) with cockpit, deck bungees and a paddle resting across it."""
    L = 3.8
    hull = Part("M_Orange", smooth=50)
    deck = Part("M_Kayak", smooth=50)
    N = 20
    rings_h, rings_d = [], []
    for k in range(N + 1):
        t = k / N
        y = lerp(-L / 2, L / 2, t)
        e = abs(2 * t - 1)
        w = 0.33 * math.sin(math.pi * t) ** 0.65
        keel = 0.02 + 0.16 * e ** 2.4
        gun = 0.2 + 0.05 * e ** 2
        top = gun + 0.12 * (1 - e ** 1.5) + (0.03 if abs(y) < 0.4 else 0.0)
        if k in (0, N):
            p = Vector((0, y, gun + 0.03))
            rings_h.append([p])
            rings_d.append([p])
            continue
        hullr = []
        for i in range(7):
            a = math.pi * i / 6
            d = math.sin(a) ** 0.7
            hullr.append(Vector((-w * math.cos(a), y, lerp(gun, keel, d))))
        deckr = []
        for i in range(7):
            a = math.pi * i / 6
            deckr.append(Vector((w * math.cos(a), y, gun + (top - gun) * math.sin(a))))
        rings_h.append(hullr)
        rings_d.append(deckr)
    hull.loft(rings_h, closed_rings=False)
    deck.loft(rings_d, closed_rings=False)
    hull.flip()
    deck.flip()
    black = Part("M_Black", smooth=50)
    cz = 0.36
    rim = [Vector((0.24 * math.cos(a), 0.1 + 0.42 * math.sin(a), cz)) for a in [TAU * k / 20 for k in range(20)]]
    black.tube(rim, 0.03, sides=5, closed=True)
    black.extrude_poly([(0.22 * math.cos(a), 0.1 + 0.4 * math.sin(a)) for a in [TAU * k / 20 for k in range(20)]],
                       cz - 0.06, cz - 0.01)
    for y0, y1 in ((-1.2, -0.45), (0.65, 1.3)):
        for sx in (-1, 1):
            black.tube([Vector((sx * 0.16, y0, 0.33 if abs(y0) < 1 else 0.3)),
                        Vector((-sx * 0.16, y1, 0.33 if abs(y1) < 1 else 0.3))], 0.01, sides=3)
    # paddle across the deck
    shaft = Part("M_Black", smooth=50)
    shaft.tube([Vector((-1.05, -0.35, 0.42)), Vector((1.05, -0.35, 0.42))], 0.022, sides=6)
    blade = Part("M_Red", smooth=45)
    for s in (-1, 1):
        blade.sphere(0.12, mat4((s * 1.18, -0.35, 0.42), (0, s * 20, 0)), segs=10, rings=5, scale=(1.8, 0.2, 0.75))
    parts = [hull, deck, black, shaft, blade]
    zmin = min(v.co.z for p in parts for v in p.bm.verts)
    for p in parts:
        p.deform(lambda v: v - Vector((0, 0, zmin)))
    return [join_parts("kayak", parts, col)]


# --------------------------------------------------------------------------------------------
def _poly_roof(tiles, ridge, curl, n, R, z_eave, rise, lift=0.35, flare=0.12, per_side=4, levels=6,
               thick=0.12, phase=0.0):
    """n-sided curved roof with upturned corners (pavilion roof). Returns the apex point."""
    M = n * per_side
    sector = TAU / n

    def pt(j, s, under):
        th = phase + TAU * j / M
        d = ((th - phase) % sector) - sector / 2
        Rp = R * math.cos(sector / 2) / math.cos(d)
        c = abs(d) / (sector / 2)
        rr = s * Rp * (1 + flare * c ** 4 * s ** 2)
        z = z_eave + rise * (1 - s) ** 1.7 + lift * c ** 4 * s ** 3
        if not under and 0.05 < s < 0.99 and j % 2 == 1:
            z += 0.04
        if under:
            z -= thick
        return Vector((rr * math.cos(th), rr * math.sin(th), z))

    ss = [k / levels for k in range(1, levels + 1)]
    rings = [[pt(0, 0.0, True)]]
    rings += [[pt(j, s, True) for j in range(M)] for s in ss]
    rings += [[pt(j, s, False) for j in range(M)] for s in reversed(ss)]
    rings.append([pt(0, 0.0, False)])
    tiles.loft(rings, closed_rings=True)
    eave = [pt(j, 1.0, False) + Vector((0, 0, 0.02)) for j in range(M)]
    ridge.tube(eave, 0.06, sides=6, closed=True)
    for k in range(n):
        j = k * per_side
        hip = [pt(j, s, False) + Vector((0, 0, 0.05)) for s in [i / 8 for i in range(1, 9)]]
        ridge.tube(hip, 0.065, sides=6, caps=True)
        c = hip[-1]
        dirv = Vector((c.x, c.y, 0)).normalized()
        pts = [c - dirv * 0.05 + dirv * (0.17 * math.sin(a)) + Vector((0, 0, 0.17 * (1 - math.cos(a))))
               for a in [i * 0.36 for i in range(9)]]
        curl.tube(pts, [0.085 * (1 - 0.7 * i / 8) for i in range(9)], sides=6, caps=True)
    return pt(0, 0.0, False)


def pavilion_titop(col):
    """Ti Tốp summit lookout: hexagonal kiosk, six red columns, curved tiled roof with upturned
    corners and a gold gourd finial, on a 4 m square stone platform with front steps.
    Walkable floor at 0.50 m."""
    stone = Part("M_StoneLight", smooth=40, bevel=(0.04, 2))
    stone.box((-2.0, -2.0, 0.0), (2.0, 2.0, PAVILION_FLOOR))
    steps = Part("M_StoneLight", smooth=40, bevel=(0.02, 1))
    steps.box((-0.9, -2.55, 0.0), (0.9, -2.3, PAVILION_FLOOR / 3))
    steps.box((-0.9, -2.3, 0.0), (0.9, -2.0, 2 * PAVILION_FLOOR / 3))
    trim = Part("M_Stone", smooth=40)
    for sx in (-1, 1):
        for sy in (-1, 1):
            trim.box((sx * 1.95 - 0.12, sy * 1.95 - 0.12, PAVILION_FLOOR), (sx * 1.95 + 0.12, sy * 1.95 + 0.12,
                                                                            PAVILION_FLOOR + 0.45))
            trim.sphere(0.12, mat4((sx * 1.95, sy * 1.95, PAVILION_FLOOR + 0.52)), segs=8, rings=4)
    red = Part("M_Red", smooth=45)
    dark = Part("M_RedDark", smooth=45)
    Rc = 1.45
    ztop = PAVILION_FLOOR + 2.45
    cols = []
    for k in range(6):
        a = TAU * k / 6
        c = Vector((Rc * math.cos(a), Rc * math.sin(a), 0))
        cols.append(c)
        trim.lathe([(0.0, 0.0), (0.2, 0.0), (0.2, 0.1), (0.15, 0.16), (0.0, 0.16)], 8,
                   Matrix.Translation(c + Vector((0, 0, PAVILION_FLOOR))))
        red.cylinder(0.11, ztop - PAVILION_FLOOR - 0.16, 10, mat4(tuple(c + Vector((0, 0, PAVILION_FLOOR + 0.16)))))
    for k in range(6):
        a, b = cols[k], cols[(k + 1) % 6]
        dark.tube([a + Vector((0, 0, ztop)), b + Vector((0, 0, ztop))], 0.1, sides=6)
        mid = (a + b) / 2
        if mid.y < -1.0:
            continue          # the front stays open
        # bench-rail between columns
        dark.tube([a + Vector((0, 0, PAVILION_FLOOR + 0.5)), b + Vector((0, 0, PAVILION_FLOOR + 0.5))], 0.05, sides=5)
        for t in (0.25, 0.5, 0.75):
            p = a.lerp(b, t)
            dark.cylinder(0.025, 0.5, 5, mat4(tuple(p + Vector((0, 0, PAVILION_FLOOR)))))
    tiles = Part("M_Roof", smooth=35)
    ridge = Part("M_RoofDark", smooth=45)
    curl = Part("M_RoofDark", smooth=45)
    apex = _poly_roof(tiles, ridge, curl, 6, 2.25, ztop + 0.05, 1.05, lift=0.35, flare=0.1)
    gold = Part("M_Gold", smooth=50)
    gold.lathe([(0.0, 0.0), (0.12, 0.02), (0.14, 0.1), (0.07, 0.18), (0.1, 0.26), (0.06, 0.38), (0.0, 0.45)], 10,
               Matrix.Translation(apex - Vector((0, 0, 0.04))))
    return [join_parts("pavilion_titop", [stone, steps, trim, red, dark, tiles, ridge, curl, gold], col)]


# --------------------------------------------------------------------------------------------
def buoy(col):
    """Red/white navigation buoy ~1.5 m: striped float, lattice tower, lamp and can topmark."""
    red = Part("M_Red", smooth=45)
    white = Part("M_White", smooth=45)
    red.lathe([(0.0, 0.0), (0.4, 0.0), (0.48, 0.05), (0.5, 0.12), (0.5, 0.26)], 18, cap1=False)
    white.lathe([(0.5, 0.26), (0.5, 0.44)], 18, cap0=False, cap1=False)
    red.lathe([(0.5, 0.44), (0.5, 0.52), (0.42, 0.62), (0.25, 0.68), (0.0, 0.7)], 18, cap0=False)
    for k in range(3):
        a = TAU * k / 3
        b = Vector((0.28 * math.cos(a), 0.28 * math.sin(a), 0.64))
        t = Vector((0.1 * math.cos(a), 0.1 * math.sin(a), 1.2))
        red.tube([b, t], 0.03, sides=5)
    white.lathe([(0.14, 0.9), (0.2, 0.9), (0.2, 0.95), (0.14, 0.95)], 12, closed=True)
    red.cylinder(0.14, 0.05, 12, mat4((0, 0, 1.18)))
    lamp = Part("M_Yellow", smooth=50)
    lamp.lathe([(0.0, 0.0), (0.07, 0.0), (0.08, 0.1), (0.05, 0.14), (0.0, 0.15)], 10, Matrix.Translation((0, 0, 1.23)))
    red.cylinder(0.09, 0.14, 10, mat4((0, 0, 1.36)))
    return [join_parts("buoy", [red, white, lamp], col)]


def seagull(col):
    """Small seagull with wings spread (~0.9 m span), for decoration. Faces -Y."""
    body = Part("M_White", smooth=60)
    body.sphere(0.1, mat4((0, 0.02, 0.12)), segs=12, rings=6, scale=(1.0, 2.0, 0.9))
    body.sphere(0.075, mat4((0, -0.18, 0.18)), segs=10, rings=5)
    body.extrude_poly([(-0.07, 0.18), (0.07, 0.18), (0.05, 0.3), (-0.05, 0.3)], 0.1, 0.13)
    beak = Part("M_Orange", smooth=45)
    beak.lathe([(0.0, 0.0), (0.025, 0.0), (0.0, 0.1)], 6, Matrix.Translation((0, -0.24, 0.17)) @ RX90)
    eyes = Part("M_Black", smooth=50)
    for s in (-1, 1):
        eyes.sphere(0.014, mat4((s * 0.05, -0.22, 0.21)), segs=6, rings=3)
    grey = Part("M_StoneLight", smooth=None)
    tips = Part("M_Black", smooth=None)

    def bend(v):
        x = abs(v.x)
        z = 0.14 * min(x, 0.18) / 0.18 - 0.09 * max(0.0, x - 0.18) / 0.27
        return Vector((v.x, v.y, v.z + z))
    for s in (-1, 1):
        outline = [(0.05, -0.07), (0.2, -0.08), (0.34, -0.03), (0.38, 0.02), (0.3, 0.07), (0.18, 0.08),
                   (0.05, 0.08)]
        tip = [(0.34, -0.03), (0.46, 0.02), (0.36, 0.065), (0.3, 0.07)]
        g = Part("M_StoneLight")
        g.extrude_poly(densify([(s * x, y) for x, y in outline], 0.05), 0.12, 0.14)
        t = Part("M_Black")
        t.extrude_poly([(s * x, y) for x, y in tip], 0.12, 0.14)
        g.deform(bend)
        t.deform(bend)
        grey.merge_part(g)
        tips.merge_part(t)
    parts = [body, beak, eyes, grey, tips]
    zmin = min(v.co.z for p in parts for v in p.bm.verts)
    for p in parts:
        p.deform(lambda v: v - Vector((0, 0, zmin)))
    return [join_parts("seagull", parts, col)]


def net_rack(col):
    """Fishing-net drying rack: two bamboo A-frames, a 3 m ridge pole and a net draped over it
    with floats along the hem."""
    bamboo = Part("M_BambooDry", smooth=50)
    H, W = 2.1, 3.0
    for x in (-1.4, 1.4):
        for sy in (-1, 1):
            _bamboo_pole(bamboo, (x, sy * 0.75, 0.0), (x, sy * 0.05, H + 0.1), 0.05, nodes=2)
        bamboo.tube([Vector((x, -0.45, 0.9)), Vector((x, 0.45, 0.9))], 0.035, sides=5)
    _bamboo_pole(bamboo, (-1.55, 0, H), (1.55, 0, H), 0.055, nodes=3)
    ties = Part("M_String", smooth=50)
    for x in (-1.4, 1.4):
        ties.lathe([(0.075, -0.07), (0.095, -0.07), (0.095, 0.07), (0.075, 0.07)], 8,
                   Matrix.Translation((x, 0, H)) @ RY90, closed=True)
    net = Part("M_Net", smooth=50)
    # section: inverted V draped over the pole, thickness 0.03; lofted along X with sagging waves
    NXs = 18
    rings = []
    for k in range(NXs + 1):
        x = lerp(-1.3, 1.3, k / NXs)
        sag = 0.12 * math.sin(math.pi * k / NXs * 3) ** 2
        sec = []
        for i in range(7):
            t = i / 6                          # 0 = left hem, 0.5 = over the pole, 1 = right hem
            y = (t - 0.5) * 2 * (0.62 + 0.05 * math.sin(k * 1.3 + i))
            z = H + 0.06 - abs(t - 0.5) * 2 * (1.25 + sag) - 0.02 * math.sin(k * 2.1)
            sec.append(Vector((x, y * (0.2 + 0.8 * abs(t - 0.5) * 2) + (0.0), z)))
        outer = sec
        inner = [p + Vector((0, 0, -0.035)) for p in reversed(sec)]
        rings.append(outer + inner)
    net.loft(rings, closed_rings=True, cap0=True, cap1=True)
    _fix_normals(net)
    floats = Part("M_Float", smooth=50)
    rope = Part("M_JadeDark", smooth=50)
    # mesh lines over the net: along the drape and across it (both faces)
    for k in range(1, NXs, 2):
        rope.tube([p + Vector((0, 0, 0.01)) for p in rings[k][:7]], 0.012, sides=3)
    for i in (1, 2, 4, 5):
        rope.tube([r_[i] + Vector((0, 0, 0.012)) for r_ in rings], 0.012, sides=3)
    for sy in (-1, 1):
        hem = [Vector((r_[0].x, r_[0 if sy < 0 else 6].y, r_[0 if sy < 0 else 6].z - 0.02)) for r_ in rings]
        rope.tube(hem, 0.02, sides=4)
        for k in range(0, NXs + 1, 3):
            p = hem[k]
            floats.sphere(0.06, mat4(tuple(p)), segs=8, rings=4, scale=(1.3, 1, 1))
    return [join_parts("net_rack", [bamboo, ties, net, floats, rope], col)]


def vietnam_flag(col):
    """Flag of Vietnam on a 3 m pole. The cloth is a separate object named "Flag" (origin at the
    pole edge, top; local X 0 -> 1.2 away from the pole; UV.x 0 -> 1) for the flag shader."""
    base = Part("M_StoneLight", smooth=40, bevel=(0.03, 2))
    base.box((-0.25, -0.25, 0.0), (0.25, 0.25, 0.3))
    pole = Part("M_Metal", smooth=50)
    pole.lathe([(0.0, 0.3), (0.05, 0.3), (0.04, 2.95), (0.0, 2.95)], 10)
    gold = Part("M_Gold", smooth=50)
    gold.sphere(0.07, mat4((0, 0, 3.0)), segs=12, rings=6)
    pole_obj = join_parts("vietnam_flag", [base, pole, gold], col)
    W, H = 1.2, 0.8
    star = [(x + W / 2, y - H / 2) for x, y in star_points(5, 0.24, 0.24 * 0.382, 90.0)]
    _cloth_flag(col, "Flag", W, H, 18, 12, "M_FlagRed", "M_FlagYellow", star, pole_obj, (0.045, 0.0, 2.9))
    return [pole_obj]
