"""Little Giant 64 - hero mascot builder.

Run headless from the repo root:

    blender -b --python-exit-code 1 -P blender/mascot/build_mascot.py

Builds everything from an empty scene (geometry, rig, weights, 17 actions),
saves blender/mascot/mascot.blend and exports assets/models/mascot.glb.
The script is deterministic: same input vectors -> same output.
See blender/mascot/README.md and docs/DESIGN.md.
"""

import math
import os
import sys

sys.dont_write_bytecode = True  # keep __pycache__ out of the repo

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import delaunay_2d_cdt
from mathutils.kdtree import KDTree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "blender", "common"))

import lg_svg  # noqa: E402

BLEND_PATH = os.path.join(HERE, "mascot.blend")
GLB_PATH = os.path.join(REPO, "assets", "models", "mascot.glb")
FPS = 30

# ----------------------------------------------------------------------------
# Brand layout: SVG -> metres. Body spans z 0.10 -> 1.15, centred on x = 0.
# SVG x -> +X (character's left, viewer's right when it faces you),
# SVG y (down) -> -Z. The SVG front becomes the -Y side.
# ----------------------------------------------------------------------------
ART = lg_svg.load_artwork()
BODY_SVG = lg_svg.parse_path(ART["body"], step=1.5)[0]
_bx0, _by0, _bx1, _by1 = lg_svg.bbox(BODY_SVG)
BODY_Z0, BODY_Z1 = 0.10, 1.15
SVG_SCALE = (BODY_Z1 - BODY_Z0) / (_by1 - _by0)
SVG_CX = 0.5 * (_bx0 + _bx1)
DEPTH = 0.35  # half-depth at the fattest point
BODY_TRIS = 10000


def svg_to_xz(p):
    return ((p[0] - SVG_CX) * SVG_SCALE, BODY_Z0 + (_by1 - p[1]) * SVG_SCALE)


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_color(h):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[k:k + 2], 16) / 255.0) for k in (0, 2, 4)) + (1.0,)


# ----------------------------------------------------------------------------
# Scene / materials
# ----------------------------------------------------------------------------
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.render.fps_base = 1.0
    sc.frame_start = 0
    sc.frame_end = 60
    sc.unit_settings.system = "METRIC"
    return sc


def make_material(name, hexcol, rough, spec=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    col = hex_color(hexcol)
    bsdf.inputs["Base Color"].default_value = col
    bsdf.inputs["Roughness"].default_value = rough
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = spec
    m.diffuse_color = col
    m.roughness = rough
    return m


MATS = {}


def build_materials():
    MATS["M_Body"] = make_material("M_Body", "#D5F64B", 0.55)
    MATS["M_Foot"] = make_material("M_Foot", "#B9D83A", 0.6)
    MATS["M_Eye"] = make_material("M_Eye", "#234D37", 0.25, spec=0.7)
    MATS["M_Ray"] = make_material("M_Ray", "#FF7447", 0.45)
    # the cape is the Vietnamese flag: official red with the yellow star
    MATS["M_Cape"] = make_material("M_Cape", "#DA251D", 0.7)
    MATS["M_FlagStar"] = make_material("M_FlagStar", "#FFFF00", 0.5)


def new_object(name, mesh):
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def bm_to_object(name, bm, mat_names):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for mn in mat_names:
        me.materials.append(MATS[mn])
    return new_object(name, me)


def evaluated_copy(ob, name):
    """Bake an object's modifiers into a fresh mesh datablock."""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    me.name = name
    return me


# ----------------------------------------------------------------------------
# 2D helpers (numpy)
# ----------------------------------------------------------------------------
def points_in_poly(px, py, poly):
    """Even-odd test, vectorised over arrays px, py."""
    poly = np.asarray(poly)
    x0, y0 = poly[:, 0], poly[:, 1]
    x1, y1 = np.roll(x0, -1), np.roll(y0, -1)
    inside = np.zeros(px.shape, dtype=bool)
    for a, b, c, d in zip(x0, y0, x1, y1):
        if b == d:
            continue
        cond = (b > py) != (d > py)
        xint = a + (py - b) * (c - a) / (d - b)
        inside ^= cond & (px < xint)
    return inside


def dist_to_poly(px, py, poly):
    """Unsigned distance from points to a closed polyline."""
    poly = np.asarray(poly)
    a = poly
    b = np.roll(poly, -1, axis=0)
    best = np.full(px.shape, np.inf)
    for (ax, ay), (bx, by) in zip(a, b):
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = np.clip(((px - ax) * dx + (py - ay) * dy) / max(L2, 1e-12), 0.0, 1.0)
        qx, qy = ax + t * dx, ay + t * dy
        best = np.minimum(best, np.hypot(px - qx, py - qy))
    return best


def resample_closed(poly, spacing):
    """Resample a closed polyline at an even arc-length spacing."""
    P = np.asarray(poly + [poly[0]])
    seg = np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1]))
    s = np.concatenate([[0.0], np.cumsum(seg)])
    n = max(8, int(round(s[-1] / spacing)))
    ts = np.linspace(0.0, s[-1], n, endpoint=False)
    xs = np.interp(ts, s, P[:, 0])
    ys = np.interp(ts, s, P[:, 1])
    return [(float(x), float(y)) for x, y in zip(xs, ys)]


def cdt_fill(outline, spacing, margin):
    """Triangulate a closed outline with an interior grid of Steiner points.

    Returns (verts2d, tris, boundary_flags).
    """
    outline = resample_closed(outline, spacing)
    if lg_svg.signed_area(outline) < 0:
        outline = outline[::-1]
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    gx = np.arange(min(xs) + spacing * 0.5, max(xs), spacing)
    gy = np.arange(min(ys) + spacing * 0.5, max(ys), spacing)
    GX, GY = np.meshgrid(gx, gy)
    # stagger every other row: nicer (more equilateral) triangles
    GX = GX + (np.arange(len(gy))[:, None] % 2) * spacing * 0.5
    GX, GY = GX.ravel(), GY.ravel()
    ins = points_in_poly(GX, GY, outline)
    GX, GY = GX[ins], GY[ins]
    far = dist_to_poly(GX, GY, outline) > margin
    GX, GY = GX[far], GY[far]
    nb = len(outline)
    coords = [Vector(p) for p in outline] + [Vector((float(x), float(y))) for x, y in zip(GX, GY)]
    edges = [(k, (k + 1) % nb) for k in range(nb)]
    vo, eo, fo, orig_v, _oe, _of = delaunay_2d_cdt(coords, edges, [list(range(nb))], 1, 1e-7)
    boundary = []
    for ov in orig_v:
        boundary.append(any(o < nb for o in ov) if ov else False)
    return [(v.x, v.y) for v in vo], fo, boundary, outline


# ----------------------------------------------------------------------------
# Body: brand outline -> pressure-balloon inflation -> remeshed pebble
# ----------------------------------------------------------------------------
class HeightField:
    """Balloon inflation of the brand outline.

    Solves the membrane equation  lap(u) = -1  inside the outline (u = 0 on the
    rim) and uses h = DEPTH * sqrt(u / u_max). For a disc this is exactly a
    sphere, so the pebble is round everywhere, meets the rim with a vertical
    tangent (the two mirrored halves close smoothly) and has no medial-axis
    creases that a plain distance-transform inflation shows.
    """

    def __init__(self, outline_xz, cell=0.004):
        P = np.asarray(outline_xz)
        self.cell = cell
        self.x0 = P[:, 0].min() - 3 * cell
        self.z0 = P[:, 1].min() - 3 * cell
        nx = int(math.ceil((P[:, 0].max() + 3 * cell - self.x0) / cell)) + 1
        nz = int(math.ceil((P[:, 1].max() + 3 * cell - self.z0) / cell)) + 1
        xs = self.x0 + np.arange(nx) * cell
        zs = self.z0 + np.arange(nz) * cell
        X, Z = np.meshgrid(xs, zs)
        mask = points_in_poly(X, Z, outline_xz).astype(np.float64)
        u = self._solve(mask, cell)
        self.u = u
        self.umax = float(u.max())
        self.nx, self.nz = nx, nz

    @staticmethod
    def _solve(mask, h):
        def A(v):
            v = v * mask
            r = 4.0 * v - (np.roll(v, 1, 0) + np.roll(v, -1, 0) + np.roll(v, 1, 1) + np.roll(v, -1, 1))
            return r * mask / (h * h)

        b = mask.copy()
        x = np.zeros_like(b)
        r = b - A(x)
        p = r.copy()
        rs = float((r * r).sum())
        b2 = float((b * b).sum())
        for _ in range(6000):
            Ap = A(p)
            alpha = rs / float((p * Ap).sum())
            x += alpha * p
            r -= alpha * Ap
            rs_new = float((r * r).sum())
            if rs_new < 1e-20 * b2:
                break
            p = r + (rs_new / rs) * p
            rs = rs_new
        return x * mask

    def u_at(self, x, z):
        fx = (np.asarray(x) - self.x0) / self.cell
        fz = (np.asarray(z) - self.z0) / self.cell
        ix = np.clip(np.floor(fx).astype(int), 0, self.nx - 2)
        iz = np.clip(np.floor(fz).astype(int), 0, self.nz - 2)
        tx = np.clip(fx - ix, 0, 1)
        tz = np.clip(fz - iz, 0, 1)
        u = self.u
        return ((1 - tx) * (1 - tz) * u[iz, ix] + tx * (1 - tz) * u[iz, ix + 1]
                + (1 - tx) * tz * u[iz + 1, ix] + tx * tz * u[iz + 1, ix + 1])

    def h(self, x, z):
        return DEPTH * np.sqrt(np.maximum(self.u_at(x, z), 0.0) / self.umax)

    def grad(self, x, z, e=0.003):
        hx = (self.h(x + e, z) - self.h(x - e, z)) / (2 * e)
        hz = (self.h(x, z + e) - self.h(x, z - e)) / (2 * e)
        return hx, hz


def build_body_mesh(hf, outline_xz):
    verts2d, tris, boundary, _ = cdt_fill(outline_xz, spacing=0.006, margin=0.004)
    V = np.asarray(verts2d)
    H = hf.h(V[:, 0], V[:, 1])
    H[np.asarray(boundary)] = 0.0
    bm = bmesh.new()
    front = [bm.verts.new((x, -hh, z)) for (x, z), hh in zip(verts2d, H)]
    back = [front[k] if boundary[k] else bm.verts.new((x, hh, z))
            for k, ((x, z), hh) in enumerate(zip(verts2d, H))]
    for t in tris:
        try:
            bm.faces.new([front[k] for k in t])
        except ValueError:
            pass
        try:
            bm.faces.new([back[k] for k in reversed(t)])
        except ValueError:
            pass
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("body_src")
    bm.to_mesh(me)
    bm.free()
    src = new_object("body_src", me)

    # voxel remesh (fuses the rim into one clean closed surface) ...
    rm = src.modifiers.new("Remesh", "REMESH")
    rm.mode = "VOXEL"
    rm.voxel_size = 0.005
    rm.adaptivity = 0.0
    rm.use_smooth_shade = True
    me2 = evaluated_copy(src, "body_vox")
    bpy.data.objects.remove(src)
    ob = new_object("LG_Body", me2)

    # ... then collapse-decimate to a game budget. (Quadriflow would give
    # nicer quads but its manifold check rejects this mesh in 5.2 even though
    # every edge is 2-manifold and consistently wound.)
    tri_now = 2 * len(ob.data.polygons)
    dec = ob.modifiers.new("Decimate", "DECIMATE")
    dec.decimate_type = "COLLAPSE"
    dec.ratio = BODY_TRIS / tri_now
    dec.use_collapse_triangulate = True
    me3 = evaluated_copy(ob, "LG_Body")
    old = ob.data
    ob.modifiers.clear()
    ob.data = me3
    bpy.data.meshes.remove(old)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.beautify_fill(bm, faces=bm.faces, edges=bm.edges)
    for _ in range(2):
        bmesh.ops.smooth_vert(bm, verts=bm.verts, factor=0.3, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.materials.append(MATS["M_Body"])
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


# ----------------------------------------------------------------------------
# Eyes: raised glossy shells that hug the curved front
# ----------------------------------------------------------------------------
def build_eyes(hf):
    """Return (object, eye_centres) - one mesh, two closed shells."""
    bm = bmesh.new()
    centres = {}
    lifts = []
    for path in ART["eyes"]:
        outline = [svg_to_xz(p) for p in lg_svg.parse_path(path, step=1.0)[0]]
        verts2d, tris, boundary, rim = cdt_fill(outline, spacing=0.0075, margin=0.003)
        V = np.asarray(verts2d)
        side = "L" if V[:, 0].mean() > 0 else "R"
        d = dist_to_poly(V[:, 0], V[:, 1], rim)
        d[np.asarray(boundary)] = 0.0
        reach = 0.035
        dome = 1.0 - (1.0 - np.minimum(d / reach, 1.0)) ** 2  # 0 at rim -> 1 inside
        H = hf.h(V[:, 0], V[:, 1])
        hx, hz = hf.grad(V[:, 0], V[:, 1])
        n = np.stack([-hx, -np.ones_like(hx), -hz], axis=1)
        n /= np.linalg.norm(n, axis=1)[:, None]
        base = np.stack([V[:, 0], -H, V[:, 1]], axis=1)
        lift = 0.007 + 0.007 * dome
        lifts.append(lift)
        front = base + n * lift[:, None]
        backp = base - n * 0.008
        # relax the front sheet a little (removes height-field grid ripples)
        fv = [bm.verts.new(tuple(p)) for p in front]
        bv = [bm.verts.new(tuple(p)) for p in backp]
        faces = []
        for t in tris:
            faces.append(bm.faces.new([fv[k] for k in t]))
            bm.faces.new([bv[k] for k in reversed(t)]).smooth = False
        # rim wall: walk the boundary loop in order
        bidx = [k for k in range(len(V)) if boundary[k]]
        # order boundary verts along the rim polyline
        order = sorted(bidx, key=lambda k: _rim_param(rim, V[k]))
        for a, b in zip(order, order[1:] + order[:1]):
            f = bm.faces.new([fv[a], fv[b], bv[b], bv[a]])
            f.smooth = False
        inner = [fv[k] for k in range(len(V)) if not boundary[k]]
        for _ in range(4):
            bmesh.ops.smooth_vert(bm, verts=inner, factor=0.5, use_axis_x=False, use_axis_y=True, use_axis_z=False)
        for f in faces:
            f.smooth = True
        # blink pivot: centre of the eye's bounding box, on the body surface
        cx = 0.5 * float(V[:, 0].min() + V[:, 0].max())
        cz = 0.5 * float(V[:, 1].min() + V[:, 1].max())
        centres[side] = Vector((cx, -float(hf.h(np.array([cx]), np.array([cz]))[0]), cz))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = bm_to_object("LG_Eyes", bm, ["M_Eye"])
    return ob, centres


def _rim_param(rim, p):
    R = np.asarray(rim)
    k = int(np.argmin(np.hypot(R[:, 0] - p[0], R[:, 1] - p[1])))
    return k


# ----------------------------------------------------------------------------
# Rays: the three logo rays, extruded 6 cm with a round bevel
# ----------------------------------------------------------------------------
def build_rays():
    obs = []
    info = []
    for i, path in enumerate(ART["rays"], start=1):
        pts = [svg_to_xz(p) for p in lg_svg.parse_path(path, step=3.0, subdivide_lines=False)[0]]
        cu = bpy.data.curves.new("ray%d_curve" % i, "CURVE")
        cu.dimensions = "2D"
        cu.fill_mode = "BOTH"
        cu.extrude = 0.012
        cu.bevel_mode = "ROUND"
        cu.bevel_depth = 0.018
        cu.bevel_resolution = 2
        cu.offset = -0.018
        cu.resolution_u = 1
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for k, (x, z) in enumerate(pts):
            sp.points[k].co = (x, z, 0.0, 1.0)
        sp.use_cyclic_u = True
        tmp = new_object("ray%d_tmp" % i, cu)
        tmp.rotation_euler = (math.radians(90), 0, 0)  # local XY -> world XZ
        bpy.context.view_layer.update()
        me = evaluated_copy(tmp, "ray%d" % i)
        me.transform(tmp.matrix_world)
        bpy.data.objects.remove(tmp)
        bpy.data.curves.remove(cu)
        ob = new_object("ray%d" % i, me)
        ob.data.materials.append(MATS["M_Ray"])
        for p in ob.data.polygons:
            p.use_smooth = True
        obs.append(ob)
        # long axis for the bone chain
        P = np.asarray(pts)
        c = P.mean(axis=0)
        cov = np.cov((P - c).T)
        w, v = np.linalg.eigh(cov)
        ax = v[:, np.argmax(w)]
        proj = (P - c) @ ax
        head_c = np.array([0.15, 0.80])  # head centre in XZ (for outward orientation)
        if np.dot(ax, c - head_c) < 0:
            ax = -ax
            proj = -proj
        base = c + ax * proj.min()
        tip = c + ax * proj.max()
        info.append((Vector((base[0], 0.0, base[1])), Vector((tip[0], 0.0, tip[1]))))
    return obs, info


# ----------------------------------------------------------------------------
# Hands and feet
# ----------------------------------------------------------------------------
def build_hand(name, centre, r=0.11):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=r)
    bmesh.ops.translate(bm, verts=bm.verts, vec=centre)
    for f in bm.faces:
        f.smooth = True
    return bm_to_object(name, bm, ["M_Body"])


FOOT_HALF = (0.085, 0.13)  # half width (x), half length (y)
FOOT_TOP, FOOT_BOT = 0.078, 0.042  # heights above/below the foot centre


def build_foot(name, centre):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=1.0)
    for v in bm.verts:
        x, y, z = v.co
        if z >= 0:
            v.co = Vector((x * FOOT_HALF[0], y * FOOT_HALF[1], z * FOOT_TOP))
        else:
            # superellipse underside: flat sole, rounded rim
            r = min(1.0, math.hypot(x, y))
            zz = -((1.0 - r ** 4) ** 0.25)
            v.co = Vector((x * FOOT_HALF[0], y * FOOT_HALF[1], zz * FOOT_BOT))
    bmesh.ops.translate(bm, verts=bm.verts, vec=centre)
    for f in bm.faces:
        f.smooth = True
    return bm_to_object(name, bm, ["M_Foot"])


# ----------------------------------------------------------------------------
# Cape with a gold Dong Son star
# ----------------------------------------------------------------------------
# A small cape: ~58 % of the first version's width, hem at z ~0.38, so the lime
# body still dominates from the (usual) behind-the-hero camera.
CAPE_COL_SPACING = 0.115
CAPE_COLS = {"R": -CAPE_COL_SPACING, "M": 0.0, "L": CAPE_COL_SPACING}
CAPE_HALF_W = (0.19, 0.21)  # half width at the top edge, at the hem (flag-like, near-rectangular)


def cape_top(x):
    return 0.80 - 0.02 * (x / CAPE_HALF_W[0]) ** 2


def cape_bottom(x):
    # straight hem with a gentle flutter wave
    return 0.38 + 0.010 * math.sin(math.pi * x / CAPE_HALF_W[1])


def back_surface_y(body_bvh, x, z):
    hit = body_bvh.ray_cast(Vector((x, 3.0, z)), Vector((0, -1, 0)))
    return hit[0].y if hit[0] is not None else 0.0


class CapeShape:
    """Draped cape surface: follows the back, then hangs clear of the belly."""

    NU, NV = 13, 16

    def __init__(self, body_bvh):
        self.bvh = body_bvh

    def half_width(self, v):
        return CAPE_HALF_W[0] + (CAPE_HALF_W[1] - CAPE_HALF_W[0]) * v ** 1.2

    def point(self, u, v):
        """u in [-1, 1] across, v in [0, 1] down. Returns outer-surface point."""
        x = u * self.half_width(v)
        zt, zb = cape_top(x), cape_bottom(x)
        z = zt + (zb - zt) * v
        # drape: max of the back surface between the top edge and here
        ymax = -1.0
        for k in range(12):
            zz = zt + (z - zt) * k / 11.0
            ymax = max(ymax, back_surface_y(self.bvh, x, zz))
        gap = 0.002 + 0.028 * min(1.0, v / 0.35)
        flare = 0.035 * v * v
        y = ymax + gap + flare
        # slight wrap at the sides, and a soft flag ripple toward the hem
        y -= 0.03 * abs(u) ** 3 * (1.0 - v * 0.5)
        y += 0.012 * v ** 1.5 * math.sin(math.pi * 1.25 * u)
        return Vector((x, y, z))


def build_cape(body_ob):
    bm_body = bmesh.new()
    bm_body.from_mesh(body_ob.data)
    bvh = BVHTree.FromBMesh(bm_body)
    shape = CapeShape(bvh)
    NU, NV = shape.NU, shape.NV
    bm = bmesh.new()
    grid = []
    uv = []
    for j in range(NV + 1):
        v = j / NV
        row = []
        for i in range(NU + 1):
            u = -1.0 + 2.0 * i / NU
            row.append(bm.verts.new(shape.point(u, v)))
            uv.append((u, v))
        grid.append(row)
    for j in range(NV):
        for i in range(NU):
            # outer normal faces +Y (away from the body)
            bm.faces.new([grid[j][i], grid[j + 1][i], grid[j + 1][i + 1], grid[j][i + 1]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # make sure normals face +Y
    avg = sum((f.normal for f in bm.faces), Vector())
    if avg.y < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = True
    ob = bm_to_object("LG_Cape", bm, ["M_Cape", "M_FlagStar"])
    sol = ob.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness = 0.014
    sol.offset = -1.0
    sol.use_even_offset = True
    sol.use_rim = True
    me = evaluated_copy(ob, "LG_Cape")
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    bpy.data.meshes.remove(old)
    bm_body.free()

    # Vietnamese flag star: yellow, 5 points, pointing up, ~60 % of the cape height
    emb = build_flag_star(ob, centre=(0.0, 0.585), r_out=0.126)
    return ob, emb, shape


def star_outline(cx, cz, r_out, points=5, per_edge=6):
    """Regular star polygon (point up), each straight edge subdivided so the
    decal can hug the curved cape. Corners are kept exactly."""
    r_in = r_out * math.sin(math.radians(18)) / math.sin(math.radians(54))
    corners = []
    for k in range(2 * points):
        r = r_out if k % 2 == 0 else r_in
        a = math.pi / 2 + k * math.pi / points
        corners.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    out = []
    for k in range(len(corners)):
        a, b = corners[k], corners[(k + 1) % len(corners)]
        for i in range(per_edge):
            t = i / per_edge
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def build_flag_star(cape_ob, centre, r_out):
    """A flat, raised star decal: closed slab from 3.5 mm above the cape's
    outer surface to 4 mm below it (inside the 14 mm cloth), so it never z-fights."""
    bmc = bmesh.new()
    bmc.from_mesh(cape_ob.data)
    bvh = BVHTree.FromBMesh(bmc)

    def project(x, z, lift):
        hit = bvh.ray_cast(Vector((x, 3.0, z)), Vector((0, -1, 0)))
        loc, nor = hit[0], hit[1]
        if nor.y < 0:
            nor = -nor
        return loc + nor * lift

    outline = star_outline(centre[0], centre[1], r_out)
    nb = len(outline)
    # interior Steiner points (inside the star, away from the edges)
    sp = 0.012
    pts = []
    xs = np.arange(centre[0] - r_out, centre[0] + r_out, sp)
    zs = np.arange(centre[1] - r_out, centre[1] + r_out, sp)
    GX, GZ = np.meshgrid(xs, zs)
    GX, GZ = GX.ravel(), GZ.ravel()
    ins = points_in_poly(GX, GZ, outline)
    GX, GZ = GX[ins], GZ[ins]
    far = dist_to_poly(GX, GZ, outline) > sp * 0.45
    pts = [(float(x), float(z)) for x, z in zip(GX[far], GZ[far])]
    coords = [Vector(p) for p in outline] + [Vector(p) for p in pts]
    edges = [(k, (k + 1) % nb) for k in range(nb)]
    vo, _eo, fo, orig_v, _oe, _of = delaunay_2d_cdt(coords, edges, [list(range(nb))], 1, 1e-7)
    # map output verts back to boundary order for the side wall
    bpos = {}
    for i, ov in enumerate(orig_v):
        for o in ov:
            if o < nb:
                bpos[o] = i
    bm = bmesh.new()
    fv = [bm.verts.new(project(v.x, v.y, 0.0035)) for v in vo]
    bv = [bm.verts.new(project(v.x, v.y, -0.004)) for v in vo]
    for t in fo:
        bm.faces.new([fv[k] for k in t]).smooth = False
        bm.faces.new([bv[k] for k in reversed(t)]).smooth = False
    ring = [bpos[k] for k in range(nb)]
    for a, b in zip(ring, ring[1:] + ring[:1]):
        bm.faces.new([fv[a], bv[a], bv[b], fv[b]]).smooth = False
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmc.free()
    return bm_to_object("flag_star", bm, ["M_FlagStar"])


# ----------------------------------------------------------------------------
# Placement helpers
# ----------------------------------------------------------------------------
def body_bvh(body_ob):
    bm = bmesh.new()
    bm.from_mesh(body_ob.data)
    tree = BVHTree.FromBMesh(bm)
    bm.free()
    return tree


def place_hand(tree, side, r=0.11, z=0.45, y=-0.03, gap=0.035):
    """Start near x = +-0.60 and slide outward until the nub floats clear."""
    sg = 1.0 if side == "L" else -1.0
    x = 0.60
    while True:
        c = Vector((sg * x, y, z))
        loc, _n, _i, d = tree.find_nearest(c)
        inside = tree.ray_cast(c, Vector((0, 0, 1)))[0] is not None and \
            tree.ray_cast(c, Vector((0, 0, -1)))[0] is not None and abs(c.x) < 0.5
        if d is not None and d >= r + gap and not inside:
            return c
        x += 0.005


# ----------------------------------------------------------------------------
# Armature
# ----------------------------------------------------------------------------
BONES_DEFORM_FALSE = {"root", "ray.1.tip", "ray.2.tip", "ray.3.tip"}


def build_armature(eye_c, ray_info, hand_c, foot_c, cape_shape):
    arm_data = bpy.data.armatures.new("Armature")
    arm = bpy.data.objects.new("Armature", arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    for o in bpy.context.scene.objects:
        o.select_set(o == arm)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_data.edit_bones

    def bone(name, head, tail, parent=None, connect=False):
        b = eb.new(name)
        b.head = Vector(head)
        b.tail = Vector(tail)
        b.roll = 0.0
        if parent:
            b.parent = eb[parent]
            b.use_connect = connect
        b.use_deform = name not in BONES_DEFORM_FALSE
        return b

    bone("root", (0, 0, 0), (0, 0, 0.12))
    bone("hips", (0, 0, 0.25), (0, 0, 0.55), "root")
    bone("spine", (0, 0, 0.55), (0, 0, 0.85), "hips", True)
    bone("head", (0, 0, 0.85), (0, 0, 1.15), "spine", True)
    for side in ("L", "R"):
        c = eye_c[side]
        bone("eye." + side, c, c + Vector((0, 0, 0.08)), "head")
    for i, (base, tip) in enumerate(ray_info, start=1):
        mid = base.lerp(tip, 0.62)
        bone("ray.%d" % i, base, mid, "head")
        bone("ray.%d.tip" % i, mid, tip, "ray.%d" % i, True)
    for side in ("L", "R"):
        c = hand_c[side]
        bone("hand." + side, c, c + Vector((0, 0, 0.10)), "spine")
    for col, x in CAPE_COLS.items():
        prev = "spine"
        for r in range(3):
            v0, v1 = r / 3.0, (r + 1) / 3.0
            h = cape_point_x(cape_shape, x, v0) + Vector((0, -0.007, 0))
            t = cape_point_x(cape_shape, x, v1) + Vector((0, -0.007, 0))
            name = "cape.%s.%d" % (col, r + 1)
            bone(name, h, t, prev, r > 0)
            prev = name
    for side in ("L", "R"):
        c = foot_c[side]
        bone("foot." + side, c, c + Vector((0, 0, 0.08)), "root")
    bpy.ops.object.mode_set(mode="OBJECT")
    arm_data.display_type = "STICK"
    return arm


def cape_point_x(shape, x, v):
    return shape.point(x / shape.half_width(v), v)


# ----------------------------------------------------------------------------
# Skin weights
# ----------------------------------------------------------------------------
def smoothstep(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def vg(ob, name):
    return ob.vertex_groups.get(name) or ob.vertex_groups.new(name=name)


def weight_body(ob, head_full_z):
    """Height blend hips -> spine -> head. The face (both eyes) is 100% head,
    so the rigid eye shells can never drift off the surface."""
    g = {n: vg(ob, n) for n in ("hips", "spine", "head")}
    hz0 = head_full_z - 0.18
    for v in ob.data.vertices:
        z = v.co.z
        a = smoothstep(0.12, 0.36, z)
        b = smoothstep(hz0, head_full_z, z)
        w = {"hips": 1 - a, "spine": a * (1 - b), "head": a * b}
        for n, x in w.items():
            if x > 1e-4:
                g[n].add([v.index], x, "REPLACE")


def weight_all(ob, bone):
    g = vg(ob, bone)
    g.add([v.index for v in ob.data.vertices], 1.0, "REPLACE")


def weight_cape(ob, shape):
    groups = {}

    def G(n):
        if n not in groups:
            groups[n] = vg(ob, n)
        return groups[n]

    for v in ob.data.vertices:
        x, z = v.co.x, v.co.z
        # recover (u, v) of the drape parameterisation
        zt, zb = cape_top(x), cape_bottom(x)
        vv = min(1.0, max(0.0, (zt - z) / (zt - zb)))
        # columns: smooth hats at the three column x's (outer columns own the edges)
        xs = sorted(CAPE_COLS.items(), key=lambda kv: kv[1])
        cw = {}
        for col, xc in xs:
            t = max(0.0, 1.0 - abs(x - xc) / CAPE_COL_SPACING)
            cw[col] = t * t * (3 - 2 * t)
        if x <= xs[0][1]:
            cw = {c: (1.0 if c == xs[0][0] else 0.0) for c, _ in xs}
        if x >= xs[-1][1]:
            cw = {c: (1.0 if c == xs[-1][0] else 0.0) for c, _ in xs}
        tot = sum(cw.values())
        cw = {c: w / tot for c, w in cw.items()}
        # rows: hats centred on each bone, clamped at the ends
        rw = []
        for r in range(3):
            m = (r + 0.5) / 3.0
            t = max(0.0, 1.0 - abs(vv - m) * 3.0)
            rw.append(t)
        if vv <= 0.5 / 3.0:
            rw = [1.0, 0.0, 0.0]
        if vv >= 2.5 / 3.0:
            rw = [0.0, 0.0, 1.0]
        tot = sum(rw)
        rw = [w / tot for w in rw]
        top = 1.0 - smoothstep(0.0, 0.14, vv)  # sewn to the back: follows the spine
        G("spine").add([v.index], max(top, 1e-4), "REPLACE")
        for col, wc in cw.items():
            for r in range(3):
                w = (1 - top) * wc * rw[r]
                if w > 1e-4:
                    G("cape.%s.%d" % (col, r + 1)).add([v.index], w, "REPLACE")


def copy_weights_nearest(dst, src):
    """Give each vertex of `dst` the weights of the nearest vertex of `src`."""
    kd = KDTree(len(src.data.vertices))
    for v in src.data.vertices:
        kd.insert(v.co, v.index)
    kd.balance()
    names = {g.index: g.name for g in src.vertex_groups}
    for v in dst.data.vertices:
        _co, idx, _d = kd.find(v.co)
        for ge in src.data.vertices[idx].groups:
            vg(dst, names[ge.group]).add([v.index], ge.weight, "REPLACE")


def join(objs, name):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.data.name = name
    return ob


def skin(ob, arm):
    ob.parent = arm
    m = ob.modifiers.new("Armature", "ARMATURE")
    m.object = arm
    m.use_vertex_groups = True


# ----------------------------------------------------------------------------
# Export
# ----------------------------------------------------------------------------
def export_glb(arm):
    os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
    arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
        pb.scale = (1, 1, 1)
    bpy.context.scene.frame_set(0)
    bpy.ops.export_scene.gltf(
        filepath=GLB_PATH,
        export_format="GLB",
        use_selection=False,
        export_yup=True,
        export_apply=True,
        export_texcoords=False,
        export_normals=True,
        export_materials="EXPORT",
        export_cameras=False,
        export_lights=False,
        export_skins=True,
        export_all_influences=False,
        export_influence_nb=4,
        # every bone is exported: root and the ray tips are non-deform in Blender
        # (no weights) but are part of the contract (spring-bone chain ends)
        export_def_bones=False,
        export_leaf_bone=False,
        export_rest_position_armature=True,
        export_animations=True,
        export_animation_mode="ACTIONS",
        export_force_sampling=True,
        export_frame_step=1,
        export_anim_slide_to_zero=False,
        export_optimize_animation_size=True,
        export_optimize_animation_keep_anim_armature=True,
        export_reset_pose_bones=True,
        export_morph=False,
        export_extras=False,
    )


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    sys.path.insert(0, HERE)
    import mascot_anims

    reset_scene()
    build_materials()
    outline = [svg_to_xz(p) for p in BODY_SVG]
    hf = HeightField(outline)
    body = build_body_mesh(hf, outline)
    tree = body_bvh(body)
    eyes, eye_c = build_eyes(hf)
    rays, ray_info = build_rays()

    hand_c = {s: place_hand(tree, s) for s in ("L", "R")}
    hands = {s: build_hand("hand_" + s, hand_c[s]) for s in ("L", "R")}
    foot_c = {"L": Vector((0.22, -0.03, FOOT_BOT)), "R": Vector((-0.22, -0.03, FOOT_BOT))}
    feet = {s: build_foot("foot_" + s, foot_c[s]) for s in ("L", "R")}
    cape, flag_star, cape_shape = build_cape(body)

    # --- weights (before joining; groups merge by name) ---
    eye_min_z = min(v.co.z for v in eyes.data.vertices)
    weight_body(body, head_full_z=eye_min_z - 0.01)
    for s in ("L", "R"):
        weight_all(hands[s], "hand." + s)
        weight_all(feet[s], "foot." + s)
    ge = {s: vg(eyes, "eye." + s) for s in ("L", "R")}
    for v in eyes.data.vertices:
        ge["L" if v.co.x > 0 else "R"].add([v.index], 1.0, "REPLACE")
    for i, r in enumerate(rays, start=1):
        weight_all(r, "ray.%d" % i)
    weight_cape(cape, cape_shape)
    copy_weights_nearest(flag_star, cape)

    body = join([body, hands["L"], hands["R"], feet["L"], feet["R"]], "LG_Body")
    rays_ob = join(rays, "LG_Rays")
    cape = join([cape, flag_star], "LG_Cape")

    arm = build_armature(eye_c, ray_info, hand_c, foot_c, cape_shape)
    for ob in (body, eyes, rays_ob, cape):
        skin(ob, arm)

    rest_feet = {s: foot_c[s].copy() for s in ("L", "R")}
    actions = mascot_anims.build_all(arm, rest_feet)
    arm.animation_data.action = bpy.data.actions["idle"]
    arm.animation_data.action_slot = bpy.data.actions["idle"].slots[0]
    bpy.context.scene.frame_end = 60

    # --- report ---
    tris = 0
    for ob in (body, eyes, rays_ob, cape):
        ob.data.calc_loop_triangles()
        n = len(ob.data.loop_triangles)
        tris += n
        print("MESH %-8s tris %6d  groups %s" % (ob.name, n, sorted(g.name for g in ob.vertex_groups)))
    print("TOTAL TRIS", tris)
    print("HANDS", {k: tuple(round(c, 3) for c in v) for k, v in hand_c.items()})
    print("EYE MIN Z", round(eye_min_z, 3))
    for b in arm.data.bones:
        print("BONE %-10s head %s tail %s deform %s parent %s" % (
            b.name, tuple(round(c, 3) for c in b.head_local), tuple(round(c, 3) for c in b.tail_local),
            b.use_deform, b.parent.name if b.parent else None))
    for a in actions:
        print("ACTION %-18s frames %s cyclic %s" % (a.name, tuple(a.frame_range), a.use_cyclic))

    bpy.context.preferences.filepaths.save_version = 0  # no .blend1 backups
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    export_glb(arm)
    arm.animation_data.action = bpy.data.actions["idle"]
    print("WROTE", BLEND_PATH, GLB_PATH)


if __name__ == "__main__":
    main()
