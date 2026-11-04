#!/usr/bin/env python3
"""Jarvis-style spec HUD over the Samsung spec film (Narayan, 4 Nov: "add the specs ... Jarvis type of animated text").

Every value is from Samsung's official Galaxy Z Fold8 Ultra page (samsung.com, read 4 Nov 2026; see plan.md). No
invented numbers: the only other text is a shot index and a plain label. Per component shot: corner brackets lock on,
a leader line draws out, then the label types on and the value decodes left to right. It all cuts with the shot.

Frames are those of takes/edit-v1-720.mp4 (289 frames, 24 fps); any resolution of it works (positions are relative).
Run it last, on the finished film, so the lines stay crisp.

  python3 ads/samsung-spec/fold8-ultra-12s/hud_overlay.py <in.mp4> <out.mp4> [--qa <dir>]
"""
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FPS = 24
LINE = (226, 242, 255)
ACCENT = (110, 214, 255)
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
SANS = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
LIGHT = "/usr/share/fonts/opentype/inter/Inter-Light.otf"
SCRAMBLE = "0123456789ABCDEF#%/<>"

# One callout per shot. box = what the brackets lock onto, anchor = where the leader starts, text = the panel's top-left
# corner (all as fractions of the frame); lines = (label, value, sub). Shots and frames from the cut list in plan.md.
CALLOUTS = [
    dict(shot=(76, 106), idx="03", box=(0.20, 0.06, 0.86, 0.94), anchor=(0.80, 0.58), text=(0.55, 0.585),
         lines=("CAMERA", "200MP WIDE", "50MP ULTRA-WIDE\n10MP 3X TELEPHOTO"), small=True),
    dict(shot=(124, 136), idx="05", box=(0.50, 0.50, 0.76, 0.72), anchor=(0.56, 0.56), text=(0.07, 0.30),
         lines=("HINGE", "ARMOR FLEXHINGE", None)),
    dict(shot=(147, 159), idx="07", box=(0.42, 0.18, 0.86, 0.52), anchor=(0.50, 0.50), text=(0.07, 0.80),
         lines=("ZOOM", "UP TO 30X", "DIGITAL ZOOM")),
    dict(shot=(159, 177), idx="08", box=(0.33, 0.36, 0.82, 0.64), anchor=(0.36, 0.62), text=(0.07, 0.76),
         lines=("PROCESSOR", "SNAPDRAGON 8 ELITE GEN 5", "FOR GALAXY")),
    dict(shot=(177, 192), idx="09", box=(0.27, 0.10, 0.56, 0.92), anchor=(0.55, 0.42), text=(0.62, 0.36),
         lines=("BATTERY", "5000 mAh", None)),
    dict(shot=(192, 205), idx="10", box=(0.06, 0.24, 0.94, 0.90), anchor=(0.50, 0.24), text=(0.07, 0.06),
         lines=("DISPLAY", "FLEX TITANIUM", "GORILLA GLASS VICTUS 2")),
    dict(shot=(205, 234), idx="11", box=(0.08, 0.30, 0.90, 0.81), anchor=(0.50, 0.30), text=(0.07, 0.08),
         lines=("MAIN SCREEN", '8.0"', "3000 NITS PEAK")),
    dict(shot=(234, 248), idx="12", box=(0.17, 0.24, 0.63, 0.95), anchor=(0.63, 0.50), text=(0.68, 0.44),
         lines=("BUILD", "4.1 MM", "215 G")),
]


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def decode(text, p, seed):
    """`text` revealed left to right for progress p (0..1), with a short run of scrambled glyphs at the head."""
    n = len(text)
    r = int(round(p * n))
    rng = np.random.default_rng(seed)
    head = "".join(c if c == " " else SCRAMBLE[rng.integers(len(SCRAMBLE))] for c in text[r:r + 3])
    return text[:r] + (head if p < 1 else "")


def draw_callout(W, H, c, t, L):
    """The callout's RGBA layer at frame t (0-based) of a shot L frames long."""
    s = W / 1080
    k = min(1.0, L / 24)                                   # short shots animate faster
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    flicker = [0.45, 1.0, 0.7][t] if t < 3 else 1.0
    a = int(255 * flicker)
    lw = max(2, round(2 * s))

    # 1. brackets lock onto the component, closing in from 12% out
    x0, y0, x1, y1 = c["box"]
    g = 1 + 0.12 * (1 - ease(t / (6 * k)))
    cx, cy, hw, hh = (x0 + x1) / 2 * W, (y0 + y1) / 2 * H, (x1 - x0) / 2 * W * g, (y1 - y0) / 2 * H * g
    arm = 0.18 * min(hw, hh) * 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = cx + sx * hw, cy + sy * hh
            d.line([(px, py - sy * arm), (px, py), (px - sx * arm, py)], fill=LINE + (a,), width=lw)
    # tick marks along the top edge of the box, like a range scale
    for i in range(1, 12):
        tx = cx - hw + i * 2 * hw / 12
        d.line([(tx, cy - hh), (tx, cy - hh + (10 if i % 3 == 0 else 5) * s)], fill=LINE + (a // 2,), width=1)

    # 2. a rotating reticle on the anchor
    ax, ay = c["anchor"][0] * W, c["anchor"][1] * H
    rr = 16 * s
    rot = t * 9
    for q in range(4):
        st = rot + q * 90
        d.arc([ax - rr, ay - rr, ax + rr, ay + rr], st, st + 50, fill=ACCENT + (a,), width=lw)
    d.ellipse([ax - 3 * s, ay - 3 * s, ax + 3 * s, ay + 3 * s], fill=ACCENT + (a,))

    # 3. the leader line draws out from the reticle to the panel
    tx, ty = c["text"][0] * W, c["text"][1] * H
    right = tx > ax
    ex = tx - 14 * s if right else tx + 14 * s
    pts = [(ax, ay), (ex, ty + 18 * s), (tx, ty + 18 * s)] if right else [(ax, ay), (ax, ty + 18 * s), (tx - 6 * s, ty + 18 * s)]
    p = ease((t - 2 * k) / (5 * k))
    segs = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    want, drawn = p * sum(segs), [pts[0]]
    for i, sl in enumerate(segs):
        if want <= 0:
            break
        f = min(1.0, want / sl) if sl else 1.0
        drawn.append((pts[i][0] + f * (pts[i + 1][0] - pts[i][0]), pts[i][1] + f * (pts[i + 1][1] - pts[i][1])))
        want -= sl
    if len(drawn) > 1:
        d.line(drawn, fill=LINE + (int(a * 0.8),), width=lw)

    # 4. the panel: a dark glass plate, a shot index, the label typing on, the value decoding
    label, value, sub = c["lines"]
    small = c.get("small")
    f_lab = ImageFont.truetype(MONO, round(24 * s))
    f_val = ImageFont.truetype(SANS, round((46 if small else 64) * s))
    f_sub = ImageFont.truetype(LIGHT, round((26 if small else 30) * s))
    px, py = tx + 10 * s, ty + 34 * s
    t0 = 4 * k
    lab = f"[{c['idx']}]  {label}"
    lab_s = decode(lab, ease((t - t0) / (4 * k)), seed=t)
    val_s = decode(value, ease((t - t0 - 2 * k) / (8 * k)), seed=t + 99) if t >= t0 + 2 * k else ""
    sub_s = [decode(x, ease((t - t0 - (5 + 2 * j) * k) / (6 * k)), seed=t + 7 + j) if t >= t0 + (5 + 2 * j) * k else ""
             for j, x in enumerate(sub.split("\n"))] if sub else []
    subs = sub.split("\n") if sub else []
    wv = max([d.textlength(value, font=f_val), d.textlength(lab, font=f_lab)] + [d.textlength(x, font=f_sub) for x in subs])
    hv = (24 + 14 + (46 if small else 64) + (14 + 36 * len(subs) if subs else 0) + 14) * s
    if t >= t0:
        plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(plate).rectangle([px - 14 * s, py - 12 * s, px + wv + 18 * s, py + hv], fill=(2, 8, 16, int(120 * flicker)))
        layer = Image.alpha_composite(plate, layer)
        d = ImageDraw.Draw(layer)
        d.line([(px - 14 * s, py - 12 * s), (px - 14 * s, py + hv)], fill=ACCENT + (a,), width=lw)
    d.text((px, py), lab_s, font=f_lab, fill=ACCENT + (a,))
    vy = py + 38 * s
    d.text((px, vy), val_s, font=f_val, fill=(255, 255, 255, a))
    if val_s and len(val_s) < len(value) + 3 and val_s != value:
        cw = d.textlength(val_s, font=f_val)
        d.rectangle([px + cw + 4 * s, vy + 8 * s, px + cw + 4 * s + 0.45 * f_val.size, vy + f_val.size * 1.05], fill=ACCENT + (a,))
    for j, x in enumerate(sub_s):
        d.text((px, vy + ((46 if small else 64) + 14 + 36 * j) * s), x, font=f_sub, fill=LINE + (int(a * 0.9),))
    return layer


def composite(frame_rgb, layer, s):
    """The HUD over the frame with a soft glow under its lines."""
    base = Image.fromarray(frame_rgb).convert("RGBA")
    glow = layer.filter(ImageFilter.GaussianBlur(5 * s))
    base = Image.alpha_composite(base, glow)
    return np.asarray(Image.alpha_composite(base, layer).convert("RGB"))


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height",
                          "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
    return tuple(int(v) for v in out.split(","))


def main():
    a = sys.argv[1:]
    src, dst = a[0], a[1]
    qa = Path(a[a.index("--qa") + 1]) if "--qa" in a else None
    W, H = probe(src)
    s = W / 1080
    dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "12", "-preset", "slow", "-pix_fmt",
                            "yuv420p", "-movflags", "+faststart", dst], stdin=subprocess.PIPE)
    n = 0
    while True:
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        f = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        for c in CALLOUTS:
            if c["shot"][0] <= n < c["shot"][1]:
                L = c["shot"][1] - c["shot"][0]
                f = composite(f, draw_callout(W, H, c, n - c["shot"][0], L), s)
                if qa and n - c["shot"][0] == L - 2:
                    qa.mkdir(parents=True, exist_ok=True)
                    Image.fromarray(f).save(qa / f"f{n:03d}.png")
        enc.stdin.write(np.ascontiguousarray(f).tobytes())
        n += 1
    enc.stdin.close()
    enc.wait()
    dec.wait()
    print(f"wrote {dst}: {n} frames")


if __name__ == "__main__":
    main()
