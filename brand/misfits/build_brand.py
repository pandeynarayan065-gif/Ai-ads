#!/usr/bin/env python3
"""Misfits brand kit: logo (SVG), social and web assets (HTML -> PNG via render.js), palette.

Idea: the misfit is the one piece that doesn't line up. The symbol is four tiles with one knocked off-axis in the
accent colour; the wordmark MISFITS tilts its second I the same way. Display type: Archivo Expanded Black;
text: Inter (both SIL OFL, in fonts/, free for the website too).

  python3 brand/misfits/build_brand.py [midnight-volt|noir-acid|noir-signal] && node brand/misfits/render.js
Writes brand/misfits/<theme>/logo and /social.
"""
import json
import math
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
FONT = HERE / "fonts/Archivo-ExpandedBlack.ttf"

THEMES = {
    "noir-acid": {"name": "Noir / Acid (primary)", "bg": "#0B0B0D", "ink": "#EEEBE4", "accent": "#C6FF33",
                  "muted": "#8C8C91", "panel": "#17171B", "glow": "#1b1d14", "on_accent": "#0B0B0D"},
    "noir-signal": {"name": "Noir / Signal", "bg": "#0B0B0D", "ink": "#EEEBE4", "accent": "#FF4B2B",
                    "muted": "#8C8C91", "panel": "#17171B", "glow": "#1f1410", "on_accent": "#0B0B0D"},
    "midnight-volt": {"name": "Midnight / Volt", "bg": "#0A0F1F", "ink": "#E8EEFF", "accent": "#3D6BFF",
                      "muted": "#8A93AD", "panel": "#131A30", "glow": "#17245a", "on_accent": "#FFFFFF"},
}
import sys
THEME = sys.argv[1] if len(sys.argv) > 1 else "midnight-volt"   # Narayan picked Midnight / Volt (4 Nov)
T = THEMES[THEME]
TILT_DEG = -14          # the misfit's angle
WORD = "MISFITS"
MISFIT_INDEX = 4         # the second I


def glyph_paths(text, upm_to=1.0, tracking=0.02):
    """SVG path data for each letter (font units scaled, y down), plus advance positions and cap height."""
    f = TTFont(FONT)
    gs, cmap, hmtx = f.getGlyphSet(), f.getBestCmap(), f["hmtx"]
    upm = f["head"].unitsPerEm
    cap = f["OS/2"].sCapHeight
    out, x = [], 0.0
    for ch in text:
        g = cmap[ord(ch)]
        pen = SVGPathPen(gs)
        # flip y (font y up -> svg y down), baseline at y = cap
        gs[g].draw(TransformPen(pen, (upm_to, 0, 0, -upm_to, x * upm_to, cap * upm_to)))
        adv = hmtx[g][0]
        # the glyph's ink box, for rotating a letter about its own centre
        from fontTools.pens.boundsPen import BoundsPen
        bp = BoundsPen(gs)
        gs[g].draw(bp)
        xmin, ymin, xmax, ymax = bp.bounds
        out.append({"d": pen.getCommands(), "x": x, "adv": adv,
                    "cx": (x + (xmin + xmax) / 2) * upm_to, "cy": (cap - (ymin + ymax) / 2) * upm_to})
        x += adv + tracking * upm
    return out, x - tracking * upm, cap, upm


def wordmark_group(ink, accent, scale=1.0):
    letters, width, cap, upm = glyph_paths(WORD, scale)
    parts = []
    for i, L in enumerate(letters):
        if i == MISFIT_INDEX:
            dy = cap * scale * 0.06
            parts.append(f'<path d="{L["d"]}" fill="{accent}" transform="translate(0 {dy:.1f}) '
                         f'rotate({TILT_DEG} {L["cx"]:.1f} {L["cy"]:.1f})"/>')
        else:
            parts.append(f'<path d="{L["d"]}" fill="{ink}"/>')
    return "\n".join(parts), width * scale, cap * scale


def symbol_group(ink, accent, size):
    """2x2 tiles in a size x size box; the top-right one rotated and nudged out, in the accent."""
    gap = size * 0.10
    t = (size - gap) / 2
    rx = t * 0.14
    tiles = []
    for (cx, cy) in ((0, 0), (0, 1), (1, 1)):
        tiles.append(f'<rect x="{cx * (t + gap):.2f}" y="{cy * (t + gap):.2f}" width="{t:.2f}" height="{t:.2f}" '
                     f'rx="{rx:.2f}" fill="{ink}"/>')
    mx, my = (t + gap) + t / 2 + size * 0.035, t / 2 - size * 0.035
    tiles.append(f'<rect x="{mx - t / 2:.2f}" y="{my - t / 2:.2f}" width="{t:.2f}" height="{t:.2f}" rx="{rx:.2f}" '
                 f'fill="{accent}" transform="rotate({TILT_DEG + 30} {mx:.2f} {my:.2f})"/>')
    return "\n".join(tiles)


def svg(w, h, body, bg=None):
    rect = f'<rect width="100%" height="100%" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}">'
            f'{rect}{body}</svg>')


def lockup(ink, accent, cap_px=200):
    """Horizontal logo: symbol + wordmark, cap height cap_px."""
    letters, width, cap, upm = glyph_paths(WORD)
    s = cap_px / cap
    wm, wmw, wmh = wordmark_group(ink, accent, s)
    sym = cap_px * 1.18
    pad = cap_px * 0.12
    gap = cap_px * 0.5
    W = pad + sym + gap + wmw + pad
    H = pad * 2 + sym
    body = (f'<g transform="translate({pad:.1f} {pad:.1f})">{symbol_group(ink, accent, sym)}</g>'
            f'<g transform="translate({pad + sym + gap:.1f} {pad + (sym - cap_px) / 2:.1f})">{wm}</g>')
    return W, H, body


def main():
    root = HERE / THEME
    logo = root / "logo"
    logo.mkdir(parents=True, exist_ok=True)
    logo.mkdir(exist_ok=True)
    for tone, ink in (("on-dark", T["ink"]), ("on-light", T["bg"])):
        W, H, body = lockup(ink, T["accent"])
        (logo / f"misfits-logo-{tone}.svg").write_text(svg(W, H, body))
        _, width, cap, _ = glyph_paths(WORD)
        s = 200 / cap
        wm, wmw, wmh = wordmark_group(ink, T["accent"], s)
        p = 24
        (logo / f"misfits-wordmark-{tone}.svg").write_text(
            svg(wmw + 2 * p, 200 * 1.25 + 2 * p, f'<g transform="translate({p} {p + 200 * 0.12})">{wm}</g>'))
        (logo / f"misfits-symbol-{tone}.svg").write_text(svg(240, 240, f'<g transform="translate(20 20)">'
                                                                     f'{symbol_group(ink, T["accent"], 200)}</g>'))
    # assets as HTML pages (rendered by render.js): inline SVG logos + local fonts
    css = (f"@font-face{{font-family:ArchivoX;src:url(../../fonts/Archivo-ExpandedBlack.ttf)}}"
           f"@font-face{{font-family:ArchivoXS;src:url(../../fonts/Archivo-ExpandedSemiBold.ttf)}}"
           f"@font-face{{font-family:Inter;src:url(../../fonts/Inter-VF.ttf)}}"
           f"*{{margin:0;box-sizing:border-box}}body{{background:{T['bg']};color:{T['ink']};font-family:Inter;"
           f"-webkit-font-smoothing:antialiased}}"
           ".grain{position:absolute;inset:0;opacity:.07;background-image:url(\"data:image/svg+xml;utf8,"
           "<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence "
           "type='fractalNoise' baseFrequency='.9' numOctaves='2'/></filter><rect width='200' height='200' "
           "filter='url(%23n)'/></svg>\")}")
    tilt = lambda word, k: "".join(  # noqa: E731
        f'<span style="display:inline-block;color:{T["accent"]};transform:translateY(.06em) rotate({TILT_DEG}deg)">'
        f'{c}</span>' if i == k else c for i, c in enumerate(word))
    LW, LH, LB = lockup(T["ink"], T["accent"])
    lock_svg = lambda h: svg(LW, LH, LB).replace(f'width="{LW:.0f}" height="{LH:.0f}"',  # noqa: E731
                                                 f'height="{h}" width="{h * LW / LH:.0f}"')
    sym_svg = lambda px: (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="{px}" height="{px}">'  # noqa: E731
                          f'{symbol_group(T["ink"], T["accent"], 200)}</svg>')
    pages = {
        "ig-profile-1080": (1080, 1080, f'<div style="width:1080px;height:1080px;display:grid;place-items:center;'
                                        f'background:{T["bg"]}">{sym_svg(500)}</div>'),
        "ig-launch-post-1080x1350": (1080, 1350, f'''
<div style="position:relative;width:1080px;height:1350px;padding:120px 110px;display:flex;flex-direction:column;
justify-content:space-between;background:radial-gradient(120% 80% at 80% 10%, {T['glow']} 0%, {T['bg']} 60%)">
<div class="grain"></div>
<div style="font:22px ArchivoXS;letter-spacing:.3em;color:{T['muted']}">AI-POWERED CREATIVE STUDIO</div>
<div style="font:118px/0.98 ArchivoX;letter-spacing:-.01em">ADS THAT<br>DON&#8217;T {tilt("FIT", 1)}<br>IN.</div>
<div style="display:flex;justify-content:space-between;align-items:flex-end">
<div style="font:30px/1.4 Inter;font-weight:500;color:{T['ink']};opacity:.82;max-width:520px">Cinematic product ads
for brands that refuse to blend in.</div>{lock_svg(62)}</div></div>'''),
        "banner-1500x500": (1500, 500, f'''
<div style="position:relative;width:1500px;height:500px;padding:0 110px;display:flex;align-items:center;
justify-content:space-between;background:linear-gradient(100deg,{T['bg']} 55%,{T['glow']})">
<div class="grain"></div>{lock_svg(120)}
<div style="text-align:right"><div style="font:54px/1.05 ArchivoX">ADS THAT DON&#8217;T<br>{tilt("FIT", 1)} IN.</div>
<div style="margin-top:18px;font:22px Inter;font-weight:500;color:{T['muted']};white-space:nowrap">Cinematic AI ads &middot;
Product films &middot; Motion</div></div></div>'''),
        "web-hero-1920x1080": (1920, 1080, f'''
<div style="position:relative;width:1920px;height:1080px;padding:70px 120px;background:radial-gradient(90% 70% at 85% 15%,
{T['glow']} 0%,{T['bg']} 62%)"><div class="grain"></div>
<div style="display:flex;justify-content:space-between;align-items:center">{lock_svg(46)}
<div style="display:flex;gap:46px;font:20px Inter;font-weight:500;color:{T['muted']}"><span>Work</span>
<span>Services</span><span>Process</span><span style="color:{T['ink']}">Contact</span></div></div>
<div style="margin-top:150px;font:150px/0.95 ArchivoX">ADS THAT<br>DON&#8217;T {tilt("FIT", 1)} IN.</div>
<div style="margin-top:46px;font:30px/1.45 Inter;font-weight:500;opacity:.8;max-width:820px">Cinematic, AI-powered product
ads for brands that refuse to blend in. Concept to final cut, without the film crew.</div>
<div style="margin-top:54px;display:flex;gap:20px"><span style="background:{T['accent']};color:{T['on_accent']};font:22px ArchivoXS;
padding:24px 40px;border-radius:999px">BOOK A CALL</span><span style="border:2px solid #3a3a40;font:22px ArchivoXS;
padding:22px 40px;border-radius:999px">SEE THE WORK</span></div></div>'''),
    }
    # palette sheet: the three themes
    rows = []
    for key, th in THEMES.items():
        sw = "".join(f'<div style="flex:1;background:{th[c]};padding:26px;display:flex;flex-direction:column;'
                     f'justify-content:flex-end;color:{"#0B0B0D" if c in ("ink", "accent") else "#EEEBE4"};'
                     f'font:20px Inter;font-weight:600">{c.upper()}<br><span style="font-weight:400">{th[c]}</span></div>'
                     for c in ("bg", "panel", "ink", "muted", "accent"))
        rows.append(f'<div style="margin-bottom:34px"><div style="font:26px ArchivoXS;margin-bottom:14px">{th["name"]}'
                    f'</div><div style="display:flex;height:220px;border-radius:18px;overflow:hidden;'
                    f'border:1px solid #2a2a30">{sw}</div></div>')
    pages["palette-1600x1200"] = (1600, 1200, f'<div style="width:1600px;height:1200px;padding:80px 90px;'
                                              f'background:#0B0B0D">{"".join(rows)}</div>')
    soc = root / "social"
    soc.mkdir(exist_ok=True)
    jobs = []
    for name, (w, h, html) in pages.items():
        (soc / f"{name}.html").write_text(f"<!doctype html><meta charset=utf-8><style>{css}</style><body>{html}</body>")
        jobs.append({"html": str(soc / f"{name}.html"), "png": str(soc / f"{name}.png"), "w": w, "h": h})
    for tone in ("on-dark", "on-light"):
        for kind in ("logo", "wordmark", "symbol"):
            p = logo / f"misfits-{kind}-{tone}.svg"
            bg = T["bg"] if tone == "on-dark" else "#FFFFFF"
            s = p.read_text()
            import re
            w_, h_ = (float(v) for v in re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', s).groups())
            sc = 2000 / w_
            page = logo / f"_{kind}-{tone}.html"
            old_wh = 'width="%.0f" height="%.0f"' % (w_, h_)
            new_wh = 'width="2000" height="%.0f"' % (h_ * sc)
            page.write_text('<!doctype html><style>*{margin:0}body{background:transparent}</style><body>'
                            + s.replace(old_wh, new_wh) + '</body>')
            jobs.append({"html": str(page), "png": str(logo / f"misfits-{kind}-{tone}.png"), "w": 2000,
                         "h": int(round(h_ * sc)), "transparent": True})
    (HERE / "_render_jobs.json").write_text(json.dumps(jobs, indent=1))
    print(f"wrote {len(list(logo.glob('*.svg')))} SVGs and {len(pages)} pages; {len(jobs)} render jobs")


if __name__ == "__main__":
    main()
