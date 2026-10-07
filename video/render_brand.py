#!/usr/bin/env python3
"""Spraymax 15 s brand film, studio look (v2).

Same real-label 3D bottle as render_typo.py, rebuilt for a premium feel:
ice-grey studio set with hazy Himalayan ridges, grounded bottle (contact
shadow + floor reflection), Outfit type in brand indigo, mask-reveal text,
callout lines, a fine horizontal spray fan, film grain and restrained SFX.

Usage: python3 video/render_brand.py [--preview]
"""
import math
import subprocess
import sys
import wave
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_typo import Bottle, ASSETS, clamp, ease_in_out, ease_out, prog  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "video/fonts"
OUT = ROOT / "ads/spraymax/himalayan-launch/video"
W, H, FPS, DUR = 1080, 1920, 30, 15.0
N = int(FPS * DUR)

INDIGO = (16, 14, 140)
SLATE = (74, 84, 112)
FLOOR_Y = 1540          # horizon where the floor meets the backdrop
BASE_Y = 1600           # bottle base line on the floor
rng = np.random.default_rng(21)


def ease_out_quint(x):
    return 1 - (1 - x) ** 5


# ---------- type ----------
@lru_cache(None)
def font(weight, size):
    return ImageFont.truetype(str(FONTS / f"Outfit-{weight}.ttf"), size)


@lru_cache(None)
def fallback(size):
    return ImageFont.truetype(str(FONTS / "Montserrat-Medium.ttf"), size)


@lru_cache(None)
def text(txt, weight, size, color=INDIGO, tracking=0):
    f = font(weight, size)
    asc, desc = f.getmetrics()
    x, chars = 0, []
    for ch in txt:
        adv = (fallback(size) if ch == "₹" else f).getlength(ch)
        chars.append((ch, x))
        x += adv + tracking
    im = Image.new("RGBA", (int(x - tracking) + 4, asc + desc + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for ch, cx in chars:
        d.text((cx + 2, 2), ch, font=fallback(size) if ch == "₹" else f, fill=color + (255,))
    return im


def reveal(canvas, img, cx, cy, t, t0, dur=0.6, out_t=None, out_dur=0.35, anchor="center"):
    """Mask reveal: text rises into a clipping line, exits upward with a fade."""
    p = ease_out_quint(prog(t, t0, dur))
    if p <= 0:
        return
    alpha = 1.0
    shift = (1 - p) * img.height
    if out_t is not None and t >= out_t:
        q = ease_in_out(prog(t, out_t, out_dur))
        alpha = 1 - q
        shift = -q * img.height * 0.35
    vis = img.crop((0, 0, img.width, img.height))
    layer = Image.new("RGBA", vis.size, (0, 0, 0, 0))
    layer.paste(vis, (0, int(shift)))
    if shift > 0:  # clip below the baseline window
        layer = layer.crop((0, 0, vis.width, vis.height))
    if alpha < 1:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
    x = cx - layer.width / 2 if anchor == "center" else cx
    canvas.alpha_composite(layer, (int(x), int(cy - layer.height / 2)))


# ---------- set ----------
def make_set():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    top, mid, floor_far, floor_near = (np.array(c, np.float32) for c in ((222, 229, 240), (205, 214, 230), (190, 200, 218), (172, 183, 205)))
    g = np.clip(yy / FLOOR_Y, 0, 1)[..., None]
    back = top * (1 - g) + mid * g
    f = np.clip((yy - FLOOR_Y) / (H - FLOOR_Y), 0, 1)[..., None]
    floor = floor_far * (1 - f) + floor_near * f
    blend = np.clip((yy - (FLOOR_Y - 40)) / 80, 0, 1)[..., None]
    arr = back * (1 - blend) + floor * blend
    # hazy Himalayan ridges, atmospheric perspective: evenly spaced summits, smoothed, soft-masked
    x = np.arange(W)
    for ridge_top, ridge_floor, col, strength, blur, seed in ((1150, 1400, (184, 195, 216), 0.45, 10, 5), (1290, 1490, (166, 178, 204), 0.6, 6, 9)):
        r = np.random.default_rng(seed)
        px = np.linspace(-220, W + 220, 9) + r.uniform(-45, 45, 9)
        py = np.where(np.arange(9) % 2 == 0, r.uniform(ridge_top, ridge_top + 110, 9), r.uniform(ridge_floor - 110, ridge_floor, 9))
        ridge = np.interp(x, px, py)
        ridge = np.convolve(np.pad(ridge, 40, mode="edge"), np.ones(41) / 41, mode="same")[40:-40]
        j = np.cumsum(r.normal(0, 1.4, W))
        ridge += (j - np.convolve(j, np.ones(41) / 41, mode="same")) * 1.0
        inside = ((yy >= ridge[None, :]) & (yy < FLOOR_Y + 20)).astype(np.float32)
        m = np.asarray(Image.fromarray((inside * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))).astype(np.float32) / 255 * strength
        snow = np.clip(1 - (yy - ridge[None, :]) / 60, 0, 1) * 0.35
        c = np.array(col, np.float32) * (1 - snow[..., None]) + np.array([236, 240, 248], np.float32) * snow[..., None]
        arr = arr * (1 - m[..., None]) + c * m[..., None]
    # key light behind the product + vignette
    d = ((xx - W / 2) / (W * 0.55)) ** 2 + ((yy - 1080) / (H * 0.42)) ** 2
    arr += (np.exp(-d * 1.4) * 34)[..., None]
    v = ((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2
    arr *= np.clip(1 - v * 0.55, 0.7, 1)[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")


GRAIN = [rng.normal(0, 2.8, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]
SALT = rng.uniform(0, 1, (22, 4))


def salt_bokeh(canvas, t):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for x, y, s, sp in SALT:
        px = (x * W + t * (6 + 14 * sp)) % W
        py = (y * 1450 - t * (10 + 25 * sp)) % 1450
        r = 3 + s * 12
        d.ellipse((px - r, py - r, px + r, py + r), fill=(255, 255, 255, int(40 + 70 * (1 - s))))
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(4)))


SPRAY = rng.uniform(0, 1, (900, 4))


def spray(canvas, t, t0, ox, oy, dur=0.75):
    """Fine horizontal mist fan from the nozzle: fast streaks + a soft expanding cloud."""
    a = t - t0
    if a < 0 or a > dur + 0.5:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i, (ang, sp, sz, born) in enumerate(SPRAY):
        b = born * dur * 0.55
        age = a - b
        if age < 0 or age > 0.55:
            continue
        theta = math.radians((ang - 0.5) * 24 - 4)      # ±12° fan, slightly up
        v = 900 + sp * 1700                               # px/s, decelerating
        dist = v * (1 - math.exp(-age * 4)) / 4
        x, y = ox + math.cos(theta) * dist, oy + math.sin(theta) * dist + age * age * 120
        life = 1 - age / 0.55
        al = int(200 * life * (0.35 + 0.65 * sz))
        tail = min(24, v * 0.012 * life)
        d.line((x - math.cos(theta) * tail, y - math.sin(theta) * tail, x, y), fill=(255, 255, 255, al), width=1 + int(sz * 2))
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(0.8)))
    # soft cloud
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(c)
    k = ease_out(prog(a, 0.05, dur + 0.3))
    fade = 1 - prog(a, dur * 0.5, 0.75)
    cx, rx, ry = ox + 60 + 260 * k, 50 + 230 * k, 22 + 70 * k
    cd.ellipse((cx - rx, oy - ry, cx + rx, oy + ry), fill=(255, 255, 255, int(55 * fade)))
    canvas.alpha_composite(c.filter(ImageFilter.GaussianBlur(38)))


# ---------- product: split the clear overcap off the cut-out ----------
# crop coords of Bottle.base (crop origin 440,770 in bottle-blank.png)
CAP_BOX = (134, 14, 361, 306)          # clear overcap incl. rims
ACT = (207, 322, 58, 215)              # actuator x0, x1, y0, y1
FERRULE = (168, 326, 215, 304)         # pump base under the actuator


def _cyl(x0, x1, y0, y1, h, w, tint=(244, 246, 251), spec=0.12):
    xs = np.arange(w)
    u = np.clip((xs - (x0 + x1) / 2) / ((x1 - x0) / 2), -1, 1)
    lum = 0.66 + 0.34 * np.sqrt(np.clip(1 - u ** 2, 0, 1)) ** 0.7 + spec * np.exp(-((u + 0.38) / 0.12) ** 2)
    col = np.clip(np.array(tint, np.float32)[None, :] / 255 * lum[:, None], 0, 1)
    return col


def make_capless(base):
    a = base.copy()
    h, w = a.shape[:2]
    a[:FERRULE[3], :, 3] = 0                      # drop cap + everything above the collar
    for (x0, x1, y0, y1), tint in ((FERRULE, (236, 239, 246)), (ACT, (246, 248, 252))):
        col = _cyl(x0, x1, y0, y1, h, w, tint)
        a[y0:y1, x0:x1, :3] = col[x0:x1][None, :, :]
        a[y0:y1, x0:x1, 3] = 1
    # rounded top of the actuator and a soft shadow line where it meets the ferrule
    x0, x1, y0, _ = ACT
    r = 10
    for yy in range(r):
        inset = int(r - math.sqrt(max(0, r * r - (r - yy) ** 2)))
        a[y0 + yy, x0:x0 + inset, 3] = 0
        a[y0 + yy, x1 - inset:x1, 3] = 0
    a[ACT[3] - 2:ACT[3] + 3, FERRULE[0]:FERRULE[1], :3] *= 0.82
    # spray orifice on the actuator's right side
    yy, xx = np.mgrid[0:h, 0:w]
    hole = ((xx - 313) / 6) ** 2 + ((yy - 98) / 8) ** 2 <= 1
    a[hole, :3] = np.array([0.36, 0.38, 0.45])
    return a


def make_cap(base):
    x0, y0, x1, y1 = CAP_BOX
    cap = base[y0:y1, x0:x1].copy()
    h, w = cap.shape[:2]
    alpha = np.zeros((h, w), np.float32)
    for y in range(h):
        xs = np.where(cap[y, :, 3] > 0.5)[0]
        if len(xs) < 20:
            continue
        l, r_ = xs.min(), xs.max()
        cl, cr = cap[y, l + 8, :3], cap[y, r_ - 8, :3]
        for x in range(l + 12, r_ - 11):  # clear interior: remove the actuator seen through it
            k = (x - l) / max(1, r_ - l)
            cap[y, x, :3] = np.minimum(1, (cl * (1 - k) + cr * k) * 0.6 + 0.4)
        alpha[y, l:r_ + 1] = 0.28
        alpha[y, l:l + 12] = alpha[y, r_ - 11:r_ + 1] = 0.85
    alpha[:16][alpha[:16] > 0] = 0.85                 # top rim
    alpha[-24:][alpha[-24:] > 0] = np.maximum(alpha[-24:][alpha[-24:] > 0], 0.7)  # bottom rim
    cap[:, :, 3] = alpha
    return Image.fromarray((np.clip(cap, 0, 1) * 255).astype(np.uint8), "RGBA")


BOTTLE = None
BOTTLE_NC = None
CAP = None
SET = None
LOGO = None


def place_bottle(canvas, t, angle, cx, scale, tilt=0.0, lift=0.0, presence=1.0, capped=True, cap_fx=None):
    img = (BOTTLE if capped else BOTTLE_NC).render(angle)
    if scale != 1:
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.BICUBIC)
    if tilt:
        img = img.rotate(tilt, resample=Image.BICUBIC, expand=True)
    bw, bh = img.size
    base = BASE_Y - lift
    top = base - bh
    # contact + ambient shadow on the floor
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    k = clamp(1 - lift / 300) * presence
    rx = 170 * scale
    sd.ellipse((cx - rx * 1.5, BASE_Y - 26, cx + rx * 1.5, BASE_Y + 34), fill=(40, 48, 80, int(60 * k)))
    sd.ellipse((cx - rx * 0.9, BASE_Y - 10, cx + rx * 0.9, BASE_Y + 12), fill=(25, 30, 60, int(120 * k)))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    # floor reflection
    if presence > 0:
        ref = img.transpose(Image.FLIP_TOP_BOTTOM).crop((0, 0, bw, int(bh * 0.4)))
        grad = np.linspace(0.22 * k, 0, ref.height)[:, None]
        a = (np.asarray(ref.getchannel("A")).astype(np.float32) * grad).astype(np.uint8)
        ref.putalpha(Image.fromarray(a))
        ref = ref.filter(ImageFilter.GaussianBlur(2))
        canvas.alpha_composite(ref, (int(cx - bw / 2), int(base + 4 + lift * 2)))
    if presence < 1:
        img = img.copy()
        img.putalpha(img.getchannel("A").point(lambda v: int(v * presence)))
    canvas.alpha_composite(img, (int(cx - bw / 2), int(top)))
    s = BOTTLE.scale * scale
    if cap_fx is not None:  # separate cap in flight: (dx, dy, rotation, alpha)
        dx, dy, rot, al = cap_fx
        if al > 0.01:
            cp = CAP.resize((max(1, int(CAP.width * s)), max(1, int(CAP.height * s))), Image.BICUBIC)
            if rot:
                cp = cp.rotate(rot, resample=Image.BICUBIC, expand=True)
            if al < 1:
                cp.putalpha(cp.getchannel("A").point(lambda v: int(v * al)))
            ccx = cx - bw / 2 + (CAP_BOX[0] + CAP_BOX[2]) / 2 * s + dx
            ccy = top + (CAP_BOX[1] + CAP_BOX[3]) / 2 * s + dy
            canvas.alpha_composite(cp, (int(ccx - cp.width / 2), int(ccy - cp.height / 2)))
    # spray orifice on the actuator (crop x≈319, y≈98; bottle crop centre x=250)
    return cx - bw / 2 + 319 * s, top + 98 * s, top, bh


def callout(canvas, t, t0, x0, y0, x1, label, sub):
    """Dot on the bottle, a line that draws out, then label + sub reveal."""
    p = ease_out_quint(prog(t, t0, 0.55))
    if p <= 0:
        return
    d = ImageDraw.Draw(canvas)
    d.ellipse((x0 - 7, y0 - 7, x0 + 7, y0 + 7), fill=INDIGO + (int(255 * min(1, p * 3)),))
    d.ellipse((x0 - 15, y0 - 15, x0 + 15, y0 + 15), outline=INDIGO + (int(110 * p),), width=2)
    xe = x0 + (x1 - x0) * p
    d.line((x0 + 15, y0, xe, y0), fill=INDIGO + (220,), width=3)
    reveal(canvas, text(label, 600, 52, INDIGO), x1 + 18, y0 - 26, t, t0 + 0.3, 0.55, anchor="left")
    reveal(canvas, text(sub, 300, 32, SLATE), x1 + 20, y0 + 28, t, t0 + 0.42, 0.55, anchor="left")


# ---------- timeline ----------
def frame(t):
    c = SET.copy()
    salt_bokeh(c, t)

    # S1 0–2.4  Flat hair?
    reveal(c, text("Flat hair?", 600, 168, INDIGO), W / 2, 880, t, 0.25, 0.75, out_t=2.15)
    reveal(c, text("EVERY. SINGLE. MORNING.", 500, 34, SLATE, tracking=8), W / 2, 1030, t, 0.75, 0.6, out_t=2.15)

    # S2 2.4–4.8  the problem
    reveal(c, text("Gel feels stiff.", 300, 92, SLATE), W / 2, 800, t, 2.45, 0.6, out_t=4.55)
    reveal(c, text("Wax feels greasy.", 300, 92, SLATE), W / 2, 930, t, 2.95, 0.6, out_t=4.6)
    reveal(c, text("There's a better way.", 600, 64, INDIGO), W / 2, 1100, t, 3.6, 0.6, out_t=4.65)

    # product motion
    cx, scale, angle, tilt, lift, presence = W / 2, 0.92, 0.0, 0.0, 0.0, 0.0
    if t >= 4.75:
        presence = 1.0
        if t < 7.0:  # enters from below the floor? no: descends softly from above and settles, 1 turn
            p = ease_out_quint(prog(t, 4.8, 1.9))
            lift = 1100 * (1 - p)
            angle = 360 * (1 - p)
            presence = clamp((t - 4.75) / 0.25)
        elif t < 10.75:  # stage left for callouts, small turn to show it's 3D
            p = ease_in_out(prog(t, 7.0, 0.7))
            cx = W / 2 - 200 * p
            scale = 0.92 - 0.06 * p
            angle = -14 * math.sin(prog(t, 7.6, 3.0) * math.pi)
        elif t < 12.8:  # back to centre, shake
            p = ease_in_out(prog(t, 10.75, 0.6))
            cx = W / 2 - 200 * (1 - p)
            scale = 0.86 + 0.02 * p
            if 11.05 <= t < 11.55:
                tilt = 4 * math.sin((t - 11.05) * 38) * (1 - prog(t, 11.05, 0.5))
        else:  # hero end card
            p = ease_in_out(prog(t, 12.8, 0.9))
            scale = 0.88 + 0.06 * p
            angle = -360 * (1 - ease_out_quint(prog(t, 12.8, 1.4)))
        capped, cap_fx = True, None
        if 7.15 <= t < 14.1:
            capped = False
            if t < 7.9:  # pop the cap off: up, out to the right, spinning, fading
                p = prog(t, 7.15, 0.75)
                cap_fx = (420 * p ** 1.6, -300 * ease_out(p) + 160 * p * p, -40 * p, 1 - prog(t, 7.55, 0.35))
            elif t >= 13.5:  # cap drops back on during the end-card turn
                p = ease_out_quint(prog(t, 13.5, 0.6))
                cap_fx = (0, -420 * (1 - p), 0, clamp((t - 13.5) / 0.2))
        nx, ny, top, bh = place_bottle(c, t, angle, cx, scale, tilt, lift, presence, capped, cap_fx)
        spray(c, t, 8.0, nx, ny)
        spray(c, t, 11.55, nx, ny, dur=0.6)

    # S3 5.2–7.0  name
    reveal(c, text("INTRODUCING", 500, 32, SLATE, tracking=14), W / 2, 280, t, 5.3, 0.6, out_t=6.95)
    reveal(c, text("Himalayan Sea Salt", 600, 86, INDIGO), W / 2, 380, t, 5.5, 0.7, out_t=6.95)
    reveal(c, text("Hair Spray", 300, 86, INDIGO), W / 2, 480, t, 5.7, 0.7, out_t=6.95)

    # S4 7.6–10.6  callouts (bottle at x≈340, top≈580)
    if 7.5 <= t < 10.75:
        fade_out = prog(t, 10.45, 0.3)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bx = W / 2 - 200
        callout(layer, t, 8.4, bx + 40, 880, 620, "Instant volume", "styled in under 10 seconds")
        callout(layer, t, 8.9, bx + 95, 1170, 620, "Matte texture", "looks styled, feels untouched")
        callout(layer, t, 9.4, bx + 95, 1440, 620, "Zero grease", "never sticky, never heavy")
        if fade_out:
            layer.putalpha(layer.getchannel("A").point(lambda v: int(v * (1 - fade_out))))
        c.alpha_composite(layer)

    # S5 10.8–12.8  Shake. Spray. Style.
    if 10.8 <= t < 12.85:
        words = (("Shake.", 11.0), ("Spray.", 11.5), ("Style.", 12.0))
        xs = (W / 2 - 300, W / 2, W / 2 + 300)
        for (wd, t0), x in zip(words, xs):
            active = t0 <= t < t0 + 0.5 or (wd == "Style." and t >= t0)
            col = INDIGO if active else SLATE
            reveal(c, text(wd, 600 if active else 300, 88, col), x, 420, t, t0, 0.45, out_t=12.6, out_dur=0.25)

    # S6 12.8–15  end card
    if t >= 12.8:
        p = ease_out_quint(prog(t, 13.1, 0.8))
        if p > 0:
            lg = LOGO.copy()
            lg.putalpha(lg.getchannel("A").point(lambda v: int(v * p)))
            c.alpha_composite(lg, (int(W / 2 - lg.width / 2), int(250 + 30 * (1 - p))))
        reveal(c, text("Born in Himachal.", 300, 56, SLATE), W / 2, 450, t, 13.45, 0.6)
        q = ease_out_quint(prog(t, 13.8, 0.6))
        if q > 0:
            label = text("₹449  ·  spraymax.in", 500, 40, (255, 255, 255))
            pw, ph = label.width + 90, label.height + 46
            pill = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
            ImageDraw.Draw(pill).rounded_rectangle((0, 0, pw - 1, ph - 1), radius=ph // 2, fill=INDIGO + (255,))
            pill.alpha_composite(label, (45, 23))
            pill.putalpha(pill.getchannel("A").point(lambda v: int(v * q)))
            c.alpha_composite(pill, (int(W / 2 - pw / 2), int(1745 + 20 * (1 - q))))

    # film grain
    arr = np.asarray(c.convert("RGB")).astype(np.float32)
    g = GRAIN[int(t * FPS) % len(GRAIN)].repeat(2, 0).repeat(2, 1)[:H, :W]
    arr += g[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


# ---------- audio: restrained ----------
def audio(path, sr=44100):
    n = int(sr * DUR)
    out = np.zeros(n)
    tt = np.arange(n) / sr

    def add(t0, sig):
        i = int(t0 * sr)
        out[i:i + len(sig)] += sig[: n - i]

    def smooth(x, k):
        return np.convolve(x, np.ones(k) / k, mode="same")

    # warm pad: two soft chords with slow swell
    pad = np.zeros(n)
    for f, a in ((110, 0.05), (164.8, 0.035), (220, 0.025), (277.2, 0.018)):
        pad += a * np.sin(2 * np.pi * f * tt + np.sin(2 * np.pi * 0.2 * tt) * 0.4)
    pad *= np.clip(tt / 2.5, 0, 1) * np.clip((DUR - tt) / 1.2, 0, 1)
    out += pad
    # soft ticks on text reveals
    for t0 in (0.25, 2.45, 2.95, 3.6, 5.5, 8.7, 9.2, 9.7):
        L = int(0.05 * sr)
        x = np.arange(L) / sr
        add(t0, np.sin(2 * np.pi * 1400 * x) * np.exp(-x * 90) * 0.12)
    # airy whoosh as the bottle descends
    L = int(1.6 * sr)
    w = rng.standard_normal(L)
    w = smooth(w, 6) - smooth(w, 60)
    env = np.sin(np.linspace(0, np.pi, L)) ** 2
    add(4.8, w * env * 0.22)
    # soft low thud when it lands
    L = int(0.5 * sr)
    x = np.arange(L) / sr
    add(6.7, np.sin(2 * np.pi * (70 + 40 * np.exp(-x * 25)) * x) * np.exp(-x * 9) * 0.35)
    # spray: crisp, high-frequency "tss"
    for t0, d in ((8.0, 0.55), (11.55, 0.45)):
        L = int(d * sr)
        w = rng.standard_normal(L)
        w = w - smooth(w, 4)                       # high-pass
        x = np.linspace(0, 1, L)
        env = np.minimum(x * 25, 1) * np.exp(-x * 3.2)
        add(t0, w * env * 0.28)
    # shake rattle
    for k in range(3):
        L = int(0.06 * sr)
        w = rng.standard_normal(L) - smooth(rng.standard_normal(L), 3)
        add(11.08 + k * 0.13, w * np.exp(-np.arange(L) / sr * 60) * 0.12)
    # cap pop and snap-back
    for t0, g in ((7.17, 0.22), (14.08, 0.3)):
        L = int(0.04 * sr)
        x = np.arange(L) / sr
        w = rng.standard_normal(L) - smooth(rng.standard_normal(L), 3)
        add(t0, (w * 0.6 + np.sin(2 * np.pi * 2200 * x)) * np.exp(-x * 140) * g)
    # end chime
    L = int(2.0 * sr)
    x = np.arange(L) / sr
    add(13.1, (np.sin(2 * np.pi * 880 * x) * 0.08 + np.sin(2 * np.pi * 1318.5 * x) * 0.05) * np.exp(-x * 2.2))
    out = np.tanh(out * 1.2)
    out *= 0.84 / np.max(np.abs(out))                  # peak at about -1.5 dBFS
    pcm = (np.clip(out, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def main():
    global BOTTLE, BOTTLE_NC, CAP, SET, LOGO
    OUT.mkdir(parents=True, exist_ok=True)
    SET = make_set()
    BOTTLE = Bottle(height=1060)
    BOTTLE_NC = Bottle(height=1060)
    BOTTLE_NC.base = make_capless(BOTTLE.base)
    CAP = make_cap(BOTTLE.base)
    logo = Image.open(ASSETS / "logo-wide.png").convert("RGBA")
    logo = logo.crop(logo.getbbox())
    LOGO = logo.resize((560, int(560 * logo.height / logo.width)), Image.LANCZOS)

    if "--preview" in sys.argv:
        for ts in (6.9, 7.3, 7.6, 8.15, 9.0, 11.65, 13.7, 13.95, 14.6):
            frame(ts).save(OUT / f"v2_preview_{ts:05.2f}.jpg", quality=90)
        print("previews written")
        return

    wav = OUT / "sfx_v2.wav"
    audio(wav)
    mp4 = OUT / "spraymax-brand-15s.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", str(wav), "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(mp4)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(N):
        p.stdin.write(frame(i / FPS).tobytes())
        if i % 90 == 0:
            print(f"frame {i}/{N}", flush=True)
    p.stdin.close()
    p.wait()
    wav.unlink()
    print("wrote", mp4)


if __name__ == "__main__":
    main()
