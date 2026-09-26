"""Shared helpers for the Little Giant 64 prop builder.

Everything is built procedurally from bmesh. A prop is a list of `Part`s; each part owns one
material, an optional bevel and a smoothing angle. `Prop.finish()` evaluates every part (bevel /
boolean modifiers), marks sharp edges by angle, then concatenates the parts into one mesh object
whose material slots are the union of the part materials.

Conventions (docs/DESIGN.md): metres, Blender Z-up, the prop's front faces -Y, origin at the
centre of the base (z = 0 is the ground contact).
"""

import math
import re

import bmesh
import bpy
from mathutils import Matrix, Vector, Euler

TAU = math.tau

# --------------------------------------------------------------------------------------------
# Palette. sRGB hex, roughness, metallic. Materials are named by role (Godot keeps the colours).
# --------------------------------------------------------------------------------------------
PALETTE = {
    "M_Gold":        ("#F7BC2F", 0.28, 0.35),
    "M_GoldLight":   ("#FFDC6A", 0.25, 0.30),
    "M_Bronze":      ("#C98237", 0.32, 0.35),
    "M_BronzeLight": ("#E3A35A", 0.30, 0.30),
    "M_BronzeDark":  ("#7C4A25", 0.50, 0.30),
    "M_Patina":      ("#4FAE93", 0.45, 0.10),
    "M_Leaf":        ("#5BC24A", 0.45, 0.0),
    "M_LeafLight":   ("#A3E25A", 0.45, 0.0),
    "M_LeafDark":    ("#2E8B3F", 0.50, 0.0),
    "M_Lotus":       ("#48B86A", 0.35, 0.0),
    "M_Wood":        ("#A0612F", 0.55, 0.0),
    "M_WoodLight":   ("#D39A5B", 0.55, 0.0),
    "M_WoodDark":    ("#62381D", 0.60, 0.0),
    "M_Bamboo":      ("#8CCB3C", 0.35, 0.0),
    "M_BambooLight": ("#B9E35C", 0.35, 0.0),
    "M_BambooDark":  ("#4E8F2A", 0.45, 0.0),
    "M_BambooDry":   ("#E3C872", 0.55, 0.0),
    "M_Red":         ("#E0452B", 0.35, 0.0),
    "M_RedDark":     ("#9E2A1E", 0.45, 0.0),
    "M_Orange":      ("#FF8A2B", 0.35, 0.0),
    "M_Stone":       ("#9AA8BC", 0.70, 0.0),
    "M_StoneLight":  ("#C9D1DD", 0.70, 0.0),
    "M_StoneDark":   ("#66758C", 0.75, 0.0),
    "M_White":       ("#F8F6EF", 0.35, 0.0),
    "M_Black":       ("#1B1B22", 0.20, 0.0),
    "M_Terracotta":  ("#D2683A", 0.60, 0.0),
    "M_TerracottaDark": ("#B9532E", 0.60, 0.0),
    "M_Mortar":      ("#EED9B4", 0.80, 0.0),
    "M_Water":       ("#46C2EA", 0.10, 0.0),
    "M_Pink":        ("#F27DAE", 0.40, 0.0),
    "M_PinkLight":   ("#FFC8DD", 0.40, 0.0),
    "M_Yellow":      ("#FFD23F", 0.40, 0.0),
    "M_Lime":        ("#D5F64B", 0.45, 0.0),
    "M_EyeGreen":    ("#234D37", 0.40, 0.0),
    "M_Roof":        ("#B14E34", 0.50, 0.0),
    "M_RoofDark":    ("#7E3325", 0.55, 0.0),
    "M_Jelly":       ("#86D46A", 0.18, 0.0),
    "M_JellyDark":   ("#4FA650", 0.25, 0.0),
    "M_String":      ("#EEDB9A", 0.60, 0.0),
    "M_Shell":       ("#F2553A", 0.30, 0.0),
    "M_ShellLight":  ("#FFB38A", 0.40, 0.0),
    "M_Cloud":       ("#FFFFFF", 0.60, 0.0),
    "M_Coconut":     ("#7A5230", 0.55, 0.0),
}


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_to_linear(h):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))


def material(name):
    """Get or create a role material (Principled BSDF base colour + roughness)."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    hexcol, rough, metal = PALETTE[name]
    lin = hex_to_linear(hexcol)
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*lin, 1.0)  # workbench / viewport
    m.roughness = rough
    m.metallic = metal
    m.use_backface_culling = True  # every prop is a closed shell; exported as single-sided
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*lin, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    # A touch of coat makes the toy gloss read in the contact-sheet renders (not exported).
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.25 if rough < 0.45 else 0.0
    return m


# --------------------------------------------------------------------------------------------
# Matrices and small maths
# --------------------------------------------------------------------------------------------
def mat4(loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    """Matrix from location, Euler XYZ in DEGREES and scale (scalar or 3-tuple)."""
    if isinstance(scale, (int, float)):
        scale = (scale, scale, scale)
    r = Euler(tuple(math.radians(a) for a in rot), "XYZ").to_matrix().to_4x4()
    s = Matrix.Diagonal((*scale, 1.0))
    return Matrix.Translation(Vector(loc)) @ r @ s


def look_matrix(origin, direction, up=(0, 0, 1)):
    """Matrix whose local +Z points along `direction` (used to orient tubes/primitives)."""
    d = Vector(direction).normalized()
    u = Vector(up)
    if abs(d.dot(u)) > 0.999:
        u = Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((1, 0, 0))
    x = u.cross(d).normalized()
    y = d.cross(x).normalized()
    m = Matrix((x, y, d)).transposed().to_4x4()
    m.translation = Vector(origin)
    return m


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def rng(seed):
    """Tiny deterministic LCG so every rebuild is identical."""
    state = [seed * 2654435761 % 4294967296 or 1]

    def r(a=0.0, b=1.0):
        state[0] = (1664525 * state[0] + 1013904223) % 4294967296
        return a + (b - a) * state[0] / 4294967296.0

    return r


def star_points(n, r_out, r_in, rot=90.0):
    """2D star outline (CCW), 2n points, first tip at angle `rot` degrees."""
    pts = []
    for i in range(2 * n):
        a = math.radians(rot) + i * math.pi / n
        r = r_out if i % 2 == 0 else r_in
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def circle_points(n, r, rot=0.0):
    return [(r * math.cos(math.radians(rot) + TAU * i / n), r * math.sin(math.radians(rot) + TAU * i / n))
            for i in range(n)]


def rounded_rect_points(w, h, r, seg=4):
    """CCW rounded rectangle centred at origin."""
    pts = []
    corners = [(w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180),
               (w / 2 - r, -h / 2 + r, 270)]
    for cx, cy, a0 in corners:
        for k in range(seg + 1):
            a = math.radians(a0 + 90 * k / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def signed_area(pts):
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                     for i in range(len(pts)))


def svg_path_points(d, samples=6, scale=1.0, offset=(0.0, 0.0), flip_y=True):
    """Parse an SVG path made of M/L/Q/Z (absolute) into a list of 2D points."""
    toks = re.findall(r"[MLQZmlqz]|-?\d*\.?\d+", d)
    pts, i, cur, cmd = [], 0, (0.0, 0.0), None
    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd = t.upper()
            i += 1
            if cmd == "Z":
                continue
        if cmd in ("M", "L"):
            cur = (float(toks[i]), float(toks[i + 1]))
            pts.append(cur)
            i += 2
        elif cmd == "Q":
            c = (float(toks[i]), float(toks[i + 1]))
            e = (float(toks[i + 2]), float(toks[i + 3]))
            for k in range(1, samples + 1):
                s = k / samples
                x = (1 - s) ** 2 * cur[0] + 2 * (1 - s) * s * c[0] + s * s * e[0]
                y = (1 - s) ** 2 * cur[1] + 2 * (1 - s) * s * c[1] + s * s * e[1]
                pts.append((x, y))
            cur = e
            i += 4
        else:
            i += 1
    # drop duplicates
    out = []
    for p in pts:
        if not out or (abs(p[0] - out[-1][0]) > 1e-6 or abs(p[1] - out[-1][1]) > 1e-6):
            out.append(p)
    if len(out) > 2 and abs(out[0][0] - out[-1][0]) < 1e-6 and abs(out[0][1] - out[-1][1]) < 1e-6:
        out.pop()
    sy = -1.0 if flip_y else 1.0
    return [((x - offset[0]) * scale, sy * (y - offset[1]) * scale) for x, y in out]


def simplify_points(pts, min_dist):
    out = [pts[0]]
    for p in pts[1:]:
        if math.dist(p, out[-1]) >= min_dist:
            out.append(p)
    if len(out) > 3 and math.dist(out[0], out[-1]) < min_dist:
        out.pop()
    return out


def bezier(p0, p1, p2, p3, n):
    """Cubic bezier sampled into n+1 Vectors."""
    p0, p1, p2, p3 = map(Vector, (p0, p1, p2, p3))
    out = []
    for i in range(n + 1):
        t = i / n
        out.append((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3)
    return out


# --------------------------------------------------------------------------------------------
# Part: one material worth of geometry
# --------------------------------------------------------------------------------------------
class Part:
    def __init__(self, mat, smooth=40.0, bevel=None, name="part"):
        """smooth: auto-smooth angle in degrees (None = flat shaded, 180 = fully smooth).
        bevel: (width, segments) or (width, segments, angle_deg) applied as a modifier."""
        self.bm = bmesh.new()
        self.mat = mat
        self.smooth = smooth
        self.bevel = bevel
        self.name = name
        self.cutters = []  # Parts subtracted with an exact boolean (after bevel)
        self.mods = []     # extra modifiers: (type, {prop: value}) applied after bevel/booleans
        self.group = None  # vertex group (bone) this part is rigidly skinned to
        self.weights = {}  # vertex group name -> list of vertex indices (used by rigs)

    # -- low level ---------------------------------------------------------------------------
    def _v(self, co):
        return self.bm.verts.new(co)

    def face(self, verts):
        try:
            return self.bm.faces.new(verts)
        except ValueError:
            return None

    def transform_new(self, verts, m):
        bmesh.ops.transform(self.bm, matrix=m, verts=list(verts))

    # -- primitives ----------------------------------------------------------------------------
    def cube(self, size=(1, 1, 1), m=Matrix()):
        if isinstance(size, (int, float)):
            size = (size, size, size)
        r = bmesh.ops.create_cube(self.bm, size=1.0, matrix=m @ Matrix.Diagonal((*size, 1)))
        return r["verts"]

    def box(self, lo, hi, m=Matrix()):
        c = [(lo[i] + hi[i]) / 2 for i in range(3)]
        s = [hi[i] - lo[i] for i in range(3)]
        return self.cube(s, m @ Matrix.Translation(c))

    def cylinder(self, r, h, segs=16, m=Matrix(), r2=None, caps=True):
        """Cylinder/cone with its base at local z=0, height h along +Z."""
        r2 = r if r2 is None else r2
        return self.lathe([(r, 0), (r2, h)], segs, m, cap0=caps, cap1=caps)

    def sphere(self, r, m=Matrix(), segs=16, rings=8, scale=(1, 1, 1)):
        res = bmesh.ops.create_uvsphere(self.bm, u_segments=segs, v_segments=rings, radius=r,
                                        matrix=m @ Matrix.Diagonal((*scale, 1)))
        return res["verts"]

    def ico(self, r, m=Matrix(), subdiv=2, scale=(1, 1, 1)):
        res = bmesh.ops.create_icosphere(self.bm, subdivisions=subdiv, radius=r,
                                         matrix=m @ Matrix.Diagonal((*scale, 1)))
        return res["verts"]

    # -- surfaces of revolution / lofts ------------------------------------------------------
    def loft(self, rings, closed_rings=True, closed_loft=False, cap0=False, cap1=False):
        """Connect a list of rings (each a list of 3D points, equal lengths).
        Faces are wound (a, b, c, d) = (ring k j, ring k j+1, ring k+1 j+1, ring k+1 j)."""
        vrings = []
        for ring in rings:
            if len(ring) == 1:
                vrings.append([self._v(ring[0])])
            else:
                vrings.append([self._v(p) for p in ring])
        n = max(len(r) for r in vrings)
        jmax = n if closed_rings else n - 1
        pairs = list(zip(range(len(vrings) - 1), range(1, len(vrings))))
        if closed_loft:
            pairs.append((len(vrings) - 1, 0))
        faces = []
        for k0, k1 in pairs:
            ra, rb = vrings[k0], vrings[k1]
            for j in range(jmax):
                j1 = (j + 1) % n
                if len(ra) == 1:
                    f = self.face([ra[0], rb[j1], rb[j]])
                elif len(rb) == 1:
                    f = self.face([ra[j], ra[j1], rb[0]])
                else:
                    f = self.face([ra[j], ra[j1], rb[j1], rb[j]])
                if f:
                    faces.append(f)
        if cap0 and len(vrings[0]) > 2:
            f = self.face(list(reversed(vrings[0])))
            if f:
                faces.append(f)
        if cap1 and len(vrings[-1]) > 2:
            f = self.face(vrings[-1])
            if f:
                faces.append(f)
        return vrings, faces

    def lathe(self, profile, segs=24, m=Matrix(), cap0=None, cap1=None, shape=None, phase=0.0,
              closed=False):
        """Revolve a profile [(r, z), ...] around local Z.

        Traverse the profile so that the outside of the surface is on the RIGHT of the direction
        of travel in the (r, z) plane (bottom->top for an outer wall).
        shape(theta, ring_index) -> radial factor lets rings become squares, ribs, stars...
        cap0/cap1 default to True when the end ring has r > 0 (flat n-gon caps).
        """
        rings = []
        for k, (r, z) in enumerate(profile):
            if r < 1e-7:
                rings.append([m @ Vector((0, 0, z))])
                continue
            ring = []
            for j in range(segs):
                th = phase + TAU * j / segs
                f = shape(th, k) if shape else 1.0
                ring.append(m @ Vector((r * f * math.cos(th), r * f * math.sin(th), z)))
            rings.append(ring)
        if cap0 is None:
            cap0 = profile[0][0] > 1e-7 and not closed
        if cap1 is None:
            cap1 = profile[-1][0] > 1e-7 and not closed
        # cap orientation: loft caps assume ring0 is the "bottom" (normal -Z)
        return self.loft(rings, closed_rings=True, closed_loft=closed, cap0=cap0, cap1=cap1)

    def tube(self, path, radius, sides=8, caps=True, up=(0, 0, 1), section=None, twist=0.0,
             closed=False):
        """Sweep a circle (or `section` 2D points, CCW) along a polyline with parallel-transport
        frames. radius: float or list (one per path point) or callable(t).
        closed=True joins the last ring back to the first (path must not repeat its start)."""
        path = [Vector(p) for p in path]
        n = len(path)
        tangents = []
        for i in range(n):
            if closed:
                t = path[(i + 1) % n] - path[i - 1]
            elif i == 0:
                t = path[1] - path[0]
            elif i == n - 1:
                t = path[-1] - path[-2]
            else:
                t = (path[i + 1] - path[i - 1])
            tangents.append(t.normalized())
        # initial normal
        u = Vector(up)
        if abs(tangents[0].dot(u)) > 0.99:
            u = Vector((1, 0, 0))
        nrm = (u - tangents[0] * u.dot(tangents[0])).normalized()
        frames = []
        for i in range(n):
            if i > 0:
                q = tangents[i - 1].rotation_difference(tangents[i])
                nrm = q @ nrm
                nrm = (nrm - tangents[i] * nrm.dot(tangents[i])).normalized()
            b = tangents[i].cross(nrm)
            frames.append((nrm, b))
        rings = []
        for i in range(n):
            t = i / (n - 1)
            r = radius(t) if callable(radius) else (radius[i] if isinstance(radius, (list, tuple)) else radius)
            nrm, b = frames[i]
            if r < 1e-7:
                rings.append([path[i]])
                continue
            ring = []
            sec = section or [(math.cos(TAU * j / sides), math.sin(TAU * j / sides)) for j in range(sides)]
            tw = twist * t
            for (sx, sy) in sec:
                cx = sx * math.cos(tw) - sy * math.sin(tw)
                cy = sx * math.sin(tw) + sy * math.cos(tw)
                # (nrm, b) ordering is CCW around the tangent -> outward faces with loft
                ring.append(path[i] + (nrm * cx + b * cy) * r)
            rings.append(ring)
        if closed:
            return self.loft(rings, closed_rings=True, closed_loft=True)
        return self.loft(rings, closed_rings=True, cap0=caps, cap1=caps)

    def extrude_poly(self, pts2d, z0, z1, m=Matrix()):
        """Prism from a simple 2D polygon (XY plane), between local z0 and z1."""
        pts = list(pts2d)
        if signed_area(pts) < 0:
            pts.reverse()
        bot = [self._v(m @ Vector((x, y, z0))) for x, y in pts]
        top = [self._v(m @ Vector((x, y, z1))) for x, y in pts]
        n = len(pts)
        self.face(list(reversed(bot)))
        self.face(top)
        for i in range(n):
            j = (i + 1) % n
            self.face([bot[i], bot[j], top[j], top[i]])
        return bot + top

    def extrude_poly_tapered(self, pts2d, z0, z1, inset, m=Matrix()):
        """Prism whose top face is shrunk by `inset` (scale about the centroid) – embossed look."""
        pts = list(pts2d)
        if signed_area(pts) < 0:
            pts.reverse()
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        bot = [self._v(m @ Vector((x, y, z0))) for x, y in pts]
        top = [self._v(m @ Vector((cx + (x - cx) * inset, cy + (y - cy) * inset, z1))) for x, y in pts]
        n = len(pts)
        self.face(list(reversed(bot)))
        self.face(top)
        for i in range(n):
            j = (i + 1) % n
            self.face([bot[i], bot[j], top[j], top[i]])
        return bot + top

    def faceted_star(self, n, r_out, r_in, h_center, h_edge, m=Matrix(), rot=90.0, back=True):
        """Crystal star: ridges run from a raised centre to every tip (both sides if back)."""
        pts = star_points(n, r_out, r_in, rot)
        top_c = self._v(m @ Vector((0, 0, h_center)))
        top = [self._v(m @ Vector((x, y, h_edge))) for x, y in pts]
        bot = [self._v(m @ Vector((x, y, -h_edge))) for x, y in pts]
        bot_c = self._v(m @ Vector((0, 0, -h_center))) if back else None
        k = len(pts)
        for i in range(k):
            j = (i + 1) % k
            self.face([top_c, top[i], top[j]])
            self.face([bot[i], bot[j], top[j], top[i]])
            if back:
                self.face([bot_c, bot[j], bot[i]])
        if not back:
            self.face(list(reversed(bot)))
        return top + bot

    def rounded_box(self, half, r, n=6, m=Matrix()):
        """Box with evenly rounded edges/corners: an n x n grid per face projected onto the
        rounded-box surface (half = half extents, r = corner radius)."""
        half = Vector(half)
        inner = Vector([h - r for h in half])
        X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
        faces_def = [(Z, X, Y), (-Z, Y, X), (X, Y, Z), (-X, Z, Y), (Y, Z, X), (-Y, X, Z)]
        for N, A, B in faces_def:
            grid = []
            for i in range(n + 1):
                row = []
                for j in range(n + 1):
                    u = -1 + 2 * i / n
                    w = -1 + 2 * j / n
                    p = N + A * u + B * w
                    q = Vector((p.x * half.x, p.y * half.y, p.z * half.z))
                    c = Vector((max(-inner.x, min(inner.x, q.x)), max(-inner.y, min(inner.y, q.y)),
                                max(-inner.z, min(inner.z, q.z))))
                    d = q - c
                    q2 = c + d.normalized() * r if d.length > 1e-9 else q
                    row.append(self._v(m @ q2))
                grid.append(row)
            for i in range(n):
                for j in range(n):
                    self.face([grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]])

    def leaf(self, base, direction, length, width, up=(0, 0, 1), droop=0.3, fold=0.3, steps=6,
             thick=0.012, serrate=0.0, width_fn=None, curl=0.0):
        """A closed lens-section leaf blade grown from `base` along `direction`.
        droop bends the blade down (fraction of length, negative curls up); fold lowers the
        edges (V section, negative cups them up); serrate notches every other step."""
        base = Vector(base)
        d = Vector(direction).normalized()
        upv = Vector(up)
        lat = d.cross(upv)
        if lat.length < 1e-6:
            lat = d.cross(Vector((1, 0, 0)))
        lat.normalize()
        nrm = lat.cross(d).normalized()
        rings = []
        pts = []
        for i in range(steps + 1):
            t = i / steps
            p = base + d * length * t - nrm * droop * length * t * t + nrm * curl * length * t ** 3
            pts.append(p)
        for i in range(steps + 1):
            t = i / steps
            p = pts[i]
            if i == 0 or i == steps:
                rings.append([p])
                continue
            tang = (pts[min(i + 1, steps)] - pts[i - 1]).normalized()
            la = tang.cross(nrm).normalized()
            la = lat if la.length < 1e-6 else la
            nn = la.cross(tang).normalized()
            w = (width_fn(t) if width_fn else math.sin(math.pi * min(1.0, t * 1.15)) ** 0.8) * width / 2
            if serrate and i % 2 == 0:
                w *= (1 - serrate)
            edge_drop = nn * (-fold * w)
            rings.append([p + la * w + edge_drop, p - nn * thick, p - la * w + edge_drop, p + nn * thick])
        self.loft(rings, closed_rings=True)
        return pts

    def merge_part(self, other, m=Matrix()):
        me = bpy.data.meshes.new("tmp")
        other.bm.to_mesh(me)
        me.transform(m)
        self.bm.from_mesh(me)
        bpy.data.meshes.remove(me)

    def recalc_normals(self):
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces[:])

    def flip(self):
        bmesh.ops.reverse_faces(self.bm, faces=self.bm.faces[:])

    def deform(self, fn):
        """fn(Vector) -> Vector applied to every vertex."""
        for v in self.bm.verts:
            v.co = fn(v.co.copy())

    # -- evaluation --------------------------------------------------------------------------
    def to_mesh(self):
        """Return a new bpy Mesh with modifiers applied and sharp edges marked."""
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts[:], dist=1e-6)
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        needs_eval = self.bevel or self.cutters or self.mods
        if needs_eval:
            obj = bpy.data.objects.new(self.name, me)
            bpy.context.scene.collection.objects.link(obj)
            if self.bevel:
                w, segs = self.bevel[0], self.bevel[1]
                ang = self.bevel[2] if len(self.bevel) > 2 else 30.0
                mod = obj.modifiers.new("bevel", "BEVEL")
                mod.width = w
                mod.segments = segs
                mod.limit_method = "ANGLE"
                mod.angle_limit = math.radians(ang)
                mod.use_clamp_overlap = True
                mod.miter_outer = "MITER_ARC"
            cutter_objs = []
            for c in self.cutters:
                cme = c.to_mesh()
                cobj = bpy.data.objects.new("cut", cme)
                bpy.context.scene.collection.objects.link(cobj)
                cutter_objs.append(cobj)
                mod = obj.modifiers.new("bool", "BOOLEAN")
                mod.operation = "DIFFERENCE"
                mod.solver = "EXACT"
                mod.object = cobj
            for mtype, props in self.mods:
                mod = obj.modifiers.new(mtype.lower(), mtype)
                for k, v in props.items():
                    setattr(mod, k, v)
            dg = bpy.context.evaluated_depsgraph_get()
            dg.update()
            ev = obj.evaluated_get(dg)
            me2 = bpy.data.meshes.new_from_object(ev)
            bpy.data.objects.remove(obj)
            bpy.data.meshes.remove(me)
            for cobj in cutter_objs:
                cm = cobj.data
                bpy.data.objects.remove(cobj)
                bpy.data.meshes.remove(cm)
            me = me2
        # smoothing
        bm = bmesh.new()
        bm.from_mesh(me)
        if self.smooth is None:
            for f in bm.faces:
                f.smooth = False
        else:
            thr = math.radians(self.smooth)
            for f in bm.faces:
                f.smooth = True
            for e in bm.edges:
                if not e.is_manifold:
                    continue
                if e.calc_face_angle(0.0) > thr:
                    e.smooth = False
        bm.to_mesh(me)
        bm.free()
        return me


# --------------------------------------------------------------------------------------------
# Prop assembly
# --------------------------------------------------------------------------------------------
REGISTRY = []  # (name, collection) in build order
DEBUG_TRIS = bool(__import__("os").environ.get("PROPS_DEBUG_TRIS"))


def join_parts(name, parts, collection):
    """Evaluate parts and concatenate them into one mesh object."""
    mats = []
    bm = bmesh.new()
    group_names = []
    dl = None
    if any(getattr(p, "group", None) for p in parts):
        dl = bm.verts.layers.deform.verify()
    for p in parts:
        if len(p.bm.verts) == 0:
            continue
        me = p.to_mesh()
        me.calc_loop_triangles()
        if DEBUG_TRIS:
            print(f"   [{name}] part {p.mat:14s} tris {len(me.loop_triangles)}")
        uses = {}
        for poly in me.polygons:
            for ek in poly.edge_keys:
                uses[ek] = uses.get(ek, 0) + 1
        closed = all(c == 2 for c in uses.values())
        vol = 0.0
        for tri in (me.loop_triangles if closed else []):
            a, b, c = (me.vertices[i].co for i in tri.vertices)
            vol += a.dot(b.cross(c)) / 6.0
        if vol < -1e-5:
            print(f"   WARNING [{name}] part {p.mat} ({p.name}) has inward normals (volume {vol:.4f})")
        mi = None
        mat = material(p.mat)
        if mat not in mats:
            mats.append(mat)
        mi = mats.index(mat)
        n0 = len(bm.faces)
        nv0 = len(bm.verts)
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        for f in bm.faces[n0:]:
            f.material_index = mi
        if dl is not None:
            g = getattr(p, "group", None)
            if g not in group_names:
                group_names.append(g)
            gi = group_names.index(g)
            bm.verts.ensure_lookup_table()
            for v in bm.verts[nv0:]:
                v[dl][gi] = 1.0
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    obj = bpy.data.objects.new(name, me)
    collection.objects.link(obj)
    for g in group_names:
        obj.vertex_groups.new(name=g)
    return obj


def new_collection(name):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def tri_count(obj):
    if obj.type != "MESH":
        return 0
    me = obj.data
    me.calc_loop_triangles()
    return len(me.loop_triangles)


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.objects, bpy.data.curves,
                  bpy.data.armatures, bpy.data.actions):
        for item in list(block):
            block.remove(item)


def text_part(part, text, size, depth, m=Matrix(), font_path=None, resolution=3, bevel=0.0,
              bevel_res=1, align="CENTER"):
    """Add extruded text geometry to a Part (used for the "?" glyph)."""
    cu = bpy.data.curves.new("txt", "FONT")
    cu.body = text
    cu.size = size
    cu.extrude = depth / 2
    cu.bevel_depth = bevel
    cu.bevel_resolution = bevel_res
    cu.resolution_u = resolution
    cu.align_x = align
    cu.align_y = "CENTER"
    if font_path:
        try:
            cu.font = bpy.data.fonts.load(font_path, check_existing=True)
        except Exception:
            pass
    obj = bpy.data.objects.new("txt", cu)
    bpy.context.scene.collection.objects.link(obj)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev)
    if me.vertices:
        xs = [v.co.x for v in me.vertices]
        ys = [v.co.y for v in me.vertices]
        me.transform(Matrix.Translation((-(min(xs) + max(xs)) / 2, -(min(ys) + max(ys)) / 2, 0)))
    me.transform(m)
    part.bm.from_mesh(me)
    bpy.data.objects.remove(obj)
    bpy.data.curves.remove(cu)
    bpy.data.meshes.remove(me)


def face_frame(w, centre):
    """Matrix for decorating a face: local +Z = outward normal w, +Y = up (or +Y for top faces),
    +X = right as seen from outside."""
    w = Vector(w).normalized()
    up = Vector((0, 0, 1)) if abs(w.z) < 0.9 else Vector((0, 1, 0))
    u = up.cross(w).normalized()
    v = w.cross(u).normalized()
    m = Matrix((u, v, w)).transposed().to_4x4()
    m.translation = Vector(centre)
    return m


def densify(pts, max_len):
    """Insert points so no polygon edge is longer than max_len (for wrapping onto curves)."""
    out = []
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        d = math.dist(a, b)
        k = max(1, int(math.ceil(d / max_len)))
        for s in range(k):
            t = s / k
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def ellipse_points(cx, cy, rx, ry, n=16, rot=0.0):
    return [(cx + rx * math.cos(rot + TAU * i / n), cy + ry * math.sin(rot + TAU * i / n)) for i in range(n)]


def profile_radius(prof, z):
    """Radius of a (r, z) lathe profile at height z (first crossing on the outer wall)."""
    for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
        if z0 <= z <= z1 and z1 > z0 and r0 > 0 and r1 > 0:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return max(r for r, _ in prof)
