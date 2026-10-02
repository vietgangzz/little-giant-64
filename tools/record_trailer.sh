#!/usr/bin/env bash
# Records the trailer clips with Godot's Movie Maker at 60 fps, then cuts, joins and encodes
# them (see docs/TRAILER.md). Keep the Godot window visible while it records: macOS stops
# drawing occluded windows.
#   tools/record_trailer.sh           # the two-map trailer, 2560x1440
#   tools/record_trailer.sh danang    # the Đà Nẵng – Hội An trailer in an iPhone Duo frame
#                                     # (needs python3 with numpy and Pillow)
set -euo pipefail
cd "$(dirname "$0")/.."
FFMPEG=$(ls /opt/homebrew/Cellar/ffmpeg-full/*/bin/ffmpeg 2>/dev/null | tail -1 || command -v ffmpeg)
CUT="${1:-full}"

override() {
  cat > override.cfg <<CFG
[display]
window/size/window_width_override=$1
window/size/window_height_override=$2

[editor]
movie_writer/mjpeg_quality=0.95
CFG
}
trap 'rm -f override.cfg' EXIT
godot --headless --path . --import >/dev/null 2>&1 || true

if [ "$CUT" = danang ]; then
  OUT=build/trailer_dn
  mkdir -p "$OUT"
  # the Duo's unfolded screen, drawn by the phone renderer
  override 2034 1398
  godot --path . --rendering-method mobile --always-on-top --write-movie "$OUT/danang.avi" \
    -- --level=danang --phone --trailer=danang 2>&1 | tee "$OUT/danang.log" | grep -E "SHOT|DONE"
  rm -f override.cfg
  python3 tools/edit_trailer.py "$OUT" "$OUT/game_cut.mp4" "$FFMPEG" danang
  python3 tools/frame_trailer.py "$OUT/game_cut.mp4" "$OUT/danang-trailer-2k.mp4" "$FFMPEG"
  exit 0
fi

OUT=build/trailer
RAW=$OUT/raw
mkdir -p "$RAW"
override 2560 1440
for clip in skies halong finale; do
  extra=""
  [ "$clip" = halong ] && extra="--level=halong"
  echo "recording ${clip}..."
  godot --path . --always-on-top --write-movie "$RAW/$clip.avi" -- --trailer=$clip $extra 2>&1 \
    | tee "$RAW/$clip.log" | grep -E "SHOT|DONE|frames at"
done
rm -f override.cfg
python3 tools/edit_trailer.py "$RAW" "$OUT/little-giant-64-trailer.mp4" "$FFMPEG"
