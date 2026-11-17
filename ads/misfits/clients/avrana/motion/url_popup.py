#!/usr/bin/env python3
"""End-of-ad overlay for Avrana: a black pill pops in with the AV monogram, then stretches open to reveal the URL,
a soft shine passes over it, and it holds. Made to drop over the last seconds of any Avrana ad.

  python3 url_popup.py [--url www.avrana.co] [--seconds 5] [--y 0.72] [--out-dir out]

Writes, from one 2160x3840 60fps render with transparency:
  avrana-url-popup-alpha.mov        ProRes 4444 with alpha, 1080x1920 (Premiere, Final Cut, Resolve, CapCut desktop)
  avrana-url-popup-alpha-4k.mov     PNG-in-MOV with alpha, 2160x3840 (lossless)
  avrana-url-popup-greenscreen.mp4  on pure green, 1080x1920 (phone CapCut / InShot: Chroma key)
  avrana-url-popup-greenscreen-4k.mp4
The shadow is left out of the green-screen versions so chroma key stays clean.
"""
import argparse
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
FONT = ROOT / "brand/misfits/fonts/Archivo-ExpandedSemiBold.ttf"
LOGO = HERE.parent / "product-images/avrana-logo-white.png"
W, H, FPS, SS = 2160, 3840, 60, 3
GREEN = (0, 177, 64)


def clamp(x):
    return min(max(x, 0.0), 1.0)


def out_back(x, s=1.9):
    x = clamp(x) - 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def out_expo(x):
    x = clamp(x)
    return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def pill_mask(w, h, inset=0.0):
    big = Image.new("L", (w * SS, h * SS), 0)
    i = inset * SS
    ImageDraw.Draw(big).rounded_rectangle((i, i, w * SS - 1 - i, h * SS - 1 - i), radius=(h * SS - 2 * i) / 2, fill=255)
    return big.resize((w, h), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="www.avrana.co")
    ap.add_argument("--seconds", type=float, default=5.0)
    ap.add_argument("--y", type=float, default=0.72, help="centre of the pill, as a fraction of the height")
    ap.add_argument("--out-dir", default=str(HERE / "out"))
    a = ap.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    k = W / 1080

    PH = round(132 * k)                          # pill height
    font = ImageFont.truetype(str(FONT), round(46 * k))
    track = 1.5 * k
    tw = sum(font.getlength(c) for c in a.url) + track * (len(a.url) - 1)
    pad, gap = round(14 * k), round(26 * k)
    icon_d = PH - 2 * pad                         # dark disc with the monogram
    FW = int(pad + icon_d + gap + tw + round(44 * k))
    asc, desc = font.getmetrics()
    text = Image.new("RGBA", (int(tw) + 8, asc + desc + 8), (0, 0, 0, 0))
    d, x = ImageDraw.Draw(text), 4
    for c in a.url:
        d.text((x, 4), c, font=font, fill=(255, 255, 255, 255))
        x += font.getlength(c) + track
    text = text.crop(text.getbbox())

    logo = Image.open(LOGO).convert("RGBA")
    logo = logo.crop(logo.getbbox())
    lh = round(icon_d * 0.62)
    logo = logo.resize((round(logo.width * lh / logo.height), lh), Image.LANCZOS)
    disc = Image.new("RGBA", (icon_d, icon_d), (0, 0, 0, 0))
    disc.paste((32, 32, 32, 255), (0, 0), pill_mask(icon_d, icon_d))
    ring = Image.new("RGBA", (icon_d, icon_d), (255, 255, 255, 0))
    rm = np.array(pill_mask(icon_d, icon_d), np.float32) - np.array(pill_mask(icon_d, icon_d, 1.6 * k), np.float32)
    ring.putalpha(Image.fromarray(np.clip(rm * 0.28, 0, 255).astype(np.uint8)))
    disc.alpha_composite(ring)

    m = round(60 * k)                              # margin for the shadow and the overshoot
    LW, LH = FW + 2 * m, PH + 2 * m
    cx, cy = W // 2, round(H * a.y)
    n = round(a.seconds * FPS)

    alpha_dst = [out / "avrana-url-popup-alpha-4k.mov", out / "avrana-url-popup-alpha.mov"]
    enc_master = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                                   "-r", str(FPS), "-i", "-", "-c:v", "png", "-pix_fmt", "rgba", str(alpha_dst[0])],
                                  stdin=subprocess.PIPE)
    for i in range(n):
        t = i / FPS
        pop = out_back(t / 0.42)                   # 0 -> 1 with overshoot
        grow = out_expo((t - 0.32) / 0.75)         # disc stretches into the full pill
        w = round(PH + (FW - PH) * grow)
        layer = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
        x0 = (LW - w) // 2
        mask = pill_mask(w, PH)
        sh = Image.new("L", (LW, LH), 0)
        sh.paste(mask, (x0, m + round(10 * k)))
        sh = sh.filter(ImageFilter.GaussianBlur(22 * k)).point(lambda v: int(v * 0.5))
        shadow = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
        shadow.putalpha(sh)
        body = Image.new("RGBA", (w, PH), (0, 0, 0, 0))
        grad = np.linspace(22, 8, PH, dtype=np.float32)[:, None, None] * np.ones((1, w, 1), np.float32)
        body = Image.fromarray(np.concatenate([np.repeat(grad, 3, 2), np.full((PH, w, 1), 255, np.float32)], 2).astype(np.uint8))
        # monogram disc: springs in on its own, a beat after the pill
        ds = out_back((t - 0.12) / 0.45, 2.2)
        if ds > 0.01:
            dd = max(2, round(icon_d * ds))
            dsc = disc.resize((dd, dd), Image.LANCZOS)
            lg = logo.resize((max(1, round(logo.width * ds)), max(1, round(logo.height * ds))), Image.LANCZOS)
            dsc.alpha_composite(lg, ((dd - lg.width) // 2, (dd - lg.height) // 2))
            body.alpha_composite(dsc, (pad + (icon_d - dd) // 2, pad + (icon_d - dd) // 2))
        # URL: rides in from the left as the pill opens, clipped by the pill
        ta = smooth((t - 0.55) / 0.5)
        if ta > 0:
            tl = text.copy()
            tl.putalpha(text.getchannel("A").point(lambda v: int(v * ta)))
            tx = pad + icon_d + gap - round(28 * k * (1 - out_expo((t - 0.5) / 0.7)))
            body.alpha_composite(tl, (tx, (PH - text.height) // 2 - round(2 * k)))
        # shine: a soft diagonal band once the pill is open
        st = (t - 1.25) / 0.9
        if 0 < st < 1:
            band = np.zeros((PH, w), np.float32)
            xs = np.arange(w)[None, :] + np.arange(PH)[:, None] * 0.6
            c = -0.2 * w + st * 1.4 * w
            band = np.exp(-((xs - c) / (60 * k)) ** 2) * 0.16 * 255
            shine = Image.new("RGBA", (w, PH), (255, 255, 255, 0))
            shine.putalpha(Image.fromarray(band.astype(np.uint8)))
            body.alpha_composite(shine)
        # hairline border
        bm = np.array(mask, np.float32) - np.array(pill_mask(w, PH, 1.6 * k), np.float32)
        border = Image.new("RGBA", (w, PH), (255, 255, 255, 0))
        border.putalpha(Image.fromarray(np.clip(bm * 0.32, 0, 255).astype(np.uint8)))
        body.alpha_composite(border)
        body.putalpha(Image.fromarray(np.minimum(np.array(body.getchannel("A")), np.array(mask))))
        layer.alpha_composite(shadow)
        layer.alpha_composite(body, (x0, m))
        # whole thing pops: scale and fade
        s = max(pop, 0.001)
        sw, shh = max(1, round(LW * s)), max(1, round(LH * s))
        layer = layer.resize((sw, shh), Image.LANCZOS)
        fade = smooth(t / 0.18)
        if fade < 1:
            layer.putalpha(layer.getchannel("A").point(lambda v: int(v * fade)))
        frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        frame.alpha_composite(layer, (cx - sw // 2, cy - shh // 2))
        enc_master.stdin.write(frame.tobytes())
    enc_master.stdin.close()
    enc_master.wait()

    src = str(alpha_dst[0])
    run = lambda *x: subprocess.run(["ffmpeg", "-v", "error", "-y", *x], check=True)
    run("-i", src, "-vf", "scale=1080:1920:flags=lanczos", "-c:v", "prores_ks", "-profile:v", "4444",
        "-pix_fmt", "yuva444p10le", "-alpha_bits", "16", str(alpha_dst[1]))
    # green screen: no shadow, so key out by threshold on alpha (shadow alpha < ~50% is dropped)
    for size, name in (("2160x3840", "avrana-url-popup-greenscreen-4k.mp4"), ("1080x1920", "avrana-url-popup-greenscreen.mp4")):
        run("-f", "lavfi", "-i", f"color=c=0x00B140:s={size}:r={FPS}:d={a.seconds}", "-i", src, "-filter_complex",
            f"[1:v]scale={size.replace('x', ':')}:flags=lanczos,format=rgba,"
            "geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='if(lt(r(X,Y)+g(X,Y)+b(X,Y),6)*lt(alpha(X,Y),200),0,alpha(X,Y))'[o];"
            "[0:v][o]overlay=format=auto,format=yuv420p", "-c:v", "libx264", "-crf", "12", "-preset", "slow",
            "-movflags", "+faststart", str(out / name))
    print("Saved to", out)


if __name__ == "__main__":
    main()
