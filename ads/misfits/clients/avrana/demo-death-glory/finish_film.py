#!/usr/bin/env python3
"""Finish the Death & Glory demo film for Avrana: a 1080x1920 master with an end card.

- the Seedance take upscaled 720x1280 -> 1080x1920 (Lanczos), light sharpening, fine film grain;
- an end card on black: Avrana's own AV monogram (from avrana.co), their own line REBORN. NEVER DEFEATED.,
  and avrana.co, each fading in;
- sound: the take's own location sound, faded under the card, a low hit on the card, loudness to -14 LUFS.

  python3 ads/misfits/clients/avrana/demo-death-glory/finish_film.py <take.mp4> <out.mp4> [--trim 12.0] [--card 2.6]

The logo lives in the gitignored client folder (product-images/avrana-logo-white.png); it is Avrana's artwork.
"""
import argparse
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
FONTS = ROOT / "brand/misfits/fonts"
LOGO = HERE.parent / "product-images/avrana-logo-white.png"
W, H, FPS, SR = 1080, 1920, 24, 48000


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout
    return float(out.strip())


def tracked(text, font, spacing):
    """A white text layer with letter spacing (tracking), cropped to its ink."""
    widths = [font.getlength(c) for c in text]
    w = int(sum(widths) + spacing * (len(text) - 1)) + 4
    asc, desc = font.getmetrics()
    layer = Image.new("RGBA", (w, asc + desc + 4), (0, 0, 0, 0))
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


def card_frames(seconds):
    logo = Image.open(LOGO).convert("RGBA")
    logo = logo.crop(logo.getbbox())
    lh = 360
    logo = logo.resize((round(logo.width * lh / logo.height), lh), Image.LANCZOS)
    tag = tracked("REBORN. NEVER DEFEATED.", ImageFont.truetype(str(FONTS / "InstrumentSerif-Regular.ttf"), 66), 7)
    url = tracked("avrana.co", ImageFont.truetype(str(FONTS / "JetBrainsMono-Regular.ttf"), 30), 3)
    url = with_alpha(url, 0.62)
    for i in range(round(seconds * FPS)):
        t = i / FPS
        frame = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        a = ease((t - 0.10) / 0.70)
        s = 0.965 + 0.035 * ease(t / seconds)  # the monogram settles in very slowly
        lg = logo.resize((round(logo.width * s), round(logo.height * s)), Image.LANCZOS)
        frame.alpha_composite(with_alpha(lg, a), ((W - lg.width) // 2, 700 - lg.height // 2))
        frame.alpha_composite(with_alpha(tag, ease((t - 0.45) / 0.70)), ((W - tag.width) // 2, 1010))
        frame.alpha_composite(with_alpha(url, ease((t - 0.85) / 0.60)), ((W - url.width) // 2, 1690))
        yield frame.convert("RGB").tobytes()


def boom(path, seconds):
    """A low, soft hit for the cut to the card (stereo 48 kHz WAV)."""
    t = np.arange(int(SR * seconds)) / SR
    x = 0.55 * np.sin(2 * np.pi * 46 * t) * np.exp(-t * 2.8) + 0.25 * np.sin(2 * np.pi * 69 * t) * np.exp(-t * 4.5)
    x *= np.minimum(t / 0.008, 1.0)  # 8 ms attack, no click
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(np.repeat(pcm, 2).tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("take")
    ap.add_argument("out")
    ap.add_argument("--trim", type=float, help="end of the film part in seconds (default: the whole take)")
    ap.add_argument("--card", type=float, default=2.6, help="end card length in seconds")
    args = ap.parse_args()
    T = args.trim or duration(args.take)
    C = args.card
    with tempfile.TemporaryDirectory() as tmp:
        card, hit = Path(tmp) / "card.mp4", Path(tmp) / "hit.wav"
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p",
                                str(card)], stdin=subprocess.PIPE)
        for f in card_frames(C):
            enc.stdin.write(f)
        enc.stdin.close()
        enc.wait()
        boom(hit, C)
        fc = (f"[0:v]trim=0:{T},setpts=PTS-STARTPTS,fps={FPS},scale={W}:{H}:flags=lanczos,unsharp=5:5:0.45,"
              f"noise=alls=3:allf=t,format=yuv420p,setsar=1[v0];"
              f"[1:v]fps={FPS},format=yuv420p,setsar=1[v1];[v0][v1]concat=n=2:v=1:a=0[v];"
              f"[0:a]atrim=0:{T},asetpts=PTS-STARTPTS,aresample={SR},aformat=channel_layouts=stereo,"
              f"apad=whole_dur={T + C},afade=t=out:st={T - 0.15}:d=1.4[a0];"
              f"[2:a]adelay={int(T * 1000)}:all=1,apad=whole_dur={T + C}[a1];"
              f"[a0][a1]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample={SR},atrim=0:{T + C}[a]")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", args.take, "-i", str(card), "-i", str(hit),
                        "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "16",
                        "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-movflags",
                        "+faststart", args.out], check=True)
    print(f"Saved {args.out}: {T:.2f} s film + {C:.1f} s card at {W}x{H}")


if __name__ == "__main__":
    main()
