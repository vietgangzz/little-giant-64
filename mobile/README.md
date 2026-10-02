# Little Giant: Star Hop, React Native (iOS)

This folder runs the Godot game at the repo root inside a React Native app. The game is not rewritten; the same scripts, models, shaders and audio are used:

- **The game** is packed into `ios/LittleGiant64.pck`. [`@borndotcom/react-native-godot`](https://github.com/borndotcom/react-native-godot) runs it with the LibGodot engine on its own thread. It uses Metal with Godot's Mobile renderer.
- **React Native** owns the shell around the game, described below.

## Around the game

- **Splash and loading screen:** drawn with **Skia** and animated by **Reanimated** (`src/Curtain.tsx`). It shows:
  - a Hạ Long sky, a turning Đông Sơn sun and drifting clouds over a rolling sea
  - Little Giant hopping on an island
  - the rainbow LITTLE GIANT / STAR HOP title
  - a loading bar and a gameplay tip

  The splash stays up until the game reports that it has drawn its first frames, including the shaders they need. Then it opens like a Mario 64 iris, from the mascot outwards. When you sail to another map (Hạ Long Skies, Vịnh Hạ Long, Đà Nẵng – Hội An), it closes the same way over the reload and opens again once the new level is on screen.
- **A bridge to the game** (`src/gameBridge.ts`):
  - JS worklets (react-native-worklets-core) run on the Godot thread and hand a callback to the game's `Game` autoload.
  - The game reports its state through that callback (`boot`, `ready`, `loading:<level>`) and asks for haptics.
- **Haptics** use expo-haptics (the iOS haptic engine):
  - light for button presses
  - heavy for a ground pound
  - success for a star
  - error for getting hurt
- **Pausing:** leaving the app (home, a call, Control Center) opens the game's pause menu, and going to the background halts the engine.
- **A game screen:**
  - landscape only, no status bar, and the home indicator fades out
  - swipes that start at a screen edge reach the game first, as in any iOS game (`GameViewController` in `AppDelegate.swift`)

## Inside the game on phones

`Game.is_phone()` is true in the embed. On a phone:

- **Touch controls** (`scripts/ui/touch_controls.gd`):
  - A floating analog stick sits under the left thumb. How far you push sets the speed.
  - The right thumb gets a big lime JUMP button, with DASH, POUND, camera recenter and camera zoom on an arc around it.
  - Dragging anywhere else on the right half swings the camera.
  - DASH greys out while it recharges, and POUND greys out on the ground.
  - The controls press the same input actions as the keyboard, so gameplay code doesn't change.
- **First run** shows three tips that name the controls. The pause menu has a camera speed setting.
- **Graphics:** MSAA is off, because on the Mobile renderer it breaks the depth texture the sea's shore foam reads, and FXAA smooths edges instead. 3D renders at 80% size, shadows are lighter, SSAO is off (it is Forward+ only), and the frame rate is capped at 60.
- **Menus** read taps before the GUI. A tap arrives both as a touch and as an emulated click, so only the touch counts.
- **Pads:** gamepad bindings are skipped, because LibGodot on iOS reports a phantom joypad.
- **Screen size:** the embed resizes without `size_changed`, so the window size is polled. That covers the iPhone Duo folding and unfolding.

## Versions that matter

| Piece | Version | Why |
|---|---|---|
| LibGodot (in react-native-godot 1.0.1) | **4.5.1** | The pack must be made by a Godot **4.5.1** editor. The game targets 4.7 and runs unchanged on 4.5. Every star route in the QA bot passes on both. |
| React Native / Expo | 0.81.6 / SDK 54 | What react-native-godot is built against |
| react | 19.1.4 | Must equal RN 0.81.6's renderer, or the app dies at start |
| @shopify/react-native-skia | 2.2.12 | The splash |
| react-native-reanimated / react-native-worklets | 4.1 / 0.5 | They drive the splash. babel-preset-expo adds the worklets plugin; react-native-worklets-core's plugin sits next to it (both emit the same worklet format). |
| Xcode | 27.1 | See the two iOS 27 fixes below |

## Build and run (simulator)

```sh
cd mobile
npm install --legacy-peer-deps
npx download-prebuilt              # fetches the LibGodot 4.5.1 xcframeworks
cd ios && pod install && cd ..
GODOT_EDITOR=/path/to/Godot_v4.5.1/Godot.app/Contents/MacOS/Godot ./build_ios_sim.sh [simulator-udid]
```

`build_ios_sim.sh` re-packs the game (`export_game.sh`) and builds the Release app, so the JS bundle is embedded and no Metro server is needed. Given a simulator id, it also installs and launches the app. The default editor path is `~/Applications/godot-4.5.1/Godot.app`. Get Godot 4.5.1 from https://github.com/godotengine/godot/releases/tag/4.5.1-stable (macOS universal).

Xcode 27 replaces Simulator.app with **Device Hub** (`Xcode.app/Contents/Applications/DeviceHub.app`). Its toolbar folds and unfolds the iPhone Duo, and clicking the screen is a real touch.

## Testing touch on a device or simulator

The game can drive its own touch controls:

- **How to run it:** drop an empty `touch_qa.txt` into the app's Documents folder, then relaunch.

  ```sh
  D=$(xcrun simctl get_app_container <udid> studio.vgang.littlegiant64.native data)/Documents
  touch "$D/touch_qa.txt"; xcrun simctl launch <udid> studio.vgang.littlegiant64.native
  sleep 25; cat "$D/touch_qa.log"; rm "$D/touch_qa.txt"
  ```

- **What it does:** it taps Start on the title, runs with the stick, then jumps, dashes and ground-pounds with the buttons. It drags the camera, and opens and resumes the pause menu.
- **Results:** each step writes a PASS or FAIL line with numbers, such as metres run or degrees turned. A `kept_health` line checks that no health was lost, and a `perf` line logs fps, draw calls and primitives.
- **Travel:** with `travel` written in `touch_qa.txt`, it sails on from Hạ Long Skies to Vịnh Hạ Long to Đà Nẵng – Hội An through the pause menu and runs the checks again on each map.
- **How the touches travel:** they go through `Input.parse_input_event` at window coordinates, so they take the same path as a finger.
- **On desktop:** `godot --path . --resolution 1400x986 -- --touch-qa --quit` runs the same checks.

## iOS 27 fixes

- **UIScene lifecycle.** iOS 27 kills apps that still create their window in the app delegate, so `AppDelegate.swift` builds the React Native factory and a `SceneDelegate` makes the window.
- **fmt vs. Xcode 27's clang.** RN 0.81's `fmt` 11.0.2 uses `consteval` format strings that the new clang rejects. The Podfile `post_install` defines `FMT_USE_CONSTEVAL=0` and patches fmt's header so it honours that define.
