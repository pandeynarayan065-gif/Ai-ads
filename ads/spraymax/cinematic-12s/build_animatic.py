#!/usr/bin/env python3
"""Spraymax 12 s film: assemble the 3D animatic (moving storyboard) from the film_anim.py renders.

The cut copies the Higgsfield perfume film's grammar (reference/creators/higgsfield-seedance-ex-nihilo.md):
15 hard cuts in 12 s, an opening push with a light sweep, ingredient macros, the product rising from an
ingredient, a fast rack across ridges, lateral drifts past backlit gaps, a long packshot with the logo.

  python3 ads/spraymax/cinematic-12s/build_animatic.py --anim <dir with F*/F*_0000.png> [--out animatic.mp4]
"""
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import make_pov  # noqa: E402

FPS = 24
# (render id, frames). F12 is the POV shot: Narayan's real video frame + the animated 3D mist (F15 renders).
CUT = [("F1", 29), ("F16", 14), ("F17", 14), ("F18", 14), ("F19", 17), ("F6", 26), ("F20", 19), ("F21", 14),
       ("F22", 14), ("F2", 14), ("F23", 17), ("F12", 17), ("F10", 14), ("F4", 14), ("F9", 51)]
assert sum(n for _, n in CUT) == 12 * FPS


def font(size, bold=False):
    for f in ("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else
              "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if Path(f).exists():
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def white_logo(width):
    lg = Image.open(ROOT / "brand/spraymax/assets/logo-wide.png").convert("RGBA")
    a = np.asarray(lg)[..., 3]
    ys, xs = np.nonzero(a > 20)
    lg = lg.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    lg = lg.resize((width, int(width * lg.height / lg.width)), Image.LANCZOS)
    w = Image.new("RGBA", lg.size, (240, 245, 255, 0))
    w.putalpha(lg.getchannel("A"))
    return w


LOGO = None


def end_card(img, k, n):
    """Logo + BORN IN HIMACHAL fade in over the packshot's empty dark top half (done in post in the real film)."""
    global LOGO
    if LOGO is None:
        LOGO = white_logo(620)
    a = min(max((k - n * 0.3) / (n * 0.25), 0), 1)
    if a <= 0:
        return img
    img = img.convert("RGBA")
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    lg = LOGO.copy()
    lg.putalpha(lg.getchannel("A").point(lambda v: int(v * a)))
    x = (img.width - lg.width) // 2 + 130
    lay.alpha_composite(lg, (x, 430))
    d = ImageDraw.Draw(lay)
    f = font(34)
    txt = "B O R N   I N   H I M A C H A L"
    tw = d.textlength(txt, font=f)
    d.text((x + (lg.width - tw) / 2, 430 + lg.height + 40), txt, font=f, fill=(200, 215, 240, int(220 * a)))
    return Image.alpha_composite(img, lay).convert("RGB")


def tag(img):
    """A small, quiet label so nobody mistakes the preview for the final film."""
    d = ImageDraw.Draw(img)
    d.text((44, 40), "3D PREVIEW  ·  final film: Seedance 2.5 from real photos", font=font(24), fill=(150, 160, 185))
    return img


def frames(anim):
    k_total = 0
    for sid, n in CUT:
        for k in range(n):
            if sid == "F12":
                t = k / FPS
                shake = (3.0 * math.sin(2 * math.pi * 0.9 * t + 0.4), 2.2 * math.sin(2 * math.pi * 0.6 * t + 1.3),
                         0.25 * math.sin(2 * math.pi * 0.5 * t))
                img = make_pov.compose(Image.open(anim / "F15" / f"F15_{k:04d}.png"), shake)
            else:
                img = Image.open(anim / sid / f"{sid}_{k:04d}.png").convert("RGB").resize((1080, 1920), Image.LANCZOS)
            if sid == "F9":
                img = end_card(img, k, n)
            yield tag(img)
            k_total += 1


def main():
    a = sys.argv[1:]
    anim = Path(a[a.index("--anim") + 1])
    out = Path(a[a.index("--out") + 1]) if "--out" in a else HERE / "animatic-v3.mp4"
    enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "slow",
                            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    for img in frames(anim):
        enc.stdin.write(img.tobytes())
    enc.stdin.close()
    enc.wait()
    print("wrote", out)


if __name__ == "__main__":
    main()
