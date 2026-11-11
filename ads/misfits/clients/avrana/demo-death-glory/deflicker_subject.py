#!/usr/bin/env python3
"""Take the glow flashes off the print in a Seedance take, shot by shot.

Seedance turned "the train's lit windows strobe across the print" into the print and the emblem flashing bright
for a few frames (Narayan, 11 Nov: "what's that bump glow happening in clip 2 and 3 stop it make it normal", then
"There's no glow ryt? Make sure of that"). The walking close-up looked like it flashed too, but that was sky
entering the measuring box: measure the print only (edge_bright) before fixing anything. The last trace in the
platform back shot went with patch_frames.py.

Each shot is FIRST:LAST[:MODE] (frame numbers, inclusive):
  still      (default) locked-off shot: everything that holds still (the wearer, the floor) is relit frame by
             frame to the shot's normal light with a smooth gain map; moving parts (the train) are left alone.
  all        the same, but the whole frame counts as still (a macro of the chest).
  highlight  moving shot: in frames where the print's highlights jump above the shot's running level, only the
             highlights inside a soft box around the print are brought back down; midtones and darks stay.
Frames outside the shots pass through untouched. Streams frame by frame, so it also runs on a 4K upscale.
Writes a near-lossless copy with the original audio, ready for finish_film.py.

  python3 deflicker_subject.py <take.mp4> <out.mp4> --shot 25:45 --shot 46:64 --shot 65:88:all [--report]
  (Avrana: then patch_frames.py ... --copy 34-41=26-33 --copy 47=48, then finish_film.py)
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


def fix_still(frames, r, still_lo=4.0, still_hi=14.0, whole=False):
    """Locked-off shot -> relit frames, plus the 'still' mask used.

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


def edge_bright(y, thr):
    """Soft mask of the bright regions connected to the frame border (sky, ground), found on a ~180 px wide copy."""
    h, w = y.shape
    sc = max(1, w // 180)
    small = y[::sc, ::sc] > thr
    reach = np.zeros_like(small)
    reach[0], reach[-1], reach[:, 0], reach[:, -1] = small[0], small[-1], small[:, 0], small[:, -1]
    while True:  # grow from the border through bright pixels only (flood fill)
        grown = reach.copy()
        grown[1:] |= reach[:-1]
        grown[:-1] |= reach[1:]
        grown[:, 1:] |= reach[:, :-1]
        grown[:, :-1] |= reach[:, 1:]
        grown &= small
        if np.array_equal(grown, reach):
            break
        reach = grown
    m = np.repeat(np.repeat(reach.astype(np.float32), sc, axis=0), sc, axis=1)
    m = np.pad(m, ((0, max(0, h - m.shape[0])), (0, max(0, w - m.shape[1]))), mode="edge")[:h, :w]
    return np.clip(blur(m, max(2, w // 120)) * 2, 0, 1)  # soft edge, grown a little past the sky's rim


def print_level(frames, core):
    """The print's highlight level per frame: 98th percentile of luma inside the core box."""
    y0, y1, x0, x1 = core
    return np.array([np.percentile(luma(f[y0:y1:2, x0:x1:2].astype(np.float32)), 98) for f in frames])


def fix_highlight(frames, win=11, area=(0.21, 0.69, 0.19, 0.81), feather=0.04):
    """Moving shot: pull the print's highlights back to the running level in the frames where they flash."""
    n, h, w, _ = frames.shape
    y0, y1, x0, x1 = int(h * area[0]), int(h * area[1]), int(w * area[2]), int(w * area[3])
    core = (y0, y1, x0, x1)
    p = print_level(frames, core)
    # running level from the lower values around each frame: the flashes only ever brighten
    ref = np.array([np.percentile(p[max(0, k - win // 2):k + win // 2 + 1], 30) for k in range(n)])
    fw = feather * w
    xs, ys = np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32)
    mx = np.clip((xs - (x0 - fw)) / fw, 0, 1) * np.clip(((x1 + fw) - xs) / fw, 0, 1)
    my = np.clip((ys - (y0 - fw)) / fw, 0, 1) * np.clip(((y1 + fw) - ys) / fw, 0, 1)
    mask = my[:, None] * mx[None, :]
    out = []
    for k, f in enumerate(frames):
        if p[k] > ref[k] * 1.03:
            y = luma(f.astype(np.float32))
            knee = 0.5 * ref[k]  # darks and midtones below the knee stay as they are
            s = (ref[k] - knee) / (p[k] - knee)
            g = np.where(y > knee, (knee + (y - knee) * s) / np.maximum(y, 1.0), 1.0)
            # only on the print: bright areas that reach the frame edge are sky or ground, the print is enclosed
            # by black cotton, so the bright regions connected to the border are left alone
            g = 1 + mask * (1 - edge_bright(y, knee)) * (g - 1)
            f = np.clip(f.astype(np.float32) * g[..., None], 0, 255).astype(np.uint8)
        out.append(f)
    out = np.stack(out)
    return out, p, print_level(out, core)


def process(frames, a, b, mode, args):
    if mode == "highlight":
        out, before, after = fix_highlight(frames)
        print(f"shot {a}-{b} (highlight): print level max {before.max():.0f} -> {after.max():.0f}, "
              f"median {np.median(before):.0f}")
        if args.report:
            print("   before: " + " ".join(f"{v:.0f}" for v in before))
            print("   after:  " + " ".join(f"{v:.0f}" for v in after))
        return out
    out, still = fix_still(frames, args.radius, whole=mode == "all")
    print(f"shot {a}-{b} ({mode}): still area {still.mean() * 100:.0f}% of the frame")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("take")
    ap.add_argument("out")
    ap.add_argument("--shot", action="append", required=True, help="FIRST:LAST[:still|all|highlight], inclusive")
    ap.add_argument("--radius", type=int, default=2, help="blur radius of the still-mode gain map in pixels")
    ap.add_argument("--crf", type=int, default=10, help="x264 CRF of the output (10 = near-lossless)")
    ap.add_argument("--report", action="store_true", help="print the print level per frame, before/after")
    args = ap.parse_args()
    specs = []
    for spec in args.shot:
        parts = spec.split(":")
        specs.append((int(parts[0]), int(parts[1]), parts[2] if len(parts) > 2 else "still"))
    w, h, rate = probe(args.take)
    fsize = w * h * 3
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", args.take, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                            "-r", rate, "-i", "-", "-i", args.take, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264",
                            "-crf", str(args.crf), "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "copy",
                            "-shortest", args.out], stdin=subprocess.PIPE)
    i, buf, cur = 0, [], None
    while True:
        raw = dec.stdout.read(fsize)
        if len(raw) < fsize:
            break
        spec = next((s for s in specs if s[0] <= i <= s[1]), None)
        if spec is None:
            enc.stdin.write(raw)
        else:
            cur = spec
            buf.append(np.frombuffer(raw, np.uint8).reshape(h, w, 3))
            if i == spec[1]:
                enc.stdin.write(process(np.stack(buf), *spec, args).tobytes())
                buf = []
        i += 1
    if buf:  # a shot that runs past the end of the video
        enc.stdin.write(process(np.stack(buf), *cur, args).tobytes())
    enc.stdin.close()
    enc.wait()
    dec.wait()
    print(f"Saved {args.out} ({i} frames)")


if __name__ == "__main__":
    main()
