#!/usr/bin/env python3
"""Spraymax "Combo Drop" — Pack of 2 / Pack of 3 campaign.

Concept: One's good. Two's better. Three's the move.
Seven short clips cut on a 120 BPM beat, alternating grainy brand indigo and
paper-white sets, in the visual language of Spraymax's own combo creatives
(tight grotesk type, indigo price tags, red strike-throughs, dashed arrows,
frosted-glass panels, italic hand-note).

Deliverables (1080x1920, 30 fps, H.264 + AAC):
  combo-15s.mp4        full film
  combo-pack2-6s.mp4   Stories cut-down, Pack of 2
  combo-pack3-6s.mp4   Stories cut-down, Pack of 3

Usage: python3 video/render_combo.py [--preview] [--only main|pack2|pack3]
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
from render_brand import CAP_BOX, make_cap, make_capless, reveal, ease_out_quint  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "video/fonts"
OUT = ROOT / "ads/spraymax/combo-packs/video"
W, H, FPS = 1080, 1920, 30

INDIGO = (16, 4, 158)
INDIGO_BG = (14, 8, 148)
INK = (18, 18, 20)
PAPER = (243, 243, 241)
RED = (186, 22, 38)
ARROW = (92, 88, 214)
WHITE = (255, 255, 255)
rng = np.random.default_rng(11)

PRICES = {2: ("₹899", "₹799", "₹100"), 3: ("₹1,347", "₹999", "₹348")}


# ---------------------------------------------------------------- type
@lru_cache(None)
def font(name, size):
    return ImageFont.truetype(str(FONTS / f"{name}.ttf"), size)


@lru_cache(None)
def txt(s, name, size, color=INK, gradient=False, tracking=0):
    f = font(name, size)
    l, t, r, b = f.getbbox(s) if not tracking else (0, 0, int(sum(f.getlength(ch) + tracking for ch in s)), size)
    asc, desc = f.getmetrics()
    w, h = int(r - min(0, l)) + 8, asc + desc + 8
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    if tracking:
        x = 4
        for ch in s:
            d.text((x, 4), ch, font=f, fill=255)
            x += f.getlength(ch) + tracking
    else:
        d.text((4 - min(0, l), 4), s, font=f, fill=255)
    if gradient:  # their headline: near-black edges with a soft metallic mid band
        y = np.linspace(0, 1, h)[:, None]
        g = 20 + 52 * np.exp(-((y - 0.45) / 0.22) ** 2)
        fill = np.repeat(np.repeat(g, w, 1)[..., None], 3, 2).astype(np.uint8)
        im = Image.fromarray(fill, "RGB").convert("RGBA")
    else:
        im = Image.new("RGBA", (w, h), color + (255,))
    im.putalpha(mask)
    return im.crop(mask.getbbox())


def put(c, img, cx, cy, alpha=1.0, scale=1.0, anchor="center"):
    if alpha <= 0.004 or scale <= 0.01:
        return
    im = img
    if scale != 1:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 1:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    x = cx - im.width / 2 if anchor == "center" else cx
    c.alpha_composite(im, (int(x), int(cy - im.height / 2)))


def pill(label, fill, pad=(26, 12), radius=None, outline=None):
    pw, ph = label.width + pad[0] * 2, label.height + pad[1] * 2
    im = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, pw - 1, ph - 1), radius=radius or ph // 2,
                                         fill=fill + (255,) if fill else None,
                                         outline=outline + (255,) if outline else None, width=3)
    im.alpha_composite(label, (pad[0], pad[1]))
    return im


# ---------------------------------------------------------------- sets
def make_paper(floor_y=1395):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    arr = np.zeros((H, W, 3), np.float32) + np.array(PAPER, np.float32)
    d = ((xx - W / 2) / W) ** 2 + ((yy - 900) / H) ** 2
    arr += (np.exp(-d * 3) * 8 - 6)[..., None]
    if floor_y:
        f = np.clip((yy - floor_y) / 6, 0, 1)[..., None]       # crisp-ish horizon like their set
        floor = np.array([226, 226, 229], np.float32) + (np.clip((yy - floor_y) / 500, 0, 1) * 10)[..., None]
        arr = arr * (1 - f) + floor * f
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")


def make_indigo():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = ((xx - W / 2) / W) ** 2 + ((yy - H * 0.48) / H) ** 2
    k = np.clip(1 - v * 1.25, 0.55, 1)[..., None]
    arr = np.array(INDIGO_BG, np.float32) * k + (np.exp(-v * 6) * 18)[..., None] * np.array([0.5, 0.5, 1.0])
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")


GRAIN = [rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32) for _ in range(5)]


def grain(img, i, strength):
    arr = np.asarray(img.convert("RGB")).astype(np.float32)
    g = GRAIN[i % len(GRAIN)].repeat(2, 0).repeat(2, 1)[:H, :W, None] * strength
    lum = arr.mean(2, keepdims=True) / 255
    weight = np.clip(1.25 - lum * 1.1, 0.12, 1.0)
    return Image.fromarray(np.clip(arr + g * weight, 0, 255).astype(np.uint8))


def glass(c, box, radius=34, tint=0.10, blur=22):
    x0, y0, x1, y1 = (int(v) for v in box)
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    if x1 - x0 < 4 or y1 - y0 < 4:
        return
    region = c.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(blur))
    region = Image.blend(region, Image.new("RGBA", region.size, (255, 255, 255, 255)), tint)
    hl = Image.new("RGBA", region.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    for i in range(60):  # top highlight gradient
        hd.line((0, i, region.width, i), fill=(255, 255, 255, int(28 * (1 - i / 60))))
    region.alpha_composite(hl)
    mask = Image.new("L", region.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, region.width - 1, region.height - 1), radius=radius, fill=255)
    c.paste(region, (x0, y0), mask)
    ImageDraw.Draw(c).rounded_rectangle((x0, y0, x1 - 1, y1 - 1), radius=radius, outline=(255, 255, 255, 80), width=2)


# ---------------------------------------------------------------- product
class Packshot:
    """The real-label bottle with the rebuilt pump and the clear cap seated: one consistent model."""

    def __init__(self, height=1000):
        self.b = Bottle(height=height)
        self.b.base = make_capless(self.b.base)
        self.b.cache = {}
        s = self.b.scale
        cap = make_cap()
        self.cap = cap.resize((int(cap.width * s), int(cap.height * s)), Image.LANCZOS)
        self.full = {}
        self.sized = {}

    def get(self, angle, h):
        key = int(round(angle / 3.0)) % 120
        if key not in self.full:
            im = self.b.render(key * 3.0).copy()
            s = self.b.scale
            im.alpha_composite(self.cap, (int(CAP_BOX[0] * s), int(CAP_BOX[1] * s)))
            self.full[key] = im
        hq = max(40, int(round(h / 6.0)) * 6)
        k2 = (key, hq)
        if k2 not in self.sized:
            im = self.full[key]
            self.sized[k2] = im.resize((int(im.width * hq / im.height), hq), Image.LANCZOS)
            if len(self.sized) > 400:
                self.sized.pop(next(iter(self.sized)))
        return self.sized[k2]


PS = None
BOW = None
BAND_TEX = None
RIB = (37, 63, 118)           # satin navy measured from the brand's combo creative


def make_band_texture(w=1400, h=120):
    """Satin band: measured navy, soft sheen across the middle, fine woven grain, stitched edges."""
    r = np.random.default_rng(3)
    y = np.linspace(0, 1, h)[:, None]
    sheen = 0.82 + 0.34 * np.exp(-((y - 0.36) / 0.15) ** 2) - 0.14 * (np.abs(y - 0.5) * 2) ** 3
    fine = r.normal(0, 1, (h, w))
    low = np.cumsum(r.normal(0, 1, (h, w)), 1)
    low = (low - np.convolve(low.mean(0), np.ones(25) / 25, mode="same")[None, :]) / 40
    tex = sheen * (1 + 0.045 * fine + 0.08 * np.tanh(low))
    for e in (0.07, 0.93):  # stitch lines near the edges
        tex += 0.10 * np.exp(-((y - e) / 0.012) ** 2)
    rgb = np.clip(np.array(RIB, np.float32)[None, None, :] / 255 * tex[..., None], 0, 1)
    return Image.fromarray((rgb * 255).astype(np.uint8), "RGB").convert("RGBA")


def ribbon(L, items, band_p, bow_p, alpha=1.0):
    """Wrap a satin band across the pack (grows from the centre) and pop the brand's bow on top."""
    if band_p <= 0 or not items:
        return
    front = items[-1]
    hf = front["h"]
    cy = front["base"] - hf + 0.59 * hf
    t = max(6, int(0.091 * hf))
    halfw = [0.2514 * it["h"] / 2 for it in items]
    x0 = min(it["x"] - hw for it, hw in zip(items, halfw))
    x1 = max(it["x"] + hw for it, hw in zip(items, halfw))
    mid = (x0 + x1) / 2
    gx0 = mid - (mid - x0) * ease_out_quint(band_p)
    gx1 = mid + (x1 - mid) * ease_out_quint(band_p)
    wpx = int(gx1 - gx0)
    if wpx < 2:
        return
    band = BAND_TEX.resize((BAND_TEX.width, t), Image.BICUBIC).crop((0, 0, wpx, t))
    xs = np.arange(wpx) + gx0
    shade = np.full(wpx, 0.78)
    for it, hw in zip(items, halfw):  # wrap shading: darker where the band turns away on each bottle
        u = (xs - it["x"]) / hw
        inside = np.abs(u) < 1
        shade = np.where(inside, 0.6 + 0.4 * np.sqrt(np.clip(1 - u ** 2, 0, 1)), shade)  # front bottle wins
    arr = np.asarray(band).astype(np.float32)
    arr[..., :3] *= shade[None, :, None]
    arr[..., 3] = 255 * alpha
    band = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    shadow = Image.new("RGBA", (wpx + 40, t + 40), (0, 0, 0, 0))
    sd = Image.new("RGBA", (wpx, t), (10, 10, 40, int(110 * alpha)))
    shadow.alpha_composite(sd, (20, 26))
    L.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(7)), (int(gx0 - 20), int(cy - t / 2 - 20)))
    L.alpha_composite(band, (int(gx0), int(cy - t / 2)))
    q = prog(bow_p, 0, 1)
    if q > 0:
        k = hf / 1055.0
        sc = (0.4 + 0.6 * (1 + 2.7 * (q - 1) ** 3 + 1.7 * (q - 1) ** 2)) if q < 1 else 1.0
        bw, bh = int(BOW.width * k * sc), int(BOW.height * k * sc)
        if bw > 4 and bh > 4:
            bow = BOW.resize((bw, bh), Image.LANCZOS)
            a_ = min(1, q * 3) * alpha
            if a_ < 1:
                bow.putalpha(bow.getchannel("A").point(lambda v: int(v * a_)))
            bsh = Image.new("RGBA", (bw + 40, bh + 40), (0, 0, 0, 0))
            sil = Image.new("RGBA", bow.size, (10, 10, 40, 0))
            sil.putalpha(bow.getchannel("A").point(lambda v: int(v * 0.45)))
            bsh.alpha_composite(sil, (20, 28))
            L.alpha_composite(bsh.filter(ImageFilter.GaussianBlur(8)), (int(mid - bw / 2 - 20), int(cy - 86 * k * sc - 20)))
            L.alpha_composite(bow, (int(mid - bw / 2), int(cy - 86 * k * sc)))


def bottles(c, items, floor=True, glow=False, layer_rot=0.0, layer_off=(0, 0), pivot=None, wrap=None):
    """items: dicts x, base, h, angle, [alpha]; drawn in list order (back to front).
    wrap: (band_progress, bow_progress[, alpha]) to add the ribbon."""
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)) if (layer_rot or layer_off != (0, 0)) else c
    for it in items:
        img = PS.get(it.get("angle", 0), it["h"])
        a = it.get("alpha", 1.0)
        x, base = it["x"], it["base"]
        top = base - img.height
        if floor:  # contact + ambient shadow
            sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            sd = ImageDraw.Draw(sh)
            rx = img.width * 0.55
            sd.ellipse((x - rx * 1.35, base - 22, x + rx * 1.35, base + 26), fill=(30, 30, 40, int(55 * a)))
            sd.ellipse((x - rx * 0.8, base - 8, x + rx * 0.8, base + 10), fill=(20, 20, 30, int(110 * a)))
            L.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
        # occlusion shadow onto whatever is behind (gives overlap depth)
        sil = Image.new("RGBA", img.size, (10, 10, 30, 0))
        sil.putalpha(img.getchannel("A").point(lambda v: int(v * (0.32 if floor else 0.45) * a)))
        sil = sil.filter(ImageFilter.GaussianBlur(14))
        L.alpha_composite(sil, (int(x - img.width / 2 + 10), int(top + 6)))
        if glow:
            gl = Image.new("RGBA", img.size, WHITE + (0,))
            gl.putalpha(img.getchannel("A").point(lambda v: int(v * 0.35 * a)))
            pad = Image.new("RGBA", (img.width + 80, img.height + 80), (0, 0, 0, 0))
            pad.alpha_composite(gl, (40, 40))
            L.alpha_composite(pad.filter(ImageFilter.GaussianBlur(16)), (int(x - img.width / 2 - 40), int(top - 40)))
        im = img
        if a < 1:
            im = img.copy()
            im.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
        L.alpha_composite(im, (int(x - img.width / 2), int(top)))
    if wrap:
        ribbon(L, items, *wrap)
    if L is not c:
        if layer_rot:
            L = L.rotate(layer_rot, resample=Image.BICUBIC, center=pivot or (W / 2, H / 2))
        c.alpha_composite(L, (int(layer_off[0]), int(layer_off[1])) if layer_off != (0, 0) else (0, 0))


# ---------------------------------------------------------------- graphic devices
def price_line(c, lt, t0, n, cy, on_dark=False):
    """AT <old> (struck) <new tag>. Returns the tag's right-middle point once visible."""
    old, new, _ = PRICES[n]
    col = WHITE if on_dark else INDIGO
    at = txt("AT", "InterTight-800", 92, col)
    old_i = txt(old, "InterTight-800", 92, col)
    new_lbl = txt(new, "InterTight-800", 100, INDIGO if on_dark else WHITE)
    tag = pill(new_lbl, WHITE if on_dark else INDIGO, pad=(22, 10), radius=22)
    gap = 26
    total = at.width + gap + old_i.width + gap + tag.width
    x = W / 2 - total / 2
    p = ease_out_quint(prog(lt, t0, 0.45))
    reveal(c, at, x, cy, lt, t0, 0.45, anchor="left")
    reveal(c, old_i, x + at.width + gap, cy, lt, t0 + 0.06, 0.45, anchor="left")
    # strike-through, drawn left to right with a slight upward slant
    s = ease_in_out(prog(lt, t0 + 0.45, 0.25))
    if s > 0:
        sx0 = x + at.width + gap - 8
        sx1 = sx0 + (old_i.width + 16) * s
        d = ImageDraw.Draw(c)
        d.line((sx0, cy + 16, sx1, cy + 16 - 34 * s * (old_i.width + 16) / (old_i.width + 16)), fill=RED + (255,), width=8)
    # tag pops with a soft overshoot
    q = prog(lt, t0 + 0.72, 0.38)
    if q > 0:
        sc = 0.6 + 0.4 * (1 + 2.7 * (q - 1) ** 3 + 1.7 * (q - 1) ** 2) if q < 1 else 1.0
        tx = x + at.width + gap + old_i.width + gap + tag.width / 2
        put(c, tag, tx, cy, alpha=min(1, q * 3), scale=sc)
        return (tx + tag.width / 2, cy)
    return None


def dashed_arrow(c, lt, t0, p0, p3, bend=(260, 40), color=ARROW, dur=0.55):
    p = ease_in_out(prog(lt, t0, dur))
    if p <= 0 or p0 is None:
        return
    (x0, y0), (x3, y3) = p0, p3
    p1 = (x0 + bend[0], y0 + bend[1])
    p2 = (x3 + bend[0] * 0.9, y3 - 140)
    ts = np.linspace(0, p, max(2, int(140 * p)))
    pts = [((1 - t) ** 3 * x0 + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t * t * p2[0] + t ** 3 * x3,
            (1 - t) ** 3 * y0 + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t * t * p2[1] + t ** 3 * y3) for t in ts]
    d = ImageDraw.Draw(c)
    acc, on = 0.0, True
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        seg = math.hypot(bx - ax, by - ay)
        if on:
            d.line((ax, ay, bx, by), fill=color + (255,), width=5)
        acc += seg
        if acc > (16 if on else 11):
            acc, on = 0.0, not on
    if p > 0.97:
        (ax, ay), (bx, by) = pts[-4], pts[-1]
        ang = math.atan2(by - ay, bx - ax)
        L = 30
        tip = (bx, by)
        left = (bx - L * math.cos(ang - 0.45), by - L * math.sin(ang - 0.45))
        right = (bx - L * math.cos(ang + 0.45), by - L * math.sin(ang + 0.45))
        d.polygon((tip, left, right), fill=color + (255,))


def save_chip(c, lt, t0, n, cx, cy, on_dark=False):
    q = ease_out_quint(prog(lt, t0, 0.4))
    if q <= 0:
        return
    col = WHITE if on_dark else INDIGO
    lbl = txt(f"SAVE {PRICES[n][2]}", "InterTight-800", 40, col, tracking=2)
    put(c, pill(lbl, None, pad=(24, 10), outline=col), cx, cy + 16 * (1 - q), alpha=q)


def hand_note(c, lt, t0, cx, cy, on_dark=False, size=50):
    """Italic 'Less price… More texture.' with an indigo swoosh drawn under 'texture'."""
    col = WHITE if on_dark else INK
    l1 = txt("Less price…", "InterTight-500i", size, col)
    l2a = txt("More", "InterTight-500i", size, col)
    l2b = txt("texture.", "InterTight-500i", size, col)
    sp = int(size * 0.26)
    w2 = l2a.width + sp + l2b.width
    x = cx - max(l1.width, w2) / 2
    reveal(c, l1, x, cy - size * 0.62, lt, t0, 0.45, anchor="left")
    reveal(c, l2a, x, cy + size * 0.62, lt, t0 + 0.12, 0.45, anchor="left")
    reveal(c, l2b, x + l2a.width + sp, cy + size * 0.62, lt, t0 + 0.12, 0.45, anchor="left")
    s = ease_in_out(prog(lt, t0 + 0.5, 0.4))
    if s > 0:
        sx = x + l2a.width + sp
        sw = l2b.width - 8
        y = cy + size * 0.62 + size * 0.62
        pts = []
        for i in range(int(40 * s) + 1):
            t = i / 40
            pts.append((sx + sw * t, y + 6 * math.sin(t * math.pi) - 4 * t))
        d = ImageDraw.Draw(c)
        swc = (150, 160, 255) if on_dark else INDIGO
        if len(pts) > 1:
            d.line(pts, fill=swc + (255,), width=4, joint="curve")
        if s > 0.95:  # flick
            ex, ey = pts[-1]
            d.line((ex, ey, ex - 22, ey + 12), fill=swc + (255,), width=4)


# ---------------------------------------------------------------- scenes (local time lt)
PAPER_SET = None
PAPER_PLAIN = None
INDIGO_SET = None
LOGO = None
LOGO_WHITE = None


def s_one(lt, dur):
    c = INDIGO_SET.copy()
    p = ease_out_quint(prog(lt, 0.05, 0.75))
    bottles(c, [dict(x=W / 2, base=1745 + 900 * (1 - p), h=1000, angle=70 * (1 - p))], floor=False, glow=True)
    reveal(c, txt("ONE’S", "InterTight-800", 210, WHITE), W / 2, 330, lt, 0.15, 0.5, out_t=dur - 0.2, out_dur=0.2)
    reveal(c, txt("GOOD.", "InterTight-800", 210, WHITE), W / 2, 535, lt, 0.28, 0.5, out_t=dur - 0.2, out_dur=0.2)
    q = ease_out_quint(prog(lt, 0.9, 0.4))
    put(c, txt("1 × 100 ml  ·  ₹449", "InterTight-600", 40, (205, 205, 255)), W / 2, 1840 + 12 * (1 - q), alpha=q)
    return c, "indigo"


def pair_items(lt, slide_t0=0.0):
    p = ease_out_quint(prog(lt, slide_t0, 0.55))
    return [dict(x=W / 2 - 112 * p, base=1590, h=920, angle=-8 * p),
            dict(x=W / 2 + 112 + 700 * (1 - p), base=1590, h=920, angle=10 + 30 * (1 - p))]


def s_two(lt, dur):
    c = PAPER_SET.copy()
    bottles(c, pair_items(lt, 0.05), wrap=(prog(lt, 0.72, 0.4), prog(lt, 1.02, 0.42)))
    reveal(c, txt("TWO’S", "InterTight-800", 210, gradient=True), W / 2, 330, lt, 0.15, 0.5, out_t=dur - 0.22, out_dur=0.22)
    reveal(c, txt("BETTER.", "InterTight-800", 210, gradient=True), W / 2, 535, lt, 0.28, 0.5, out_t=dur - 0.22, out_dur=0.22)
    return c, "paper"


def s_pack(n):
    def scene(lt, dur):
        c = PAPER_SET.copy()
        if n == 2:
            items = pair_items(10)
            target = (W / 2 + 230, 820)
        else:
            p = ease_out_quint(prog(lt, 0.0, 0.6))
            items = [dict(x=W / 2 - 205 * p, base=1585, h=860, angle=-12 * p),
                     dict(x=W / 2 + 205 * p, base=1585, h=860, angle=12 * p),
                     dict(x=W / 2, base=1600, h=930, angle=0)]
            target = (W / 2 + 300, 860)
        wrap = (1, 1) if n == 2 else (prog(lt, 0.55, 0.4), prog(lt, 0.85, 0.42))
        bottles(c, items, wrap=wrap)
        reveal(c, txt(f"PACK OF {n}", "InterTight-800", 172, gradient=True), W / 2, 300, lt, 0.05, 0.5)
        tag_end = price_line(c, lt, 0.3, n, 468)
        dashed_arrow(c, lt, 1.15, tag_end, target)
        save_chip(c, lt, 1.25, n, W / 2, 590)
        hand_note(c, lt, 1.45, W / 2, 1770, size=46)
        return c, "paper"
    return scene


def s_three(lt, dur):
    c = INDIGO_SET.copy()
    p = ease_out_quint(prog(lt, 0.02, 0.7))
    f = ease_out_quint(prog(lt, 0.2, 0.6))  # crisp indigo frame behind the pack (brand trio creative)
    fy = 700 * (1 - f)
    d = ImageDraw.Draw(c)
    d.rectangle((330, 650 + fy, 750, 1720 + fy), fill=(10, 0, 178, 255))
    d.rectangle((330, 650 + fy, 750, 1720 + fy), outline=(185, 185, 255, 150), width=2)
    items = [dict(x=W / 2 - 185, base=1630, h=900, angle=-6),
             dict(x=W / 2, base=1630, h=900, angle=0),
             dict(x=W / 2 + 185, base=1630, h=900, angle=6)]
    bottles(c, items, floor=False, glow=True, layer_rot=22 + 18 * (1 - p),
            layer_off=(620 * (1 - p), 520 * (1 - p) - 70), pivot=(W / 2, 1180), wrap=(1, 1))
    reveal(c, txt("THREE’S", "InterTight-800", 176, WHITE), W / 2, 300, lt, 0.15, 0.5, out_t=dur - 0.2, out_dur=0.2)
    reveal(c, txt("THE MOVE.", "InterTight-800", 176, WHITE), W / 2, 482, lt, 0.28, 0.5, out_t=dur - 0.2, out_dur=0.2)
    return c, "indigo"


def s_compare(lt, dur):
    c = INDIGO_SET.copy()
    reveal(c, txt("PICK YOUR PACK.", "InterTight-800", 112, WHITE), W / 2, 300, lt, 0.05, 0.45)
    for i, (n, x0, x1) in enumerate(((2, 60, 525), (3, 555, 1020))):
        p = ease_out_quint(prog(lt, 0.12 + i * 0.12, 0.55))
        dy = 900 * (1 - p)
        glass(c, (x0, 470 + dy, x1, 1560 + dy), radius=34, tint=0.12, blur=20)
        cx = (x0 + x1) / 2
        put(c, txt(f"PACK OF {n}", "InterTight-800", 62, WHITE), cx, 560 + dy)
        if n == 2:
            its = [dict(x=cx - 62, base=1150 + dy, h=520, angle=-10), dict(x=cx + 62, base=1150 + dy, h=520, angle=10)]
        else:
            its = [dict(x=cx - 110, base=1140 + dy, h=470, angle=-14), dict(x=cx + 110, base=1140 + dy, h=470, angle=14),
                   dict(x=cx, base=1150 + dy, h=505, angle=0)]
        bottles(c, its, floor=False, wrap=(1, 1))
        tag = pill(txt(PRICES[n][1], "InterTight-800", 78, INDIGO), WHITE, pad=(22, 8), radius=18)
        put(c, tag, cx, 1270 + dy)
        each = "Under ₹400 each" if n == 2 else "Just ₹333 each"
        put(c, txt(each, "InterTight-600", 40, (215, 215, 255)), cx, 1375 + dy)
        put(c, txt(f"{n} × 100 ml", "InterTight-600", 32, (170, 170, 235)), cx, 1450 + dy)
    q = prog(lt, 0.75, 0.35)
    if q > 0:
        sc = 0.6 + 0.4 * (1 + 2.7 * (q - 1) ** 3 + 1.7 * (q - 1) ** 2) if q < 1 else 1.0
        badge = pill(txt("BEST VALUE", "InterTight-800", 34, INDIGO, tracking=2), (205, 225, 255), pad=(20, 9))
        put(c, badge, 935, 470, alpha=min(1, q * 3), scale=sc)
    return c, "indigo"


def s_end(variant):
    def scene(lt, dur):
        c = PAPER_PLAIN.copy()
        p = ease_out_quint(prog(lt, 0.05, 0.55))
        put(c, LOGO, W / 2, 330 + 24 * (1 - p), alpha=p)
        reveal(c, txt("THE COMBO COLLECTION", "InterTight-800", 44, INK, tracking=6), W / 2, 450, lt, 0.2, 0.45)
        k = ease_out_quint(prog(lt, 0.1, 0.6))
        if variant == 2:
            its = [dict(x=W / 2 - 92, base=1270 + 60 * (1 - k), h=640, angle=-8), dict(x=W / 2 + 92, base=1270 + 60 * (1 - k), h=640, angle=8)]
        else:
            its = [dict(x=W / 2 - 150, base=1262 + 60 * (1 - k), h=600, angle=-12), dict(x=W / 2 + 150, base=1262 + 60 * (1 - k), h=600, angle=12),
                   dict(x=W / 2, base=1272 + 60 * (1 - k), h=650, angle=0)]
        for it in its:
            it["alpha"] = k
        bottles(c, its, wrap=(1, 1, k))
        hand_note(c, lt, 0.35, W / 2, 1405, size=50)
        q = ease_out_quint(prog(lt, 0.55, 0.45))
        if q > 0:
            btn = pill(txt("Shop now  ·  spraymax.in", "InterTight-800", 44, WHITE), INDIGO, pad=(46, 22))
            put(c, btn, W / 2, 1585 + 18 * (1 - q), alpha=q)
        r = ease_out_quint(prog(lt, 0.7, 0.45))
        line = {2: "Pack of 2  ·  ₹799", 3: "Pack of 3  ·  ₹999", 0: "Pack of 2  ·  ₹799        Pack of 3  ·  ₹999"}[variant]
        put(c, txt(line, "InterTight-600", 36, (70, 70, 90)), W / 2, 1712 + 10 * (1 - r), alpha=r)
        return c, "paper"
    return scene


TIMELINES = {
    "main": [(s_one, 2.0, True), (s_two, 2.0, True), (s_pack(2), 2.5, False), (s_three, 2.0, True),
             (s_pack(3), 2.5, True), (s_compare, 2.0, True), (s_end(0), 2.0, True)],
    "pack2": [(s_two, 2.0, True), (s_pack(2), 2.5, False), (s_end(2), 1.5, True)],
    "pack3": [(s_three, 2.0, True), (s_pack(3), 2.5, True), (s_end(3), 1.5, True)],
}
FILES = {"main": "combo-15s.mp4", "pack2": "combo-pack2-6s.mp4", "pack3": "combo-pack3-6s.mp4"}


def frame_at(tl, t, i):
    acc = 0.0
    for fn, dur, settle in tl:
        if t < acc + dur or fn is tl[-1][0]:
            lt = t - acc
            c, kind = fn(lt, dur)
            if settle and lt < 0.3:  # cut punch: scene lands 3% large and settles
                k = 1 + 0.03 * (1 - ease_out_quint(lt / 0.3))
                big = c.resize((int(W * k), int(H * k)), Image.BICUBIC)
                c = big.crop(((big.width - W) // 2, (big.height - H) // 2, (big.width - W) // 2 + W, (big.height - H) // 2 + H))
            return grain(c, i, 11.0 if kind == "indigo" else 4.0)
        acc += dur


def cuts(tl):
    out, acc = [], 0.0
    for _, dur, _ in tl:
        out.append(acc)
        acc += dur
    return out, acc


# ---------------------------------------------------------------- audio: 120 BPM groove
def audio(path, tl, sr=44100):
    cut_t, dur = cuts(tl)
    n = int(sr * dur)
    out = np.zeros(n)

    def add(t0, sig):
        i = int(t0 * sr)
        if i < n:
            out[i:i + len(sig)] += sig[: n - i]

    def sm(x, k):
        return np.convolve(x, np.ones(k) / k, mode="same")

    def kick(g=0.8):
        x = np.arange(int(0.35 * sr)) / sr
        return np.sin(2 * np.pi * np.cumsum(48 + 95 * np.exp(-x * 32)) / sr) * np.exp(-x * 9) * g

    def clap(g=0.22):
        L = int(0.18 * sr)
        w = rng.standard_normal(L)
        w = sm(w, 2) - sm(w, 12)
        env = np.zeros(L)
        for d in (0, 0.011, 0.022):
            i = int(d * sr)
            env[i:] += np.exp(-np.arange(L - i) / sr * 38)
        return w * env * g

    def hat(g=0.06):
        L = int(0.03 * sr)
        w = rng.standard_normal(L)
        return (w - sm(w, 3)) * np.exp(-np.arange(L) / sr * 160) * g

    beat = 0.5
    end_start = cut_t[-1]
    roots = [55.0, 43.65, 65.41, 49.0]
    t = 0.0
    k = 0
    while t < end_start - 1e-6:
        add(t, kick())
        if k % 2 == 1:
            add(t, clap())
        add(t + 0.25, hat())
        add(t, hat(0.04))
        # sub bass, one root per bar
        f = roots[(k // 4) % 4]
        L = int(0.42 * sr)
        x = np.arange(L) / sr
        add(t, np.sin(2 * np.pi * f * x) * np.minimum(1, x * 60) * np.exp(-x * 3) * 0.22)
        t += beat
        k += 1
    for ct in cut_t[1:]:  # transition swish into each cut
        L = int(0.25 * sr)
        w = rng.standard_normal(L)
        w = sm(w, 3) - sm(w, 30)
        add(ct - 0.25, w * np.linspace(0, 1, L) ** 2 * 0.18)
    # end: riser into a soft chord stab
    L = int(1.0 * sr)
    w = rng.standard_normal(L)
    w = sm(w, 2) - sm(w, 20)
    add(end_start - 1.0, w * np.linspace(0, 1, L) ** 3 * 0.12)
    x = np.arange(int(1.8 * sr)) / sr
    chord = sum(a * np.sin(2 * np.pi * f * x) for f, a in ((220, 0.12), (277.2, 0.09), (329.6, 0.08), (440, 0.05)))
    add(end_start, chord * np.exp(-x * 1.8))
    add(end_start, kick(0.9))
    out = np.tanh(out * 1.3)
    out *= 0.84 / np.max(np.abs(out))
    fade = int(0.25 * sr)
    out[-fade:] *= np.linspace(1, 0, fade)
    pcm = (out * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def setup():
    global PS, PAPER_SET, PAPER_PLAIN, INDIGO_SET, LOGO, LOGO_WHITE, BOW, BAND_TEX
    PS = Packshot(1000)
    BOW = Image.open(ASSETS / "ribbon-bow.png").convert("RGBA")
    BAND_TEX = make_band_texture()
    PAPER_SET = make_paper(1395)
    PAPER_PLAIN = make_paper(None)
    INDIGO_SET = make_indigo()
    logo = Image.open(ASSETS / "logo-wide.png").convert("RGBA")
    logo = logo.crop(logo.getbbox())
    LOGO = logo.resize((560, int(560 * logo.height / logo.width)), Image.LANCZOS)


def render(name):
    tl = TIMELINES[name]
    _, dur = cuts(tl)
    OUT.mkdir(parents=True, exist_ok=True)
    wav = OUT / f"_{name}.wav"
    audio(wav, tl)
    mp4 = OUT / FILES[name]
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", str(wav), "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(mp4)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    N = int(round(dur * FPS))
    for i in range(N):
        p.stdin.write(frame_at(tl, i / FPS, i).tobytes())
    p.stdin.close()
    p.wait()
    wav.unlink()
    print("wrote", mp4, f"{dur:.1f}s")


def main():
    setup()
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    if "--preview" in sys.argv:
        tl = TIMELINES[only or "main"]
        times = [float(x) for x in sys.argv[sys.argv.index("--times") + 1].split(",")] if "--times" in sys.argv else \
            [1.2, 3.4, 5.9, 7.6, 10.4, 12.6, 14.6]
        (OUT / "preview").mkdir(parents=True, exist_ok=True)
        for t in times:
            frame_at(tl, t, int(t * FPS)).save(OUT / "preview" / f"{only or 'main'}_{t:05.2f}.jpg", quality=90)
        print("previews written")
        return
    for name in ([only] if only else ["main", "pack2", "pack3"]):
        render(name)


if __name__ == "__main__":
    main()
