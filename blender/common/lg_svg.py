"""Tiny SVG path helpers shared by the Little Giant 64 Blender scripts.

Pure Python (no bpy), so it can be unit-tested outside Blender.
Supports the commands used by the brand vectors (M, L, H, V, Q, T, C, S, Z,
absolute and relative). Curves are flattened into polylines.
"""

import json
import math
import os
import re

_TOKEN = re.compile(r"[MmLlHhVvQqTtCcSsZz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")

HERE = os.path.dirname(os.path.abspath(__file__))


def load_artwork():
    """Return the approved brand vectors (body, eyes, rays) as a dict."""
    with open(os.path.join(HERE, "mascot_artwork.json"), "r", encoding="utf-8") as fh:
        return json.load(fh)


def _quad(p0, p1, p2, t):
    a = (1 - t) * (1 - t)
    b = 2 * (1 - t) * t
    c = t * t
    return (a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1])


def _cubic(p0, p1, p2, p3, t):
    u = 1 - t
    a, b, c, d = u * u * u, 3 * u * u * t, 3 * u * t * t, t * t * t
    return (a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
            a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1])


def _dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def parse_path(d, step=2.0, subdivide_lines=True):
    """Flatten an SVG path string into a list of closed polylines.

    `step` is the approximate spacing between samples in SVG units. Straight
    segments are subdivided too (unless `subdivide_lines` is False), so the
    output is evenly sampled.
    Returns a list of subpaths; each is a list of (x, y) in SVG space
    (y down), without the duplicated closing point.
    """
    toks = _TOKEN.findall(d)
    i = 0
    cmd = None
    cur = (0.0, 0.0)
    start = (0.0, 0.0)
    last_ctrl = None
    subpaths = []
    pts = []

    def num():
        nonlocal i
        v = float(toks[i])
        i += 1
        return v

    def add_line(a, b):
        n = max(1, int(math.ceil(_dist(a, b) / step))) if subdivide_lines else 1
        for k in range(1, n + 1):
            t = k / n
            pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))

    def add_curve(fn, approx_len):
        n = max(2, int(math.ceil(approx_len / step)))
        for k in range(1, n + 1):
            pts.append(fn(k / n))

    while i < len(toks):
        t = toks[i]
        if re.match(r"[A-Za-z]", t):
            cmd = t
            i += 1
            if cmd in "Zz":
                if pts:
                    if _dist(cur, start) > 1e-9:
                        add_line(cur, start)
                    subpaths.append(pts)
                pts = []
                cur = start
                last_ctrl = None
                continue
        rel = cmd.islower()
        c = cmd.upper()
        ox, oy = (cur if rel else (0.0, 0.0))
        if c == "M":
            p = (num() + ox, num() + oy)
            if pts:
                subpaths.append(pts)
            pts = [p]
            cur = start = p
            cmd = "l" if rel else "L"  # implicit lineto after moveto
            last_ctrl = None
        elif c == "L":
            p = (num() + ox, num() + oy)
            add_line(cur, p)
            cur = p
            last_ctrl = None
        elif c == "H":
            p = (num() + (cur[0] if rel else 0.0), cur[1])
            add_line(cur, p)
            cur = p
            last_ctrl = None
        elif c == "V":
            p = (cur[0], num() + (cur[1] if rel else 0.0))
            add_line(cur, p)
            cur = p
            last_ctrl = None
        elif c in "QT":
            if c == "Q":
                c1 = (num() + ox, num() + oy)
            else:
                c1 = (2 * cur[0] - last_ctrl[0], 2 * cur[1] - last_ctrl[1]) if last_ctrl else cur
            p = (num() + ox, num() + oy)
            p0 = cur
            approx = _dist(p0, c1) + _dist(c1, p)
            add_curve(lambda tt, p0=p0, c1=c1, p=p: _quad(p0, c1, p, tt), approx)
            cur = p
            last_ctrl = c1
        elif c in "CS":
            if c == "C":
                c1 = (num() + ox, num() + oy)
            else:
                c1 = (2 * cur[0] - last_ctrl[0], 2 * cur[1] - last_ctrl[1]) if last_ctrl else cur
            c2 = (num() + ox, num() + oy)
            p = (num() + ox, num() + oy)
            p0 = cur
            approx = _dist(p0, c1) + _dist(c1, c2) + _dist(c2, p)
            add_curve(lambda tt, p0=p0, c1=c1, c2=c2, p=p: _cubic(p0, c1, c2, p, tt), approx)
            cur = p
            last_ctrl = c2
        else:
            raise ValueError("unsupported SVG command %r" % cmd)
    if pts:
        subpaths.append(pts)

    # drop near-duplicate points and the closing duplicate
    out = []
    for sp in subpaths:
        clean = []
        for p in sp:
            if not clean or _dist(clean[-1], p) > step * 0.25:
                clean.append(p)
        if len(clean) > 2 and _dist(clean[0], clean[-1]) < step * 0.25:
            clean.pop()
        out.append(clean)
    return out


def signed_area(poly):
    a = 0.0
    n = len(poly)
    for k in range(n):
        x0, y0 = poly[k]
        x1, y1 = poly[(k + 1) % n]
        a += x0 * y1 - x1 * y0
    return 0.5 * a


def bbox(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return min(xs), min(ys), max(xs), max(ys)
