#!/usr/bin/env python3
"""Grade the chrome Apple-logo shot to match the iPhone Duo opener (Narayan, 4 Nov: "Cc the chrome shot to make it
look like the 1st phone").

The opener's iPhone Duo is Star White: a light, almost neutral warm-grey back (Lab L ~175) with a tone-on-tone logo.
v1's logo shot (its frames 0-37) is a black-chrome logo on a dark taupe back (back L ~115, logo L ~10-50, a slight
magenta cast). One fixed tone curve for the whole shot (no per-frame fitting, so nothing flickers; no masks, so nothing
looks pasted): lifts the back to Star White and the black chrome to a polished mid-grey, keeping every reflection and
highlight shape; the taupe cast goes neutral-warm like the opener, but strongly coloured pixels (the Fold8's violet
reflection in the logo) keep their colour.

  python3 ads/samsung-spec/fold8-ultra-12s/grade_logo_shot.py <edit.mp4> <out.mp4> [--from 62]

--from = the shot's first frame in the edit (62 in v4: after the 62-frame opener). Any resolution.
"""
import subprocess
import sys

import cv2
import numpy as np

FPS = 24
LEN = 38                                   # v1 frames 0-37
L_IN = [0, 10, 48, 90, 116, 138, 200, 255]    # Lab L (0-255) in ...
L_OUT = [70, 88, 118, 158, 176, 188, 224, 250]  # ... and out
AB_TARGET = (127.2, 130.4)                 # lands the back on the opener's back: Lab a 128.5, b 130.8
AB_KEEP = 0.3                              # how much of the shot's own cast stays on neutral pixels
LUT = np.interp(np.arange(256), L_IN, L_OUT).astype(np.float32)


def grade(bgr):
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    chroma = np.hypot(a - 128, b - 128)
    keep = np.clip((chroma - 6) / 6, 0, 1)             # 0 = neutral (re-tinted), 1 = coloured (kept)
    na = AB_TARGET[0] + (a - 128) * AB_KEEP
    nb = AB_TARGET[1] + (b - 128) * AB_KEEP
    lab[..., 0] = LUT[np.clip(L, 0, 255).astype(np.uint8)]
    lab[..., 1] = na * (1 - keep) + a * keep
    lab[..., 2] = nb * (1 - keep) + b * keep
    return cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height",
                          "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
    return tuple(int(v) for v in out.split(","))


def main():
    a = sys.argv[1:]
    src, dst = a[0], a[1]
    start = int(a[a.index("--from") + 1]) if "--from" in a else 62
    W, H = probe(src)
    dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "10", "-preset", "slow", "-pix_fmt",
                            "yuv420p", dst], stdin=subprocess.PIPE)
    n = 0
    while True:
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        f = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        if start <= n < start + LEN:
            f = grade(f)
        enc.stdin.write(np.ascontiguousarray(f).tobytes())
        n += 1
    enc.stdin.close()
    enc.wait()
    dec.wait()
    print(f"wrote {dst}: {n} frames, graded {start}-{start + LEN - 1}")


if __name__ == "__main__":
    main()
