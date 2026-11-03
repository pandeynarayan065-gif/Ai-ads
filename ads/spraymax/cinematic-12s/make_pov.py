#!/usr/bin/env python3
"""POV preview for the first-person shot (one press, mist onto the open palm).

Narayan's real-bottle test video (Drive: VID_20261102_194033428.mp4, frame at 29.0 s, saved as pov-source-t29.jpg):
his hand holding the real bottle with the cap off, turned upright (a pump spray can't spray upside down: the
dip tube would draw air), graded to the film's cold blue, with the 3D mist (film_shots.py --shot F15: F4's mist
alone on black) screened on at the nozzle. The nozzle is a hole in the SIDE of the pump head, so the mist leaves
sideways, never out of the tip (that reads as a nasal spray).

  python3 ads/spraymax/cinematic-12s/make_pov.py <F15.png> <out F12.png>
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
NOZZLE = (482, 1008)        # left side of the pump head, near its top, in the upright 1080x1920 frame
NOZZLE_F4 = (0.30, 0.42)    # nozzle position in the F4/F15 render, as fractions of width/height
_BASE = None


def base():
    """The graded upright frame (cached)."""
    global _BASE
    if _BASE is None:
        im = Image.open(HERE / "pov-source-t29.jpg").convert("RGB").transpose(Image.Transpose.ROTATE_90)
        b = np.asarray(im).astype(np.float32) / 255
        b = np.clip((b - 0.06) / 0.94, 0, 1) ** 1.25            # crush the blacks
        b *= np.array([0.86, 0.95, 1.10])                       # cold
        H, W = b.shape[:2]
        yy, xx = np.mgrid[0:H, 0:W]
        vig = 1 - 0.55 * (((xx - W * 0.5) / (W * 0.75)) ** 2 + ((yy - H * 0.45) / (H * 0.7)) ** 2)
        _BASE = b * np.clip(vig, 0.25, 1)[..., None]
    return _BASE


def compose(mist, shake=(0.0, 0.0, 0.0)):
    """mist: PIL image of the F15 render (any size, 9:16). shake: (dx px, dy px, rotation deg) handheld sway."""
    b = base()
    H, W = b.shape[:2]
    mist = mist.convert("RGB").resize((1080, 1920), Image.LANCZOS)
    w4, h4 = mist.size
    nx, ny = int(NOZZLE_F4[0] * w4), int(NOZZLE_F4[1] * h4)
    mist = mist.transpose(Image.Transpose.FLIP_LEFT_RIGHT)     # leave the side of the pump head to the left
    nx = w4 - 1 - nx
    sc = 0.85
    mist = mist.resize((int(mist.width * sc), int(mist.height * sc)), Image.LANCZOS)
    nx, ny = int(nx * sc), int(ny * sc)
    mist = mist.rotate(-14, resample=Image.BICUBIC, center=(nx, ny))   # aim a little upward, clear of the thumb
    m = np.asarray(mist).astype(np.float32) / 255 * np.array([0.88, 0.95, 1.0])
    canvas = np.zeros_like(b)
    ox, oy = NOZZLE[0] - nx, NOZZLE[1] - ny
    x1, y1, x2, y2 = max(ox, 0), max(oy, 0), min(ox + m.shape[1], W), min(oy + m.shape[0], H)
    canvas[y1:y2, x1:x2] = m[y1 - oy:y2 - oy, x1 - ox:x2 - ox]
    out = 1 - (1 - b) * (1 - canvas)                            # screen: black adds nothing
    img = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
    dx, dy, rot = shake
    if dx or dy or rot:                                         # handheld: a little sway, slightly overscanned
        img = img.rotate(rot, resample=Image.BICUBIC, translate=(dx, dy), center=NOZZLE).resize((1134, 2016), Image.LANCZOS)
        img = img.crop((27, 48, 27 + 1080, 48 + 1920))
    return img


def main():
    mist_png, out = sys.argv[1], sys.argv[2]
    compose(Image.open(mist_png)).save(out)
    print("wrote", out)


if __name__ == "__main__":
    main()
