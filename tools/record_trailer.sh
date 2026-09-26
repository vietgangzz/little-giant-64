#!/usr/bin/env bash
# Records the three trailer clips with Godot's Movie Maker at 2560x1440 / 60 fps, then cuts,
# joins and encodes them (see docs/TRAILER.md). Keep the Godot window visible while it records:
# macOS stops drawing occluded windows.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=build/trailer
RAW=$OUT/raw
mkdir -p "$RAW"
FFMPEG=$(ls /opt/homebrew/Cellar/ffmpeg-full/*/bin/ffmpeg 2>/dev/null | tail -1 || command -v ffmpeg)

cat > override.cfg <<'CFG'
[display]
window/size/window_width_override=2560
window/size/window_height_override=1440

[editor]
movie_writer/mjpeg_quality=0.95
CFG
trap 'rm -f override.cfg' EXIT

godot --headless --path . --import >/dev/null 2>&1 || true
for clip in skies halong finale; do
  extra=""
  [ "$clip" = halong ] && extra="--level=halong"
  echo "recording ${clip}..."
  godot --path . --always-on-top --write-movie "$RAW/$clip.avi" -- --trailer=$clip $extra 2>&1 \
    | tee "$RAW/$clip.log" | grep -E "SHOT|DONE|frames at"
done
rm -f override.cfg
python3 tools/edit_trailer.py "$RAW" "$OUT/little-giant-64-trailer.mp4" "$FFMPEG"
