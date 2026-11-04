#!/usr/bin/env python3
"""Misfits Instagram portfolio: the four Spraymax pieces as reels with a Misfits outro, plus matching grid covers.
Theme: Noir / Acid (Narayan, 4 Nov).

Outro (1.8 s): the three bone tiles pop in, the acid tile drops in, then turns off-axis (the misfit). Then MISFITS
and "ADS THAT DON'T FIT IN." fade up, and the frame holds.
Covers (1080x1920): a hero frame, a dark fade and the title, kept inside the 3:4 grid crop (y 240-1680).

  python3 brand/misfits/portfolio/make_portfolio.py
"""
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FONTS = HERE.parent / "fonts"
BG, INK, ACCENT, MUTED = (11, 11, 13), (238, 235, 228), (198, 255, 51), (140, 140, 145)
W, H, FPS = 1080, 1920, 24
TILT = 16                                    # the acid tile's angle in the symbol (as in build_brand.py)

PIECES = [
    ("01", "cinematic", "ads/spraymax/cinematic-12s/spraymax-cinematic-12s.mp4", 4.5, "CINEMATIC",
     "Cinematic product film · 12 s"),
    ("02", "ocean", "ads/spraymax/cinematic-12s-ocean/spraymax-ocean-12s-endcard.mp4", 3.135, "INTO THE OCEAN",
     "Cinematic product film · 12.5 s"),
    ("03", "found-it", "ads/spraymax/intro-found-it/spraymax-intro-found-it-4s.mp4", 3.6, "FOUND IT",
     "POV hook · 4 s"),
    ("04", "shelf", "ads/spraymax/shelf-still/spraymax-shelf-motion-lockup.mp4", 0.0, "THE SHELF",
     "Product still + motion · 4 s"),
]


def font(name, size):
    f = ImageFont.truetype(str(FONTS / name), size)
    return f


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def ease_back(x, s=1.7):
    x = min(max(x, 0.0), 1.0)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def grain(img, amt=7, seed=0):
    n = np.random.default_rng(seed).normal(0, amt, (img.height, img.width, 1))
    a = np.clip(np.asarray(img).astype(np.float32) + n, 0, 255).astype(np.uint8)
    return Image.fromarray(a)


def tile(draw_img, cx, cy, size, angle, color, alpha=1.0, ss=4):
    """A rounded square centred at (cx, cy), rotated `angle` degrees, drawn supersampled."""
    if size <= 1 or alpha <= 0:
        return
    big = int(size * 1.6 * ss)
    t = Image.new("L", (big, big), 0)
    d = ImageDraw.Draw(t)
    s = size * ss
    o = (big - s) / 2
    d.rounded_rectangle([o, o, o + s, o + s], radius=s * 0.14, fill=int(255 * alpha))
    t = t.rotate(angle, resample=Image.BICUBIC).resize((big // ss, big // ss), Image.LANCZOS)
    layer = Image.new("RGB", t.size, color)
    draw_img.paste(layer, (int(cx - t.width / 2), int(cy - t.height / 2)), t)


def outro_frames(dur=1.8):
    wm = Image.open(HERE.parent / "noir-acid/logo/misfits-wordmark-on-dark.png").convert("RGBA")
    wm = wm.resize((640, int(640 * wm.height / wm.width)), Image.LANCZOS)
    slogan_f = font("Archivo-ExpandedSemiBold.ttf", 30)
    size = 300
    gap = size * 0.10
    t = (size - gap) / 2
    ox, oy = W / 2 - size / 2, 700 - size / 2
    centres = [(ox + t / 2, oy + t / 2), (ox + t / 2, oy + t + gap + t / 2), (ox + t + gap + t / 2, oy + t + gap + t / 2)]
    acc_home = (ox + t + gap + t / 2, oy + t / 2)
    acc_out = (acc_home[0] + size * 0.035, acc_home[1] - size * 0.035)
    frames = []
    for k in range(int(round(dur * FPS))):
        tt = k / FPS
        im = Image.new("RGB", (W, H), BG)
        for i, (cx, cy) in enumerate(centres):
            sc = ease_back((tt - 0.08 * i) / 0.28)
            tile(im, cx, cy, t * sc, 0, INK)
        # acid tile: drops in aligned, then turns off-axis
        a_in = ease_out((tt - 0.26) / 0.22)
        turn = ease_back((tt - 0.5) / 0.32, 2.2)
        cx = acc_home[0] + (acc_out[0] - acc_home[0]) * turn
        cy = acc_home[1] - 60 * (1 - a_in) + (acc_out[1] - acc_home[1]) * turn
        tile(im, cx, cy, t, TILT * turn, ACCENT, alpha=a_in)
        # wordmark and slogan
        e = ease_out((tt - 0.78) / 0.35)
        if e > 0:
            w2 = wm.copy()
            w2.putalpha(w2.getchannel("A").point(lambda v: int(v * e)))
            im.paste(w2, (int(W / 2 - w2.width / 2), int(960 + 24 * (1 - e))), w2)
        e2 = ease_out((tt - 1.05) / 0.3)
        if e2 > 0:
            d = ImageDraw.Draw(im, "RGBA")
            txt = "A D S   T H A T   D O N ' T   F I T   I N ."
            tw = d.textlength(txt, font=slogan_f)
            d.text(((W - tw) / 2, 1150), txt, font=slogan_f, fill=MUTED + (int(255 * e2),))
        frames.append(grain(im, 6, k))
    return frames


def cover(num, src, t_hero, title, sub, out):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(t_hero), "-i", str(ROOT / src), "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    im = Image.frombytes("RGB", (W, H), raw).convert("RGBA")
    # dark fade over the lower part, and a little at the top, so the type reads
    g = np.zeros((H, W, 4), np.uint8)
    yy = np.arange(H)[:, None]
    a = np.clip((yy - 980) / 620, 0, 1) ** 1.3 * 235 + np.clip((420 - yy) / 420, 0, 1) * 120
    g[..., 3] = np.repeat(a, W, axis=1).astype(np.uint8)
    im.alpha_composite(Image.fromarray(g, "RGBA"))
    d = ImageDraw.Draw(im)
    # top: the symbol + MISFITS, small (inside the 3:4 crop)
    sym = Image.open(HERE.parent / "noir-acid/logo/misfits-logo-on-dark.png").convert("RGBA")
    sym = sym.resize((300, int(300 * sym.height / sym.width)), Image.LANCZOS)
    im.alpha_composite(sym, (80, 270))
    lab = font("Archivo-ExpandedSemiBold.ttf", 26)
    d.text((W - 80 - d.textlength(num, font=lab), 280), num, font=lab, fill=ACCENT)
    # bottom block
    big = font("Archivo-ExpandedBlack.ttf", 96 if len(title) < 12 else 78)
    y = 1400
    d.text((80, y - 60), "S P R A Y M A X", font=lab, fill=ACCENT)
    d.text((80, y), title, font=big, fill=INK)
    body = ImageFont.truetype(str(FONTS / "Inter-VF.ttf"), 34)
    try:
        body.set_variation_by_axes([24, 500])
    except Exception:
        pass
    d.text((82, y + big.size + 34), sub, font=body, fill=(230, 228, 222))
    grain(im.convert("RGB"), 4, int(float(num))).save(out, quality=95)


def main():
    out = HERE
    frames = outro_frames()
    outro = out / "misfits-outro-1080x1920.mp4"
    p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt",
                          "yuv420p", str(outro)], stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(f.tobytes())
    p.stdin.close()
    p.wait()
    frames[-1].save(out / "misfits-outro-still.png")
    for num, slug, src, t_hero, title, sub in PIECES:
        cover(num, src, t_hero, title, sub, out / f"{num}-{slug}-cover.jpg")
        has_audio = "audio" in subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of",
                                               "csv=p=0", str(ROOT / src)], capture_output=True, text=True).stdout
        reel = out / f"{num}-{slug}-reel.mp4"
        if has_audio:      # keep the ad's sound, silence under the outro
            fc = ("[0:v]setsar=1[a];[1:v]setsar=1[b];[0:a]aresample=48000[x];anullsrc=r=48000:cl=stereo,atrim=0:1.8[y];"
                  "[a][x][b][y]concat=n=2:v=1:a=1[v][au]")
            maps = ["-map", "[v]", "-map", "[au]", "-c:a", "aac", "-b:a", "192k"]
        else:
            fc = "[0:v]setsar=1[a];[1:v]setsar=1[b];[a][b]concat=n=2:v=1:a=0[v]"
            maps = ["-map", "[v]"]
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(ROOT / src), "-i", str(outro), "-filter_complex",
                        fc] + maps + ["-c:v", "libx264", "-crf", "17", "-preset", "slow", "-pix_fmt", "yuv420p", "-r",
                                      str(FPS), "-movflags", "+faststart", str(reel)], check=True)
        print("wrote", reel.name, "and", f"{num}-{slug}-cover.jpg")


if __name__ == "__main__":
    main()
