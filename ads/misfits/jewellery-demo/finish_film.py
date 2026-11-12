#!/usr/bin/env python3
"""Finish the jewellery demo film for showing to shop owners: 1080x1920 with a sound bed and an end card.

- the Seedance take upscaled 720x1280 -> 1080x1920 (Lanczos), light sharpening (no grain: jewellery wants clean blacks);
- an end card on black: a line for the shop's own name ("YOUR STORE HERE" by default, or --store "Name") and a small
  Misfits credit, fading in;
- sound: the take's quiet studio sounds plus a soft bed made here (a warm low pad and a small bell on each hard cut),
  to -14 LUFS. The bed is a placeholder: swap in the shop's choice of music with --music <file>.

  python3 finish_film.py <take.mp4> <out.mp4> [--store "Shop name"] [--trim 12.0] [--card 2.4] [--music track.m4a]
         [--size 2160x3840 --audio <original take> --sharpen 0]   (for a Real-ESRGAN upscale, which has no sound)
"""
import argparse
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
FONTS = ROOT / "brand/misfits/fonts"
W, H, FPS, SR = 1080, 1920, 24, 48000


def duration(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                                capture_output=True, text=True).stdout.strip())


def cuts(path, end):
    """Hard cuts (seconds) by frame differencing on a small grey copy."""
    w, h = 72, 128
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"fps={FPS},scale={w}:{h},format=gray",
                          "-f", "rawvideo", "-"], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)
    d = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))
    thr = max(14.0, float(np.median(d)) * 6)
    out, last = [], -99
    for i, v in enumerate(d):
        if v > thr and i - last > 8:
            out.append((i + 1) / FPS)
            last = i
    return [t for t in out if t < end - 0.2]


def tracked(text, font, spacing):
    widths = [font.getlength(c) for c in text]
    asc, desc = font.getmetrics()
    layer = Image.new("RGBA", (int(sum(widths) + spacing * (len(text) - 1)) + 4, asc + desc + 4), (0, 0, 0, 0))
    d, x = ImageDraw.Draw(layer), 2
    for c, cw in zip(text, widths):
        d.text((x, 2), c, font=font, fill=(255, 255, 255, 255))
        x += cw + spacing
    return layer.crop(layer.getbbox())


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def with_alpha(layer, a):
    out = layer.copy()
    out.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
    return out


def card_frames(seconds, store):
    k = W / 1080  # laid out for 1080x1920, scales with --size
    name = tracked(store.upper(), ImageFont.truetype(str(FONTS / "InstrumentSerif-Regular.ttf"), round(84 * k)), 9 * k)
    if name.width > W - 140 * k:
        nw = round(W - 140 * k)
        name = name.resize((nw, round(name.height * nw / name.width)), Image.LANCZOS)
    rule = Image.new("RGBA", (round(120 * k), max(2, round(2 * k))), (214, 178, 110, 255))
    credit = with_alpha(tracked("FILM BY MISFITS  ·  MISFITSAGENCY.IN", ImageFont.truetype(str(FONTS / "JetBrainsMono-Regular.ttf"), round(24 * k)), 4 * k), 0.6)
    for i in range(round(seconds * FPS)):
        t = i / FPS
        f = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        f.alpha_composite(with_alpha(name, ease((t - 0.10) / 0.7)), ((W - name.width) // 2, round(880 * k) - name.height // 2))
        f.alpha_composite(with_alpha(rule, ease((t - 0.35) / 0.6)), ((W - rule.width) // 2, round(980 * k)))
        f.alpha_composite(with_alpha(credit, ease((t - 0.7) / 0.6)), ((W - credit.width) // 2, round(1700 * k)))
        yield f.convert("RGB").tobytes()


def bed(path, total, cut_times, film_end):
    """A warm low pad with a slow swell, and a small soft bell on each cut (stereo 48 kHz WAV)."""
    t = np.arange(int(SR * total)) / SR
    pad = np.zeros_like(t)
    for f, a in ((110.0, 0.30), (164.81, 0.20), (220.0, 0.16), (329.63, 0.10), (493.88, 0.05)):  # A2 E3 A3 E4 B4
        pad += a * np.sin(2 * np.pi * f * t + 0.6 * np.sin(2 * np.pi * 0.11 * t + f))
    swell = 0.55 + 0.45 * np.sin(2 * np.pi * t / max(total, 1) * 0.5 * np.pi / np.pi) ** 2
    env = np.minimum(t / 1.2, 1.0) * np.minimum(np.maximum(total - t, 0) / 1.6, 1.0)
    x = pad * swell * env * 0.22
    notes = [880.0, 1318.5, 987.77, 1174.66, 1318.5, 880.0, 1479.98, 1760.0]
    for k, c in enumerate([0.0] + list(cut_times) + [film_end]):
        f0 = notes[k % len(notes)]
        i0 = int(c * SR)
        tt = np.arange(min(int(SR * 2.2), len(t) - i0)) / SR
        if len(tt) == 0:
            continue
        bell = (np.sin(2 * np.pi * f0 * tt) + 0.35 * np.sin(2 * np.pi * f0 * 2.01 * tt) * np.exp(-tt * 3)) * np.exp(-tt * 2.4)
        bell *= np.minimum(tt / 0.004, 1.0)
        x[i0:i0 + len(tt)] += bell * (0.075 if c else 0.05)
    left = x
    right = np.roll(x, int(0.011 * SR))  # a little width
    pcm = (np.clip(np.stack([left, right], axis=1), -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("take")
    ap.add_argument("out")
    ap.add_argument("--store", default="Your store here")
    ap.add_argument("--trim", type=float)
    ap.add_argument("--card", type=float, default=2.4)
    ap.add_argument("--music", help="use this track instead of the built-in bed")
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--size", default="1080x1920")
    ap.add_argument("--audio", help="take the sound (and the cut times) from this file, e.g. the original take")
    ap.add_argument("--sharpen", type=float, default=0.5, help="unsharp amount; 0 for an upscaled source")
    ap.add_argument("--maxrate", help="cap the video bitrate, e.g. 60M for a 4K master")
    args = ap.parse_args()
    global W, H
    W, H = (int(v) for v in args.size.split("x"))
    snd = args.audio or args.take
    T = args.trim or duration(args.take)
    C = args.card
    with tempfile.TemporaryDirectory() as tmp:
        card, bedf = Path(tmp) / "card.mp4", Path(tmp) / "bed.wav"
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p",
                                str(card)], stdin=subprocess.PIPE)
        for f in card_frames(C, args.store):
            enc.stdin.write(f)
        enc.stdin.close()
        enc.wait()
        music = args.music
        if not music:
            bed(bedf, T + C, cuts(snd, T), T)
            music = str(bedf)
        fc = (f"[0:v]trim=0:{T},setpts=PTS-STARTPTS,fps={FPS},scale={W}:{H}:flags=lanczos,{f'unsharp=5:5:{args.sharpen},' if args.sharpen else ''}"
              f"format=yuv420p,setsar=1[v0];[1:v]fps={FPS},format=yuv420p,setsar=1[v1];[v0][v1]concat=n=2:v=1:a=0[v];"
              f"[3:a]atrim=0:{T},asetpts=PTS-STARTPTS,aresample={SR},aformat=channel_layouts=stereo,volume=0.8,"
              f"apad=whole_dur={T + C},afade=t=out:st={T - 0.2}:d=1.0[a0];"
              f"[2:a]aresample={SR},aformat=channel_layouts=stereo,atrim=0:{T + C},afade=t=out:st={T + C - 1.2}:d=1.2[a1];"
              f"[a0][a1]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample={SR},atrim=0:{T + C}[a]")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", args.take, "-i", str(card), "-i", music, "-i", snd,
                        "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", str(args.crf),
                        *(["-maxrate", args.maxrate, "-bufsize", str(int(args.maxrate.rstrip("M")) * 2) + "M"] if args.maxrate else []),
                        "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-movflags",
                        "+faststart", args.out], check=True)
    print(f"Saved {args.out}: {T:.2f} s film + {C:.1f} s card at {W}x{H}")


if __name__ == "__main__":
    main()
