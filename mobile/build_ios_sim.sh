#!/bin/bash
# Re-packs the Godot game and builds the Release app for an iOS simulator, then
# installs and launches it there when a simulator id is given.
#   ./build_ios_sim.sh                   # build for "iPhone Duo"
#   ./build_ios_sim.sh <simulator-udid>  # build, install and launch on that simulator
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd -P)"
"$HERE/export_game.sh"
DEST="${1:+id=$1}"
cd "$HERE/ios"
set +o pipefail
xcodebuild -workspace LittleGiant64.xcworkspace -scheme LittleGiant64 \
  -configuration Release -sdk iphonesimulator \
  -destination "platform=iOS Simulator,${DEST:-name=iPhone Duo}" \
  -derivedDataPath build/dd ARCHS=arm64 ONLY_ACTIVE_ARCH=YES build | grep -E "BUILD (SUCCEEDED|FAILED)|error:"
set -o pipefail
APP="$HERE/ios/build/dd/Build/Products/Release-iphonesimulator/LittleGiant64.app"
[ -d "$APP" ] || exit 1
echo "App: $APP"
if [ -n "${1:-}" ]; then
  xcrun simctl install "$1" "$APP"
  xcrun simctl launch "$1" studio.vgang.littlegiant64.native
fi
