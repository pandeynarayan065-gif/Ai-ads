# Spraymax — Combo Drop (Pack of 2 / Pack of 3)

**Concept:** One's good. Two's better. Three's the move. A counting story that lands on the best deal,
cut as quick clips on a 120 BPM beat in the visual language of Spraymax's own combo creatives.

## Offer (from the brand's creatives)
| Pack | Was | Now | Save | Per bottle |
|---|---|---|---|---|
| Pack of 2 | ₹899 | ₹799 | ₹100 | ₹399.50 ("Under ₹400 each") |
| Pack of 3 | ₹1,347 | ₹999 | ₹348 | ₹333 ("Just ₹333 each") |
Single bottle: ₹449 (site sale price). "Was" prices = 2× / 3× ₹449.

## Deliverables (`video/`, 1080×1920, 30 fps)
| File | Length | Clips |
|---|---|---|
| combo-15s.mp4 | 15 s | ONE'S GOOD → TWO'S BETTER → PACK OF 2 price → THREE'S THE MOVE → PACK OF 3 price → PICK YOUR PACK → end card |
| combo-pack2-6s.mp4 | 6 s | TWO'S BETTER → PACK OF 2 price → end card (Pack of 2) |
| combo-pack3-6s.mp4 | 6 s | THREE'S THE MOVE → PACK OF 3 price → end card (Pack of 3) |

## Notes
- Their combo creatives say "100% natural sea salt spray"; left out on purpose (formula contains preservatives).
- Soundtrack is a synthesized placeholder groove; swap in licensed music in the edit.
- The full ribbon (band + bow) appears only on the two pack-reveal clips (Pack of 2, Pack of 3); every other shot shows clean bottles. A band without the bow reads as a bar over the logo, so never use it alone. Bow source: the bow is cut from the brand's own combo creative (`brand/spraymax/assets/ribbon-bow.png`), the band is drawn to match its measured navy.
- Re-render: `python3 video/render_combo.py` (all) or `--only main|pack2|pack3`.

## AI B-roll cut (`video/combo-ai-broll-15s.mp4`)
Gemini clips (Drive folder) cut as 1–1.5 s full-screen B-roll between the graphics, with text, offer stickers,
light leak and frame-mark overlays. Only frame-checked windows are used (g2 2.0–3.5, g5 3.0–4.5, g7 2.3–3.8,
g6 1.8–3.3 s). Source clips are 720p, so B-roll is softer than the graphics. Turn on Meta's "AI info" label
when posting. Re-render: `python3 video/render_mix.py <clips_dir>`.

## "Beach hair, bottled." (`video/combo-beach-hair-19s.mp4`)
Desire first, offer second. Slow-motion B-roll (ffmpeg minterpolate) from frame-checked windows:
hair = g7 9.42–10.0 s @0.19×, sea = g2 2.0–3.5 s @0.57×, spray = g7 2.3–3.8 s @0.48×, splash = g6 1.8–3.3 s @0.48×.
0–3 "That beach-day hair?" · 3–5.5 "We bottled it." · 5.5–8.5 "Shake. Spray. Style." / "Done in under 10 seconds." ·
8.5–11.5 "Himalayan sea salt." / "Matte texture. Zero grease." · 11.5–16 offer cards (₹799 / ₹999, per-bottle, save, best value,
free shipping) · 16–19 end card. 0.35 s dissolves, ~90 BPM placeholder bed.
Re-render: `python3 video/render_beach.py <slowmo_dir>`.

## Real UGC ad, Hinglish (`video/combo-real-ugc-20s.mp4`)
Real phone footage (Drive, VID_2026…): hook "FLAT HAIR? Roz subah yahi scene?" (r5 1.0 s) → "Bas spray karo…" (r5 33.0 s)
→ "…aur haathon se scrunch." (r5 52.2 s) → stacked before/after, same session (r5 12.5 s vs 78.3 s) "Same din. Same banda."
→ close-up result (r6 0–2.5 s) "Volume. Texture. Chipchipa bilkul nahi." → bottle in hand (r4 2.0 s, mirrored front-camera
shot flipped so the label reads) → parking lot (r2 2.0 s) "College ready. Office ready." → "Combo mein aur sasta." offer → end card.
Re-render: `python3 video/render_real.py <real_clips_dir>`.

## Slower graphics-only cut (`video/combo-slow-20s.mp4`)
Same seven graphic clips as `combo-15s.mp4` with longer holds (2.5–3.5 s each, 20.5 s) and no cut punch.
Re-render: `python3 video/render_combo.py --only slow`.
