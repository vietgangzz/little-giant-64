#!/usr/bin/env bash
# Records the trailer clips with Godot's Movie Maker at 60 fps, then cuts, joins and encodes
# them (see docs/TRAILER.md). Keep the Godot window visible while it records: macOS stops
# drawing occluded windows.
#   tools/record_trailer.sh           # the two-map trailer, 2560x1440
#   tools/record_trailer.sh danang    # the Đà Nẵng – Hội An trailer in an iPhone Duo frame, 4K
#                                     # (needs python3 with numpy and Pillow, ~20 GB of disk)
set -euo pipefail
cd "$(dirname "$0")/.."
# FFMPEG=/path/to/ffmpeg overrides; Homebrew's ffmpeg-full is preferred when installed
FFMPEG=${FFMPEG:-$(command -v /opt/homebrew/opt/ffmpeg-full/bin/ffmpeg || command -v ffmpeg || true)}
: "${FFMPEG:?install ffmpeg or set FFMPEG=/path/to/ffmpeg}"
CUT="${1:-full}"

# A borderless window may be larger than the display; a titled one is shrunk to fit it, and
# Movie Maker would then record a stretched picture with the UI laid out for the wrong size.
override() {
  cat > override.cfg <<CFG
[display]
window/size/window_width_override=$1
window/size/window_height_override=$2
window/size/borderless=true

[editor]
movie_writer/mjpeg_quality=0.95
CFG
}
trap 'rm -f override.cfg' EXIT
godot --headless --path . --import >/dev/null 2>&1 || true

if [ "$CUT" = danang ]; then
  # 4K: the game is filmed as lossless PNG frames at the Duo's screen size in a 3840x2160
  # frame (2220x1526), with the 3D supersampled 2x; the cut stays lossless (FFV1 + PCM); the
  # result is a ProRes 422 HQ master plus an H.264 copy for upload
  OUT=build/trailer_4k
  rm -rf "$OUT/danang"
  mkdir -p "$OUT/danang"
  override 2220 1526
  godot --path . --rendering-method mobile --always-on-top --position 0,0 --write-movie "$OUT/danang/frame.png" \
    -- --level=danang --phone --ssaa --trailer=danang 2>&1 | tee "$OUT/danang.log" | grep -E "SHOT|DONE"
  rm -f override.cfg
  python3 tools/edit_trailer.py "$OUT" "$OUT/game_cut.mkv" "$FFMPEG" danang
  python3 tools/frame_trailer.py "$OUT/game_cut.mkv" "$OUT/danang-trailer-4k-master.mov" "$FFMPEG" "$OUT/danang-trailer-4k.mp4"
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
  godot --path . --always-on-top --position 0,0 --write-movie "$RAW/$clip.avi" -- --trailer=$clip $extra 2>&1 \
    | tee "$RAW/$clip.log" | grep -E "SHOT|DONE|frames at"
done
rm -f override.cfg
python3 tools/edit_trailer.py "$RAW" "$OUT/little-giant-64-trailer.mp4" "$FFMPEG"
