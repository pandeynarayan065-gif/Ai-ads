#!/usr/bin/env python3
"""Showcase reel for Misfits: the one product photo we were given, then the ad we made from it, then a Misfits card.

  1. THE BRIEF (2.6 s): the original photo on a blurred copy of itself, slow push, "ONE PHOTO." / "No shoot..."
  2. THE AD: the watermarked demo, with a "THE AD · MADE BY MISFITS" chip and the photo inset bottom-left ("INPUT")
     while the film plays, so the viewer compares the two.
  3. Misfits card (2.8 s): Noir/Acid logo, "Your product. Our film.", misfitsagency.in.

  python3 ads/misfits/jewellery-demo/make_showcase.py <ad-wm.mp4> <photo.jpg> <out.mp4> [--film 12.04]
"""
import argparse
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[3]
FONTS = ROOT / "brand/misfits/fonts"
LOGO = ROOT / "brand/misfits/noir-acid/logo/misfits-logo-on-dark.png"
W, H, FPS, SR = 1080, 1920, 24, 48000
BG, INK, MUTED, ACID = (11, 11, 13), (238, 235, 228), (140, 140, 145), (198, 255, 51)
A_SEC, C_SEC = 2.6, 2.8


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def rounded(im, r):
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255)
    out = im.convert("RGBA")
    out.putalpha(m)
    return out


def chip(text, fill, ink, size=26, pad=(22, 12)):
    f = font("JetBrainsMono-Bold.ttf", size)
    l, t, r, b = f.getbbox(text)
    im = Image.new("RGBA", (r - l + pad[0] * 2, b - t + pad[1] * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), im.height // 2, fill=fill)
    d.text((pad[0] - l, pad[1] - t), text, font=f, fill=ink)
    return im


def text_layer(text, fnt, fill):
    l, t, r, b = fnt.getbbox(text)
    im = Image.new("RGBA", (r - l + 4, b - t + 4), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((2 - l, 2 - t), text, font=fnt, fill=fill)
    return im


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def fade(layer, a):
    out = layer.copy()
    out.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
    return out


def encode(frames, path):
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", str(path)],
                           stdin=subprocess.PIPE)
    for f in frames:
        enc.stdin.write(f)
    enc.stdin.close()
    enc.wait()


def brief_frames(photo):
    bg = photo.resize((W, round(photo.height * W / photo.width) + 400)).crop((0, 0, W, H)) if False else None
    big = photo.resize((round(photo.width * H / photo.height * 1.15), round(H * 1.15)), Image.LANCZOS)
    big = big.crop(((big.width - W) // 2, (big.height - H) // 2, (big.width - W) // 2 + W, (big.height - H) // 2 + H))
    back = Image.blend(big.filter(ImageFilter.GaussianBlur(40)).convert("RGB"), Image.new("RGB", (W, H), BG), 0.55)
    pw = 880
    card = rounded(photo.resize((pw, round(photo.height * pw / photo.width)), Image.LANCZOS), 30)
    shadow = Image.new("RGBA", (card.width + 80, card.height + 80), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((40, 50, card.width + 40, card.height + 50), 34, fill=(0, 0, 0, 150))
    shadow = shadow.filter(ImageFilter.GaussianBlur(24))
    tag = chip("THE BRIEF", ACID, BG)
    head = text_layer("ONE PHOTO.", font("Archivo-ExpandedBlack.ttf", 92), INK)
    sub = text_layer("No shoot. No studio. No model.", font("JetBrainsMono-Regular.ttf", 32), MUTED)
    for i in range(round(A_SEC * FPS)):
        t = i / FPS
        s = 1.0 + 0.035 * ease(t / A_SEC)
        c = card.resize((round(card.width * s), round(card.height * s)), Image.LANCZOS)
        f = back.convert("RGBA")
        cy = 1010
        f.alpha_composite(shadow, ((W - shadow.width) // 2, cy - shadow.height // 2))
        f.alpha_composite(c, ((W - c.width) // 2, cy - c.height // 2))
        f.alpha_composite(fade(tag, ease(t / 0.4)), ((W - tag.width) // 2, 150))
        f.alpha_composite(fade(head, ease((t - 0.15) / 0.5)), ((W - head.width) // 2, 225))
        f.alpha_composite(fade(sub, ease((t - 0.5) / 0.5)), ((W - sub.width) // 2, 1745))
        yield f.convert("RGB").tobytes()


def card_frames():
    logo = Image.open(LOGO).convert("RGBA")
    logo = logo.crop(logo.getbbox())
    logo = logo.resize((640, round(logo.height * 640 / logo.width)), Image.LANCZOS)
    line = text_layer("Your product. Our film.", font("InstrumentSerif-Italic.ttf", 76), INK)
    url = text_layer("misfitsagency.in  ·  DM us", font("JetBrainsMono-Regular.ttf", 32), MUTED)
    rule = Image.new("RGBA", (140, 4), ACID + (255,))
    for i in range(round(C_SEC * FPS)):
        t = i / FPS
        f = Image.new("RGBA", (W, H), BG + (255,))
        s = 0.97 + 0.03 * ease(t / C_SEC)
        lg = logo.resize((round(logo.width * s), round(logo.height * s)), Image.LANCZOS)
        f.alpha_composite(fade(lg, ease((t - 0.05) / 0.5)), ((W - lg.width) // 2, 800 - lg.height // 2))
        f.alpha_composite(fade(rule, ease((t - 0.35) / 0.4)), ((W - rule.width) // 2, 900))
        f.alpha_composite(fade(line, ease((t - 0.45) / 0.5)), ((W - line.width) // 2, 950))
        f.alpha_composite(fade(url, ease((t - 0.8) / 0.5)), ((W - url.width) // 2, 1700))
        yield f.convert("RGB").tobytes()


def overlays(photo, tmp):
    """PNG overlays for the ad section: the top chip and the inset photo with its label."""
    top = chip("THE AD  ·  MADE BY MISFITS", (11, 11, 13, 200), INK, size=24)
    top.save(tmp / "top.png")
    iw = 250
    inset = rounded(photo.resize((iw, round(photo.height * iw / photo.width)), Image.LANCZOS), 18)
    framed = Image.new("RGBA", (inset.width + 8, inset.height + 8), (0, 0, 0, 0))
    ImageDraw.Draw(framed).rounded_rectangle((0, 0, framed.width - 1, framed.height - 1), 22, fill=ACID + (255,))
    framed.alpha_composite(inset, (4, 4))
    lab = chip("INPUT", ACID, BG, size=20, pad=(14, 8))
    pip = Image.new("RGBA", (framed.width, framed.height + lab.height + 10), (0, 0, 0, 0))
    pip.alpha_composite(lab, (0, 0))
    pip.alpha_composite(framed, (0, lab.height + 10))
    pip.save(tmp / "pip.png")
    return top.size, pip.size


def sound(path, total, ad_start, card_start):
    """A soft rising air into the ad, and a low hit on the Misfits card (the ad brings its own sound)."""
    n = int(SR * total)
    t = np.arange(n) / SR
    rng = np.random.default_rng(3)
    x = np.zeros(n)
    k = int(SR * ad_start)
    noise = rng.normal(0, 1, k)
    # crude low-pass by moving average, then rise
    noise = np.convolve(noise, np.ones(40) / 40, mode="same")
    x[:k] += noise * np.linspace(0.0, 1.0, k) ** 2 * 0.5
    x[:k] += 0.12 * np.sin(2 * np.pi * 110 * t[:k]) * np.linspace(0, 1, k)
    c = int(SR * card_start)
    tt = t[c:] - t[c]
    x[c:] += (0.6 * np.sin(2 * np.pi * 52 * tt) * np.exp(-tt * 2.5) + 0.2 * np.sin(2 * np.pi * 880 * tt) * np.exp(-tt * 3)) \
        * np.minimum(tt / 0.006, 1)
    pcm = (np.clip(np.repeat(x[:, None], 2, axis=1), -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ad")
    ap.add_argument("photo")
    ap.add_argument("out")
    ap.add_argument("--film", type=float, default=12.04, help="where the film ends inside the ad (before its card)")
    args = ap.parse_args()
    photo = Image.open(args.photo).convert("RGB")
    ad_len = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                   args.ad], capture_output=True, text=True).stdout)
    total = A_SEC + ad_len + C_SEC
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        encode(brief_frames(photo), tmp / "a.mp4")
        encode(card_frames(), tmp / "c.mp4")
        (tw, th), (pw, ph) = overlays(photo, tmp)
        sound(tmp / "sfx.wav", total, A_SEC, A_SEC + ad_len)
        F = args.film
        fc = (f"[1:v]fps={FPS},scale={W}:{H},setsar=1[ad];"
              f"[4:v]format=rgba,fade=t=in:st=0.3:d=0.4:alpha=1,fade=t=out:st={F - 0.5}:d=0.4:alpha=1[tp];"
              f"[5:v]format=rgba,fade=t=in:st=0.5:d=0.4:alpha=1,fade=t=out:st={F - 0.5}:d=0.4:alpha=1[pp];"
              f"[ad][tp]overlay=({W}-{tw})/2:120:format=auto[ad1];[ad1][pp]overlay=48:{H}-{ph}-150:format=auto,format=yuv420p[b];"
              f"[0:v]setsar=1[a];[2:v]setsar=1[c];[a][b][c]concat=n=3:v=1:a=0[v];"
              f"[1:a]aresample={SR},aformat=channel_layouts=stereo,adelay={int(A_SEC * 1000)}:all=1,apad=whole_dur={total}[a1];"
              f"[3:a]aresample={SR}[a2];[a1][a2]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample={SR},"
              f"atrim=0:{total}[aud]")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp / "a.mp4"), "-i", args.ad, "-i", str(tmp / "c.mp4"),
                        "-i", str(tmp / "sfx.wav"), "-loop", "1", "-t", str(ad_len), "-i", str(tmp / "top.png"),
                        "-loop", "1", "-t", str(ad_len), "-i", str(tmp / "pip.png"),
                        "-filter_complex", fc, "-map", "[v]", "-map", "[aud]", "-c:v", "libx264", "-crf", "18",
                        "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart",
                        args.out], check=True)
    print(f"Saved {args.out}: {total:.1f} s (brief {A_SEC} s + ad {ad_len:.1f} s + card {C_SEC} s)")


if __name__ == "__main__":
    main()
