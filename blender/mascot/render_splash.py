"""Renders the waving mascot on a transparent background for the phone app's splash screen.

    blender -b blender/mascot/mascot.blend --python-exit-code 1 -P blender/mascot/render_splash.py
"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(__file__))
sys.argv = [sys.argv[0], "--", "--only", "none"]
import render_qa as qa  # noqa: E402  (reuses its lights, camera rig and pose helpers)

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "mobile", "assets", "hero.png")

cam = bpy.data.objects["QA_Cam"]  # render_qa's main() already built the rig on import
qa.sc.render.film_transparent = True
for o in list(bpy.data.objects):
    if o.name.startswith("QA_Floor"):
        bpy.data.objects.remove(o)
qa.set_action("wave", 17)
qa.aim(cam, 26, dist=3.6, height=1.0, target=(0.05, 0, 0.66))
qa.render(os.path.abspath(OUT), 640, 640)
print("splash ->", os.path.abspath(OUT))
