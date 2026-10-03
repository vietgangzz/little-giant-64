#!/usr/bin/env python3
"""Cuts the Movie Maker clips into a trailer (docs/TRAILER.md).

Reads the SHOT frame ranges each clip printed, keeps a window of every shot, joins the pieces
with short cross-fades (picture and sound) and encodes H.264 at 60 fps + AAC.
  full:   the ~60 s two-map trailer from skies/halong/finale clips, 2560x1440
  danang: the ~30 s Đà Nẵng – Hội An cut, at the clip's own size; tools/frame_trailer.py then
          puts it in the phone frame. When OUT ends in .mkv the cut is lossless (FFV1 RGB + PCM).
A clip is RAW/<clip>.avi, or a Movie Maker PNG sequence RAW/<clip>/frame%08d.png + frame.wav.
usage: edit_trailer.py RAW_DIR OUT FFMPEG [full|danang]
"""
import re, subprocess, sys
from pathlib import Path

RAW, OUT, FFMPEG = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
CUT = sys.argv[4] if len(sys.argv) > 4 else "full"
FPS = 60
XF = 0.25  # cross-fade seconds

# clip, shot, how many seconds to keep, where from: "head" (start) or "tail" (end) or seconds offset
PLANS = {}
PLANS["full"] = [
    ("skies", "title", 3.5, "head"),
    ("skies", "mascot", 4.4, "head"),
    ("skies", "moves", 4.8, "head"),
    ("skies", "block_spring", 4.6, "head"),
    ("skies", "terraces_star", 5.2, "tail"),
    ("skies", "montage", 5.2, "head"),
    ("skies", "boat", 3.0, "head"),
    ("halong", "bay", 4.4, "head"),
    ("halong", "village", 3.4, "head"),
    ("halong", "cave", 3.6, "head"),
    ("halong", "trongmai", 3.6, "head"),
    ("halong", "board_dragon", 3.2, "head"),
    ("halong", "titop_star", 6.6, "tail"),
    ("finale", "all_stars", 5.4, 0.9),
    ("finale", "all_stars", 4.2, "tail"),
]
PLANS["danang"] = [
    ("danang", "intro", 4.0, "head"),
    ("danang", "dragon_star", 4.0, "head"),
    ("danang", "dragon_star", 2.6, "tail"),
    ("danang", "fire", 3.0, 0.3),
    ("danang", "cable_car", 3.2, 0.2),
    ("danang", "golden_star", 3.8, "tail"),
    ("danang", "hoi_an", 2.6, "head"),
    ("danang", "chua_cau", 2.8, "tail"),
    ("danang", "baskets", 3.0, 0.2),
    ("danang", "fireworks", 4.2, 0.8),
]
PLAN = PLANS[CUT]
CLIPS = list(dict.fromkeys(c for c, *_ in PLAN))

shots = {}
for clip in CLIPS:
    for line in (RAW / f"{clip}.log").read_text().splitlines():
        m = re.match(r"SHOT (\S+) (\d+) (\d+)", line)
        if m:
            shots[(clip, m[1])] = (int(m[2]) / FPS, int(m[3]) / FPS)

LOSSLESS = OUT.endswith(".mkv")
PIX = "gbrp" if LOSSLESS else "yuv420p"
# every clip brings a video and an audio input: [video index, audio index]
inputs, in_args = {}, []
for clip in CLIPS:
    seq = RAW / clip
    if seq.is_dir():
        inputs[clip] = (len(in_args), len(in_args) + 1)
        in_args += [["-framerate", str(FPS), "-i", str(seq / "frame%08d.png")], ["-i", str(seq / "frame.wav")]]
    else:
        inputs[clip] = (len(in_args), len(in_args))
        in_args += [["-i", str(RAW / f"{clip}.avi")]]
parts, durs = [], []
for i, (clip, name, keep, where) in enumerate(PLAN):
    a, b = shots[(clip, name)]
    offset = 0.0 if where in ("head", "tail") else where
    keep = min(keep, b - a - offset)
    start = a if where == "head" else (b - keep if where == "tail" else a + offset)
    vi, ai = inputs[clip]
    parts.append(f"[{vi}:v]trim=start={start:.3f}:duration={keep:.3f},setpts=PTS-STARTPTS,fps={FPS},format={PIX}[v{i}];"
                 f"[{ai}:a]atrim=start={start:.3f}:duration={keep:.3f},asetpts=PTS-STARTPTS,aresample=48000[a{i}];")
    durs.append(keep)
    print(f"{clip:7s} {name:14s} {start:7.2f}s + {keep:.2f}s")

chain = "".join(parts)
v, a, t = "v0", "a0", durs[0]
for i in range(1, len(durs)):
    t -= XF
    chain += f"[{v}][v{i}]xfade=transition=fade:duration={XF}:offset={t:.3f}[vx{i}];"
    chain += f"[{a}][a{i}]acrossfade=d={XF}[ax{i}];"
    v, a = f"vx{i}", f"ax{i}"
    t += durs[i]
total = t
chain += f"[{v}]fade=t=in:d=0.4,fade=t=out:st={total - 0.8:.3f}:d=0.8[vout];"
chain += f"[{a}]afade=t=in:d=0.3,afade=t=out:st={total - 1.0:.3f}:d=1.0,loudnorm=I=-15:TP=-1.0[aout]"
print(f"total {total:.2f}s")

cmd = [FFMPEG, "-y", "-v", "error"]
for args in in_args:
    cmd += args
cmd += ["-filter_complex", chain, "-map", "[vout]", "-map", "[aout]", "-r", str(FPS)]
if LOSSLESS:
    cmd += ["-c:v", "ffv1", "-level", "3", "-pix_fmt", "gbrp", "-c:a", "pcm_s16le", OUT]
else:
    cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", "16" if CUT == "full" else "10", "-profile:v", "high",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT]
subprocess.run(cmd, check=True)
print("wrote", OUT)
