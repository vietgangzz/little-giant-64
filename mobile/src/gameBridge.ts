import { RTNGodot, runOnGodotThread } from "@borndotcom/react-native-godot";
import { Worklets } from "react-native-worklets-core";

/**
 * The line between the React Native shell and the game.
 *
 * The game's `Game` autoload (scripts/autoload/game.gd) keeps a listener: it
 * reports its state (boot → ready, loading:<level> while a level reloads) and
 * asks for haptics ("haptic:light" … "haptic:error"). Calls into Godot run on
 * the Godot thread as react-native-worklets-core worklets; the listener hops
 * back to the React Native JS thread with Worklets.createRunOnJS.
 */

export type GameEvent = { kind: "state"; value: string } | { kind: "haptic"; value: string };

/** Starts the engine with the packed game, on Metal with Godot's Mobile renderer. */
export function startGame(packPath: string) {
  return runOnGodotThread(() => {
    "worklet";
    if (RTNGodot.getInstance() != null) {
      return;
    }
    RTNGodot.createInstance([
      "--main-pack", packPath,
      "--display-driver", "embedded",
      "--rendering-driver", "metal",
      "--rendering-method", "mobile",
    ]);
  });
}

/**
 * Registers `onEvent` with the game. Resolves true once the Game autoload
 * exists and has taken the listener; false while the engine is still booting.
 */
export function listen(onEvent: (e: GameEvent) => void): Promise<boolean> {
  const toJS = Worklets.createRunOnJS((raw: string) => {
    const i = raw.indexOf(":");
    const kind = raw.slice(0, i);
    if (kind === "state" || kind === "haptic") onEvent({ kind, value: raw.slice(i + 1) });
  });
  return runOnGodotThread(() => {
    "worklet";
    try {
      if (RTNGodot.getInstance() == null) return false;
      const loop = RTNGodot.API().Engine.get_main_loop();
      if (loop == null) return false;
      const game = loop.get_root().find_child("Game", false, false);
      if (game == null) return false;
      game.rn_listen((raw: string) => {
        toJS(raw);
      });
      return true;
    } catch (e) {
      return false;
    }
  });
}

/** The app was left: the game opens its pause menu. */
export function pauseMenu(): Promise<void> {
  return runOnGodotThread(() => {
    "worklet";
    try {
      const loop = RTNGodot.API().Engine.get_main_loop();
      const game = loop?.get_root().find_child("Game", false, false);
      game?.rn_background();
    } catch (e) {
      // the engine isn't up yet: nothing to pause
    }
  });
}
