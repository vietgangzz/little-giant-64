import "setimmediate"; // required by the New Architecture
import React, { useCallback, useEffect, useRef, useState } from "react";
import { AppState, StatusBar, StyleSheet, View } from "react-native";
import { RTNGodot, RTNGodotView } from "@borndotcom/react-native-godot";
import * as FileSystem from "expo-file-system/legacy";
import * as Haptics from "expo-haptics";
import { Easing, useSharedValue, withTiming } from "react-native-reanimated";
import { Curtain } from "./src/Curtain";
import { type GameEvent, listen, pauseMenu, startGame } from "./src/gameBridge";

/**
 * Little Giant: Star Hop on phones. The whole game is the Godot project at
 * the repo root, packed into ios/LittleGiant64.pck and run by the LibGodot
 * engine embedded through @borndotcom/react-native-godot. React Native owns
 * the shell around it:
 *
 *  - a Skia + Reanimated splash that stays up until the game reports it is
 *    on screen, then irises open onto it (and closes again for level trips)
 *  - the iOS haptic engine, played when the game asks
 *  - pausing: leaving the app opens the game's pause menu and halts the engine
 */

const PACK = "LittleGiant64.pck";
/** The splash never flashes by faster than this. */
const MIN_SPLASH_MS = 1800;
/** If the game never reports in (a broken bridge), open anyway. */
const FALLBACK_MS = 15000;

const LEVELS: Record<string, string> = { skies: "Hạ Long Skies", halong: "Vịnh Hạ Long" };
const TIPS = [
  "Jump again in the air for a double jump",
  "Jump just as you land to jump higher",
  "Ground-pound a spring drum for a super bounce",
  "Every 50 coins restores a health pebble",
  "The junk boat sails between the two maps",
];

export default function App() {
  const [gameState, setGameState] = useState("boot");
  const [minDone, setMinDone] = useState(false);
  const [tip] = useState(() => TIPS[Math.floor(Math.random() * TIPS.length)]);
  const progress = useSharedValue(0);
  const booted = useRef(false);

  const onEvent = useCallback((e: GameEvent) => {
    if (e.kind === "state") {
      setGameState(e.value);
    } else {
      playHaptic(e.value);
    }
  }, []);

  // boot the engine, then keep offering the listener until the game takes it
  useEffect(() => {
    startGame(FileSystem.bundleDirectory + PACK);
    progress.value = withTiming(0.88, { duration: 7000, easing: Easing.out(Easing.cubic) });
    let alive = true;
    const attach = async () => {
      while (alive && !(await listen(onEvent))) {
        await new Promise<void>((r) => setTimeout(r, 250));
      }
    };
    attach();
    const minTimer = setTimeout(() => setMinDone(true), MIN_SPLASH_MS);
    const fallback = setTimeout(() => setGameState((s) => (s === "boot" ? "ready" : s)), FALLBACK_MS);
    return () => {
      alive = false;
      clearTimeout(minTimer);
      clearTimeout(fallback);
    };
  }, [onEvent, progress]);

  useEffect(() => {
    if (gameState === "ready") {
      booted.current = true;
      progress.value = withTiming(1, { duration: 250 });
    } else if (gameState.startsWith("loading")) {
      progress.value = 0.15;
      progress.value = withTiming(0.9, { duration: 2500, easing: Easing.out(Easing.cubic) });
    }
  }, [gameState, progress]);

  // leaving the app pauses the game; coming back resumes the engine on the pause menu
  useEffect(() => {
    const sub = AppState.addEventListener("change", (s) => {
      if (RTNGodot.getInstance() == null) return;
      if (s === "active") {
        RTNGodot.resume();
      } else {
        pauseMenu().then(() => {
          if (s === "background") RTNGodot.pause();
        });
      }
    });
    return () => sub.remove();
  }, []);

  const covered = gameState !== "ready" || !minDone;
  const trip = gameState.startsWith("loading:") ? LEVELS[gameState.slice(8)] : undefined;
  const caption = trip ? `Sailing to ${trip}…` : `Tip: ${tip}`;

  return (
    <View style={styles.root}>
      <StatusBar hidden />
      <RTNGodotView style={styles.godot} />
      <Curtain covered={covered} progress={progress} caption={caption} />
    </View>
  );
}

function playHaptic(kind: string) {
  switch (kind) {
    case "light":
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      break;
    case "medium":
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      break;
    case "heavy":
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
      break;
    case "success":
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      break;
    case "error":
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      break;
  }
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: "#5fb4ee" },
  godot: { flex: 1 },
});
