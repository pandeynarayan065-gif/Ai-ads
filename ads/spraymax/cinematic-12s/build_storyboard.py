#!/usr/bin/env python3
"""Spraymax 12 s cinematic film: build the storyboard PDF, the shot cards and the Seedance reference images.

v2 (2026-11-03), after the partners' feedback on v1:
- "too detailed": the PDF is now one full frame per page and one line, on phone-shaped pages;
- "purple? should be blue": blue palette;
- "the real bottle isn't like this": milky semi-matte plastic, matched to Narayan's video;
- variety: splash, smoke, first-person use (spray onto the palm), macro beads, five-bottle lineup.

Inputs:
  <frames dir>/F*.png            1080x1920 Blender renders (video/blender/film_shots.py); F12 is the POV preview
                                 made from Narayan's video frame + the 3D mist (make_pov.py)
  prompt-seedance-12s.md         the one Seedance 2.5 prompt (lint: --kind seedance --faceless)
  product-sheet-v2.jpg           real photos of the bottle + the flat label (Image 1)
Outputs:
  frames/F*.jpg                  1080x1920 JPEGs (F9 with the end card)
  refs/01-product-sheet.jpg, refs/02-layout-F1.jpg ...   Seedance references (Images 1..16), <= 720x1280 JPEG
  shots/<nn>-<slug>.md           one shot card per shot
  storyboard.html / storyboard.pdf

  python3 ads/spraymax/cinematic-12s/build_storyboard.py --frames <dir with F*.png>
"""
import html
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
SHEET = HERE / "product-sheet-v2.jpg"            # real photos: Narayan's low-light front, pump side, nozzle; flat label
PROMPT = HERE / "prompt-seedance-12s.md"

# Seedance 2.5 on kie, credits per second, no video input (kie.ai/seedance-2-5, checked 2026-11-02). 1 cr = $0.005.
RATE = {"480p": 28, "720p": 63, "1080p": 158}
BALANCE = 2037
LEN = 12

# v3 (2026-11-03): the Higgsfield perfume film's grammar, shot for shot, in Spraymax's world (Narayan: "there's no
# shots and motions like the ones in the blue perfume shot"). 15 hard cuts in 12 s; t in seconds.
SHOTS = [
    dict(id="F1", slug="collar-sweep", t=(0.0, 1.2), title="Light on the ribs", kind="Macro · push-in",
         line="A hard white light sweeps round the ribbed collar, lighting it rib by rib."),
    dict(id="F16", slug="salt-mist", t=(1.2, 1.8), title="Salt in sea mist", kind="Ingredient · drift",
         line="Two raw pink salt chunks meet as a fine sea mist drifts across them."),
    dict(id="F17", slug="aloe", t=(1.8, 2.4), title="Aloe vera", kind="Ingredient · drift",
         line="An aloe rosette from above, its leaf edges catching cold light."),
    dict(id="F18", slug="rise", t=(2.4, 3.0), title="Out of the aloe", kind="Product reveal · push-in",
         line="The pump and ribbed collar rise out of the heart of the aloe."),
    dict(id="F19", slug="smoke", t=(3.0, 3.7), title="Cold smoke", kind="Smoke · drift",
         line="A slow curl of silvery-blue smoke; the camera drifts through it."),
    dict(id="F6", slug="bloom", t=(3.7, 4.8), title="Blue bloom", kind="Hero · push-in",
         line="The bottle in the dark as a deep blue glow rises behind it."),
    dict(id="F20", slug="wave-band", t=(4.8, 5.6), title="The wave band", kind="Macro · push-in",
         line="Macro on the ocean-wave band at the base of the label."),
    dict(id="F21", slug="drop", t=(5.6, 6.2), title="A drop runs", kind="Macro · water",
         line="One bead of sea water runs down the bottle, back-lit ice blue."),
    dict(id="F22", slug="rack", t=(6.2, 6.8), title="The rack", kind="Abstract · fast track",
         line="The camera whips across the ribs: streaks of black and blue-white."),
    dict(id="F2", slug="silhouette", t=(6.8, 7.4), title="Silhouette", kind="Product · rise",
         line="The bottle in near-silhouette, one silver line down its edge."),
    dict(id="F23", slug="lineup", t=(7.4, 8.1), title="Five bottles", kind="Multi-pack · drift",
         line="Five bottles shoulder to shoulder, cold light burning through the gaps."),
    dict(id="F12", slug="pov-spray", t=(8.1, 8.8), title="In your hand", kind="POV · use",
         line="First person: one press, and a fine mist drifts onto your open palm.",
         note="Preview: your test video plus a 3D mist. In the film, the other hand's open palm catches the mist"),
    dict(id="F10", slug="splash", t=(8.8, 9.4), title="The splash", kind="Elemental · slow motion",
         line="Dark sea water erupts in a crown round the bottle."),
    dict(id="F4", slug="mist", t=(9.4, 10.0), title="The mist", kind="Macro · slow motion",
         line="The mist bursts out of the side nozzle, backlit ice blue."),
    dict(id="F9", slug="packshot", t=(10.0, 12.0), title="Packshot", kind="End card",
         line="The bottle on deep blue, a long shadow, the logo and BORN IN HIMACHAL."),
]


def shot_prompts():
    """The prompt line for each shot, keyed by its start second."""
    text = PROMPT.read_text()
    return {round(int(m.group(1)) * 60 + float(m.group(2)), 1): m.group(3)
            for m in re.finditer(r"^\[(\d+):(\d+\.\d)\] (.+)$", text, re.M)}


def tc(x):
    return f"0:{x:04.1f}"


def prep_images(frames):
    for d in ("frames", "refs"):
        shutil.rmtree(HERE / d, ignore_errors=True)
        (HERE / d).mkdir()
    for s in SHOTS:
        src = Path(frames) / f"{s['id']}.png"
        im = Image.open(src).convert("RGB")
        assert im.size == (1080, 1920), (src, im.size)
        if s["id"] == "F9":                                    # show the end card the edit will add
            import build_animatic
            im = build_animatic.end_card(im, 51, 51)
        im.save(HERE / "frames" / f"{s['id']}.jpg", quality=90, subsampling=0)
    # Seedance refs: no bigger than the output (720x1280) in pixel count, standard 4:2:0 JPEG
    sheet = Image.open(SHEET).convert("RGB")
    sheet.thumbnail((1024, 1024))
    sheet.save(HERE / "refs/01-product-sheet.jpg", quality=92, subsampling=2)
    for i, s in enumerate(SHOTS, 2):
        im = Image.open(HERE / "frames" / f"{s['id']}.jpg").resize((720, 1280), Image.LANCZOS)
        im.save(HERE / "refs" / f"{i:02d}-layout-{s['id']}.jpg", quality=90, subsampling=2)


def write_cards(lines):
    d = HERE / "shots"
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir()
    for n, s in enumerate(SHOTS, 1):
        a, b = s["t"]
        card = f"""# Shot {n:02d}: {s['slug']} ({s['kind']})

Part of one Seedance 2.5 multi-shot generation (`prompt-seedance-12s.md`). Rules: `reference/ai-video-playbook.md`.

- **On screen:** {b - a:.1f} s, {a:.1f}–{b:.1f} s
- **The shot:** {s['line']}
- **Layout frame:** `frames/{s['id']}.jpg`, sent as Image {n + 1}{' (' + s['note'] + ')' if s.get('note') else ''}
- **Product truth:** Image 1, `refs/01-product-sheet.jpg` (real photos)
- **People:** {'first-person hands only, no face' if s['id'] == 'F12' else 'none'}

## Prompt line

> {lines.get(a, '')}

## Pass criteria

1. One camera move at most; a hard cut at {b:.1f} s, no morph into the next shot
2. {'Mist only: airborne droplets, no stream, no drips' if s['id'] in ('F4', 'F12') else 'Reads as real footage, not 3D' if s['id'] in ('F16', 'F17', 'F19') else 'Bottle proportions, milky matte plastic and label match the real bottle'}
3. Blue light, never purple; no light fixtures, no glossy studio floor, no text other than the label

## Takes

| Take | Cost | Usable range | Verdict | Failures |
|---|---|---|---|---|
"""
        (d / f"{n:02d}-{s['slug']}.md").write_text(card)


CSS = """
@page { size: 108mm 216mm; margin: 0; }
:root { --ink: #eef2fa; --dim: #9aa6c0; --faint: #5d6a88; --bg: #04060c; --blue: #2f6bff; }
* { box-sizing: border-box; }
html, body { margin: 0; background: var(--bg); color: var(--ink);
  font-family: Inter, "Liberation Sans", sans-serif; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.page { width: 108mm; height: 216mm; position: relative; overflow: hidden; page-break-after: always; background: var(--bg); }
.frame { width: 108mm; height: 192mm; object-fit: cover; display: block; }
.cap { position: absolute; left: 0; right: 0; bottom: 0; height: 24mm; padding: 3.2mm 5mm 0; }
.row { display: flex; align-items: baseline; gap: 2.5mm; }
.num { font-size: 7pt; letter-spacing: .18em; color: var(--faint); }
.tc { font-size: 7pt; letter-spacing: .08em; color: var(--blue); font-variant-numeric: tabular-nums; }
.kind { font-size: 6.5pt; letter-spacing: .16em; text-transform: uppercase; color: var(--dim); margin-left: auto; }
.title { font-family: "Instrument Serif", "Liberation Serif", serif; font-size: 17pt; line-height: 1.05; margin: 1mm 0 .8mm; }
.line { font-size: 8.4pt; line-height: 1.35; color: #c9d1e4; }
.note { font-size: 6.4pt; color: var(--faint); margin-top: .8mm; }
.cover { padding: 9mm 6mm 6mm; display: flex; flex-direction: column; justify-content: center; }
.cover h1 { font-family: "Instrument Serif", "Liberation Serif", serif; font-weight: 400; font-size: 25pt; line-height: 1;
  margin: 2mm 0 2mm; }
.eyebrow { font-size: 6.5pt; letter-spacing: .2em; text-transform: uppercase; color: var(--dim); }
.grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 1.4mm; margin-top: 4mm; }
.grid figure { margin: 0; }
.grid img { width: 100%; aspect-ratio: 9/16; object-fit: cover; display: block; border-radius: .8mm; }
.grid figcaption { font-size: 5.2pt; color: var(--dim); margin-top: .8mm; line-height: 1.25; }
.grid figcaption b { color: var(--blue); font-weight: 600; }
.lead { font-size: 8.4pt; line-height: 1.45; color: #c9d1e4; }
.opt { border: 1px solid #1c2640; border-radius: 1.5mm; padding: 4mm; margin-top: 4mm; }
.opt.rec { border-color: var(--blue); background: #071233; }
.opt h3 { margin: 0 0 1.5mm; font-size: 11pt; font-weight: 600; }
.opt .price { float: right; color: var(--blue); font-weight: 600; }
.tag { font-size: 6pt; letter-spacing: .14em; text-transform: uppercase; color: var(--blue); }
"""


def esc(s):
    return html.escape(s, quote=True)


def build_html():
    grid = "".join(f'<figure><img src="frames/{s["id"]}.jpg"><figcaption><b>{tc(s["t"][0])}</b> {esc(s["title"])}'
                   f'</figcaption></figure>' for s in SHOTS)
    pages = [f"""
<section class="page cover">
  <div class="eyebrow">Spraymax · 12 s film · storyboard v3</div>
  <h1>Fifteen cuts.<br>Cold blue light.</h1>
  <p class="lead">Built on the perfume film you sent, shot for shot, in Spraymax's world: the light sweep, the
  ingredient macros, the product rising out of an ingredient, the fast rack, light through the gaps, the packshot.
  Watch the 12 s 3D animatic sent with this PDF to see the camera moves.</p>
  <div class="grid">{grid}</div>
  <p class="lead" style="margin-top:4mm;color:var(--dim)">3D previews with the real bottle and label. The film is made
  with Seedance 2.5 from your real bottle photos, so it will look like real footage. 9:16, 1080&times;1920, 12 s.</p>
</section>"""]
    for n, s in enumerate(SHOTS, 1):
        a, b = s["t"]
        note = f'<div class="note">{esc(s["note"])}</div>' if s.get("note") else ""
        pages.append(f"""
<section class="page">
  <img class="frame" src="frames/{s['id']}.jpg">
  <div class="cap">
    <div class="row"><span class="num">{n:02d}/{len(SHOTS)}</span><span class="tc">{tc(a)}–{tc(b)}</span>
      <span class="kind">{esc(s['kind'])}</span></div>
    <div class="title">{esc(s['title'])}</div>
    <div class="line">{esc(s['line'])}</div>{note}
  </div>
</section>""")
    c720, c1080 = RATE["720p"] * LEN, RATE["1080p"] * LEN
    fix = 4 * RATE["720p"]
    pages.append(f"""
<section class="page cover">
  <div class="eyebrow">To start</div>
  <h1>Pick A or B.</h1>
  <div class="opt rec"><span class="tag">Recommended</span>
    <h3>A · 720p, finished at 1080p <span class="price">${c720 * 0.005:.2f}</span></h3>
    <div class="lead">One Seedance 2.5 generation at 720p, upscaled to 1080&times;1920 in the finish. If a shot misses,
    I remake just that shot (${fix * 0.005:.2f} each). Two fixes still stay under $7.</div></div>
  <div class="opt">
    <h3>B · native 1080p <span class="price">${c1080 * 0.005:.2f}</span></h3>
    <div class="lead">Sharpest. Over the $7 budget, and one take only: no money left to fix a shot.</div></div>
  <p class="lead" style="margin-top:6mm;color:var(--dim)">Nothing has been spent yet. After your pick I send the
  prompt, check every shot against your real bottle, fix what fails, then grade, add sound and the end card.</p>
</section>""")
    fonts = ('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Instrument+Serif'
             '&display=swap" rel="stylesheet">')
    return (f'<!doctype html><html><head><meta charset="utf-8"><title>Spraymax storyboard v3</title>{fonts}'
            f'<style>{CSS}</style></head><body>{"".join(pages)}</body></html>')


def main():
    frames = sys.argv[sys.argv.index("--frames") + 1]
    prep_images(frames)
    lines = shot_prompts()
    assert sorted(lines) == [s["t"][0] for s in SHOTS], f"prompt shots {sorted(lines)} don't match the storyboard"
    write_cards(lines)
    page = HERE / "storyboard.html"
    page.write_text(build_html())
    js = (f"const {{chromium}}=require('playwright');(async()=>{{const b=await chromium.launch();"
          f"const p=await b.newPage();await p.goto('file://{page}',{{waitUntil:'networkidle'}});"
          f"await p.evaluate(()=>document.fonts.ready);"
          f"await p.pdf({{path:'{HERE / 'storyboard.pdf'}',width:'108mm',height:'216mm',printBackground:true}});"
          f"await b.close();}})();")
    subprocess.run(["node", "-e", js], check=True)
    print("wrote", HERE / "storyboard.pdf")


if __name__ == "__main__":
    main()
