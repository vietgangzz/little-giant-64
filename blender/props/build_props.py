"""Build every Little Giant 64 world prop, save props.blend and export one .glb per prop.

    blender -b --factory-startup --python-exit-code 1 -P blender/props/build_props.py
    blender -b --factory-startup --python-exit-code 1 -P blender/props/build_props.py -- --render
    blender -b ... -P build_props.py -- --only coin,star --render --no-save

Options after `--`:
    --only a,b,c   build just these props (no .blend save unless --save is given)
    --render       render labelled contact sheets into blender/props/renders/
    --no-export    skip glTF export
    --no-save      skip saving props.blend
    --save         force saving props.blend even with --only
"""

import importlib
import os
import sys
import time

import bpy

sys.dont_write_bytecode = True  # keep blender/props free of __pycache__
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import lib  # noqa: E402

MODULES = ["lib", "motifs", "p_collect", "p_blocks", "p_nature", "p_structures", "p_crab", "p_cave",
           "p_dragon", "p_halong", "render"]
for _m in MODULES:
    if _m in sys.modules:
        importlib.reload(sys.modules[_m])


# (glb name, builder). Order = layout order in props.blend.
PROPS = [
    ("coin", "p_collect", "coin"),
    ("coin_red", "p_collect", "coin_red"),
    ("star", "p_collect", "star"),
    ("drum_block", "p_blocks", "drum_block"),
    ("used_block", "p_blocks", "used_block"),
    ("brick_block", "p_blocks", "brick_block"),
    ("jelly_block", "p_blocks", "jelly_block"),
    ("drum_spring", "p_blocks", "drum_spring"),
    ("crusher", "p_blocks", "crusher"),
    ("drum_big", "p_blocks", "drum_big"),
    ("bamboo_pipe", "p_nature", "bamboo_pipe"),
    ("tree_round", "p_nature", "tree_round"),
    ("tree_palm", "p_nature", "tree_palm"),
    ("bamboo_cluster", "p_nature", "bamboo_cluster"),
    ("lotus_pad", "p_nature", "lotus_pad"),
    ("lotus_flower", "p_nature", "lotus_flower"),
    ("flower_pink", "p_nature", "flower_pink"),
    ("flower_yellow", "p_nature", "flower_yellow"),
    ("grass_tuft", "p_nature", "grass_tuft"),
    ("mushroom", "p_nature", "mushroom"),
    ("rock_karst", "p_nature", "rock_karst"),
    ("cloud", "p_nature", "cloud"),
    ("checkpoint", "p_structures", "checkpoint"),
    ("pagoda", "p_structures", "pagoda"),
    ("sampan", "p_structures", "sampan"),
    ("lantern", "p_structures", "lantern"),
    ("fence_bamboo", "p_structures", "fence_bamboo"),
    ("bridge_plank", "p_structures", "bridge_plank"),
    ("cong_lang", "p_structures", "cong_lang"),
    ("crab", "p_crab", "crab"),
    # --- level 2: Vịnh Hạ Long ---
    ("junk_boat", "p_halong", "junk_boat"),
    ("raft_house", "p_halong", "raft_house"),
    ("raft_platform", "p_halong", "raft_platform"),
    ("fish_cage_ring", "p_halong", "fish_cage_ring"),
    ("kayak", "p_halong", "kayak"),
    ("pearl", "p_cave", "pearl"),
    ("stalactite", "p_cave", "stalactite"),
    ("stalagmite", "p_cave", "stalagmite"),
    ("crystal_cluster", "p_cave", "crystal_cluster"),
    ("pavilion_titop", "p_halong", "pavilion_titop"),
    ("dragon_head", "p_dragon", "dragon_head"),
    ("dragon_body", "p_dragon", "dragon_body"),
    ("dragon_tail", "p_dragon", "dragon_tail"),
    ("dragon_leg", "p_dragon", "dragon_leg"),
    ("buoy", "p_halong", "buoy"),
    ("seagull", "p_halong", "seagull"),
    ("net_rack", "p_halong", "net_rack"),
    ("vietnam_flag", "p_halong", "vietnam_flag"),
]
# contact-sheet groups: props from FIRST_HALONG on render into halong_sheet_*.png
FIRST_HALONG = "junk_boat"


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    opts = {"only": None, "render": False, "export": True, "save": None}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--only":
            opts["only"] = [s.strip() for s in argv[i + 1].split(",") if s.strip()]
            i += 1
        elif a == "--render":
            opts["render"] = True
        elif a == "--no-export":
            opts["export"] = False
        elif a == "--no-save":
            opts["save"] = False
        elif a == "--save":
            opts["save"] = True
        i += 1
    if opts["save"] is None:
        opts["save"] = opts["only"] is None
    return opts


def _claim_names(col):
    """Blender keeps object names unique ("Flag", "Flag.001"...) but glTF node names must be
    exact (Godot looks for "Flag"). Temporarily give this collection's objects their base names."""
    swaps = []
    for o in col.all_objects:
        base, dot, num = o.name.rpartition(".")
        if dot and num.isdigit():
            other = bpy.data.objects.get(base)
            if other is not None:
                other.name = base + "__parked"
                swaps.append((other, base))
            old = o.name
            o.name = base
            swaps.append((o, old))
    return swaps


def _restore_names(swaps):
    for o, name in reversed(swaps):
        o.name = name


def export_collection(col, path, animated):
    swaps = _claim_names(col)
    try:
        _export(col, path, animated)
    finally:
        _restore_names(swaps)


def _export(col, path, animated):
    bpy.ops.object.select_all(action="DESELECT")
    objs = list(col.all_objects)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    kw = dict(
        filepath=path,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_cameras=False,
        export_lights=False,
        export_materials="EXPORT",
        export_animations=animated,
        export_skins=animated,
    )
    if animated:
        kw.update(export_animation_mode="ACTIONS", export_anim_slide_to_zero=True,
                  export_force_sampling=True, export_optimize_animation_size=False)
    try:
        bpy.ops.export_scene.gltf(**kw)
    except TypeError:
        kw.pop("export_force_sampling", None)
        bpy.ops.export_scene.gltf(**kw)


def main():
    opts = parse_args()
    t0 = time.time()
    lib.reset_scene()
    out_dir = os.path.join(REPO, "assets", "models", "props")
    os.makedirs(out_dir, exist_ok=True)
    selected = []
    for name, mod, func in PROPS:
        if opts["only"] is not None and name not in opts["only"]:
            continue
        selected.append((name, getattr(importlib.import_module(mod), func)))
    report = []
    x_cursor = 0.0
    built = []
    for name, fn in selected:
        col = lib.new_collection(name)
        roots = fn(col)
        settle_on_ground(col)
        animated = any(o.type == "ARMATURE" for o in col.all_objects)
        if opts["export"]:
            export_collection(col, os.path.join(out_dir, f"{name}.glb"), animated)
        # measure
        tris = sum(lib.tri_count(o) for o in col.all_objects)
        lo, hi = lib_bbox(col)
        size = [hi[i] - lo[i] for i in range(3)]
        report.append((name, tris, size, lo[2]))
        # lay the props out in a row along +X
        shift = x_cursor - lo[0]
        for o in roots:
            o.location.x += shift
        x_cursor += size[0] + 1.0
        built.append(col)
    bpy.context.view_layer.update()
    print("\n=== props ===")
    for name, tris, size, zmin in report:
        print(f"{name:16s} tris {tris:6d}   size {size[0]:.2f} x {size[1]:.2f} x {size[2]:.2f}   zmin {zmin:+.3f}")
    if opts["save"]:
        bpy.context.preferences.filepaths.save_version = 0  # no props.blend1 backups
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "props.blend"), compress=True)
    if opts["render"]:
        import render
        importlib.reload(render)
        rdir = os.path.join(HERE, "renders")
        names = [p[0] for p in PROPS]
        split = names.index(FIRST_HALONG)
        groups = (("sheet", [c for c in built if names.index(c.name) < split]),
                  ("halong_sheet", [c for c in built if names.index(c.name) >= split]))
        per = 12
        for prefix, cols in groups:
            if not cols:
                continue
            paths = render.render_tiles(cols, os.path.join(rdir, "tiles"))
            for k in range(0, len(paths), per):
                render.compose(paths[k:k + per], os.path.join(rdir, f"{prefix}_{k // per + 1}.png"), cols=4)
    print(f"done in {time.time() - t0:.1f}s")


def settle_on_ground(col, tol=0.03):
    """Tilted trunk/stem caps can poke a centimetre or two under z = 0; flatten them onto the
    ground plane so every prop's lowest point is exactly its origin height."""
    for o in col.all_objects:
        if o.type != "MESH" or o.parent is not None:
            continue
        zs = [v.co.z for v in o.data.vertices]
        if zs and -tol < min(zs) < 0.0:
            for v in o.data.vertices:
                if v.co.z < 0.0:
                    v.co.z = 0.0


def lib_bbox(col):
    from mathutils import Vector
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for o in col.all_objects:
        if o.type != "MESH":
            continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            for i in range(3):
                lo[i] = min(lo[i], w[i])
                hi[i] = max(hi[i], w[i])
    return lo, hi


if __name__ == "__main__":
    main()
