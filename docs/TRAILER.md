# Little Giant: Star Hop trailers

There are two trailers:
- **The two-map trailer:** ~60 s at 2560×1440, 60 fps. It covers Hạ Long Skies and Hạ Long Bay.
- **The Đà Nẵng – Hội An trailer:** ~30 s. It shows the third map inside an iPhone Duo frame on an animated backdrop.

**How the footage is made:**
- Every shot is real gameplay running in the engine.
- The QA bot plays with real inputs.
- A director inside the game (`scripts/qa/trailer.gd`) moves the camera.
- Godot's Movie Maker writes every frame at a fixed 60 fps, so the footage is perfectly smooth however fast or slow the machine is.

**What is on screen:**
- There are no captions or credit lines. The "Caption" column below only notes what each shot is about; turn captions back on with `CAPTIONS` in `trailer.gd`.
- The game's own chapter cards ("MAP 2", "MAP 3") and its STAR GET! and ALL STARS! banners stay.

**Sound:** the game's own audio, Kevin MacLeod's music plus the real sound effects.

## The two-map trailer

### Part 1: Hạ Long Skies (~30 s)

| # | Length | Picture | Caption |
|---|---|---|---|
| 1 | 3.5 s | **Title screen.** The rainbow logo; the camera circles the bronze drum while the mascot waves | — |
| 2 | 4.5 s | **Mascot close-up.** The camera swings from the front round to the back to show the **Vietnamese flag cape**; the mascot waves, then dances | *The VGANG mascot, modelled, rigged and animated in Blender* |
| 3 | 5 s | **Moves.** Behind-the-back gameplay: running for coins, the **triple jump flip**, a dash, a **ground pound** in a puff of dust | *Triple jump · flip · dash · ground pound* |
| 4 | 4.5 s | **Blocks and springs.** Bonking a **"?" block** for 5 coins, then a **spring drum** up to a sky island | *? blocks pay out coins · spring drums* |
| 5 | 5.5 s | **Terraces star.** Up the **rice terraces** to the star: **STAR GET!**, the mascot holds it high | *8 bronze Đông Sơn stars* |
| 6 | 5 s | **Fly-through.** Three camera flights: the **One Pillar Pagoda** and its bamboo pipes, the **waterfall**, the **karst towers** | *Hạ Long Skies · 146 coins · 8 stars* |
| 7 | 2.5 s | **Junk boat.** Stepping onto the **junk boat**; the picture fades | *All aboard → Hạ Long Bay* |

### Part 2: Hạ Long Bay (~23 s)

| # | Length | Picture | Caption |
|---|---|---|---|
| 8 | 4 s | **The bay.** A high flight down over the emerald bay, the dragon flying between the towers. Chapter card **MAP 2 · VỊNH HẠ LONG** | (chapter card) |
| 9 | 3.5 s | **Floating village.** Running the boardwalk of the **floating fishing village** | *The floating fishing village* |
| 10 | 3.5 s | **Surprise Cave.** Inside, stalactites, glowing crystals and the skylight beam; hopping up the stalagmites | *Surprise Cave* |
| 11 | 3.5 s | **Fighting Cock rocks.** **Wall kicks** up between the two rocks | *Wall kicks · the Fighting Cock rocks* |
| 12 | 3 s | **Dragon stop.** Jumping onto the **dragon's** back at the Dragon stop | *Ride the dragon round the bay!* |
| 13 | 6 s | **Ti Tốp.** Riding up past **Ti Tốp**, jumping off onto the pavilion: **STAR GET!** | — |

### Part 3: Ending (~8.5 s)

| # | Length | Picture |
|---|---|---|
| 14 | 5 s | **ALL STARS!** on the bronze drum: the mascot dances, confetti, the gong, the camera circling |
| 15 | 3.5 s | **End card.** The ink-blue card with the title, the map name and the score (the trailer leaves out the "Made with…" and hint lines) |

## The Đà Nẵng – Hội An trailer (~31 s, iPhone Duo frame)

**How it differs:**
- **Renderer:** filmed with the phone renderer (`--rendering-method mobile --phone`) at the iPhone Duo's unfolded screen size, 2034×1398, so the picture is what the Duo draws.
- **Sharpness and buttons:** the director turns the 3D scale back to 100% and hides the on-screen buttons.
- **Signs:** it also hides the in-world name signs.

| # | Length | Picture |
|---|---|---|
| 1 | 4 s | **Intro.** A flight in over the sea to Dragon Bridge. Chapter card **MAP 3 · ĐÀ NẴNG – HỘI AN** |
| 2 | 4 s | **Dragon's back.** Running along the golden dragon's back, hump by hump |
| 3 | 2.6 s | **Dragon star.** **STAR GET!** on the dragon's head |
| 4 | 3 s | **Fire.** The head breathes fire, then water, over the end of the road |
| 5 | 3.2 s | **Cable car.** Hopping onto the Bà Nà cable car roof and climbing into the clouds |
| 6 | 3.8 s | **Golden Bridge.** Out between the two stone hands: **STAR GET!** |
| 7 | 2.6 s | **Hội An street.** Down Hội An's lantern street |
| 8 | 2.8 s | **Chùa Cầu.** Over the rooftops onto Chùa Cầu |
| 9 | 3 s | **Coconut forest.** Hopping the spinning basket boats |
| 10 | 4.2 s | **Fireworks.** Over Mỹ Khê for **ĐÀ NẴNG CLEAR!** |

**The frame (`tools/frame_trailer.py`):**
- **Phone:** the gameplay goes into a drawn iPhone Duo, unfolded, with a graphite band, a black glass border, the hinge crease and a punch-hole camera on the right panel. It floats gently, with its reflection on the floor.
- **Backdrop:**
  - a dusk sky with twinkling stars
  - a retro sun in brand lime and orange setting behind Hội An's roofs
  - silhouettes of the Marble Mountains and Dragon Bridge on the left, and Bà Nà's Golden Bridge on the right
  - silk lanterns drifting up and four-point sparkles
  - a lime perspective grid rolling towards the viewer
- **Watermark:** a small `vgang.studio` at the bottom.

## Recording

```bash
tools/record_trailer.sh            # the two-map trailer → build/trailer/little-giant-64-trailer.mp4
tools/record_trailer.sh danang     # the Đà Nẵng – Hội An trailer → build/trailer_dn/danang-trailer-2k.mp4
```

**What the script does:**
- **Recording:** each clip is recorded separately with `godot --path . --write-movie <clip>.avi -- --trailer=<skies|halong|finale|danang>`.
- **Shot marks:** the director prints the frame range of every shot (`SHOT <name> <first frame> <last frame>`).
- **Cutting:** `tools/edit_trailer.py` uses those marks to cut every shot to length and joins them with short cross-fades.
- **Framing:** for the Đà Nẵng cut, `tools/frame_trailer.py` then puts it in the phone frame. It needs `numpy` and `Pillow`.
- **Output:** H.264 2560×1440 60 fps with AAC sound.

Keep the Godot window visible while it records: macOS stops drawing windows that are covered.
