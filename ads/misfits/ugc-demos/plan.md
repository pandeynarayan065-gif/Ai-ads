# Misfits: 3 talking-head UGC demo ads (portfolio, invented products)

Format (from the 0xROAS study): a creator talks to the phone's front camera, with hard-cut rear-camera b-roll of the
product in between, one 12 s Seedance 2.5 take with dialogue and lip sync. His inherited phone-realism + audio blocks
are in every prompt. Products are invented for the demo ([VERIFY] the names MOSSO / DEWLAB / CLASP aren't real
trademarks in the category before posting). Post with an "AI-generated" label (Meta AI info / ASCI).

| # | Style | Creator / place | Product | Script |
|---|---|---|---|---|
| 1 | First-person review | Woman, 26, parked car | MOSSO cold brew can | "Okay, I need to talk about this coffee." → sip → "So smooth. Not bitter…" → "I keep two in my bag now. Link's below." |
| 2 | How-to | Man, 24, morning bathroom | DEWLAB water gel | "My whole morning skincare is one step." → 2 pumps → "pat it in, don't rub" → "Feels like water… done." |
| 3 | How-to + review | Woman, 28, home desk | CLASP magnetic grip | "Three ways I use it." → snap on → stand → one-hand scroll → "And three, it just looks cute." |

Files per ad: `0N-*-still-creator.md` (Nano Banana, one face), `0N-*-still-product.md` (Nano Banana packshot),
`0N-*-seedance.md` (Image 1 = creator, Image 2 = product). Lint: PASS (seedance); still warnings are only "no refs".

## Cost
- Stills: 6 × 18 cr = 108 cr.
- Videos: 3 × 756 cr (720p, 12 s, audio on) = 2,268 cr.
- **Total ~2,376 cr ($11.88)**, ~1.5x with a retake. Balance on 7 Nov: 7 cr, so top up first.

## Run order (after OK on each)
```bash
python3 scripts/kie_generate.py image --prompt-file ads/misfits/ugc-demos/01-coldbrew-still-creator.md --out ads/misfits/ugc-demos/stills --aspect 9:16 --resolution 2K --yes
python3 scripts/kie_generate.py image --prompt-file ads/misfits/ugc-demos/01-coldbrew-still-product.md --out ads/misfits/ugc-demos/stills --aspect 1:1 --resolution 2K --yes
python3 scripts/kie_generate.py seedance --prompt-file ads/misfits/ugc-demos/01-coldbrew-seedance.md --out ads/misfits/ugc-demos/takes --ref <creator.png> --ref <product.png> --resolution 720p --aspect 9:16 --duration 12 --audio --yes
```
## Post
Word-by-word captions (one or two words, key word highlighted), trim dead air, a cart/"link below" CTA, "AI-generated"
label. QA: transcribe the speech (Whisper) and check for ad-libbed claims; product text not garbled; no second face;
the product doesn't jump between hands.
