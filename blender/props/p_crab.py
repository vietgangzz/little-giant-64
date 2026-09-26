"""Crab enemy (cua): cute red crab, rigid-skinned to an armature named "Armature".

Bones: body (root, head at the ground so scale-Y squashes to the floor), claw.L / claw.R,
pincer.L / pincer.R (upper finger, extra), leg.L.1..3 / leg.R.1..3, eye.L / eye.R.
.L is the crab's left = +X (it faces -Y). Actions (30 fps): walk (0.6 s loop), snap (0.5 s),
squash (0.4 s, ends flattened).
"""

import math

import bpy
from mathutils import Euler, Matrix, Vector

from lib import TAU, Part, join_parts, mat4

FPS = 30
SCALE = 0.88  # the crab is authored ~1.02 m wide; scaled to the 0.9 m spec


def _p(mat, group, smooth=60):
    p = Part(mat, smooth=smooth)
    p.group = group
    return p


def _bone_layout():
    """name -> (head, tail, parent, roll_z_vector)."""
    B = {
        "body": ((0, 0, 0), (0, 0, 0.3), None, (0, -1, 0)),
    }
    for s, side in ((1, "L"), (-1, "R")):
        B[f"claw.{side}"] = ((s * 0.19, -0.12, 0.25), (s * 0.34, -0.33, 0.27), "body", (0, 0, 1))
        B[f"pincer.{side}"] = ((s * 0.35, -0.4, 0.33), (s * 0.33, -0.56, 0.31), f"claw.{side}", (0, 0, 1))
        B[f"eye.{side}"] = ((s * 0.09, -0.13, 0.36), (s * 0.12, -0.15, 0.52), "body", (0, -1, 0))
        for i, y in enumerate((-0.02, 0.08, 0.17), start=1):
            B[f"leg.{side}.{i}"] = ((s * 0.24, y, 0.24), (s * 0.4, y + 0.05 * i, 0.34), "body", (0, 0, 1))
    return B


def _build_mesh(col):
    parts = []
    shell = _p("M_Shell", "body")
    belly = _p("M_ShellLight", "body")
    S = Matrix.Diagonal((1.0, 0.8, 1.0, 1.0))
    shell.lathe([(0.3, 0.255), (0.297, 0.29), (0.27, 0.345), (0.21, 0.39), (0.12, 0.418), (0.0, 0.425)], 24, S,
                cap0=False)
    belly.lathe([(0.0, 0.15), (0.14, 0.158), (0.23, 0.18), (0.285, 0.215), (0.3, 0.255)], 24, S, cap1=False)
    rim = _p("M_ShellLight", "body")
    rim.lathe([(0.29, 0.245), (0.315, 0.25), (0.318, 0.258), (0.315, 0.266), (0.29, 0.27)], 24, S, closed=True)
    spots = _p("M_ShellLight", "body")
    for x, y, r in ((0.1, 0.05, 0.035), (-0.12, 0.08, 0.03), (0.02, 0.14, 0.028), (0.18, -0.06, 0.025),
                    (-0.2, -0.04, 0.027)):
        zz = 0.255 + (0.425 - 0.255) * math.sqrt(max(0.0, 1 - (x * x + (y / 0.8) ** 2) / 0.09))
        spots.sphere(r, mat4((x, y, zz - 0.004)), segs=8, rings=4, scale=(1, 1, 0.35))
    # smile
    mouth = _p("M_Black", "body")
    pts = [Vector((0.05 * math.cos(a), -0.245, 0.235 + 0.018 * math.sin(a))) for a in
           [math.radians(200 + 140 * i / 6) for i in range(7)]]
    mouth.tube(pts, 0.009, sides=5, caps=True)
    parts += [shell, belly, rim, spots, mouth]
    # eyes on stalks
    for s, side in ((1, "L"), (-1, "R")):
        stalk = _p("M_ShellLight", f"eye.{side}")
        stalk.tube([Vector((s * 0.09, -0.13, 0.35)), Vector((s * 0.11, -0.145, 0.45)),
                    Vector((s * 0.12, -0.15, 0.5))], [0.028, 0.022, 0.02], sides=7)
        eye = _p("M_White", f"eye.{side}")
        c = Vector((s * 0.12, -0.155, 0.53))
        eye.sphere(0.075, mat4(tuple(c)), segs=14, rings=8)
        pupil = _p("M_Black", f"eye.{side}")
        pupil.sphere(0.038, mat4(tuple(c + Vector((-s * 0.012, -0.056, 0.0)))), segs=10, rings=5,
                     scale=(1, 0.55, 1.15))
        glint = _p("M_White", f"eye.{side}")
        glint.sphere(0.012, mat4(tuple(c + Vector((-s * 0.0, -0.078, 0.018)))), segs=6, rings=3)
        parts += [stalk, eye, pupil, glint]
        # claw: arm + palm + fixed lower finger (claw bone) and movable upper finger (pincer bone)
        arm = _p("M_Shell", f"claw.{side}")
        arm.tube([Vector((s * 0.2, -0.1, 0.25)), Vector((s * 0.29, -0.22, 0.27)), Vector((s * 0.33, -0.3, 0.28))],
                 [0.045, 0.04, 0.045], sides=8)
        palm = _p("M_Shell", f"claw.{side}")
        palm.sphere(0.1, mat4((s * 0.35, -0.37, 0.3), (0, 0, s * 12)), segs=12, rings=7, scale=(0.95, 1.2, 0.85))
        low = _p("M_Shell", f"claw.{side}")
        low.tube([Vector((s * 0.36, -0.44, 0.28)), Vector((s * 0.35, -0.53, 0.27)), Vector((s * 0.31, -0.59, 0.28))],
                 [0.045, 0.03, 0.012], sides=7)
        up = _p("M_Shell", f"pincer.{side}")
        up.tube([Vector((s * 0.35, -0.42, 0.34)), Vector((s * 0.345, -0.51, 0.345)),
                 Vector((s * 0.31, -0.575, 0.315))], [0.04, 0.028, 0.01], sides=7)
        tips = _p("M_ShellLight", f"claw.{side}")
        tips.sphere(0.03, mat4((s * 0.37, -0.36, 0.38)), segs=8, rings=4)
        parts += [arm, palm, low, up, tips]
        # three legs per side: body -> knee -> tip on the ground
        for i, y in enumerate((-0.02, 0.08, 0.17), start=1):
            leg = _p("M_Shell", f"leg.{side}.{i}")
            spread = 0.05 * i
            leg.tube([Vector((s * 0.22, y, 0.24)), Vector((s * 0.4, y + spread, 0.33)),
                      Vector((s * 0.48, y + spread * 1.6, 0.16)), Vector((s * 0.5, y + spread * 1.8, 0.0))],
                     [0.048, 0.042, 0.032, 0.016], sides=7)
            parts.append(leg)
    for p in parts:
        p.deform(lambda v: v * SCALE)
    return join_parts("crab", parts, col)


def _set_pose(pb, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    """loc / rot (degrees, XYZ) in armature space around the bone head; scale in bone space."""
    M = pb.bone.matrix_local.to_3x3()
    Mi = M.inverted()
    pb.location = Mi @ Vector(loc)
    Rw = Euler(tuple(math.radians(a) for a in rot), "XYZ").to_matrix()
    pb.rotation_quaternion = (Mi @ Rw @ M).to_quaternion()
    pb.scale = scale


def _key(arm, frame):
    for pb in arm.pose.bones:
        pb.keyframe_insert("location", frame=frame)
        pb.keyframe_insert("rotation_quaternion", frame=frame)
        pb.keyframe_insert("scale", frame=frame)


def _rest(arm):
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
        _set_pose(pb)


def _make_action(arm, name, frames, pose_fn, start):
    ad = arm.animation_data or arm.animation_data_create()
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    ad.action = act
    for f in frames:
        _rest(arm)
        pose_fn(arm.pose.bones, f)
        _key(arm, f)
    ad.action = None
    tr = ad.nla_tracks.new()
    tr.name = name
    st = tr.strips.new(name, start, act)
    st.extrapolation = "NOTHING"
    return act


def _walk(pbs, f):
    ph = TAU * f / 18
    _set_pose(pbs["body"], loc=(0.022 * math.sin(ph), 0, 0.01 + 0.01 * math.cos(2 * ph)),
              rot=(0, 4 * math.sin(ph), 0))
    groups = {("L", 1): 0, ("R", 2): 0, ("L", 3): 0, ("R", 1): math.pi, ("L", 2): math.pi, ("R", 3): math.pi}
    for (side, i), off in groups.items():
        s = 1 if side == "L" else -1
        lift = max(0.0, math.sin(ph + off)) * 28
        swing = math.cos(ph + off) * 14
        _set_pose(pbs[f"leg.{side}.{i}"], rot=(0, -s * lift, swing))
    for side, s in (("L", 1), ("R", -1)):
        _set_pose(pbs[f"claw.{side}"], rot=(-8 * math.sin(ph + (0 if s > 0 else math.pi)), 0, 0))
        _set_pose(pbs[f"pincer.{side}"], rot=(-10 * max(0.0, math.sin(2 * ph)), 0, 0))
        _set_pose(pbs[f"eye.{side}"], rot=(0, 9 * math.sin(ph - 0.8), 0))


def _snap(pbs, f):
    # keys: 0 rest, 4 raise+open, 7 shut, 9 open, 11 shut, 15 rest
    table = {0: (0, 0, 0), 4: (-32, -38, -6), 7: (-26, 4, 4), 9: (-28, -30, 2), 11: (-24, 4, 5), 15: (0, 0, 0)}
    raise_, opn, lean = table[f]
    _set_pose(pbs["body"], rot=(lean, 0, 0))
    for side, s in (("L", 1), ("R", -1)):
        _set_pose(pbs[f"claw.{side}"], rot=(raise_, 0, s * raise_ * 0.25))
        _set_pose(pbs[f"pincer.{side}"], rot=(opn, 0, 0))
        _set_pose(pbs[f"eye.{side}"], rot=(lean * 1.5, 0, 0))


def _squash(pbs, f):
    table = {0: (1.0, 1.0, 0, 1.0), 2: (1.25, 0.55, 20, 1.2), 4: (1.45, 0.28, 35, 1.35),
             7: (1.35, 0.36, 32, 1.25), 12: (1.45, 0.26, 36, 1.3)}
    wide, flat, splay, eye = table[f]
    _set_pose(pbs["body"], scale=(wide, flat, wide))
    for side, s in (("L", 1), ("R", -1)):
        for i in (1, 2, 3):
            _set_pose(pbs[f"leg.{side}.{i}"], rot=(0, s * splay, 0))
        _set_pose(pbs[f"claw.{side}"], rot=(0, s * splay * 0.8, s * 10))
        _set_pose(pbs[f"eye.{side}"], rot=(0, s * splay * 0.9, 0), scale=(eye, 1.0 / eye, eye))


def crab(col):
    sc = bpy.context.scene
    sc.render.fps = FPS
    mesh = _build_mesh(col)
    arm_data = bpy.data.armatures.new("Armature")
    arm = bpy.data.objects.new("Armature", arm_data)
    col.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    layout = _bone_layout()
    ebs = {}
    for name, (h, t, parent, roll) in layout.items():
        eb = arm_data.edit_bones.new(name)
        eb.head = Vector(h) * SCALE
        eb.tail = Vector(t) * SCALE
        eb.align_roll(Vector(roll))
        eb.use_deform = True
        ebs[name] = eb
    for name, (h, t, parent, roll) in layout.items():
        if parent:
            ebs[name].parent = ebs[parent]
            ebs[name].use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")
    mesh.parent = arm
    mod = mesh.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    _make_action(arm, "walk", list(range(0, 19, 3)), _walk, 0)
    _make_action(arm, "snap", [0, 4, 7, 9, 11, 15], _snap, 40)
    _make_action(arm, "squash", [0, 2, 4, 7, 12], _squash, 80)
    _rest(arm)
    sc.frame_set(30)  # between strips: rest pose for the contact sheet
    return [arm]
