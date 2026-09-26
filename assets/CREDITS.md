# Audio & Font Credits — Little Giant 64

All audio below is real, sampled/produced recordings by named human authors (chiptune sound
design, foley, field recordings, or commercially released music) — none of it is
programmatically synthesised. Every licence was verified on its source page on 2026-09-26.
Files were then re-encoded/processed locally (trim, normalize, format conversion, and — where
noted — arranged from several source clips); no new sound was synthesised in that process.

## Music (`assets/audio/music/`)

| File | Original title | Author | Source | Licence | Processing |
|---|---|---|---|---|---|
| `title.ogg` | "Wallpaper" | Kevin MacLeod | https://incompetech.com/music/royalty-free/mp3-royaltyfree/Wallpaper.mp3 (page: https://incompetech.com/music/royalty-free/music.html) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | 2-pass `loudnorm` to −16 LUFS integrated (TP −1.5 dBTP), resampled 44.1 kHz stereo, encoded `libvorbis -q:a 5`. Kept whole track (3:40) — Godot loops the full file. |
| `world.ogg` | "Monkeys Spinning Monkeys" | Kevin MacLeod | https://incompetech.com/music/royalty-free/mp3-royaltyfree/Monkeys%20Spinning%20Monkeys.mp3 | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Same loudnorm/encode pipeline. Whole track (2:05) kept for looping — bouncy, high-energy exploration theme. |
| `underwater_or_night.ogg` | "Water Lily" | Kevin MacLeod | https://incompetech.com/music/royalty-free/mp3-royaltyfree/Water%20Lily.mp3 | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Same pipeline. Whole track (2:24) kept — calm alternate loop. |
| `ending.ogg` | "Wholesome" | Kevin MacLeod | https://incompetech.com/music/royalty-free/mp3-royaltyfree/Wholesome.mp3 | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Same pipeline. Whole track (6:04) kept as the credits loop. |
| `star_get.ogg` | "And the winner is" (`winneris.ogg`) | congusbongus | https://opengameart.org/content/and-the-winner-is | [CC0](https://creativecommons.org/publicdomain/zero/1.0/) | Short chiptune victory sting, made with the TIC-80 fantasy console. Peak-normalized to −1 dBTP (no loudnorm — too short for stable LUFS measurement), resampled 44.1 kHz, `libvorbis -q:a 5`. 3.9 s. |
| `all_stars.ogg` | "VictoryBig" + "Fanfare 01" (combined) | Dizzy Crow (`VictoryBig.wav`) / ARoachIFoundOnMyPillow (`fanfare1.ogg`) | https://opengameart.org/content/8-bit-sound-fx (Lunar Lander pack) and https://opengameart.org/content/victory-fanfare | Both [CC0](https://creativecommons.org/publicdomain/zero/1.0/) | Arranged: the 8-bit `VictoryBig` hit is layered with a 250 ms delay against the church-organ `fanfare1` swell (`amix`), then padded with a 1 s tail fade so the two real recordings read as one bigger 8.1 s "collect all stars" fanfare. Peak-normalized to −1 dBTP, `libvorbis -q:a 5`. |

## SFX (`assets/audio/sfx/`)

Most one-shot SFX come from Juhani Junkala's **"The Essential Retro Video Game Sound Effects
Collection [512 sounds]"** (CC0) — https://opengameart.org/content/512-sound-effects-8-bit-style
— a hand-designed chiptune SFX library ("classically trained composer, producer and sound
designer", per the pack's own INFO.txt), and from Kenney Vleugels' CC0 packs
(https://kenney.nl) — **Impact Sounds**, **Interface Sounds**, and **Music Jingles**.
Field-recorded/foley material for water, spring, and gong sounds comes from individual CC0/CC-BY
OpenGameArt uploads, credited individually below.

Processing for every SFX file below (unless noted): leading/trailing silence trimmed
(`silenceremove`), peak-normalized to ≈ −1 dBTP, downmixed to mono, resampled to 44.1 kHz,
encoded `libvorbis -q:a 5`.

| File | Original file | Author | Source | Licence |
|---|---|---|---|---|
| `jump.ogg` | `sfx_movement_jump1.wav` | Juhani Junkala | 512 SFX collection (Movement/Jumping and Landing) | CC0 |
| `jump2.ogg` | `sfx_movement_jump2.wav` | Juhani Junkala | 512 SFX collection | CC0 |
| `double_jump.ogg` | `sfx_movement_jump7.wav` | Juhani Junkala | 512 SFX collection | CC0 |
| `land.ogg` | `sfx_movement_jump9_landing.wav` | Juhani Junkala | 512 SFX collection | CC0 |
| `footstep_grass_1.ogg` | `footstep_grass_000.ogg` | Kenney Vleugels | https://kenney.nl/assets/impact-sounds | CC0 |
| `footstep_grass_2.ogg` | `footstep_grass_001.ogg` | Kenney Vleugels | https://kenney.nl/assets/impact-sounds | CC0 |
| `footstep_grass_3.ogg` | `footstep_grass_002.ogg` | Kenney Vleugels | https://kenney.nl/assets/impact-sounds | CC0 |
| `footstep_grass_4.ogg` | `footstep_grass_003.ogg` | Kenney Vleugels | https://kenney.nl/assets/impact-sounds | CC0 |
| `dash.ogg` | `sfx_movement_portal2.wav` | Juhani Junkala | 512 SFX collection (Movement/Portals and Transitions) | CC0 |
| `ground_pound.ogg` | `sfx_movement_portal4.wav` | Juhani Junkala | 512 SFX collection | CC0 |
| `ground_pound_land.ogg` | `impactSoft_heavy_000.ogg` | Kenney Vleugels | https://kenney.nl/assets/impact-sounds | CC0 |
| `coin.ogg` | `sfx_coin_single1.wav` | Juhani Junkala | 512 SFX collection (General Sounds/Coins) | CC0 |
| `coin_red.ogg` | `sfx_coin_double1.wav` | Juhani Junkala | 512 SFX collection | CC0 |
| `star_appear.ogg` | `sfx_sound_bling.wav` | Juhani Junkala | 512 SFX collection (General Sounds/Weird Sounds) | CC0 |
| `star_collect.ogg` | `sfx_sounds_powerup10.wav` | Juhani Junkala | 512 SFX collection (General Sounds/Positive Sounds) | CC0 |
| `one_up.ogg` | `sfx_sounds_powerup15.wav` | Juhani Junkala | 512 SFX collection | CC0 |
| `block_hit.ogg` | `impactWood_medium_000.ogg` | Kenney Vleugels | https://kenney.nl/assets/impact-sounds | CC0 |
| `block_break.ogg` | `impactWood_heavy_002.ogg` | Kenney Vleugels | https://kenney.nl/assets/impact-sounds | CC0 |
| `spring.ogg` | `door spring - Region #1.wav` ("Spring sounds") | bart | https://opengameart.org/content/spring-sounds | CC0 |
| `checkpoint.ogg` | `jingles_STEEL00.ogg` (Steel jingles) | Kenney Vleugels | https://kenney.nl/assets/music-jingles | CC0 |
| `splash.ogg` | `splash_03.ogg` ("40 CC0 water/splash/slime SFX") | rubberduck | https://opengameart.org/content/40-cc0-water-splash-slime-sfx | CC0 |
| `hurt.ogg` | `sfx_damage_hit1.wav` | Juhani Junkala | 512 SFX collection (General Sounds/Simple Damage Sounds) | CC0 |
| `enemy_stomp.ogg` | `impactSoft_medium_000.ogg` | Kenney Vleugels | https://kenney.nl/assets/impact-sounds | CC0 |
| `enemy_hit.ogg` | `sfx_damage_hit3.wav` | Juhani Junkala | 512 SFX collection | CC0 |
| `crusher_slam.ogg` | `impactMetal_heavy_004.ogg` | Kenney Vleugels | https://kenney.nl/assets/impact-sounds | CC0 |
| `crab_snap.ogg` | `switch_003.ogg` | Kenney Vleugels | https://kenney.nl/assets/interface-sounds | CC0 |
| `menu_move.ogg` | `sfx_menu_move1.wav` | Juhani Junkala | 512 SFX collection (General Sounds/Menu Sounds) | CC0 |
| `menu_select.ogg` | `sfx_menu_select1.wav` | Juhani Junkala | 512 SFX collection | CC0 |
| `menu_back.ogg` | `back_004.ogg` | Kenney Vleugels | https://kenney.nl/assets/interface-sounds | CC0 |
| `pause.ogg` | `sfx_sounds_pause1_in.wav` | Juhani Junkala | 512 SFX collection (General Sounds/Pause Sounds) | CC0 |
| `text_blip.ogg` | `sfx_sounds_Blip1.wav` | Juhani Junkala | 512 SFX collection (General Sounds/Simple Bleeps) | CC0 |
| `whoosh_camera.ogg` | `sfx_movement_portal6.wav` | Juhani Junkala | 512 SFX collection (Movement/Portals and Transitions) | CC0 |
| `drum_boom.ogg` | `gong_01.ogg` ("100 CC0 SFX") | rubberduck | https://opengameart.org/content/100-cc0-sfx | CC0 |
| `ambient_sea.ogg` | `wave_01`–`wave_04_cc0-18363__jasinski__alkaibeach.flac` ("Beach Ocean Waves") | jasinski (uploaded by qubodup) | https://opengameart.org/content/beach-ocean-waves | CC0 |
| `ambient_birds.ogg` | `birds-isaiah658_0.ogg` ("Ambient Bird Sounds") | isaiah658 | https://opengameart.org/content/ambient-bird-sounds | CC0 |
| `waterfall.ogg` | `waterfall2.ogg` ("Stream Sounds") | kurt | https://opengameart.org/content/stream-sounds | **CC BY 3.0** — credit "kurt" |

Notes on specific processing:
- `ambient_sea.ogg`: the four real wave-crash recordings (`wave_01`…`wave_04`) were arranged
  into one continuous ~20 s loop (`wave01→02→03→04→02→04→03→01`) with 0.6 s equal-power
  crossfades between each, then peak-normalized to ≈ −3 dBTP. No synthesis — only sequencing
  and crossfading of the real field recordings.
- `ambient_birds.ogg` and `waterfall.ogg` are used as downloaded (peak-normalized only, no
  trimming) since both are already continuous, edit-ready loop recordings (30.7 s and 34.7 s
  respectively).
- `all_stars.ogg`: see the Music table above — a layered arrangement of two CC0 recordings.

## Fonts (`assets/fonts/`)

| Font | Family | Files | Source | Licence |
|---|---|---|---|---|
| Display / titles / HUD | **Baloo 2** ExtraBold | `Baloo2/Baloo2-ExtraBold.ttf`, `Baloo2/OFL.txt` | https://github.com/google/fonts/tree/main/ofl/baloo2 (Google Fonts, designed by Ek Type) | [SIL Open Font License 1.1](https://openfontlicense.org/) |
| UI body text | **Nunito** Regular & Bold | `Nunito/Nunito-Regular.ttf`, `Nunito/Nunito-Bold.ttf`, `Nunito/OFL.txt` | https://github.com/google/fonts/tree/main/ofl/nunito (Google Fonts, designed by Vernon Adams, Cyreal, Jacques Le Bailly) | [SIL Open Font License 1.1](https://openfontlicense.org/) |

Processing note: Google Fonts currently ships both families upstream only as variable fonts
(`Baloo2[wght].ttf`, `Nunito[wght].ttf`, `wght` axis). Each was instanced to a static TTF at the
named weight with `fonttools varLib.instancer` (Baloo 2 → wght 800 "ExtraBold"; Nunito → wght 400
"Regular" and wght 700 "Bold"), then the `name` table was cleaned up to reflect the fixed weight.
No glyph outlines were altered — instancing only fixes the variable axis to a single point.

Vietnamese glyph coverage was verified programmatically with `fontTools` by checking the cmap of
each final TTF against the test string `"Hạ Long ẫ ặ ộ ữ đ"` (covering stacked tone/diacritic
marks ạ, ẫ, ặ, ộ, ữ and the đ-stroke). All three files (Baloo2-ExtraBold, Nunito-Regular,
Nunito-Bold) have **every glyph present** — no missing characters.

## In-game credits

Compact block suitable for a credits screen:

```
MUSIC
"Wallpaper", "Monkeys Spinning Monkeys", "Water Lily", "Wholesome"
by Kevin MacLeod (incompetech.com)
Licensed under Creative Commons: By Attribution 4.0 License
http://creativecommons.org/licenses/by/4.0/

"And the winner is" by congusbongus (OpenGameArt, CC0)
"Fanfare 01" by ARoachIFoundOnMyPillow (OpenGameArt, CC0)
"8-bit Sound FX" (VictoryBig) by Dizzy Crow (OpenGameArt, CC0)

SOUND EFFECTS
"The Essential Retro Video Game Sound Effects Collection"
by Juhani Junkala (OpenGameArt, CC0)

Interface Sounds, Impact Sounds, Music Jingles
by Kenney (kenney.nl, CC0)

"Spring sounds" by bart (OpenGameArt, CC0)
"40 CC0 water/splash/slime SFX" and "100 CC0 SFX" by rubberduck (OpenGameArt, CC0)
"Beach Ocean Waves" by jasinski (OpenGameArt, CC0)
"Ambient Bird Sounds" by isaiah658 (OpenGameArt, CC0)
"Stream Sounds" by kurt (OpenGameArt, CC BY 3.0)
https://creativecommons.org/licenses/by/3.0/

FONTS
Baloo 2 by Ek Type — SIL Open Font License 1.1
Nunito by Vernon Adams, Cyreal, Jacques Le Bailly — SIL Open Font License 1.1
```
