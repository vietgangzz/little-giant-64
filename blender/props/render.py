"""Contact-sheet renderer: one EEVEE tile per prop (labelled), composed into PNG sheets."""

import math
import os

import bpy
import numpy as np
from mathutils import Vector

from lib import hex_to_linear

TILE = 400


def _world():
    w = bpy.data.worlds.new("SheetWorld")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*hex_to_linear("#BFE3F7"), 1.0)
    bg.inputs["Strength"].default_value = 0.9
    return w


def setup():
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x = TILE
    sc.render.resolution_y = TILE
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    try:
        sc.eevee.taa_render_samples = 24
    except Exception:
        pass
    sc.world = _world()
    if "SheetSun" not in bpy.data.objects:
        ld = bpy.data.lights.new("SheetSun", "SUN")
        ld.energy = 3.2
        ld.color = (1.0, 0.96, 0.9)
        ld.angle = math.radians(8)
        sun = bpy.data.objects.new("SheetSun", ld)
        sc.collection.objects.link(sun)
        sun.rotation_euler = (math.radians(48), 0, math.radians(28))
        fd = bpy.data.lights.new("SheetFill", "SUN")
        fd.energy = 0.9
        fd.color = (0.8, 0.88, 1.0)
        fill = bpy.data.objects.new("SheetFill", fd)
        sc.collection.objects.link(fill)
        fill.rotation_euler = (math.radians(60), 0, math.radians(-140))
    cd = bpy.data.cameras.new("SheetCam")
    cd.lens = 50
    cd.clip_start = 0.01
    cd.clip_end = 500
    cam = bpy.data.objects.new("SheetCam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    # label
    cu = bpy.data.curves.new("SheetLabel", "FONT")
    cu.size = 0.0036
    cu.align_x = "CENTER"
    cu.align_y = "BOTTOM"
    lab = bpy.data.objects.new("SheetLabel", cu)
    sc.collection.objects.link(lab)
    lab.parent = cam
    lab.location = (0, -0.0345, -0.1)
    lab.visible_shadow = False
    m = bpy.data.materials.new("LabelInk")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.01, 0.01, 0.015, 1)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs[0])
    cu.materials.append(m)
    return cam, lab


def _bbox(col):
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    dg = bpy.context.evaluated_depsgraph_get()
    for o in col.all_objects:
        if o.type != "MESH":
            continue
        ev = o.evaluated_get(dg)
        for c in ev.bound_box:
            w = ev.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    return lo, hi


def render_tiles(collections, out_dir, view=(0.62, -1.0, 0.55), tile=TILE, suffix=""):
    os.makedirs(out_dir, exist_ok=True)
    cam, lab = setup() if "SheetCam" not in bpy.data.objects else (bpy.data.objects["SheetCam"],
                                                                   bpy.data.objects["SheetLabel"])
    sc = bpy.context.scene
    sc.render.resolution_x = tile
    sc.render.resolution_y = tile
    paths = []
    allcols = list(bpy.context.scene.collection.children)
    for col in collections:
        for c in allcols:
            c.hide_render = (c != col)
        lo, hi = _bbox(col)
        centre = (lo + hi) / 2
        radius = (hi - lo).length / 2
        d = Vector(view).normalized()
        fov = cam.data.angle
        dist = radius / math.sin(fov / 2) * 0.92
        cam.location = centre + d * dist
        cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        size = hi - lo
        lab.data.body = f"{col.name}.glb\n{size.x:.2f} x {size.y:.2f} x {size.z:.2f} m"
        p = os.path.join(out_dir, f"{col.name}{suffix}.png")
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        paths.append(p)
    for c in allcols:
        c.hide_render = False
    return paths


def compose(paths, out_path, cols=4):
    imgs = []
    for p in paths:
        im = bpy.data.images.load(p)
        w, h = im.size
        a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
        imgs.append(a)
        bpy.data.images.remove(im)
    th, tw = imgs[0].shape[:2]
    rows = math.ceil(len(imgs) / cols)
    sheet = np.ones((rows * th, cols * tw, 4), dtype=np.float32)
    sheet[..., :3] = 0.12
    for i, a in enumerate(imgs):
        r, c = divmod(i, cols)
        y0 = (rows - 1 - r) * th  # image rows start at the bottom
        sheet[y0:y0 + th, c * tw:(c + 1) * tw] = a
        # 2 px gutter
        sheet[y0:y0 + th, c * tw:c * tw + 2, :3] = 0.12
        sheet[y0:y0 + 2, c * tw:(c + 1) * tw, :3] = 0.12
    img = bpy.data.images.new("sheet", cols * tw, rows * th, alpha=True)
    img.pixels.foreach_set(sheet.ravel())
    img.filepath_raw = out_path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    return out_path
