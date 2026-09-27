# Little Giant: Star Hop

A Super-Mario-64-style 3D island platformer starring the VGANG **Little Giant**, who wears a
Vietnamese flag cape. The mascot is
modelled, rigged and animated in **Blender 5.2** from the approved brand vectors. The game runs in
**Godot 4.7** (Forward+).

There are two levels, and a junk boat moored in each one sails you to the other. You can also
travel from the pause menu.

It also runs on iPhone inside a React Native app, with touch controls, haptics and a Skia +
Reanimated splash: see [mobile/README.md](mobile/README.md).

- **Hạ Long Skies** has floating islands, rice terraces, limestone karsts and a lotus lagoon. It
  has 8 bronze Đông Sơn stars and 146 coins. Collect every star and the great bronze drum rings
  out for **ALL STARS!**
- **Vịnh Hạ Long (Hạ Long Bay)** is an emerald bay full of limestone towers with a floating fishing
  village and Surprise Cave. A dragon circles the whole bay, and you can ride on its back. It has
  6 stars and 8 dragon pearls.

![title](docs/shots/title.png)

## Play

```bash
godot --path .            # or open project.godot in Godot 4.7.2 and press F5
```

| | Keyboard / mouse | Gamepad |
|---|---|---|
| Move | WASD / arrows (Alt = walk) | Left stick |
| Jump / double jump | Space (tap twice; jump again on landing for a higher jump, a third time for a flip) | A |
| Dash (also in the air) | Shift / J | X / RB |
| Ground pound (in the air) | Ctrl / C / K | B / LB / LT |
| Wall kick | Jump while sliding down a wall | |
| Camera | Mouse (click to capture), Q/E 45° turns, Z zoom, Tab recenter | Right stick, Y zoom |
| Pause (stars, settings, EN/VI) | Esc / P | Start |

Spring drums launch you, and ground-pounding onto one gives a super bounce. Brick blocks break
when you bonk them or pound them. Drum "?" blocks pay out coins. Stomp crabs, but don't stand
under the crushers. Falling in the sea costs one health pebble and puts you back on safe ground.
Every 50 coins restores one pebble.

### The eight stars

| | Star | Where |
|---|---|---|
| 1 | Top of the Rice Terraces | Climb the six paddy tiers east of home |
| 2 | Eight Red Lanterns | Find all 8 lanterns; the star appears at the pagoda pond |
| 3 | Roof of the One Pillar Pagoda | Bamboo pipes up to the golden lotus crown |
| 4 | Karst Summit | Chain the spring drums up three limestone towers |
| 5 | Across the Lotus Lagoon | Sinking lotus leaves, a ferry, jelly bánh chưng blocks |
| 6 | Behind the Waterfall | Walk through the falls north-east |
| 7 | King of Crab Beach | Stomp all five crabs |
| 8 | A Hundred Đồng Xu | Collect 100 coins |

### Hạ Long Bay stars

| | Star | Where |
|---|---|---|
| 1 | Fishing Village Rooftops | Walk the boardwalk, climb the crate onto the last north roof |
| 2 | Heart of Surprise Cave | Climb the stalagmite pillars to the ledge at the back |
| 3 | Fighting Cock Rocks | Wall-kick up between Hòn Trống and Hòn Mái |
| 4 | Ti Tốp Summit | Ride the dragon up and jump off onto the pavilion |
| 5 | Star on the Dragon's Head | Board at the "Dragon stop" jetty, then run up its back |
| 6 | Eight Dragon Pearls | One is on the dragon, one rides the junk ferry; the star appears at the pier |

## How it's made

```
blender/          Python generators for every model (.blend sources are rebuilt from them)
  mascot/         build_mascot.py + mascot_anims.py → assets/models/mascot.glb
  props/          build_props.py (+ modules) → assets/models/props/*.glb (30 props)
  common/         brand SVG paths (mascot_artwork.json) and the SVG parser
assets/           glTF models, Ogg audio, fonts, CREDITS.md
scripts/
  autoload/       Game (state, save, input map, CLI flags), Sound, Fx (toon materials + VFX)
  player/         Player (controller state machine), PlayerModel (anims, spring bones, squash)
  camera/         GameCamera: SM64-style follow cam
  world/          World (Hạ Long Skies) and HalongWorld (Hạ Long Bay), both built in code; Island
                  (procedural @tool islands and karsts), CaveDome (a hollow cave), Props
  objects/        coins, stars, blocks, spring drums, flags, crabs, crushers, boats, lotus, jelly…
  ui/             HUD, title, pause, rainbow headlines
  qa/bot.gd       plays every star route with real inputs
shaders/          toon light, ink outline, island ground, sea with shore foam, sky, FX
```

- **Mascot:** the brand silhouette is balloon-inflated into a pebble, with raised gang eyes, the three
  rays, detached hand and foot nubs, and a small hero cape. It has 25 bones: root, hips, spine,
  head, eyes, 3×2 ray chains, hands, feet and a 3×3 cape grid. It has 17 clips: idle, idle_look,
  walk, run, jump, double_jump (a flip), fall, land, dash, ground_pound, ground_pound_land,
  wall_slide, hurt, star_get, dance, wave and sleep. In Godot, a `SpringBoneSimulator3D` makes the
  rays and the cape trail and bounce.
- **Look:** a toon light model with cool-tinted shadows, a spec dot and a rim; inverted-hull ink
  outlines; world-space checkered grass with striped soil; and a sea shaded by real water depth with
  foam rings round every shore. It also uses AgX tonemapping, glow, SSAO, depth fog and far
  depth-of-field.
- **Audio:** everything is sampled, from Kevin MacLeod, Juhani Junkala, Kenney and CC0 field
  recordings. See [assets/CREDITS.md](assets/CREDITS.md).

### Rebuild the Blender assets

```bash
blender -b --factory-startup --python-exit-code 1 -P blender/mascot/build_mascot.py
blender -b --factory-startup --python-exit-code 1 -P blender/props/build_props.py -- --render
godot --headless --path . --import      # REQUIRED: a running game reads the old cached import otherwise
```

## QA

```bash
# every star route, played by the bot with real inputs (fast: fixed timestep)
godot --headless --path . --fixed-fps 60 -- --bot=all
godot --headless --path . --fixed-fps 60 -- --bot=karst --trace     # one route, with a state trace
godot --headless --path . --fixed-fps 60 -- --level=halong --bot=hl_village,hl_cave,hl_trongmai,hl_dragon,hl_titop,hl_pearls

godot --path . -- --tour=/tmp/tour                  # screenshots of every area
godot --path . -- --start --warp=pagoda             # jump straight to a star (ids in Game.STARS)
godot --path . -- --start --all-stars --warp=51.5,11.6,-13   # 7 stars owned: grab the last for the finale
godot --path . -- --start --shot=3:/tmp/a.png --quit-after-shot
godot --path . -- --start --fps                     # prints fps, draw calls and primitives
```

Test runs (`--bot`, `--warp`, `--god`, `--tour`, `--shot`) never write the save file.

```bash
godot --path . -- --touch                    # the phone controls on desktop (the mouse acts as a finger)
godot --path . --resolution 1400x986 -- --touch-qa --quit   # plays the touch controls itself: PASS/FAIL per control
```

## Export

`export_presets.cfg` has a universal macOS preset (`build/macos/LittleGiant64.zip`):

```bash
mkdir -p build/macos && godot --headless --path . --export-release macOS build/macos/LittleGiant64.zip
```

Forward+ has no web export. Switching the renderer to Compatibility would allow one, but the sea
foam needs the depth texture.

---
Made with ♥ by VG TEAM · Blender · Godot
