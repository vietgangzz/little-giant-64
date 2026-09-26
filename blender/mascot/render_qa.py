"""QA renders for the Little Giant mascot.

    blender -b blender/mascot/mascot.blend --python-exit-code 1 -P blender/mascot/render_qa.py [-- --only turn]

Writes PNGs to blender/mascot/renders/:
  turnaround.png   front / 3/4 / side / back of the rest pose
  hero.png         3/4 close-up of the rest pose
  face.png         front close-up (eyes, rays)
  back.png         back close-up (flag cape)
  contact_1.png, contact_2.png   3 key frames of every action
Options after `--`: --only turn|contact|action:<name>, --yaw <deg> (camera
yaw for contact/strip renders, 0 = front, 180 = back), --tag <name> (sheet
file prefix).
Nothing is saved back into the .blend.
"""

import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "renders")
os.makedirs(OUT, exist_ok=True)
TMP = os.path.join(OUT, "_tmp")
os.makedirs(TMP, exist_ok=True)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = argv[argv.index("--only") + 1] if "--only" in argv else None
YAW = float(argv[argv.index("--yaw") + 1]) if "--yaw" in argv else 30.0
TAG = argv[argv.index("--tag") + 1] if "--tag" in argv else "contact"

sc = bpy.context.scene
arm = bpy.data.objects.get("Armature")


def setup():
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "Standard"
    try:
        sc.eevee.taa_render_samples = 32
    except AttributeError:
        pass
    world = bpy.data.worlds.new("QA_World")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.42, 0.47, 0.55, 1.0)
    bg.inputs["Strength"].default_value = 0.9

    def sun(name, rot, energy, col):
        L = bpy.data.lights.new(name, "SUN")
        L.energy = energy
        L.color = col
        L.angle = math.radians(8)
        o = bpy.data.objects.new(name, L)
        o.rotation_euler = [math.radians(a) for a in rot]
        sc.collection.objects.link(o)

    sun("QA_Key", (50, 0, -35), 3.2, (1.0, 0.95, 0.88))
    sun("QA_Rim", (60, 0, 160), 2.0, (0.85, 0.9, 1.0))

    me = bpy.data.meshes.new("QA_Floor")
    r = 3.0
    me.from_pydata([(-r, -r, 0), (r, -r, 0), (r, r, 0), (-r, r, 0)], [], [(0, 1, 2, 3)])
    fl = bpy.data.objects.new("QA_Floor", me)
    m = bpy.data.materials.new("QA_FloorMat")
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.3, 0.32, 0.34, 1)
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
    me.materials.append(m)
    sc.collection.objects.link(fl)

    cam_data = bpy.data.cameras.new("QA_Cam")
    cam_data.lens = 70
    cam = bpy.data.objects.new("QA_Cam", cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam
    return cam


def aim(cam, yaw_deg, dist=4.2, height=0.9, target=(0, 0, 0.62), lens=70):
    """yaw 0 = looking at the character's front (camera on -Y)."""
    cam.data.lens = lens
    a = math.radians(yaw_deg)
    t = Vector(target)
    pos = t + Vector((math.sin(a) * dist, -math.cos(a) * dist, height - t.z + 0.25))
    cam.location = pos
    d = t - pos
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def render(path, w, h):
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.render.resolution_percentage = 100
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def load_px(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(img)
    return a


def save_px(arr, path):
    h, w = arr.shape[:2]
    img = bpy.data.images.new("qa_sheet", w, h, alpha=True)
    img.pixels = arr.ravel().tolist()
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def label(cam, text):
    """Text object pinned to the bottom of the frame."""
    cu = bpy.data.curves.new("QA_Label", "FONT")
    cu.body = text
    cu.size = 0.11
    cu.align_x = "CENTER"
    ob = bpy.data.objects.new("QA_Label", cu)
    m = bpy.data.materials.new("QA_LabelMat")
    m.use_nodes = True
    n = m.node_tree.nodes
    n["Principled BSDF"].inputs["Emission Color"].default_value = (1, 1, 1, 1)
    n["Principled BSDF"].inputs["Emission Strength"].default_value = 1.0
    n["Principled BSDF"].inputs["Base Color"].default_value = (1, 1, 1, 1)
    cu.materials.append(m)
    sc.collection.objects.link(ob)
    ob.parent = cam
    ob.location = (0, -0.62, -4.0)
    return ob


def set_action(name, frame):
    act = bpy.data.actions[name]
    arm.animation_data.action = act
    if act.slots:
        arm.animation_data.action_slot = act.slots[0]
    sc.frame_set(int(math.floor(frame)), subframe=frame - math.floor(frame))


def rest_pose():
    if arm and arm.animation_data:
        arm.animation_data.action = None
    if arm:
        for pb in arm.pose.bones:
            pb.location = (0, 0, 0)
            pb.rotation_quaternion = (1, 0, 0, 0)
            pb.rotation_euler = (0, 0, 0)
            pb.scale = (1, 1, 1)
    sc.frame_set(0)


# key frames to show per action (3 each)
CONTACT = [
    ("idle", [0, 30, 42]), ("idle_look", [22, 45, 62]), ("walk", [0, 6, 12]),
    ("run", [0, 4, 8]), ("jump", [0, 3, 8]), ("double_jump", [3, 7, 10]),
    ("fall", [0, 5, 9]), ("land", [0, 3, 6]), ("dash", [1, 4, 9]),
    ("ground_pound", [2, 6, 12]), ("ground_pound_land", [0, 3, 6]), ("wall_slide", [0, 5, 10]),
    ("hurt", [1, 4, 9]), ("star_get", [5, 16, 42]), ("dance", [8, 22, 38]),
    ("wave", [12, 17, 22]), ("sleep", [0, 30, 45]),
]


def main():
    cam = setup()
    rest_pose()
    if ONLY in (None, "turn"):
        tiles = []
        for yaw in (0, 35, 90, 180):
            p = os.path.join(TMP, "turn_%03d.png" % yaw)
            aim(cam, yaw)
            render(p, 300, 380)
            tiles.append(load_px(p))
        save_px(np.concatenate(tiles, axis=1), os.path.join(OUT, "turnaround.png"))
        aim(cam, 30, dist=3.3, height=1.0)
        render(os.path.join(OUT, "hero.png"), 800, 800)
        aim(cam, 0, dist=2.6, height=0.8, target=(0.12, 0, 0.8))
        render(os.path.join(OUT, "face.png"), 800, 700)
        aim(cam, 165, dist=2.8, height=0.75, target=(0.0, 0, 0.62))
        render(os.path.join(OUT, "back.png"), 800, 700)
    if ONLY in (None, "contact") and arm and bpy.data.actions:
        thumbs = []
        for name, frames in CONTACT:
            if name not in bpy.data.actions:
                continue
            for f in frames:
                set_action(name, f)
                aim(cam, YAW, dist=4.6, height=0.9, target=(0, 0, 0.7))
                lab = label(cam, "%s  f%d" % (name, f))
                p = os.path.join(TMP, "c_%s_%02d.png" % (name, f))
                render(p, 200, 230)
                bpy.data.objects.remove(lab)
                thumbs.append(load_px(p))
        per_row = 6
        rows = []
        for k in range(0, len(thumbs), per_row):
            row = thumbs[k:k + per_row]
            while len(row) < per_row:
                row.append(np.zeros_like(thumbs[0]))
            rows.append(np.concatenate(row, axis=1))
        # images are bottom-up: first row must end up on top
        half = (len(rows) + 1) // 2
        save_px(np.concatenate(rows[:half][::-1], axis=0), os.path.join(OUT, TAG + "_1.png"))
        save_px(np.concatenate(rows[half:][::-1], axis=0), os.path.join(OUT, TAG + "_2.png"))
    if ONLY and ONLY.startswith("action:"):
        # full strip of one action, every 2nd frame
        name = ONLY.split(":", 1)[1]
        act = bpy.data.actions[name]
        f0, f1 = act.frame_range
        thumbs = []
        f = f0
        while f <= f1 + 1e-6:
            set_action(name, f)
            aim(cam, YAW, dist=4.6, height=0.9, target=(0, 0, 0.7))
            lab = label(cam, "%s f%d" % (name, f))
            p = os.path.join(TMP, "s_%02d.png" % f)
            render(p, 200, 230)
            bpy.data.objects.remove(lab)
            thumbs.append(load_px(p))
            f += 2
        per_row = 6
        rows = []
        for k in range(0, len(thumbs), per_row):
            row = thumbs[k:k + per_row]
            while len(row) < per_row:
                row.append(np.zeros_like(thumbs[0]))
            rows.append(np.concatenate(row, axis=1))
        save_px(np.concatenate(rows[::-1], axis=0), os.path.join(OUT, "strip_%s.png" % name))


main()
