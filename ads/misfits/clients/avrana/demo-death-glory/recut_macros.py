#!/usr/bin/env python3
"""Recut the Death & Glory film with more macro shots, at no generation cost.

Narayan, 11 Nov: "there were not enough macro shots this isn't that good", with no credits left. The macros are
tight reframes of our own footage, taken from the Real-ESRGAN 4K upscale so they stay sharp at 1080p:
  take    frames A..B of the film as they are
  punch   frames A..B reframed: a crop that moves from box0 to box1 (a cut-in on the same action)
  freeze  one frame held for N frames with a moving crop (a locked-off macro of a still subject; the finish's grain
          keeps it alive)
  still   an image file with a moving crop
A box is (cx, cy, s): centre and the fraction of the frame shown (0.5 = a 2x punch-in), all 0..1.
SWAP replaces every frame the light flashes touched with a clean frame of the same shot: levelling their
brightness (deflicker_subject.py) left the print soft and hazy for a few frames, which a 2x punch-in shows.
PAINT removes a blurred line of fake lettering Seedance left on the cotton above the skull once the screen has
lifted (frames 17-24): each row of the box is refilled from the clean cotton just left and right of it.
Sound follows the picture: every segment brings its own stretch of the take's location sound; a freeze or a still
borrows a quiet, steady stretch of ambience from the front test take (1.4 s in, about -34 dB). Writes <out>.mp4 (picture only) and <out>.wav, ready for finish_film.py:

  python3 recut_macros.py <take-4k.mp4> <out-prefix> --take-audio takes/20261111-113448-1.mp4 \
      --tone takes/20261111-112807-1.mp4 [--size 1080x1920]
  python3 finish_film.py <out-prefix>.mp4 <film.mp4> --audio <out-prefix>.wav --sharpen 0 [--size 2160x3840]
"""
import argparse
import subprocess
import tempfile
import wave
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

FPS, SR = 24, 48000
SPF = SR // FPS  # audio samples per frame
SWAP = {
    **{34 + k: 26 + k for k in range(8)},    # platform back: the flash frames -> clean frames of the same shot
    47: 48,                                   # a dark frame at the cut into the front shot
    53: 51, 54: 50, 55: 49, 56: 50, 57: 51,   # platform front: the flash left the emblem hazy for 5 frames
    # emblem macro (65-88): only frames 72-80 are crisp (both flashes left the rest soft), so it plays them
    # forward and back; the cotton only breathes, so the turn-rounds are invisible
    **dict(zip(range(65, 89), [72, 73, 74, 75, 76, 77, 78, 79, 80, 79, 78, 77,
                               76, 75, 74, 73, 72, 73, 74, 75, 76, 77, 78, 79])),
}
PAINT = [(17, 24, (0.2060, 0.1055, 0.7060, 0.1771))]  # first frame, last frame, box (x0, y0, x1, y1) 0..1

EDL = [
    ("take", 0, 24),                                                # the screen lifts off the print
    ("freeze", 20, 14, (0.50, 0.42, 0.56), (0.50, 0.42, 0.48)),     # macro: the ink of the skull, slow push
    ("freeze", 22, 11, (0.68, 0.37, 0.48), (0.74, 0.35, 0.48)),     # macro: along the antler, slow slide
    ("take", 25, 45),                                               # platform, from behind
    ("take", 46, 64),                                               # platform, front
    ("take", 65, 76),                                               # emblem macro
    ("punch", 77, 88, (0.50, 0.535, 0.64), (0.50, 0.535, 0.58)),    # macro: the script
    ("take", 89, 108),                                              # glass walkway
    ("take", 109, 136),                                             # fire field
    ("take", 137, 152),                                             # embers macro
    ("punch", 153, 168, (0.50, 0.56, 0.56), (0.50, 0.57, 0.50)),    # macro: embers across the skull
    ("take", 169, 192),                                             # crew of five
    ("take", 193, 204),                                             # tracking close
    ("punch", 205, 215, (0.50, 0.52, 0.56), (0.50, 0.53, 0.54)),    # macro: the print moving with his steps
    ("take", 216, 229),                                             # ash lifts off the shoulders
    ("punch", 230, 240, (0.40, 0.50, 0.56), (0.41, 0.50, 0.52)),    # macro: ash across the antlers
    ("take", 241, 287),                                             # ridge at sunrise
]


def ease(x):
    return x * x * (3 - 2 * x)


def lerp_box(b0, b1, u):
    return tuple(a + (b - a) * u for a, b in zip(b0, b1))


def plan(edl):
    """-> video uses [(source key, box or None)] per output frame, and audio pieces [(source, first sample, n)]."""
    video, audio = [], []
    for seg in edl:
        kind = seg[0]
        if kind == "take":
            _, a, b = seg
            video += [(SWAP.get(i, i), None) for i in range(a, b + 1)]
            audio.append(("take", a * SPF, (b - a + 1) * SPF))
        elif kind == "punch":
            _, a, b, b0, b1 = seg
            n = b - a + 1
            video += [(SWAP.get(a + k, a + k), lerp_box(b0, b1, ease(k / max(1, n - 1)))) for k in range(n)]
            audio.append(("take", a * SPF, n * SPF))
        elif kind == "freeze":
            _, f, n, b0, b1 = seg
            video += [(f, lerp_box(b0, b1, k / max(1, n - 1))) for k in range(n)]  # linear: a steady push
            audio.append(("tone", None, n * SPF))
        elif kind == "still":
            _, path, n, b0, b1 = seg
            video += [(str(path), lerp_box(b0, b1, k / max(1, n - 1))) for k in range(n)]
            audio.append(("tone", None, n * SPF))
    return video, audio


def render(im, box, size):
    if box is None:
        return im.resize(size, Image.LANCZOS)
    cx, cy, s = box
    w, h = im.size
    x0, y0 = (cx - s / 2) * w, (cy - s / 2) * h
    return im.resize(size, Image.LANCZOS, box=(x0, y0, x0 + s * w, y0 + s * h))


def paint_out(im, box):
    """Refill a box row by row from the strips just left and right of it (feathered); returns a new image."""
    a = np.asarray(im).copy()
    h, w = a.shape[:2]
    x0, y0, x1, y1 = round(box[0] * w), round(box[1] * h), round(box[2] * w), round(box[3] * h)
    sw, f = max(8, w // 72), max(4, w // 135)  # strip width, feather
    left = a[y0:y1, x0 - sw:x0].astype(np.float32).mean(axis=1)
    right = a[y0:y1, x1:x1 + sw].astype(np.float32).mean(axis=1)
    u = np.linspace(0, 1, x1 - x0, dtype=np.float32)[None, :, None]
    fill = left[:, None, :] * (1 - u) + right[:, None, :] * u
    ry, rx = np.arange(y1 - y0), np.arange(x1 - x0)
    my = np.clip(np.minimum(ry + 1, (y1 - y0) - ry) / f, 0, 1)
    mx = np.clip(np.minimum(rx + 1, (x1 - x0) - rx) / f, 0, 1)
    m = (my[:, None] * mx[None, :])[..., None]
    a[y0:y1, x0:x1] = np.clip(a[y0:y1, x0:x1] * (1 - m) + fill * m, 0, 255).astype(np.uint8)
    return Image.fromarray(a)


def load_audio(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def build_audio(pieces, take, tone, tone_start, tone_gain=1.0):
    """Concatenate the pieces; contiguous stretches of the take stay unbroken, real joins get 8 ms fades."""
    out, prev_end, tone_pos, prev_tone = [], None, int(tone_start * SR), False
    fade = int(0.008 * SR)
    ramp = np.linspace(0, 1, fade, dtype=np.float32)[:, None]
    for src, start, n in pieces:
        if src == "take":
            x = take[start:start + n].copy()
            joined = prev_end == start
            prev_end, prev_tone = start + n, False
        else:
            x = tone[tone_pos:tone_pos + n].copy() * tone_gain
            tone_pos += n
            joined, prev_end, prev_tone = prev_tone, None, True  # back-to-back inserts share one stretch of tone
        if len(x) < n:
            x = np.concatenate([x, np.zeros((n - len(x), 2), np.float32)])
        if not joined and out:
            x[:fade] *= ramp
            out[-1][-fade:] *= ramp[::-1]
        out.append(x)
    return np.concatenate(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="the 4K upscale of the take (picture)")
    ap.add_argument("out", help="output prefix: writes <out>.mp4 and <out>.wav")
    ap.add_argument("--take-audio", required=True, help="the original take (its sound)")
    ap.add_argument("--tone", required=True, help="a take to borrow quiet room tone from")
    ap.add_argument("--tone-start", type=float, default=1.4, help="where the quiet stretch starts, in seconds")
    ap.add_argument("--tone-gain", type=float, default=1.0)
    ap.add_argument("--size", default="1080x1920")
    ap.add_argument("--crf", type=int, default=12)
    args = ap.parse_args()
    size = tuple(int(v) for v in args.size.split("x"))
    video, audio = plan(EDL)
    uses = defaultdict(list)
    for j, (key, box) in enumerate(video):
        uses[key].append((j, box))
    n, (w, h) = len(video), size
    with tempfile.TemporaryDirectory(dir=Path(args.out).parent) as tmp:
        frames = np.lib.format.open_memmap(Path(tmp) / "frames.npy", mode="w+", dtype=np.uint8, shape=(n, h, w, 3))
        probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height",
                                "-of", "csv=p=0", args.src], capture_output=True, text=True).stdout.strip().split(",")
        sw, sh = int(probe[0]), int(probe[1])
        dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", args.src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                               stdout=subprocess.PIPE)
        i = 0
        while True:
            raw = dec.stdout.read(sw * sh * 3)
            if len(raw) < sw * sh * 3:
                break
            if i in uses:
                im = Image.frombytes("RGB", (sw, sh), raw)
                for first, last, box in PAINT:
                    if first <= i <= last:
                        im = paint_out(im, box)
                for j, box in uses[i]:
                    frames[j] = np.asarray(render(im, box, size))
            i += 1
        dec.wait()
        for key in (k for k in uses if isinstance(k, str)):
            im = Image.open(key).convert("RGB")
            for j, box in uses[key]:
                frames[j] = np.asarray(render(im, box, size))
        missing = [k for k in uses if isinstance(k, int) and k >= i]
        assert not missing, f"source has {i} frames, EDL needs {missing}"
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                                "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", str(args.crf), "-preset", "medium",
                                "-pix_fmt", "yuv420p", args.out + ".mp4"], stdin=subprocess.PIPE)
        for j in range(n):
            enc.stdin.write(frames[j].tobytes())
        enc.stdin.close()
        enc.wait()
        del frames
    a = build_audio(audio, load_audio(args.take_audio), load_audio(args.tone), args.tone_start, args.tone_gain)
    with wave.open(args.out + ".wav", "wb") as wv:
        wv.setnchannels(2)
        wv.setsampwidth(2)
        wv.setframerate(SR)
        wv.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())
    macros = sum(1 for s in EDL if s[0] != "take")
    print(f"Saved {args.out}.mp4 + .wav: {n} frames ({n / FPS:.2f} s), {len(EDL)} shots, {macros} new macro shots")


if __name__ == "__main__":
    main()
