#!/usr/bin/env python3
"""Finish a Seedance take of the Spraymax 12 s film for delivery: 1080x1920, 9:16.

- upscale 720x1280 -> 1080x1920 (Lanczos), light sharpening, a gentle cool S-curve, fine film grain;
- the end card over the packshot's empty dark top half: white logo + BORN IN HIMACHAL, fading in;
- a quiet sound bed: a low swell, a soft hit on every hard cut (found in the take), hiss under the mist shots.

  python3 ads/spraymax/cinematic-12s/finish_film.py <take.mp4> <out.mp4> [--end-at 10.0] [--size 1080x1920] [--qa <dir>]
"""
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_animatic  # noqa: E402

SR = 48000


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                          "stream=width,height,r_frame_rate,nb_frames:format=duration", "-of", "default=nw=1", str(path)],
                         capture_output=True, text=True).stdout
    d = dict(line.split("=", 1) for line in out.strip().splitlines() if "=" in line)
    num, den = d["r_frame_rate"].split("/")
    return int(d["width"]), int(d["height"]), float(num) / float(den), float(d["duration"])


def cuts(path, fps):
    """Hard cuts by frame differencing on a small grey copy."""
    W, H = 72, 128
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(path), "-vf", f"scale={W}:{H},format=gray",
                          "-f", "rawvideo", "-"], capture_output=True).stdout
    n = len(raw) // (W * H)
    fr = np.frombuffer(raw[:n * W * H], np.uint8).reshape(n, H, W).astype(np.float32)
    d = np.abs(np.diff(fr, axis=0)).mean((1, 2))
    out = []
    for i in range(len(d)):
        loc = np.median(d[max(0, i - 8):i + 8])
        if d[i] > max(7.0, 3.5 * loc) and (not out or i + 1 - out[-1] > 6):
            out.append(i + 1)
    return [c / fps for c in out], n


def end_card_png(path, x=480, y=700, width=540):
    """White logo + BORN IN HIMACHAL in the packshot's empty right half (like the perfume film's lockup)."""
    from PIL import ImageFont  # noqa: F401
    card = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    lg = build_animatic.white_logo(width)
    card.alpha_composite(lg, (x, y))
    d = ImageDraw.Draw(card)
    f = build_animatic.font(30)
    txt = "B O R N   I N   H I M A C H A L"
    tw = d.textlength(txt, font=f)
    d.text((x + (lg.width - tw) / 2, y + lg.height + 34), txt, font=f, fill=(200, 215, 240, 225))
    card.save(path)
    return card


def sound_bed(path, dur, cut_times, mist_spans):
    t = np.arange(int(dur * SR)) / SR
    rng = np.random.default_rng(3)
    swell = 0.10 * np.sin(2 * np.pi * 46 * t) * np.clip(t / 2.5, 0, 1) * np.clip((dur - t) / 1.0, 0, 1)
    out = swell.copy()
    for c in cut_times:                                         # a soft low hit on each cut
        k = (t >= c) & (t < c + 0.35)
        tt = t[k] - c
        out[k] += 0.22 * np.sin(2 * np.pi * (70 - 40 * tt) * tt) * np.exp(-tt * 14)
    noise = rng.normal(0, 1, len(t))
    hp = noise - np.convolve(noise, np.ones(24) / 24, mode="same")                    # crude high-pass: hiss
    for a, b in mist_spans:                                     # pump hiss under the mist shots
        k = (t >= a) & (t < b)
        env = np.sin(np.pi * (t[k] - a) / (b - a)) ** 0.7
        out[k] += 0.05 * hp[k] * env
    out = np.clip(out, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((out * 32767).astype(np.int16).tobytes())


def main():
    a = sys.argv[1:]
    take, out = Path(a[0]), Path(a[1])
    end_at = float(a[a.index("--end-at") + 1]) if "--end-at" in a else 10.0
    w, h, fps, dur = probe(take)
    cut_times, n = cuts(take, fps)
    print(f"take {w}x{h} {fps:.2f} fps {dur:.2f} s, {len(cut_times)} cuts:", [round(c, 2) for c in cut_times])
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="finish_")) / out.stem       # intermediates stay out of the repo
    card = Path(str(tmp) + "_endcard.png")
    end_card_png(card)
    snd = Path(str(tmp) + "_bed.wav")
    mist = [(8.1, 8.8), (9.4, 10.0)]
    sound_bed(snd, dur, cut_times, mist)
    ow, oh = (int(v) for v in (a[a.index("--size") + 1] if "--size" in a else "1080x1920").split("x"))
    upscaled = w >= ow                                     # e.g. a Topaz 4x master: scale down, don't sharpen
    sharpen = "" if upscaled else "unsharp=5:5:0.55:5:5:0.0,"
    grain = 3 if upscaled else 5
    if (ow, oh) != (1080, 1920):
        Image.open(card).resize((ow, oh), Image.LANCZOS).save(card)
    vf = (f"[0:v]scale={ow}:{oh}:flags=lanczos,{sharpen}"
          "curves=all='0/0 0.25/0.22 0.75/0.78 1/1',colorbalance=bs=0.02:bm=0.01,"
          f"noise=alls={grain}:allf=t+u,format=yuv420p[v];"
          f"[1:v]format=rgba,fade=in:st={end_at + 0.5}:d=0.5:alpha=1[c];"
          f"[v][c]overlay=0:0:enable='gte(t,{end_at + 0.5})'[o]")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(take), "-loop", "1", "-t", f"{dur}", "-i", str(card),
                    "-i", str(snd), "-filter_complex", vf, "-map", "[o]", "-map", "2:a", "-c:v", "libx264", "-crf", "16",
                    "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", str(out)], check=True)
    print("wrote", out)
    if "--qa" in a:
        qa = Path(a[a.index("--qa") + 1])
        qa.mkdir(parents=True, exist_ok=True)
        marks = [0.0] + cut_times
        for i, t0 in enumerate(marks):
            t1 = marks[i + 1] if i + 1 < len(marks) else dur
            tm = (t0 + t1) / 2
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{tm:.3f}", "-i", str(take), "-frames:v", "1",
                            "-q:v", "2", str(qa / f"shot{i + 1:02d}_{tm:05.2f}s.jpg")], check=True)
        print("qa frames in", qa)


if __name__ == "__main__":
    main()
