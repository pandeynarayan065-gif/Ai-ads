#!/usr/bin/env python3
"""Hold the light steady on a still subject in locked-off shots of a Seedance take.

Seedance turned "the train's lit windows strobe across the print" into the print and the emblem flashing bright
for a few frames (Narayan, 11 Nov: "what's that bump glow happening in clip 2 and 3 stop it make it normal").
For each shot given as FIRST:LAST (frame numbers, inclusive), everything that holds still (the wearer, the floor)
is relit frame by frame to the shot's median light with a smooth gain map. Moving parts (the train) are left alone,
and frames outside the shots pass through untouched. Writes a near-lossless copy with the original audio, ready
for finish_film.py.

  python3 deflicker_subject.py <take.mp4> <out.mp4> --shot 25:45 --shot 46:64 --shot 65:88:all [--report]
"""
import argparse
import subprocess

import numpy as np


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                          "stream=width,height,r_frame_rate", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout.strip().split(",")
    num, den = out[2].split("/")
    return int(out[0]), int(out[1]), f"{num}/{den}"


def box(a, r):
    """Box blur of radius r along both image axes (edge-padded), same shape."""
    for ax in (0, 1):
        pad = [(0, 0)] * a.ndim
        pad[ax] = (r + 1, r)
        c = np.cumsum(np.pad(a, pad, mode="edge"), axis=ax, dtype=np.float64)
        n = a.shape[ax]
        a = (np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=ax) - np.take(c, np.arange(n), axis=ax)) / (2 * r + 1)
    return a.astype(np.float32)


def blur(a, r):
    for _ in range(3):  # three box passes ~ a Gaussian with sigma ~ r
        a = box(a, r)
    return a


def luma(rgb):
    return rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722


def fix_shot(frames, r, still_lo, still_hi, whole=False):
    """frames: (n, h, w, 3) uint8 -> relit uint8 frames, plus the 'still' mask used.

    The reference light is the 35th percentile of each pixel over the shot: below the flashes (they only brighten)
    and above the brief dark gaps between train cars. whole=True treats the whole frame as still (a macro of the
    chest, where the flashes cover almost half the frames and would otherwise read as motion)."""
    yb = np.stack([blur(luma(f.astype(np.float32)), r) for f in frames])
    ref = np.percentile(yb, 35, axis=0).astype(np.float32)
    if whole:
        still = np.ones_like(ref)
    else:
        mad = np.median(np.abs(yb - ref), axis=0)  # robust: a few flashing frames don't count as motion
        still = blur(np.clip((still_hi - mad) / (still_hi - still_lo), 0, 1), max(2, r // 2))
    out = []
    for f, y in zip(frames, yb):
        g = np.clip(ref / np.maximum(y, 1.0), 0.25, 2.0)
        g = 1 + still * (g - 1)
        out.append(np.clip(f.astype(np.float32) * g[..., None], 0, 255).astype(np.uint8))
    return np.stack(out), still


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("take")
    ap.add_argument("out")
    ap.add_argument("--shot", action="append", required=True,
                    help="FIRST:LAST frame numbers, inclusive; FIRST:LAST:all treats the whole frame as still")
    ap.add_argument("--radius", type=int, default=2, help="blur radius of the gain map in pixels")
    ap.add_argument("--report", action="store_true", help="print the subject's brightness per frame, before/after")
    args = ap.parse_args()
    w, h, rate = probe(args.take)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", args.take, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    n = len(raw) // (w * h * 3)
    video = np.frombuffer(raw, np.uint8)[: n * w * h * 3].reshape(n, h, w, 3).copy()
    for spec in args.shot:
        parts = spec.split(":")
        a, b = int(parts[0]), int(parts[1])
        before = video[a:b + 1].copy()
        video[a:b + 1], still = fix_shot(before, args.radius, 4.0, 14.0, whole=parts[2:] == ["all"])
        print(f"shot {a}-{b}: still area {still.mean() * 100:.0f}% of the frame")
        if args.report:
            for i in range(a, b + 1):
                m = still > 0.5
                yb, ya = luma(before[i - a].astype(np.float32))[m].mean(), luma(video[i].astype(np.float32))[m].mean()
                print(f"  f{i:3d}  still-area brightness {yb:6.1f} -> {ya:6.1f}")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                            "-r", rate, "-i", "-", "-i", args.take, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264",
                            "-crf", "10", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest",
                            args.out], stdin=subprocess.PIPE)
    enc.stdin.write(video.tobytes())
    enc.stdin.close()
    enc.wait()
    print(f"Saved {args.out}")


if __name__ == "__main__":
    main()
