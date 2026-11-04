#!/usr/bin/env python3
"""Spec supers over the Samsung spec film (Narayan, 4 Nov: "Jarvis type of animated text"; then "the text looks like
slop", so v2 is stripped back: one typeface, one position, no boxes, no scrambled glyphs, no shot numbers).

Every value is from Samsung's official Galaxy Z Fold8 Ultra page (samsung.com, read 4 Nov 2026; see plan.md).
Six supers, only on shots long enough to read (short ones are skipped or share a super with the next shot). Each one:
a hairline draws out (from a small ring on the part, where the part holds still), the label wipes on, then the value
wipes on behind a thin light edge, like a scan. Same baseline every time; left-aligned, or right-aligned where the
part fills the left. A soft shadow keeps it legible; it cuts with the shot.

Frames are those of takes/edit-v1-720.mp4 (24 fps); any resolution works (positions are relative). Run it last, on
the finished film. --offset shifts every super (62 for the v4 edit: the opener before v1; 24 for v3).

  python3 ads/samsung-spec/fold8-ultra-12s/hud_overlay.py <in.mp4> <out.mp4> [--offset 62] [--crf 12] [--qa <dir>]
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FPS = 24
REG = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
LIGHT = "/usr/share/fonts/opentype/inter/Inter-Light.otf"
ICE = (178, 226, 255)
MARGIN = 0.085                    # left/right margin, fraction of width
BASE = 0.86                       # value baseline, fraction of height

# frames (end exclusive) in edit-v1 numbering; ring = a point on the part (fraction of frame), or None
SUPERS = [
    dict(frames=(76, 106), label="WIDE CAMERA", value="200MP", align="left", ring=None),
    dict(frames=(124, 147), label="HINGE", value="Armor FlexHinge", align="left", ring=None),
    dict(frames=(159, 177), label="PROCESSOR", value="Snapdragon 8 Elite Gen 5", sub="for Galaxy", align="left",
         ring=(0.58, 0.50)),
    dict(frames=(177, 192), label="BATTERY", value="5000 mAh", align="right", ring=None, size=64),
    dict(frames=(205, 234), label="MAIN SCREEN", value='8.0"', align="left", ring=None),
    dict(frames=(234, 248), label="THICKNESS", value="4.1 mm", align="right", ring=None),
]


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def tracked(d, xy, text, font, fill, track):
    """Text with extra letter spacing; returns its width."""
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + track
    return x - xy[0] - track


def tracked_len(d, text, font, track):
    return sum(d.textlength(c, font=font) for c in text) + track * (len(text) - 1)


def wipe(img, x0, x1, p):
    """Keep only the part of RGBA `img` left of x0 + p * (x1 - x0)."""
    if p >= 1:
        return img
    cut = int(x0 + p * (x1 - x0))
    a = np.array(img)
    a[:, max(cut, 0):, 3] = 0
    return Image.fromarray(a)


def render(W, H, sp, t, L):
    s = W / 1080
    k = min(1.0, L / 22)                                   # short shots animate faster
    f_lab = ImageFont.truetype(REG, round(24 * s))
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    size = sp.get("size", 78)
    f_val = ImageFont.truetype(LIGHT, round(size * s))
    while d0.textlength(sp["value"], font=f_val) > (1 - 2 * MARGIN) * W and size > 40:
        size -= 2
        f_val = ImageFont.truetype(LIGHT, round(size * s))
    f_sub = ImageFont.truetype(REG, round(24 * s))
    track = 0.22 * f_lab.size
    wv = d0.textlength(sp["value"], font=f_val)
    wl = tracked_len(d0, sp["label"], f_lab, track)
    ws = d0.textlength(sp.get("sub", ""), font=f_sub)
    wmax = max(wv, wl, ws)
    right = sp["align"] == "right"
    x0 = (1 - MARGIN) * W - wmax if right else MARGIN * W
    asc = f_val.getmetrics()[0]
    vy = BASE * H - asc                                    # value top
    ly = vy - 38 * s                                       # label top
    hy = ly - 22 * s                                       # hairline
    sy = vy + asc + 14 * s                                 # sub top

    text = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(text)
    # label
    lx = x0 + (wmax - wl if right else 0)
    tracked(d, (lx, ly), sp["label"], f_lab, (255, 255, 255, 200), track)
    text = wipe(text, lx, lx + wl, ease((t - 2 * k) / (5 * k)))
    # value, with a light edge riding the wipe
    val = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dv = ImageDraw.Draw(val)
    vx = x0 + (wmax - wv if right else 0)
    rise = (1 - ease((t - 3 * k) / (7 * k))) * 10 * s
    dv.text((vx, vy + rise), sp["value"], font=f_val, fill=(255, 255, 255, 255))
    if sp.get("sub"):
        sx = x0 + (wmax - ws if right else 0)
        dv.text((sx, sy + rise), sp["sub"], font=f_sub, fill=(255, 255, 255, 190))
    pv = ease((t - 3 * k) / (7 * k))
    val = wipe(val, vx, vx + max(wv, ws), pv)
    if 0 < pv < 1:
        ex = vx + pv * max(wv, ws)
        dv = ImageDraw.Draw(val)
        dv.rectangle([ex, vy + 4 * s, ex + 2 * s, vy + asc + 6 * s], fill=ICE + (220,))
    text = Image.alpha_composite(text, val)

    # hairline (and, where the part holds still, a ring on it with a line down to the hairline)
    lines = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lines)
    lw = max(1, round(1.5 * s))
    hl = 0.10 * W
    ph = ease(t / (6 * k))
    if right:
        dl.line([((1 - MARGIN) * W - hl * ph, hy), ((1 - MARGIN) * W, hy)], fill=ICE + (230,), width=lw)
    else:
        dl.line([(x0, hy), (x0 + hl * ph, hy)], fill=ICE + (230,), width=lw)
    if sp.get("ring"):
        rx, ry = sp["ring"][0] * W, sp["ring"][1] * H
        r = 11 * s
        pr = ease(t / (4 * k))
        dl.arc([rx - r, ry - r, rx + r, ry + r], -90, -90 + 360 * pr, fill=ICE + (230,), width=lw)
        dl.ellipse([rx - 2.5 * s, ry - 2.5 * s, rx + 2.5 * s, ry + 2.5 * s], fill=ICE + (230,))
        # an elbow: straight down from the ring, then across to the hairline's end
        ex, ey = x0 + hl, hy
        pts = [(rx, ry + r), (rx, ey), (ex, ey)]
        pl = ease((t - 1 * k) / (6 * k))
        seg1, seg2 = abs(ey - (ry + r)), abs(rx - ex)
        want = pl * (seg1 + seg2)
        drawn = [pts[0], (rx, ry + r + min(want, seg1) * (1 if ey > ry else -1))]
        if want > seg1:
            f = (want - seg1) / max(seg2, 1)
            drawn.append((rx + f * (ex - rx), ey))
        if pl > 0:
            dl.line(drawn, fill=ICE + (150,), width=lw)

    hud = Image.alpha_composite(lines, text)
    a = np.array(hud)[..., 3].astype(np.float32)
    shadow = np.zeros((H, W, 4), np.uint8)
    shadow[..., 3] = np.clip(np.array(Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(12 * s)),
                                      np.float32) * 0.7, 0, 255).astype(np.uint8)
    return Image.alpha_composite(Image.fromarray(shadow), hud)


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height",
                          "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
    return tuple(int(v) for v in out.split(","))


def main():
    a = sys.argv[1:]
    src, dst = a[0], a[1]
    qa = Path(a[a.index("--qa") + 1]) if "--qa" in a else None
    off = int(a[a.index("--offset") + 1]) if "--offset" in a else 0
    crf = a[a.index("--crf") + 1] if "--crf" in a else "12"
    W, H = probe(src)
    dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", crf, "-preset", "slow", "-pix_fmt",
                            "yuv420p", "-movflags", "+faststart", dst], stdin=subprocess.PIPE)
    n = 0
    while True:
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        f = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        for sp in SUPERS:
            a0, a1 = sp["frames"][0] + off, sp["frames"][1] + off
            if a0 <= n < a1:
                base = Image.fromarray(f).convert("RGBA")
                f = np.asarray(Image.alpha_composite(base, render(W, H, sp, n - a0, a1 - a0)).convert("RGB"))
                if qa and n - a0 == a1 - a0 - 2:
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
