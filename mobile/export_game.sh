#!/bin/bash
# Packs the Godot game (the repo root) into ios/LittleGiant64.pck for the
# React Native app. LibGodot 4.5.1 is embedded in @borndotcom/react-native-godot,
# so the pack must be made by a Godot 4.5.1 editor (the game itself targets 4.7
# and runs unchanged on 4.5; every star route passes on both). Set GODOT_EDITOR
# to that editor's binary.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd -P)"
ROOT="$(cd "$HERE/.." && pwd -P)"
GODOT="${GODOT_EDITOR:-$HOME/Applications/godot-4.5.1/Godot.app/Contents/MacOS/Godot}"
if [ ! -x "$GODOT" ]; then
  echo "Godot 4.5.1 editor not found. Set GODOT_EDITOR=/path/to/Godot (4.5.1)." >&2
  exit 1
fi
case "$("$GODOT" --version)" in
  4.5.1*) ;;
  *) echo "GODOT_EDITOR must be Godot 4.5.1 (LibGodot's version), got $("$GODOT" --version)" >&2; exit 1 ;;
esac
STAGE="$(mktemp -d)/game"
mkdir -p "$STAGE"
rsync -a --exclude .godot --exclude build --exclude mobile --exclude docs --exclude blender --exclude tools --exclude .git "$ROOT/" "$STAGE/"
sed -i '' 's/"4.7", "Forward Plus"/"4.5", "Forward Plus"/' "$STAGE/project.godot"
"$GODOT" --headless --path "$STAGE" --import >/dev/null 2>&1 || true
"$GODOT" --headless --path "$STAGE" --import >/dev/null 2>&1 || true
"$GODOT" --headless --path "$STAGE" --export-pack "iOS" "$HERE/ios/LittleGiant64.pck" 2>&1 | grep -E "ERROR|error" || true
ls -la "$HERE/ios/LittleGiant64.pck"
