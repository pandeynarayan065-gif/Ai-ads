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
