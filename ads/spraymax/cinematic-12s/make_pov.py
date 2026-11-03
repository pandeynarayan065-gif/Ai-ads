#!/usr/bin/env python3
"""POV preview for shot 05 (first person, one press, mist onto the open palm).

Narayan's real-bottle test video (Drive: VID_20261102_194033428.mp4, frame at 29.0 s, saved as pov-source-t29.jpg):
his hand holding the real bottle with the cap off. Turned so the nozzle points down, graded to the film's cold blue,
with the 3D mist (film_shots.py --shot F15: F4's mist alone on black) screened on at the nozzle.

  python3 ads/spraymax/cinematic-12s/make_pov.py <F15.png> <out F12.png>
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
TIP = (532, 935)            # actuator tip in the turned 1080x1920 frame
NOZZLE_F4 = (0.30, 0.42)    # nozzle position in the F4/F15 render, as fractions of width/height


def main():
    mist_png, out = sys.argv[1], sys.argv[2]
    base = Image.open(HERE / "pov-source-t29.jpg").convert("RGB").transpose(Image.Transpose.ROTATE_270)
    b = np.asarray(base).astype(np.float32) / 255
    b = np.clip((b - 0.06) / 0.94, 0, 1) ** 1.25            # crush the blacks
    b *= np.array([0.86, 0.95, 1.10])                       # cold
    H, W = b.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W]
    vig = 1 - 0.55 * (((xx - W * 0.5) / (W * 0.75)) ** 2 + ((yy - H * 0.45) / (H * 0.7)) ** 2)
    b *= np.clip(vig, 0.25, 1)[..., None]

    mist = Image.open(mist_png).convert("RGB")
    w4, h4 = mist.size
    nx, ny = int(NOZZLE_F4[0] * w4), int(NOZZLE_F4[1] * h4)
    # turn the mist so it leaves the nozzle downward (it leaves to the right in F4)
    mist = mist.transpose(Image.Transpose.ROTATE_270)       # (x, y) -> (h - 1 - y, x)
    nx, ny = h4 - 1 - ny, nx
    sc = 0.9
    mist = mist.resize((int(mist.width * sc), int(mist.height * sc)), Image.LANCZOS)
    nx, ny = int(nx * sc), int(ny * sc)
    m = np.asarray(mist).astype(np.float32) / 255 * np.array([0.88, 0.95, 1.0])
    canvas = np.zeros_like(b)
    ox, oy = TIP[0] - nx, TIP[1] + 4 - ny
    x1, y1, x2, y2 = max(ox, 0), max(oy, 0), min(ox + m.shape[1], W), min(oy + m.shape[0], H)
    canvas[y1:y2, x1:x2] = m[y1 - oy:y2 - oy, x1 - ox:x2 - ox]
    out_img = 1 - (1 - b) * (1 - canvas)                    # screen: black adds nothing
    Image.fromarray((np.clip(out_img, 0, 1) * 255).astype(np.uint8)).save(out)
    print("wrote", out)


if __name__ == "__main__":
    main()
