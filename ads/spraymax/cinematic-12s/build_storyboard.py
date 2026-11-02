#!/usr/bin/env python3
"""Spraymax 12 s cinematic film: build the 3D storyboard PDF, the shot cards and the Seedance reference images.

Inputs:
  frames/F1.png ... F9.png       1080x1920 Blender renders (video/blender/film_shots.py)
  prompt-seedance-12s.md         the one Seedance 2.5 prompt (lint: --kind seedance --faceless)
  ../seedance/product-sheet.jpg  real photos of the bottle (Image 1)
Outputs:
  frames/F*.jpg                  1080x1920 JPEGs (storyboard frames)
  refs/01-product-sheet.jpg, refs/02-layout-F1.jpg ...   Seedance references, <= 720x1280, yuvj420p JPEG
  shots/<nn>-<slug>.md           one shot card per shot
  storyboard.html / storyboard.pdf

  python3 ads/spraymax/cinematic-12s/build_storyboard.py [--frames <dir with F*.png>]
"""
import html
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SHEET = ROOT / "ads/spraymax/seedance/product-sheet.jpg"
PROMPT = HERE / "prompt-seedance-12s.md"

# Seedance 2.5 on kie, credits per second, no video input (kie.ai/seedance-2-5, checked 2026-11-02). 1 cr = $0.005.
RATE = {"480p": 28, "720p": 63, "1080p": 158}
BALANCE = 2037
BUDGET_CR = 1400                       # the user's ~$7

SHOTS = [
    dict(id="F1", slug="collar", t=(0, 2), title="The collar",
         see="Extreme macro of the pump head and the ribbed collar, cap off. A narrow hard white light sweeps right to "
             "left across the ribs and lights them one by one; the left side stays in shadow.",
         camera="100 mm macro, very slow push-in", light="One hard cold-white strip from the right, grazing; faint "
                "indigo rim", moves="The light sweeps across the ribs", sound="Sub-bass swell, cold air hiss",
         job="Hook: a mystery close-up before the bottle is revealed"),
    dict(id="F2", slug="blade", t=(2, 3), title="The silhouette",
         see="Low three-quarter view of the capped bottle, almost in silhouette. One thin silver highlight runs "
             "down its right edge.",
         camera="85 mm, low angle, creeps upward toward the collar", light="One hard silver strip from behind on the "
                "right; faint cool bounce at the base", moves="The highlight slides along the edge as the camera "
                "rises", sound="Deep soft whoosh", job="Reveal the shape"),
    dict(id="F3", slug="salt", t=(3, 4), title="Himalayan salt",
         see="Extreme macro of raw pale-pink Himalayan salt with beads of sea water, glowing pink from behind. "
             "The only warm colour in the film.",
         camera="100 mm macro, holds nearly still (micro drift)", light="Warm back light through the salt; small "
                "cold key catching the beads", moves="A bead rolls down a facet", sound="One soft water drip",
         job="Ingredient: Himalayan sea salt (from the label)"),
    dict(id="F4", slug="mist", t=(4, 6), title="The mist",
         see="Side macro of the pump head, cap off. A fine cone of mist bursts sideways out of the nozzle, backlit "
             "ice blue, tight at the nozzle and blooming wide before it thins into the black. Mist, never liquid.",
         camera="100 mm macro, locked off, slow motion", light="Ice-blue back light through the mist; soft cold key on "
                "the pump", moves="The mist bursts and blooms", sound="Sharp pump hiss, airy trail",
         job="Product action: what it does"),
    dict(id="F5", slug="ocean", t=(6, 7), title="The sea",
         see="Low over a night ocean. A swell rises toward the lens under a cold moon; a glittering path on the "
             "water, fine spray lifting off the crest.",
         camera="50 mm just above the water, holds still", light="Moonlight from straight ahead", moves="The swell "
                "rises and folds", sound="Deep wave roar, spray hiss (added in post)",
         job="Origin: sea salt"),
    dict(id="F6", slug="bloom", t=(7, 8), title="Indigo bloom",
         see="The bottle in a black void, a little left of centre, label to camera, with a broad soft indigo wash "
             "blooming behind it from no visible source.",
         camera="85 mm at label height, slow push-in", light="Soft silver light from high right; indigo rim on the "
                "left", moves="The indigo wash rises", sound="Rising low drone", job="Brand colour moment"),
    dict(id="F7", slug="cloud", t=(8, 9), title="Mist in the beam",
         see="A soft cloud of fine mist hanging in a single hard beam of cold light, droplets glinting as it spreads "
             "up and to the right.",
         camera="85 mm, locked off, slow motion", light="One hard ice-blue beam from behind on the right",
         moves="The cloud spreads and drifts", sound="Airy hiss fading out", job="Texture: lightweight, airy finish"),
    dict(id="F8", slug="wordmark", t=(9, 10), title="The wordmark",
         see="Macro across the front label: the indigo Spraymax wordmark running down the bottle in shallow focus, "
             "cold light grazing the print, the far side falling into shadow.",
         camera="100 mm macro at an angle, holds still", light="Cold strip grazing from the right", moves="Nothing; a "
                "still beat before the end", sound="Low hum", job="Name the brand"),
    dict(id="F9", slug="packshot", t=(10, 12), title="Packshot + end card",
         see="Wide: the capped bottle left of centre on a deep indigo matte surface, a long hard shadow raking right, "
             "the top half left dark for the end card (added in post: logo, BORN IN HIMACHAL, spraymax.in).",
         camera="85 mm just above the surface, very slow push-in", light="Hard silver spot from low left; indigo rim",
         moves="Nothing but the camera", sound="One soft low boom, then silence", job="Pack and end card"),
]


def shot_prompts():
    """The prompt line for each shot, keyed by its start second."""
    text = PROMPT.read_text()
    out = {}
    for m in re.finditer(r"^(\d+)-(\d+) seconds: (.+)$", text, re.M):
        out[int(m.group(1))] = m.group(3)
    return text, out


def prep_images(frames):
    (HERE / "frames").mkdir(exist_ok=True)
    (HERE / "refs").mkdir(exist_ok=True)
    for s in SHOTS:
        src = Path(frames) / f"{s['id']}.png"
        im = Image.open(src).convert("RGB")
        assert im.size == (1080, 1920), (src, im.size)
        im.save(HERE / "frames" / f"{s['id']}.jpg", quality=90, subsampling=0)
    # Seedance refs: no bigger than the output (720x1280), standard 4:2:0 JPEG
    sheet = Image.open(SHEET).convert("RGB")
    sheet.thumbnail((1024, 1024))                     # <= the 720x1280 output in pixel count
    sheet.save(HERE / "refs/01-product-sheet.jpg", quality=92, subsampling=2)
    for i, s in enumerate(SHOTS, 2):
        im = Image.open(HERE / "frames" / f"{s['id']}.jpg").resize((720, 1280), Image.LANCZOS)
        im.save(HERE / "refs" / f"{i:02d}-layout-{s['id']}.jpg", quality=90, subsampling=2)


def write_cards(lines):
    d = HERE / "shots"
    d.mkdir(exist_ok=True)
    for n, s in enumerate(SHOTS, 1):
        a, b = s["t"]
        card = f"""# Shot {n:02d}: {s['slug']}

Part of one Seedance 2.5 multi-shot generation (`prompt-seedance-12s.md`). Rules: `reference/ai-video-playbook.md`.

## Plan

- **Brand / campaign:** Spraymax / cinematic-12s
- **Job in the edit:** {s['job']}
- **On screen:** {b - a} s, {a}–{b} s
- **The shot:** {s['see']}
- **Real-crew test:** a tabletop / macro studio (motion-control slider, strip lights, a hidden pump rig){' or a water housing at night' if s['id'] == 'F5' else ''}.
- **Product:** {'not in shot' if s['id'] in ('F3', 'F5', 'F7') else 'the real bottle; label must match the product sheet (lock in post if it drifts)'}
- **People:** none
- **Camera (one move):** {s['camera']}
- **Light:** {s['light']}
- **What moves (one action):** {s['moves']}
- **Sound (post):** {s['sound']}

## Pipeline

- **Layout frame:** `frames/{s['id']}.jpg` (Blender, `video/blender/film_shots.py --shot {s['id']}`), sent as Image {n + 1}
- **Product truth:** Image 1, `refs/01-product-sheet.jpg` (real photos)
- **Motion:** Seedance 2.5, reference-to-video, one 12 s generation for all nine shots

## Prompt line

> {lines.get(a, '')}

## Pass criteria

1. One camera move, no morph into the next shot (hard cut at {b} s)
2. {'Mist only: airborne droplets, no stream, no drips' if s['id'] in ('F4', 'F7') else 'Bottle proportions and label match the product sheet' if s['id'] not in ('F3', 'F5') else 'Reads as real footage, not 3D'}
3. No visible light fixture, no mirror floor, no text other than the label

## Takes

| Take | Model / mode | Cost | Scorecard (1–9) | Total | Usable range | Verdict | Failures |
|---|---|---|---|---|---|---|---|
"""
        (d / f"{n:02d}-{s['slug']}.md").write_text(card)


CSS = """
@page { size: 297mm 167mm; margin: 0; }
:root { --ink: #e9ecf6; --dim: #9aa3bf; --faint: #5b6382; --bg: #07070d; --panel: #0e0f1a; --ice: #bfe4ff;
        --indigo: #4b3cff; --salt: #f29a86; }
* { box-sizing: border-box; }
html, body { margin: 0; background: var(--bg); color: var(--ink);
  font-family: Inter, "Liberation Sans", sans-serif; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.page { width: 297mm; height: 167mm; padding: 11mm 13mm; position: relative; overflow: hidden; page-break-after: always; }
.eyebrow { font-size: 7.5pt; letter-spacing: .22em; text-transform: uppercase; color: var(--dim); }
h1 { font-family: "Instrument Serif", "Liberation Serif", serif; font-weight: 400; font-size: 38pt; line-height: 1;
     margin: 3mm 0 2mm; letter-spacing: -.01em; }
h2 { font-family: "Instrument Serif", "Liberation Serif", serif; font-weight: 400; font-size: 27pt; margin: 1mm 0 3mm; line-height: 1.02; }
p, li, td { font-size: 9pt; line-height: 1.45; }
.dim { color: var(--dim); } .ice { color: var(--ice); }
.strip { display: flex; gap: 2.2mm; margin-top: 6mm; }
.strip figure { margin: 0; flex: 1; }
.strip img { width: 100%; aspect-ratio: 9/16; object-fit: cover; display: block; border-radius: 1.2mm; }
.strip figcaption { font-size: 6.5pt; color: var(--dim); margin-top: 1.2mm; letter-spacing: .04em; }
.timeline { display: flex; height: 3.2mm; margin-top: 3mm; border-radius: 1mm; overflow: hidden; }
.timeline div { border-right: 1px solid var(--bg); background: #22254a; }
.timeline div.warm { background: #8a4a44; }
.shot { display: grid; grid-template-columns: 81mm 1fr; gap: 10mm; height: 100%; }
.shot img.frame { height: 144mm; width: 81mm; object-fit: cover; border-radius: 1.5mm; display: block; }
.meta { display: grid; grid-template-columns: 24mm 1fr; row-gap: 1.6mm; column-gap: 4mm; margin: 3mm 0 4mm; }
.meta div:nth-child(odd) { font-size: 7pt; letter-spacing: .16em; text-transform: uppercase; color: var(--faint); padding-top: .6mm; }
.meta div:nth-child(even) { font-size: 9pt; }
.promptline { background: var(--panel); border-left: 2px solid var(--indigo); padding: 3mm 4mm; font-size: 8pt;
  line-height: 1.5; color: #c9cee2; border-radius: 0 1mm 1mm 0; }
.tc { font-variant-numeric: tabular-nums; color: var(--ice); }
.num { position: absolute; right: 13mm; top: 11mm; font-size: 7.5pt; color: var(--faint); letter-spacing: .2em; }
table { border-collapse: collapse; width: 100%; }
td, th { text-align: left; padding: 2.2mm 3mm; border-bottom: 1px solid #1d2036; vertical-align: top; }
th { font-size: 7pt; letter-spacing: .16em; text-transform: uppercase; color: var(--faint); font-weight: 600; }
tr.rec td { background: #101436; }
.tag { display: inline-block; font-size: 6.5pt; letter-spacing: .14em; text-transform: uppercase; padding: .6mm 1.8mm;
  border-radius: 1mm; background: var(--indigo); color: white; margin-left: 2mm; vertical-align: middle; }
.refs { display: flex; gap: 1.6mm; align-items: flex-end; margin: 2mm 0 4mm; }
.refs img { height: 30mm; border-radius: 1mm; display: block; }
.refs .sheet { height: 30mm; }
.refs figcaption { font-size: 6pt; color: var(--dim); margin-top: .8mm; }
.refs figure { margin: 0; }
.fullprompt { columns: 2; column-gap: 8mm; font-size: 7pt; line-height: 1.42; color: #aeb4cc; white-space: pre-wrap; }
.cols { display: grid; grid-template-columns: 1fr 1fr; gap: 9mm; }
"""


def esc(s):
    return html.escape(s, quote=True)


def build_html(full, lines):
    total = 12
    cover_strip = "".join(
        f'<figure><img src="frames/{s["id"]}.jpg"><figcaption><span class="tc">0:{s["t"][0]:02d}</span> '
        f'&nbsp;{esc(s["title"])}</figcaption></figure>' for s in SHOTS)
    tl = "".join(f'<div class="{"warm" if s["id"] == "F3" else ""}" style="flex:{s["t"][1] - s["t"][0]}"></div>'
                 for s in SHOTS)
    pages = [f"""
<section class="page">
  <div class="eyebrow">Spraymax · cinematic film · storyboard v1 · 2 Nov 2026</div>
  <h1>Twelve seconds of cold light.</h1>
  <p class="dim" style="max-width:190mm">Nine hard-cut shots in black, ice blue and deep indigo, with the pink Himalayan
  salt the only warm note. The frames below are 3D renders of each shot's framing and light, with the real
  bottle and label, built to show what the film will look like. The film itself is one Seedance 2.5
  generation, vertical 9:16, finished at 1080&times;1920.</p>
  <div class="strip">{cover_strip}</div>
  <div class="timeline">{tl}</div>
  <div class="dim" style="font-size:6.5pt;margin-top:1.2mm;display:flex;justify-content:space-between">
    <span>0 s</span><span>6 s</span><span>12 s</span></div>
</section>"""]
    for n, s in enumerate(SHOTS, 1):
        a, b = s["t"]
        pages.append(f"""
<section class="page"><div class="num">{n:02d} / 09</div>
  <div class="shot">
    <img class="frame" src="frames/{s['id']}.jpg">
    <div>
      <div class="eyebrow">Shot {n:02d} · <span class="tc">0:{a:02d}–0:{b:02d}</span> · {b - a} s</div>
      <h2>{esc(s['title'])}</h2>
      <p style="font-size:10.5pt;line-height:1.5;max-width:150mm">{esc(s['see'])}</p>
      <div class="meta">
        <div>Camera</div><div>{esc(s['camera'])}</div>
        <div>Light</div><div>{esc(s['light'])}</div>
        <div>Moves</div><div>{esc(s['moves'])}</div>
        <div>Sound</div><div>{esc(s['sound'])} <span class="dim">(added in the edit)</span></div>
        <div>Job</div><div>{esc(s['job'])}</div>
      </div>
      <div class="eyebrow" style="margin-bottom:1.5mm">This shot's line in the Seedance prompt</div>
      <div class="promptline">{a}-{b} seconds: {esc(lines.get(a, ''))}</div>
    </div>
  </div>
</section>""")
    refs = '<figure><img class="sheet" src="refs/01-product-sheet.jpg"><figcaption>Image 1 · real bottle</figcaption></figure>'
    refs += "".join(f'<figure><img src="refs/{i:02d}-layout-{s["id"]}.jpg"><figcaption>Image {i}</figcaption></figure>'
                    for i, s in enumerate(SHOTS, 2))
    pages.append(f"""
<section class="page">
  <div class="eyebrow">How it's made</div>
  <h2>One Seedance 2.5 generation, ten reference images.</h2>
  <p class="dim" style="max-width:240mm;margin:0">Image 1 is a sheet of real photos of the bottle (front, pump side,
  nozzle, flat label): the product truth for every shot. Images 2–10 are the 3D frames in this PDF, one per shot,
  used only for framing, angle and light. Reference images add no cost on kie. Sound comes off; SFX and music go
  on in the edit, with the end card. Prompt: <span class="ice">prompt-seedance-12s.md</span>, linted PASS.</p>
  <div class="refs">{refs}</div>
  <div class="meta" style="grid-template-columns:30mm 1fr;max-width:200mm">
    <div>Model</div><div>Seedance 2.5 on kie.ai, reference-to-video (bytedance/seedance-2-5)</div>
    <div>Output</div><div>9:16 vertical, 12 s, audio off; finished at 1080&times;1920</div>
    <div>Checks</div><div>Label against the real bottle, mist never liquid, no fixtures, mirror floors, hands or
      faces, hard cuts on the beat</div>
  </div>
</section>
<section class="page">
  <div class="eyebrow">The exact prompt (sent as is after your approval)</div>
  <div class="fullprompt" style="margin-top:4mm">{esc(full)}</div>
</section>""")
    c = {r: RATE[r] * total for r in RATE}
    pages.append(f"""
<section class="page">
  <div class="eyebrow">Budget and the one decision</div>
  <h2>Native 1080p doesn't fit in $7. 720p does, with room to fix a shot.</h2>
  <table>
    <tr><th>Option</th><th>What you get</th><th>Credits</th><th>Cost</th><th>Retakes left</th></tr>
    <tr class="rec"><td><b>A · 720p</b><span class="tag">recommended</span></td>
      <td>Seedance 2.5 at 720p, 12 s, upscaled to 1080&times;1920 in the finishing pass (sharpen, grain, grade).
      If one shot misses, regenerate just that shot as a 4 s clip (252 cr) and cut it in.</td>
      <td>{c['720p']}</td><td>${c['720p'] * 0.005:.2f}</td><td>2 single-shot fixes inside $7 ({c['720p'] + 2 * 4 * RATE['720p']} cr, ${(c['720p'] + 2 * 4 * RATE['720p']) * 0.005:.2f})</td></tr>
    <tr><td><b>B · native 1080p</b></td>
      <td>Seedance 2.5 at 1080p, 12 s. Sharpest result, but one take only: if a shot fails there's no budget to fix it.</td>
      <td>{c['1080p']}</td><td>${c['1080p'] * 0.005:.2f}</td><td>none ({BALANCE - c['1080p']} cr left)</td></tr>
    <tr><td><b>C · draft, then 1080p</b></td>
      <td>A 480p draft to check the real motion ({c['480p']} cr), then the 1080p final from the same draft.
      Kie doesn't list the final's price; at the 1080p rate it's ~{c['480p'] + c['1080p']} cr.</td>
      <td>~{c['480p'] + c['1080p']}</td><td>~${(c['480p'] + c['1080p']) * 0.005:.2f}</td><td>more than the balance ({BALANCE} cr)</td></tr>
  </table>
  <div class="cols" style="margin-top:5mm">
    <div><p><b>Prices</b> <span class="dim">(kie.ai/seedance-2-5, checked today; 1 credit = $0.005):</span>
      480p 28 cr/s · 720p 63 cr/s · 1080p 158 cr/s. Balance: {BALANCE} credits. Your cap: ~{BUDGET_CR} credits ($7).</p>
      <p class="dim">Nothing has been spent. The prompt is sent only after you approve it.</p></div>
    <div><p><b>To go ahead, reply with A or B.</b> I'll send that exact prompt with these ten images, check every
      shot (label against the real bottle, mist never liquid, no fixtures or mirror floors), fix or regenerate what
      fails, then grade, add sound and the end card, and deliver 1080&times;1920.</p></div>
  </div>
</section>""")
    fonts = ('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Instrument+Serif'
             '&display=swap" rel="stylesheet">')
    return f'<!doctype html><html><head><meta charset="utf-8"><title>Spraymax storyboard</title>{fonts}<style>{CSS}</style></head><body>{"".join(pages)}</body></html>'


def main():
    frames = sys.argv[sys.argv.index("--frames") + 1] if "--frames" in sys.argv else HERE / "frames"
    prep_images(frames)
    full, lines = shot_prompts()
    assert sorted(lines) == [s["t"][0] for s in SHOTS], f"prompt shots {sorted(lines)} don't match the storyboard"
    write_cards(lines)
    page = HERE / "storyboard.html"
    page.write_text(build_html(full, lines))
    js = (f"const {{chromium}}=require('playwright');(async()=>{{const b=await chromium.launch();"
          f"const p=await b.newPage();await p.goto('file://{page}',{{waitUntil:'networkidle'}});"
          f"await p.evaluate(()=>document.fonts.ready);"
          f"await p.pdf({{path:'{HERE / 'storyboard.pdf'}',width:'297mm',height:'167mm',printBackground:true}});"
          f"await b.close();}})();")
    subprocess.run(["node", "-e", js], check=True)
    print("wrote", HERE / "storyboard.pdf")


if __name__ == "__main__":
    main()
