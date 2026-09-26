# Little Giant — hero mascot

`build_mascot.py` builds the whole character from an empty scene: geometry, rig,
weights and 17 animations. It saves `mascot.blend` and exports
`assets/models/mascot.glb`. The asset contract is `docs/DESIGN.md`.

## Rebuild

Run these from the repo root (Blender 5.2):

```sh
blender -b --python-exit-code 1 -P blender/mascot/build_mascot.py        # ~3 s
blender -b blender/mascot/mascot.blend --python-exit-code 1 -P blender/mascot/render_qa.py
blender -b blender/mascot/mascot.blend --python-exit-code 1 -P blender/mascot/render_qa.py \
        -- --only contact --yaw 150 --tag contact_back                      # cape check
blender -b blender/mascot/mascot.blend --python-exit-code 1 -P blender/mascot/render_qa.py \
        -- --only action:walk                                               # every 2nd frame
```

`render_qa.py` writes these files to `renders/`. It uses EEVEE, which works headless on macOS.

| file | shows |
|---|---|
| `turnaround.png` | front, 3/4, side and back views |
| `hero.png` | 3/4 close-up |
| `back.png` | back close-up of the flag cape |
| `face.png` | front close-up |
| `contact_1.png`, `contact_2.png` | 3 frames of every clip |
| `contact_back_*.png` | the same frames from behind |

It never saves the scene back into the .blend.

| file | role |
|---|---|
| `build_mascot.py` | geometry, materials, armature, skin weights, export |
| `mascot_anims.py` | the `Keyer` helper and the 17 clips |
| `render_qa.py` | QA renders |
| `../common/lg_svg.py` | SVG path parser (M/L/H/V/Q/T/C/S/Z) → polylines |
| `../common/mascot_artwork.json` | the approved brand vectors (input) |

## How the model is made

- **Body.** The brand body path becomes a polyline in the XZ plane. SVG x maps to +X, SVG y
  (which runs down) maps to −Z, and the body spans z 0.10 → 1.15. The outline is inflated like
  a pressure balloon: the build solves `lap(u) = -1` inside the outline with `u = 0` on the rim,
  using conjugate gradient on a 4 mm grid. The half-depth is then `h = 0.35 * sqrt(u / u_max)`.
  For a disc this gives an exact sphere. It meets the rim with a vertical tangent, so the two
  mirrored halves close smoothly, and it has none of the creases that a distance-transform
  inflation leaves along the medial axis. After that:
  1. A constrained Delaunay fill plus interior Steiner points triangulates the outline.
  2. The front and back sheets share the rim vertices.
  3. The mesh is voxel-remeshed at 5 mm, collapse-decimated to 10k tris, then beautified and
     lightly relaxed.

  The leaf peak and the V notch survive intact.
- **Eyes.** The two eye paths are triangulated, then projected onto the analytic front surface
  along its normal. Each eye is a closed shell: the rim is lifted 7 mm with a 7 mm dome toward
  the centre, and the back sheet is buried 8 mm inside the body. The rim walls are flat-shaded,
  so each eye has a crisp lip. Eyes cannot z-fight and cannot be seen through.
- **Rays.** Each ray is a 2D curve at y = 0, 6 cm thick with a round bevel, placed exactly where
  it sits in the logo relative to the body. Each bone chain follows the ray's principal axis,
  pointing outward.
- **Hands.** UV spheres, r = 0.11, at z = 0.45. The builder starts at x = ±0.60 and slides them
  outward until they clear the body by 3.5 cm, which ends at **x = ±0.73**.
- **Feet.** Superellipsoid nubs, 0.26 × 0.17 × 0.12, at x = ±0.22 with soles at z = 0.
  Material `M_Foot`.
- **Cape.** The cape is the **Vietnamese flag**. It is deliberately small, because the game
  camera sits behind the hero and lime must dominate from there. It is a 13 × 16 grid:
  - Its shape is flag-like: nearly rectangular, 0.38 wide at the top and 0.42 at the hem
    (`CAPE_HALF_W`).
  - It spans z 0.80 → 0.38. The hem is straight with a gentle ±1 cm flutter wave, and the cloth
    has a soft ripple toward the hem.
  - Each column hangs at the maximum back depth found above it, so it hugs the upper back and
    then falls clear of the belly.
  - Its top edge sits 2 mm off the surface, and it is solidified to 14 mm inward.
  - `M_Cape` is the official red `#DA251D`.
  - It carries one yellow 5-point star, `M_FlagStar` `#FFFF00`: regular, pointing up, flat
    shaded. The star is 0.25 across (60 % of the cape height) and centred at z 0.585.
  - The star is a closed slab from 3.5 mm above the cloth to 4 mm inside it, so it never
    z-fights. It is conformed to the cape and copies its weights.
- **Objects.** There are four skinned meshes under one `Armature`:

  | object | materials |
  |---|---|
  | `LG_Body` | `M_Body`, `M_Foot` (body, hands, feet) |
  | `LG_Eyes` | `M_Eye` |
  | `LG_Rays` | `M_Ray` |
  | `LG_Cape` | `M_Cape`, `M_FlagStar` |

  The total is about 22.3k triangles:

  | object | tris |
  |---|---|
  | body shell | 10k |
  | hands and feet | 2.3k |
  | eyes | 5.1k |
  | rays | 3.3k |
  | cape and star | 1.6k |

## Rig

The armature has 25 bones. All are vertical with roll 0 unless noted. `root` and `ray.N.tip`
are non-deform (they carry no weights).

```
root (0,0,0)
├─ hips 0.25→0.55
│  └─ spine 0.55→0.85
│     ├─ head 0.85→1.15
│     │  ├─ eye.L / eye.R   at each eye's centre (blink = scale-Y about it)
│     │  └─ ray.N → ray.N.tip   along each ray, outward
│     ├─ hand.L / hand.R    at the hand centres
│     └─ cape.{L,M,R}.1→2→3 on the cape surface, columns x = +0.115 / 0 / −0.115,
│                            pointing down; joints at v = 0, ⅓, ⅔, 1 (z ≈ 0.80 → 0.38)
├─ foot.L / foot.R          at the foot centres (z 0.042)
```

Weights, all written explicitly:

| part | weighting |
|---|---|
| Body | Height smoothsteps. hips→spine blends over z 0.12–0.36, spine→head over 0.30–0.48. Everything from just below the eyes up is 100 % head, so the rigid eye shells can never slide off the face. |
| Eyes | 100 % `eye.X` |
| Rays | 100 % `ray.N` |
| Hands, feet | 100 % their own bone |
| Cape | Column hats × row hats across the nine cape bones. The top 14 % blends into `spine`, so the top edge stays sewn to the back. |

## Animations

The scene runs at 30 fps and every clip is in place. Lengths below are as reported by Godot.

| clip | length | loop | notes |
|---|---|---|---|
| idle | 2.0 | yes | breathing squash, lagged hand bob, rays trail, blink at 1.33 s |
| idle_look | 3.0 | no | turns left, then right (body pivots on its feet, face leads), pats its hands, shrugs, blinks |
| walk | 0.8 | yes | heel-toe foot roll, bob with squash at contact, sway, counter-twist, opposite hand swing on arcs |
| run | 0.5 | yes | 17° lean, 32 % stance, big hand pumps, bouncy squash, rays and cape trail |
| jump | 0.333 | no | squash anticipation → stretch launch → up pose, hands high |
| double_jump | 0.5 | no | tucked 360° forward flip about the body centre (z 0.62); feet flip with it |
| fall | 0.6 | yes | hands flail in offset circles, feet kick, cape and rays blown up |
| land | 0.267 | no | squash → overshoot → settle |
| dash | 0.333 | no | lean-back anticipation, then ~36° lean forward, stretched, hands and feet trail |
| ground_pound | 0.467 | no | tuck, 360° spin, then stretch pointing down with hands overhead |
| ground_pound_land | 0.333 | no | big squash, hands flung out, rebound |
| wall_slide | 0.6 | yes | **faces the wall** (wall in front): hands and feet braced, friction jitter, squint |
| hurt | 0.5 | no | knocked back with squinted eyes, wobble, recovers to neutral |
| star_get | 2.2 | no | crouch, hop plus 720° spin, land, `hand.R` thrust overhead (y ≈ 1.49), hold with breathing and a blink |
| dance | 2.0 | yes | ALL STARS: hop-lean-wave left, hop-lean-wave right, spin hop, "yay" with happy eyes |
| wave | 1.5 | no | `hand.R` waves three times beside the head, happy eyes, head bobs with the waves |
| sleep | 3.0 | yes | eyes closed, slow breath, droop, rays wilt |

How the clips are authored:

- Clips are key poses on Bezier curves with auto-clamped handles. Cycles are keyed per frame
  from periodic functions: walk and run foot contact, fall, wall slide, and the flips and spins.
- Squash and stretch is volume-preserving hips scale `(1/√s, 1/√s, s)`. The body bottom stays
  anchored, and hands inherit the squash.
- Looping F-curves get a Cycles modifier, so their handles stay continuous across the seam.
- Every clip keys every animated channel, so no pose leaks from one clip into the next. The
  exporter writes the union of animated channels into every clip (29 tracks each).
- The Godot check confirmed first pose == last pose (delta 0.000000) for all 7 loops.

## Godot notes

- Godot imports every clip with `loop_mode = none`, because glTF has no loop flag. Set loops
  for `idle`, `walk`, `run`, `fall`, `wall_slide`, `dance` and `sleep`, either in the import
  settings or in code.
- The model faces +Z. The body is 1.147 tall; the tip of ray 1 reaches 1.298.
- The cape and ray keys are deliberately light, because `SpringBoneSimulator3D` adds the physics
  on top. Spring chains:
  - `ray.N` → `ray.N.tip`
  - `cape.X.1` → `cape.X.3`
- Head tilts: the `head` bone pivots at z 0.85, but its weights reach down to the eyes (~0.48).
  So the clips pitch and lean the body with `spine` or `hips`, and use `head` mainly for twist.
  Procedural head look-at code in Godot should do the same: twist `head`, and tilt `spine`.

## Gotchas hit

1. **Quadriflow refuses the body.** In 5.2 it reports "mesh needs to be manifold" even though
   every edge is 2-manifold and consistently wound. The build uses voxel remesh plus collapse
   decimate instead.
2. **Blender 5 slotted actions.** `Action.fcurves` is gone. The keyer creates a slot per action
   and writes curves through `action_ensure_channelbag_for_slot`, which is fast and avoids
   `keyframe_insert`.
3. **`export_def_bones=True` drops bones.** It would drop `root` and the `ray.N.tip` bones, which
   are non-deform but part of the contract. The exporter runs with `export_def_bones=False`,
   which is safe because the rig has no helper bones.
4. **Twist shear.** A wide pebble shears badly when the head twists over a narrow weight band.
   Big turns belong on `hips`, which is rigid, with only a few degrees on spine or head.
   Widening the blend bands fixed the remaining crease.
5. **Lagged samples in loops.** Any sample lag inside a loop must wrap (`(f - lag) % L`), or the
   seam pops. That happened once in `dance`.
6. **Determinism.** Geometry, weights and animation are identical run to run. The glTF
   exporter's triangle emission order in `LG_Body` can differ between runs, even with
   `PYTHONHASHSEED`, so byte hashes of the `.glb` can change. The triangle sets are identical.
7. **Stray files.** `sys.dont_write_bytecode` and `save_version = 0` keep `__pycache__` and
   `.blend1` out of the repo.

## Deviations from the contract

| contract | actual | why |
|---|---|---|
| Cape: orange-red `#E0452B` with a gold Đông Sơn star | Vietnamese flag: red `#DA251D` with a yellow 5-point star (`M_FlagStar`) | Owner's request |
| Cape hangs to z ≈ 0.25 | Small cape, z 0.80 → 0.38 | Lime must dominate from the behind-the-hero camera (coordinator's request) |
| Body about 1.10 wide | 1.17 | Keeps the brand outline's proportions at the mandated 1.05 height |
| Hands at x ≈ ±0.60 | ±0.73 | At that height the outline itself is ±0.585 wide, so the hands would intersect the body |
| Inflation formula based on distance to the rim | Poisson/membrane `sqrt(u)` inflation | Same balloon idea, but smoother, with no medial-axis ridges |
| — | `wall_slide` has the character facing the wall | The contract doesn't say which way it faces |
