"""Animation authoring for the Little Giant mascot (imported by build_mascot.py).

All motion is hand-authored as key poses on Bezier (auto-clamped) curves, plus
a few per-frame keyed passages where the maths matters (flips, spins, walk and
run foot contact). Loops get a Cycles modifier so their handles are continuous
across the loop point.

Axis conventions used by the helpers (armature space, character faces -Y):
    pitch  +  top leans forward (toward -Y)
    twist  +  face turns toward +X (character's left)
    lean   +  top leans toward +X
    dy     +  backward, dz + up; hands/feet `out` + = away from the body
    ray droop + swings a ray down (clockwise seen from the front),
        yaw + swings it backward
    cape lift + swings the hem back/up, away from the body
"""

import math

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector
from bpy_extras.anim_utils import action_ensure_channelbag_for_slot

# ---------------------------------------------------------------------------
# small maths helpers
# ---------------------------------------------------------------------------
TAU = 2.0 * math.pi


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def sm(t):
    t = clamp(t)
    return t * t * (3.0 - 2.0 * t)


def ease_io(t):
    t = clamp(t)
    return 0.5 - 0.5 * math.cos(math.pi * t)


def ease_out(t, k=2.0):
    t = clamp(t)
    return 1.0 - (1.0 - t) ** k


def cw(p, ph=0.0, n=1):
    return math.cos(TAU * n * (p - ph))


def sw(p, ph=0.0, n=1):
    return math.sin(TAU * n * (p - ph))


def interp(keys, f):
    """Smooth (zero-slope-at-keys) interpolation through [(frame, value)]."""
    if f <= keys[0][0]:
        return keys[0][1]
    for (f0, v0), (f1, v1) in zip(keys, keys[1:]):
        if f <= f1:
            return v0 + (v1 - v0) * sm((f - f0) / (f1 - f0))
    return keys[-1][1]


def frange(a, b, step=1.0):
    out = []
    f = a
    while f <= b + 1e-6:
        out.append(round(f, 4))
        f += step
    return out


# ---------------------------------------------------------------------------
# Keyer: writes F-curves directly into a slotted action
# ---------------------------------------------------------------------------
VERTICAL = ["root", "hips", "spine", "head", "eye.L", "eye.R", "hand.L", "hand.R", "foot.L", "foot.R"]
HIPS_PIVOT_ABOVE_BOTTOM = 0.15  # hips head (0.25) - body bottom (0.10)


class Keyer:
    def __init__(self, arm):
        self.arm = arm
        self.rest = {b.name: b.matrix_local.copy() for b in arm.data.bones}
        self.quat_bones = [b.name for b in arm.data.bones if b.name not in VERTICAL]
        for pb in arm.pose.bones:
            pb.rotation_mode = "QUATERNION" if pb.name in self.quat_bones else "XYZ"
        if arm.animation_data is None:
            arm.animation_data_create()
        self.actions = []

    # -- action lifecycle ----------------------------------------------------
    def begin(self, name, length, loop):
        act = bpy.data.actions.new(name)
        act.use_fake_user = True
        slot = act.slots.new(id_type="OBJECT", name="Armature")
        self.arm.animation_data.action = act
        self.arm.animation_data.action_slot = slot
        self.act, self.slot, self.L, self.loop = act, slot, length, loop
        self.cb = action_ensure_channelbag_for_slot(act, slot)
        self.fc = {}
        self.actions.append(act)

    def _curve(self, bone, prop, idx):
        key = (bone, prop, idx)
        fc = self.fc.get(key)
        if fc is None:
            path = 'pose.bones["%s"].%s' % (bone, prop)
            fc = self.cb.fcurves.find(path, index=idx)
            if fc is None:
                fc = self.cb.fcurves.new(path, index=idx, group_name=bone)
            self.fc[key] = fc
        return fc

    def put(self, bone, prop, idx, f, v):
        if not self.loop and f > self.L + 1e-6:
            raise ValueError("%s: key at %s beyond length %s" % (self.act.name, f, self.L))
        kp = self._curve(bone, prop, idx).keyframe_points.insert(f, v, options={"FAST"})
        kp.interpolation = "BEZIER"
        kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"

    def end(self):
        # every bone gets every channel (a rest key if unanimated), so a clip
        # always fully defines the pose in Godot
        for b in self.arm.data.bones:
            n = b.name
            chans = [("location", 3, 0.0), ("scale", 3, 1.0)]
            if n in self.quat_bones:
                chans.append(("rotation_quaternion", 4, None))
            else:
                chans.append(("rotation_euler", 3, 0.0))
            for prop, cnt, rest in chans:
                for i in range(cnt):
                    if (n, prop, i) not in self.fc:
                        v = rest if rest is not None else (1.0 if i == 0 else 0.0)
                        self.put(n, prop, i, 0.0, v)
                        self.put(n, prop, i, float(self.L), v)
        for fc in self.cb.fcurves:
            fc.update()
            kps = fc.keyframe_points
            if self.loop and len(kps) >= 2:
                a, b = kps[0].co, kps[-1].co
                if abs((b.x - a.x) - self.L) < 1e-4 and abs(b.y - a.y) < 1e-5:
                    fc.modifiers.new("CYCLES")
            fc.update()
        self.act.use_frame_range = True
        self.act.frame_start = 0
        self.act.frame_end = self.L
        self.act.use_cyclic = self.loop

    # -- channel helpers --------------------------------------------------------
    def V(self, bone, f, dx=None, dy=None, dz=None, pitch=None, twist=None, lean=None,
          sx=None, sy=None, sz=None):
        """Key a vertical (roll 0) bone. Bone local X=world X, Y=world Z, Z=world -Y."""
        if dx is not None:
            self.put(bone, "location", 0, f, dx)
        if dz is not None:
            self.put(bone, "location", 1, f, dz)
        if dy is not None:
            self.put(bone, "location", 2, f, -dy)
        if pitch is not None:
            self.put(bone, "rotation_euler", 0, f, math.radians(pitch))
        if twist is not None:
            self.put(bone, "rotation_euler", 1, f, math.radians(twist))
        if lean is not None:
            self.put(bone, "rotation_euler", 2, f, math.radians(-lean))
        if sx is not None:
            self.put(bone, "scale", 0, f, sx)
        if sz is not None:
            self.put(bone, "scale", 1, f, sz)
        if sy is not None:
            self.put(bone, "scale", 2, f, sy)

    def Q(self, bone, f, rx=0.0, ry=0.0, rz=0.0, s=None):
        """Key a rotation given in armature axes (degrees) on any bone."""
        qw = Euler((math.radians(rx), math.radians(ry), math.radians(rz)), "XYZ").to_quaternion()
        B = self.rest[bone].to_quaternion()
        ql = B.inverted() @ qw @ B
        for i in range(4):
            self.put(bone, "rotation_quaternion", i, f, ql[i])
        if s is not None:
            for i in range(3):
                self.put(bone, "scale", i, f, s)

    # -- body-part vocabulary ----------------------------------------------------
    def body(self, f, s=1.0, dz=0.0, pitch=None, twist=None, lean=None, dx=None, dy=None):
        """Hips squash & stretch, volume preserving, anchored at the body bottom."""
        k = 1.0 / math.sqrt(s)
        self.V("hips", f, sx=k, sy=k, sz=s, dz=dz + HIPS_PIVOT_ABOVE_BOTTOM * (s - 1.0),
               pitch=pitch, twist=twist, lean=lean, dx=dx, dy=dy)

    def body_pivot(self, f, pitch=0.0, twist=0.0, s=1.0, pivot=(0, 0, 0.62), lift=0.0):
        """Hips rotated about a pivot in the body (for flips / spins)."""
        h0 = Vector((0, 0, 0.25))
        P = Vector(pivot)
        R = (Matrix.Rotation(math.radians(twist), 3, "Z") @ Matrix.Rotation(math.radians(pitch), 3, "X"))
        k = 1.0 / math.sqrt(s)
        S = Matrix.Diagonal((k, k, s))
        loc = (P - h0) - R @ S @ (P - h0)
        self.V("hips", f, dx=loc.x, dy=loc.y, dz=loc.z + lift, pitch=pitch, twist=twist,
               sx=k, sy=k, sz=s)

    def hand(self, side, f, out=None, dx=0.0, dy=None, dz=None, s=None):
        sg = 1.0 if side == "L" else -1.0
        x = None if out is None else sg * out + dx
        self.V("hand." + side, f, dx=x, dy=dy, dz=dz, sx=s, sy=s, sz=s)

    def hands(self, f, out=None, dy=None, dz=None, s=None, lagR=0.0):
        self.hand("L", f, out=out, dy=dy, dz=dz, s=s)
        self.hand("R", f + lagR, out=out, dy=dy, dz=dz, s=s)

    def foot(self, side, f, out=None, dx=0.0, dy=None, dz=None, pitch=None, twist=None, lean=None):
        sg = 1.0 if side == "L" else -1.0
        x = None if out is None else sg * out + dx
        self.V("foot." + side, f, dx=x, dy=dy, dz=dz, pitch=pitch, twist=twist, lean=lean)

    def feet(self, f, **kw):
        self.foot("L", f, **kw)
        self.foot("R", f, **kw)

    def eyes(self, f, o=1.0, oR=None):
        self.V("eye.L", f, sz=o)
        self.V("eye.R", f, sz=o if oR is None else oR)

    def blink(self, f, hold=1.0):
        """Fast close (2f), short hold, slower open (3f)."""
        self.eyes(f, 1.0)
        self.eyes(f + 2, 0.1)
        self.eyes(f + 2 + hold, 0.1)
        self.eyes(f + 5 + hold, 1.0)

    def ray(self, i, f, droop=0.0, yaw=0.0, s=None):
        self.Q("ray.%d" % i, f, ry=droop, rz=yaw, s=s)

    def rays(self, f, droop=0.0, yaw=0.0, s=None, lag=1.0):
        """All three rays; each successive ray lags by `lag` frames (overlap)."""
        for i in (1, 2, 3):
            ff = f + (i - 1) * lag
            if not self.loop:
                ff = min(ff, float(self.L))
            self.ray(i, ff, droop=droop, yaw=yaw, s=s)

    def cape(self, f, lift=0.0, sway=0.0, curl=0.0):
        share = (0.45, 0.32, 0.23)
        curl_share = (0.0, 0.45, 0.55)
        for c in ("L", "M", "R"):
            spread = {"L": 1.0, "M": 0.0, "R": -1.0}[c]
            for r in (1, 2, 3):
                self.Q("cape.%s.%d" % (c, r), f,
                       rx=lift * share[r - 1] + curl * curl_share[r - 1],
                       ry=sway * share[r - 1] + spread * abs(lift) * 0.06 * (r == 1))

    def feet_orbit(self, f, twist, rest_centres, offset=(0, 0, 0), pitch=0.0, pivot=(0, 0, 0.62),
                   flip=0.0, pitch_extra=0.0):
        """Feet follow a body spin (about Z) and/or flip (about X through `pivot`)."""
        P = Vector(pivot)
        R = (Matrix.Rotation(math.radians(twist), 3, "Z") @ Matrix.Rotation(math.radians(flip), 3, "X"))
        for side in ("L", "R"):
            c0 = rest_centres[side]
            off = Vector(offset) if side == "L" else Vector((-offset[0], offset[1], offset[2]))
            c = c0 + off
            c2 = P + R @ (c - P)
            d = c2 - c0
            self.V("foot." + side, f, dx=d.x, dy=d.y, dz=d.z, twist=twist, pitch=flip + pitch_extra)


# ---------------------------------------------------------------------------
# The seventeen clips
# ---------------------------------------------------------------------------
def a_idle(k):
    L = 60
    k.begin("idle", L, True)
    for f, s in ((0, 0.985), (30, 1.025), (60, 0.985)):
        k.body(f, s=s)
    for f, p in ((4, 0.6), (34, -1.4), (64, 0.6)):
        k.V("spine", f, pitch=p)
    for f, l in ((8, 0.6), (38, -0.8), (68, 0.6)):
        k.V("head", f, lean=l)
    for side, off in (("L", 5), ("R", 8)):
        for f, dz, o in ((0, -0.012, 0.0), (30, 0.018, 0.008), (60, -0.012, 0.0)):
            k.hand(side, f + off, out=o, dz=dz)
    for i, off in ((1, 7), (2, 9), (3, 11)):
        for f, d in ((0, 2.0), (30, -3.0), (60, 2.0)):
            k.ray(i, f + off, droop=d)
    for f, lift in ((6, 1.0), (36, -1.5), (66, 1.0)):
        k.cape(f, lift=lift)
    k.eyes(0, 1.0)
    k.blink(40)
    k.eyes(60, 1.0)
    k.end()


def a_idle_look(k):
    L = 90
    k.begin("idle_look", L, False)
    # the face leads, the body follows (overlap): head -> spine -> hips
    # most of the turn is the whole body pivoting on its feet (hips, rigid);
    # head and spine add a little on top so there is no visible shear
    k_head = [(0, 0), (8, 0), (18, 5), (26, 4), (42, 4), (55, -5), (60, -6), (66, -4.5),
              (72, -4.5), (82, 0.5), (90, 0)]
    k_spine = [(0, 0), (10, 0), (21, 4), (30, 3), (44, 3), (57, -4), (62, -5), (70, -4),
               (75, -4), (84, 0.5), (90, 0)]
    k_hips = [(0, 0), (12, 0), (24, 22), (30, 19), (46, 19), (60, -27), (66, -24), (78, -24),
              (86, 1), (90, 0)]
    for f, v in k_head:
        k.V("head", f, twist=v)
    for f, v in k_spine:
        k.V("spine", f, twist=v)
    # the feet shuffle round a beat later, half as far
    for f, v in k_hips:
        ff = min(90, f + 4) if 0 < f < 90 else f
        for side in ("L", "R"):
            k.foot(side, ff, twist=0.45 * v)
    for side, lag in (("L", 0), ("R", 2)):
        for f, dz in ((14, 0.0), (19, 0.03), (24, 0.0), (58, 0.0), (63, 0.03), (68, 0.0)):
            k.foot(side, f + lag, dz=dz)
    for f, s, tw in ((0, 1.0, 0), (8, 0.965, 0), (18, 1.025, None), (26, 1.0, None), (46, 1.0, None),
                     (52, 0.975, None), (60, 1.02, None), (70, 1.0, None), (74, 0.97, None),
                     (78, 1.035, None), (84, 0.99, None), (90, 1.0, 0)):
        k.body(f, s=s)
    for f, v in k_hips:
        k.V("hips", f, twist=v)
    # fidget: pat the hands together in front, later a little shrug
    for side, lag in (("L", 0), ("R", 1)):
        k.hand(side, 0 + lag, out=0.0, dy=0.0, dz=0.0)
        k.hand(side, 24 + lag, out=0.0, dy=0.0, dz=0.0)
        k.hand(side, 30 + lag, out=-0.11, dy=-0.15, dz=0.02)
        k.hand(side, 33 + lag, out=-0.10, dy=-0.15, dz=0.06)
        k.hand(side, 36 + lag, out=-0.12, dy=-0.15, dz=0.02)
        k.hand(side, 38 + lag, out=-0.10, dy=-0.15, dz=0.05)
        k.hand(side, 46 + lag, out=0.0, dy=0.0, dz=0.0)
        k.hand(side, 72 + lag, out=0.0, dy=0.0, dz=0.0)
        k.hand(side, 77 + lag, out=0.05, dy=0.0, dz=0.07)
        k.hand(side, 84 + lag, out=0.0, dy=0.0, dz=-0.01)
        k.hand(side, 89, out=0.0, dy=0.0, dz=0.0)
    for f, d, y in ((0, 0, 0), (10, 0, 0), (20, -2, -10), (27, 1, 4), (33, 0, 0), (50, 0, 0),
                    (58, -2, 10), (64, 1, -4), (70, 0, 0), (78, -6, 0), (84, 3, -5), (90, 0, 0)):
        k.rays(f, droop=d, yaw=y)
    for f, sway in ((0, 0), (22, -6), (32, 2), (58, 7), (68, -2), (86, 1), (90, 0)):
        k.cape(f, sway=sway)
    k.eyes(0, 1.0)
    k.blink(12)
    k.eyes(40, 1.0)
    k.blink(49, hold=0)
    k.eyes(74, 1.0)
    k.eyes(77, 0.7)
    k.eyes(83, 1.0)
    k.eyes(90, 1.0)
    k.end()


def _walk_foot(p, A=0.09, H=0.065, toe_up=12.0, toe_off=22.0):
    if p < 0.5:
        q = p / 0.5
        dy = -A + 2 * A * q
        dz = 0.0
        pitch = -toe_up * (1 - sm(q / 0.18)) + toe_off * sm((q - 0.78) / 0.22)
    else:
        q = (p - 0.5) / 0.5
        e = sm(q)
        dy = A - 2 * A * e
        dz = H * math.sin(math.pi * q) ** 1.2
        pitch = toe_off * (1 - sm(q / 0.45)) - toe_up * sm((q - 0.55) / 0.45)
    th = math.radians(abs(pitch))
    dz += 0.13 * math.sin(th) - 0.042 * (1 - math.cos(th))
    return dy, dz, pitch


def a_walk(k):
    L = 24
    k.begin("walk", L, True)
    for f in range(L + 1):
        p = f / L
        bob = -cw(p, 0.04, 2)
        k.body(f, s=1.0 + 0.032 * bob, dz=0.018 * bob, pitch=4 + 1.0 * cw(p, 0, 2),
               lean=4.0 * sw(p), twist=-6.0 * cw(p))
        k.V("spine", f, twist=3.0 * cw(p, 0.06), lean=-2.0 * sw(p, 0.10), pitch=1.0 * cw(p, 0.10, 2))
        k.V("head", f, twist=2.0 * cw(p, 0.10), lean=-1.2 * sw(p, 0.15))
        for side, ph in (("L", 0.0), ("R", 0.5)):
            dy, dz, pitch = _walk_foot((p + ph) % 1.0)
            k.foot(side, f, out=0.0, dy=dy, dz=dz, pitch=pitch)
            c = cw(p, 0.06 + ph)
            k.hand(side, f, dy=0.10 * c, dz=0.015 + 0.028 * cw(p, 0.06 + ph, 2),
                   out=0.02 - 0.015 * cw(p, 0.06 + ph, 2))
        for i in (1, 2, 3):
            k.ray(i, f, droop=3.5 * cw(p, 0.10 + 0.03 * i, 2), yaw=3.0 * sw(p, 0.1 + 0.03 * i))
        k.cape(f, lift=5 + 3 * cw(p, 0.18, 2), sway=4 * sw(p, 0.22))
    k.eyes(0, 1.0)
    k.eyes(L, 1.0)
    k.end()


def _run_foot(p, A=0.15, H=0.12):
    st = 0.32
    if p < st:
        q = p / st
        dy = -0.6 * A + 1.6 * A * q
        dz = 0.0
        pitch = -8 * (1 - sm(q / 0.25)) + 30 * sm((q - 0.6) / 0.4)
    else:
        q = (p - st) / (1 - st)
        e = sm(q) ** 1.25
        dy = A - 1.6 * A * e
        dz = H * math.sin(math.pi * q) ** 0.9 * (1.0 - 0.25 * q)
        pitch = 30 * (1 - sm(q / 0.35)) - 8 * sm((q - 0.55) / 0.45)
    th = math.radians(abs(pitch))
    dz += 0.13 * math.sin(th) - 0.042 * (1 - math.cos(th))
    return dy, dz, pitch


def a_run(k):
    L = 15
    k.begin("run", L, True)
    for f in range(L + 1):
        p = f / L
        c = cw(p, 0.16, 2)
        k.body(f, s=1.0 - 0.07 * cw(p, 0.18, 2), dz=0.02 - 0.03 * c, pitch=12 + 2 * c,
               lean=3.0 * sw(p, 0.16), twist=-8.0 * cw(p))
        k.V("spine", f, pitch=5 + 1.5 * cw(p, 0.24, 2), twist=4.0 * cw(p, 0.06), lean=-2.0 * sw(p, 0.22))
        k.V("head", f, pitch=-3 + 1.0 * cw(p, 0.30, 2), twist=2.0 * cw(p, 0.12))
        for side, ph in (("L", 0.0), ("R", 0.5)):
            dy, dz, pitch = _run_foot((p + ph) % 1.0)
            k.foot(side, f, out=0.0, dy=dy, dz=dz, pitch=pitch)
            c1 = cw(p, 0.05 + ph)
            k.hand(side, f, dy=0.16 * c1, dz=0.06 - 0.07 * c1 + 0.02 * cw(p, 0.26 + ph, 2),
                   out=0.01 + 0.03 * c1)
        for i in (1, 2, 3):
            k.ray(i, f, droop=-4 + 5 * cw(p, 0.26 + 0.04 * i, 2), yaw=14 + 3 * sw(p, 0.3 + 0.04 * i, 2))
        k.cape(f, lift=22 + 5 * cw(p, 0.3, 2), curl=6 * sw(p, 0.35, 2), sway=5 * sw(p, 0.3))
    k.eyes(0, 1.0)
    k.eyes(L, 1.0)
    k.end()


def a_jump(k):
    L = 10
    k.begin("jump", L, False)
    for f, s, p in ((0, 0.80, 5), (3, 1.20, -3), (6, 1.10, -2), (10, 1.05, -1)):
        k.body(f, s=s, pitch=p)
    for f, p in ((0, 3), (4, -4), (7, -1), (10, 0)):
        k.V("spine", f, pitch=p)
    for f, o, dy, dz in ((0, 0.05, 0.03, -0.10), (4, -0.05, -0.02, 0.34), (7, -0.04, 0.0, 0.40),
                         (10, -0.02, 0.0, 0.36)):
        k.hands(f, out=o, dy=dy, dz=dz)
    for f, dy, dz, pt in ((0, 0.0, 0.0, 0), (3, 0.0, -0.02, 25), (6, 0.02, -0.035, 20), (10, 0.02, -0.03, 15)):
        k.feet(f, out=0.0, dy=dy, dz=dz, pitch=pt)
    for f, o in ((0, 0.85), (3, 1.05), (6, 1.0), (10, 1.0)):
        k.eyes(f, o)
    for f, d in ((0, -6), (3, 12), (6, 6), (8, 4)):
        k.rays(f, droop=d)
    for f, l in ((0, -1.5), (4, -3), (10, 5)):
        k.cape(f, lift=l)
    k.end()


REST_FEET = {}


def a_double_jump(k):
    L = 15
    k.begin("double_jump", L, False)
    s_keys = [(0, 1.08), (2, 0.84), (10, 0.86), (13, 1.10), (15, 1.04)]
    tuck_keys = [(0, 0.0), (2, 1.0), (10, 1.0), (13, 0.0), (15, 0.0)]
    for f in range(L + 1):
        th = 360.0 * ease_io((f - 1) / 11.0)
        s = interp(s_keys, f)
        k.body_pivot(f, pitch=th, s=s)
        t = interp(tuck_keys, f)
        k.feet_orbit(f, 0.0, REST_FEET, offset=(-0.02 * t, -0.06 * t, 0.13 * t), flip=th,
                     pitch_extra=-10 * t)
        k.V("spine", f, pitch=8 * t)
    for f, o, dy, dz in ((0, -0.02, 0.0, 0.30), (2, -0.12, -0.10, 0.05), (10, -0.12, -0.10, 0.05),
                         (12, 0.12, 0.0, 0.18), (15, 0.08, 0.0, 0.22)):
        k.hands(f, out=o, dy=dy, dz=dz)
    for f, o in ((0, 1.0), (2, 0.55), (10, 0.55), (12, 1.05), (15, 1.0)):
        k.eyes(f, o)
    for f, d in ((0, 0), (3, -12), (7, 10), (11, -8), (13, 0)):
        k.rays(f, droop=d)
    for f, l in ((0, 10), (3, 25), (8, 35), (12, 15), (15, 8)):
        k.cape(f, lift=l)
    k.end()


def a_fall(k):
    L = 18
    k.begin("fall", L, True)
    for f in range(L + 1):
        p = f / L
        k.body(f, s=1.04 + 0.015 * cw(p), pitch=-4 + 2 * sw(p))
        k.V("spine", f, lean=2.0 * sw(p, 0.1))
        for side, ph, r in (("L", 0.0, 1.0), ("R", 0.37, 0.85)):
            k.hand(side, f, dz=0.28 + 0.06 * r * sw(p, ph), out=0.07 + 0.05 * r * cw(p, ph),
                   dy=0.05 * r * sw(p, ph - 0.25))
        for side, ph in (("L", 0.0), ("R", 0.5)):
            k.foot(side, f, out=0.0, dz=-0.03 + 0.02 * sw(p, ph), pitch=20 + 12 * sw(p, ph),
                   dy=0.03 * cw(p, ph))
        for i in (1, 2, 3):
            k.ray(i, f, droop=-12 + 5 * sw(p, 0.05 * i, 2), yaw=2 * sw(p, 0.1 * i))
        k.cape(f, lift=25 + 6 * sw(p, 0, 2), curl=8 * sw(p, 0.1, 2))
    k.eyes(0, 1.05)
    k.eyes(L, 1.05)
    k.end()


def a_land(k):
    L = 8
    k.begin("land", L, False)
    for f, s in ((0, 0.78), (3, 1.06), (6, 0.985), (8, 1.0)):
        k.body(f, s=s)
    for f, o, dz in ((0, 0.06, -0.06), (1, 0.08, -0.09), (4, 0.0, 0.04), (8, 0.0, 0.0)):
        k.hands(f, out=o, dz=dz, dy=0.0)
    for f, o in ((0, 0.8), (3, 1.0), (8, 1.0)):
        k.eyes(f, o)
    for f, d in ((0, 8), (2, 10), (5, -5), (8, 0)):
        k.rays(f, droop=d, lag=0.5)
    for f, l in ((0, -1.5), (3, 8), (8, 0)):
        k.cape(f, lift=l)
    k.end()


def a_dash(k):
    L = 10
    k.begin("dash", L, False)
    for f, s, p in ((0, 0.90, -6), (3, 1.12, 22), (6, 1.10, 26), (10, 1.08, 24)):
        k.body(f, s=s, pitch=p)
    for f, p in ((0, -3), (4, 8), (7, 12), (10, 10)):
        k.V("spine", f, pitch=p)
    for f, p in ((0, 0), (5, -4), (10, -3)):
        k.V("head", f, pitch=p)
    for f, o, dy, dz in ((0, 0.02, -0.05, 0.05), (4, 0.04, 0.28, 0.10), (7, 0.06, 0.32, 0.12),
                         (10, 0.05, 0.30, 0.10)):
        k.hands(f, out=o, dy=dy, dz=dz)
    for f, dy, dz, pt in ((0, 0.0, 0.0, 0), (3, 0.08, 0.02, 20), (6, 0.14, 0.05, 35), (10, 0.13, 0.05, 32)):
        k.feet(f, out=0.0, dy=dy, dz=dz, pitch=pt)
    for f, o in ((0, 0.9), (3, 0.7), (10, 0.7)):
        k.eyes(f, o)
    for f, d, y in ((0, -4, 0), (3, 0, 20), (6, 4, 25), (10, 2, 22)):
        k.rays(f, droop=d, yaw=y)
    for f, l in ((0, 5), (3, 30), (7, 40), (10, 38)):
        k.cape(f, lift=l)
    k.end()


def a_ground_pound(k):
    L = 14
    k.begin("ground_pound", L, False)
    s_keys = [(0, 1.05), (2, 0.82), (9, 0.84), (11, 1.16), (14, 1.12)]
    tuck = [(0, 0), (2, 1), (9, 1), (11, 0), (14, 0)]
    point = [(0, 0), (9, 0), (11, 1), (14, 1)]
    pitch_k = [(0, 0), (2, 10), (9, 10), (11, 0), (14, 0)]
    for f in range(L + 1):
        th = 360.0 * ease_io((f - 2) / 7.0)
        s = interp(s_keys, f)
        k.body(f, s=s, pitch=interp(pitch_k, f), twist=th)
        t, pd = interp(tuck, f), interp(point, f)
        k.feet_orbit(f, th, REST_FEET, offset=(-0.10 * pd, -0.04 * t, 0.12 * t - 0.04 * pd),
                     pitch_extra=40 * pd - 8 * t)
    for f, o, dy, dz in ((0, 0.0, 0.0, 0.20), (2, -0.12, -0.08, 0.08), (9, -0.12, -0.08, 0.08),
                         (11, -0.36, 0.02, 0.58), (14, -0.34, 0.02, 0.52)):
        k.hands(f, out=o, dy=dy, dz=dz)
    for f, o in ((0, 1.0), (2, 0.6), (9, 0.6), (11, 0.5), (14, 0.55)):
        k.eyes(f, o)
    for f, d, y in ((0, 0, 0), (2, 0, -10), (9, 0, -15), (11, -14, 0), (14, -10, 0)):
        k.rays(f, droop=d, yaw=y, lag=0.5)
    for f, l in ((0, 5), (5, 30), (9, 30), (11, 40), (14, 45)):
        k.cape(f, lift=l)
    k.end()


def a_ground_pound_land(k):
    L = 10
    k.begin("ground_pound_land", L, False)
    for f, s in ((0, 0.70), (3, 1.10), (6, 0.96), (10, 1.0)):
        k.body(f, s=s)
    for f, o, dz in ((0, 0.13, -0.12), (1, 0.15, -0.14), (4, 0.10, 0.06), (7, 0.02, -0.01), (10, 0.0, 0.0)):
        k.hands(f, out=o, dz=dz, dy=0.0)
    for f, o in ((0, 0.05), (3, 0.02), (10, 0.0)):
        k.feet(f, out=o)
    for f, o in ((0, 0.45), (3, 1.05), (6, 1.0), (10, 1.0)):
        k.eyes(f, o)
    for f, d in ((0, 16), (2, 18), (5, -8), (8, 3), (10, 0)):
        k.rays(f, droop=d, lag=0.5)
    for f, l in ((0, -2), (3, 12), (6, -1), (10, 0)):
        k.cape(f, lift=l)
    k.end()


def a_wall_slide(k):
    """Facing the wall (wall in front, -Y), hands and feet braced on it."""
    L = 18
    k.begin("wall_slide", L, True)
    for f in range(L + 1):
        p = f / L
        k.body(f, s=0.97 + 0.01 * sw(p, 0, 3), pitch=-8, dx=0.005 * sw(p, 0, 3), dz=0.004 * sw(p, 0.1, 3))
        for side, ph in (("L", 0.0), ("R", 0.33)):
            k.hand(side, f, out=-0.02, dy=-0.15, dz=0.22 + 0.012 * sw(p, ph, 3))
            k.foot(side, f, out=0.0, dy=-0.10, dz=0.03 + 0.015 * sw(p, ph + 0.2), pitch=-20 + 6 * sw(p, ph + 0.2))
        for i in (1, 2, 3):
            k.ray(i, f, droop=-8 + 4 * sw(p, 0.08 * i, 2))
        k.cape(f, lift=18 + 5 * sw(p, 0, 2), curl=6 * sw(p, 0.15, 2))
    k.eyes(0, 0.75)
    k.eyes(L, 0.75)
    k.end()


def a_hurt(k):
    L = 15
    k.begin("hurt", L, False)
    for f, s in ((0, 0.86), (3, 1.07), (6, 0.98), (10, 1.0), (15, 1.0)):
        k.body(f, s=s)
    for f, p in ((0, -18), (3, -28), (6, -22), (8, -18), (10, -12), (13, -4), (15, 0)):
        k.V("hips", f, pitch=p)
    for f, t in ((0, 0), (5, 8), (8, -6), (10, 4), (13, 0), (15, 0)):
        k.V("hips", f, twist=t)
    for f, y in ((0, 0.03), (3, 0.05), (10, 0.02), (15, 0.0)):
        k.V("hips", f, dy=y)
    for f, p in ((0, -6), (3, -10), (7, -6), (11, -2), (15, 0)):
        k.V("spine", f, pitch=p)
    for f, l in ((0, 0), (5, 6), (8, -5), (11, 3), (15, 0)):
        k.V("spine", f, lean=l)
    for f, o, dy, dz in ((0, 0.08, -0.10, 0.16), (2, 0.12, -0.14, 0.26), (5, 0.10, -0.10, 0.22),
                         (9, 0.06, -0.04, 0.10), (15, 0.0, 0.0, 0.0)):
        k.hands(f, out=o, dy=dy, dz=dz, lagR=0.0)
    for f, dy, dz, pt in ((0, -0.06, 0.04, -25), (4, -0.08, 0.06, -30), (10, -0.03, 0.02, -10), (15, 0, 0, 0)):
        k.feet(f, out=0.0, dy=dy, dz=dz, pitch=pt)
    for f, o in ((0, 0.25), (10, 0.3), (13, 0.8), (15, 1.0)):
        k.eyes(f, o)
    for f, d, y in ((0, -18, -10), (3, 12, 0), (6, -8, 4), (10, 4, 0), (15, 0, 0)):
        k.rays(f, droop=d, yaw=y, lag=0.0 if f == 15 else 1.0)
    # knocked backwards: the cape is flicked up and away, then settles
    for f, l in ((0, 6), (3, 18), (8, 4), (12, 7), (15, 0)):
        k.cape(f, lift=l)
    k.end()


def a_star_get(k):
    L = 66
    k.begin("star_get", L, False)
    hop = [(0, 0), (5, 0), (8, 0.02), (16, 0.16), (22, 0.11), (28, 0.0), (66, 0.0)]
    s_k = [(0, 1.0), (5, 0.84), (8, 1.12), (18, 1.08), (25, 1.0), (28, 0.86), (31, 1.05), (34, 1.0),
           (36, 1.08), (38, 1.10), (42, 1.06), (54, 1.075), (66, 1.06)]
    frames = sorted(set([f for f, _ in s_k] + list(range(8, 29))))
    for f in frames:
        k.body(f, s=interp(s_k, f), dz=interp(hop, f))
    for f in range(0, 29):
        th = 0.0 if f < 8 else 720.0 * ease_out((f - 8) / 20.0, 2.2)
        k.V("hips", f, twist=th)
        air = interp(hop, f)
        tuck = 0.03 * sm(air / 0.05)
        k.feet_orbit(f, th, REST_FEET, offset=(0, 0, air + tuck))
    k.V("hips", 66, twist=720.0)
    for f in (33, 66):
        k.foot("L", f, out=0.03, dx=0.0, dy=0.0, dz=0.0, pitch=0.0, twist=720.0)
        k.foot("R", f, out=0.0, dy=0.0, dz=0.0, pitch=0.0, twist=720.0)
    for f, p in ((0, 0), (5, 5), (10, -4), (28, 0), (29, 3), (36, -5), (66, -4)):
        k.V("hips", f, pitch=p)
    for f, l in ((0, 0), (31, 0), (36, -7), (66, -6)):
        k.V("hips", f, lean=l)
    for f, l in ((0, 0), (33, 0), (37, -3), (66, -3)):
        k.V("head", f, lean=l)
    # hand R: the star hand
    for f, o, dy, dz, s in ((0, 0.0, 0.0, 0.0, 1.0), (5, 0.04, 0.0, -0.08, 1.0), (8, 0.14, 0.0, 0.18, 1.0),
                            (26, 0.12, 0.0, 0.14, 1.0), (28, 0.06, 0.0, -0.04, 1.0), (31, 0.0, 0.0, 0.05, 1.0),
                            (35, -0.34, -0.02, 1.00, 1.12), (38, -0.36, -0.02, 1.06, 1.06),
                            (42, -0.34, -0.02, 1.00, 1.0), (54, -0.34, -0.02, 1.015, 1.0),
                            (66, -0.34, -0.02, 1.00, 1.0)):
        k.hand("R", f, out=o, dy=dy, dz=dz, s=s)
    for f, o, dy, dz in ((0, 0.0, 0.0, 0.0), (6, 0.04, 0.0, -0.08), (9, 0.14, 0.0, 0.18), (26, 0.12, 0.0, 0.14),
                         (29, 0.06, 0.0, -0.04), (34, 0.02, -0.04, -0.06), (54, 0.02, -0.04, -0.05),
                         (66, 0.02, -0.04, -0.06)):
        k.hand("L", f, out=o, dy=dy, dz=dz)
    for f, o in ((0, 1.0), (5, 0.8), (8, 1.0), (28, 0.7), (31, 1.0), (36, 1.05), (48, 1.05)):
        k.eyes(f, o)
    k.eyes(50, 1.05)
    k.eyes(52, 0.1)
    k.eyes(55, 1.05)
    k.eyes(66, 1.05)
    for f, d, y, s in ((0, 0, 0, 1.0), (5, -6, 0, 1.0), (10, 0, -14, 1.0), (26, 0, -10, 1.0), (28, 10, 0, 1.0),
                       (32, -6, 0, 1.0), (36, -6, 0, 1.15), (40, -3, 0, 1.1), (64, -4, 0, 1.1)):
        k.rays(f, droop=d, yaw=y, s=s)
    for f, l in ((0, 0), (8, 10), (16, 35), (26, 30), (28, 5), (31, 15), (36, 8), (66, 8)):
        k.cape(f, lift=l)
    k.end()


def a_dance(k):
    """ALL STARS! - four beats: hop left + wave, hop right + wave, spin, 'yay'."""
    L = 60
    k.begin("dance", L, True)
    pose = [(0, 0.86, 0.0, 0), (4, 1.06, 0.08, 8), (7.5, 1.08, 0.11, 10), (11, 1.02, 0.06, 6),
            (15, 0.86, 0.0, 0), (19, 1.06, 0.08, -8), (22.5, 1.08, 0.11, -10), (26, 1.02, 0.06, -6),
            (30, 0.84, 0.0, 0), (34, 1.08, 0.12, 0), (37.5, 1.10, 0.16, 0), (41, 1.03, 0.10, 0),
            (45, 0.84, 0.0, 0), (49, 1.10, 0.10, 0), (52.5, 1.14, 0.14, 0), (56, 1.04, 0.06, 0),
            (60, 0.86, 0.0, 0)]
    for f, s, dz, lean in pose:
        k.body(f, s=s, dz=dz, lean=lean)
    for f, p in ((0, 3), (7.5, -2), (15, 3), (22.5, -2), (30, 3), (37.5, 0), (45, 4), (52.5, -5), (60, 3)):
        k.V("hips", f, pitch=p)
    spin = lambda f: 0.0 if f <= 31 else 360.0 * ease_io((f - 31) / 13.0)
    hop = [(f, dz) for f, _, dz, _ in pose]
    for f in range(0, L + 1):
        th = spin(f)
        k.V("hips", f, twist=th)
        air = interp(hop, (f - 1) % L)  # feet trail the hop by a frame, wrapping the loop
        kickL = 0.05 * math.sin(math.pi * clamp((f - 17) / 10.0)) if 15 <= f <= 29 else 0.0
        kickR = 0.05 * math.sin(math.pi * clamp((f - 2) / 10.0)) if f <= 14 else 0.0
        for side, kick in (("L", kickL), ("R", kickR)):
            sg = 1.0 if side == "L" else -1.0
            c0 = REST_FEET[side]
            c = c0 + Vector((sg * kick * 1.2, 0.0, air + kick))
            c2 = Matrix.Rotation(math.radians(th), 3, "Z") @ c
            d = c2 - c0
            k.V("foot." + side, f, dx=d.x, dy=d.y, dz=d.z, twist=th, lean=sg * 25 * kick / 0.05,
                pitch=-10 * kick / 0.05)
    for f, l in ((2, 0), (9, -3), (17, 0), (24, 3), (32, 0), (40, 0), (47, 0), (54, -2), (62, 0)):
        k.V("spine", f, lean=l)
    # hands: L waves on beat 1, R waves on beat 2, both out on the spin, both up for "yay"
    hL = [(0, 0.02, -0.02), (3, 0.04, 0.50), (5.5, 0.11, 0.52), (8, -0.01, 0.50), (10.5, 0.11, 0.52),
          (13, 0.02, 0.46), (16, 0.02, 0.0), (18, 0.0, -0.04), (22.5, 0.0, 0.02), (28, 0.0, -0.02),
          (30, 0.02, -0.04), (33, 0.14, 0.20), (43, 0.14, 0.18), (45, 0.04, 0.0), (49, 0.10, 0.52),
          (52.5, 0.12, 0.56), (56, 0.10, 0.48), (58.5, 0.04, 0.10), (60, 0.02, -0.02)]
    hR = [(0, 0.02, -0.02), (4, 0.0, 0.03), (7.5, 0.0, -0.02), (11, 0.0, 0.03), (15, 0.02, -0.02),
          (18, 0.04, 0.50), (20.5, 0.11, 0.52), (23, -0.01, 0.50), (25.5, 0.11, 0.52), (28, 0.02, 0.46),
          (31, 0.02, 0.0), (33, 0.14, 0.20), (43, 0.14, 0.18), (45, 0.04, 0.0), (49.5, 0.10, 0.52),
          (53, 0.12, 0.56), (56.5, 0.10, 0.48), (59, 0.04, 0.10), (60, 0.02, -0.02)]
    for side, keys in (("L", hL), ("R", hR)):
        for f, o, dz in keys:
            k.hand(side, f, out=o, dz=dz, dy=-0.02 if dz > 0.3 else 0.0)
    k.eyes(0, 1.0)
    k.eyes(47, 1.0)
    k.eyes(50, 0.55)
    k.eyes(56, 0.55)
    k.eyes(59, 1.0)
    k.eyes(60, 1.0)
    for f, d, y, s in ((2, 8, 0, 1.0), (9, -8, 0, 1.0), (17, 8, 0, 1.0), (24, -8, 0, 1.0), (32, 8, 0, 1.0),
                       (36, 0, -12, 1.0), (42, 0, -6, 1.0), (47, 10, 0, 1.0), (53, -10, 0, 1.12),
                       (58, 2, 0, 1.0), (62, 8, 0, 1.0)):
        for i in (1, 2, 3):
            k.ray(i, f + (i - 1), droop=d, yaw=y, s=s)
    for f, l in ((0, 5), (7.5, 18), (15, 5), (22.5, 18), (30, 5), (38, 32), (45, 8), (52, 25), (60, 5)):
        k.cape(f, lift=l)
    k.end()


def a_wave(k):
    L = 45
    k.begin("wave", L, False)
    for f, s in ((0, 1.0), (4, 0.95), (9, 1.04), (13, 1.02), (33, 1.02), (39, 0.98), (45, 1.0)):
        k.body(f, s=s)
    for f, l in ((0, 0), (9, 5), (33, 5), (42, 0), (45, 0)):
        k.V("hips", f, lean=l)
    for f, l in ((0, 0), (10, 0), (14, 2.5), (18, -1.5), (22, 2.5), (26, -1.5), (30, 2.5), (36, 0), (45, 0)):
        k.V("head", f, lean=l)
    # waving hand R: x is the world offset, waves swing it out and in
    for f, x, dy, dz in ((0, 0.0, 0.0, 0.0), (4, 0.0, 0.0, -0.04), (10, -0.10, -0.06, 0.60),
                         (13, -0.18, -0.06, 0.58), (17, -0.03, -0.06, 0.61), (21, -0.18, -0.06, 0.57),
                         (25, -0.03, -0.06, 0.61), (29, -0.18, -0.06, 0.57), (33, -0.08, -0.06, 0.60),
                         (39, -0.02, 0.0, 0.08), (45, 0.0, 0.0, 0.0)):
        k.V("hand.R", f, dx=x, dy=dy, dz=dz)
    for f, o, dz in ((0, 0.0, 0.0), (9, 0.02, 0.02), (22, 0.02, -0.01), (33, 0.02, 0.02), (45, 0.0, 0.0)):
        k.hand("L", f, out=o, dz=dz, dy=0.0)
    for f, o in ((0, 1.0), (7, 1.0), (10, 0.7), (33, 0.7), (37, 1.0), (45, 1.0)):
        k.eyes(f, o)
    for f, d in ((0, 0), (5, -5), (11, 6), (16, -2), (40, 0), (45, 0)):
        k.rays(f, droop=d, lag=0.0 if f >= 40 else 1.0)
    for f, l in ((0, 0), (10, 4), (40, 0), (45, 0)):
        k.cape(f, lift=l)
    k.end()


def a_sleep(k):
    L = 90
    k.begin("sleep", L, True)
    for f, s, p, l in ((0, 0.95, 9, 3), (45, 1.02, 6, 4.5), (90, 0.95, 9, 3)):
        k.body(f, s=s, pitch=p, lean=l)
    for f, p in ((8, 4), (53, 1), (98, 4)):
        k.V("spine", f, pitch=p)
    for f, l in ((12, 3), (57, 5), (102, 3)):
        k.V("spine", f, lean=l)
    for side, off, d in (("L", 10, 0.0), ("R", 12, 0.01)):
        for f, dz in ((0, -0.10 - d), (45, -0.07 - d), (90, -0.10 - d)):
            k.hand(side, f + off, out=-0.01, dy=-0.03, dz=dz)
    for i, off in ((1, 14), (2, 16), (3, 18)):
        for f, d in ((0, 14), (45, 10), (90, 14)):
            k.ray(i, f + off, droop=d)
    for f, sw_ in ((20, 2), (65, -2), (110, 2)):
        k.cape(f, sway=sw_)
    k.eyes(0, 0.1)
    k.eyes(90, 0.1)
    k.end()


ALL = [a_idle, a_idle_look, a_walk, a_run, a_jump, a_double_jump, a_fall, a_land, a_dash,
       a_ground_pound, a_ground_pound_land, a_wall_slide, a_hurt, a_star_get, a_dance, a_wave, a_sleep]


def build_all(arm, rest_feet):
    REST_FEET.clear()
    REST_FEET.update(rest_feet)
    k = Keyer(arm)
    for fn in ALL:
        fn(k)
    return k.actions
