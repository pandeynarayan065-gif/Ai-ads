# Misfits: 3 talking-head UGC demo ads (portfolio, invented products)

Format (from the 0xROAS study): a creator talks to the phone's front camera, with hard-cut rear-camera b-roll of the
product in between, one 12 s Seedance 2.0 take with dialogue and lip sync. His inherited phone-realism + audio blocks
are in every prompt. Products are invented for the demo ([VERIFY] the names MOSSO / DEWLAB / CLASP aren't real
trademarks in the category before posting). Post with an "AI-generated" label (Meta AI info / ASCI).

| # | Style | Creator / place | Product | Script |
|---|---|---|---|---|
| 1 | First-person review | Woman, 26, parked car | MOSSO cold brew can | "Okay, I need to talk about this coffee." → sip → "So smooth. Not bitter…" → "I keep two in my bag now. Link's below." |
| 2 | How-to | Man, 24, morning bathroom | DEWLAB water gel | "My whole morning skincare is one step." → 2 pumps → "pat it in, don't rub" → "Feels like water… done." |
| 3 | How-to + review | Woman, 28, home desk | CLASP magnetic grip | "Three ways I use it." → snap on → stand → one-hand scroll → "And three, it just looks cute." |

Files per ad: `0N-*-still-creator.md` (GPT Image, one face), `0N-*-still-product.md` (GPT Image packshot),
`0N-*-seedance.md` (Image 1 = creator, Image 2 = product). 
## Models (Narayan, 7 Nov)
- **Stills: GPT Image 2.6 Flare** (`--model gpt-image-2-6/flare-text-to-image --quality high`), 2K. Token-billed: the
  exact charge prints after each run. Fallback: Nano Banana Pro (18 cr).
- **Video: Seedance 2.0** (`seedance --version 2.0`), 720p, 12 s, audio on (dialogue + lip sync). Prompts use his 2.0
  wording: "Reference Image1 for the character only", "Reference Image2 for the product only". Lint PASS `--sd 2.0`.

## Cost
- Seedance 2.0: kie lists "from 11.5 cr/s" (138 cr for 12 s is the floor); the 720p rate isn't in the docs, so the
  real charge shows after the first run. Run ad 1 first and read the charge before the other two.
- Balance on 7 Nov: 7 cr, so top up first.

## Run order (after OK on each)
```bash
python3 scripts/kie_generate.py image --model gpt-image-2-6/flare-text-to-image --quality high --prompt-file ads/misfits/ugc-demos/01-coldbrew-still-creator.md --out ads/misfits/ugc-demos/stills --aspect 9:16 --resolution 2K --yes
python3 scripts/kie_generate.py image --model gpt-image-2-6/flare-text-to-image --quality high --prompt-file ads/misfits/ugc-demos/01-coldbrew-still-product.md --out ads/misfits/ugc-demos/stills --aspect 1:1 --resolution 2K --yes
python3 scripts/kie_generate.py seedance --version 2.0 --prompt-file ads/misfits/ugc-demos/01-coldbrew-seedance.md --out ads/misfits/ugc-demos/takes --ref <creator.png> --ref <product.png> --resolution 720p --aspect 9:16 --duration 12 --audio --yes
```
## Post
Word-by-word captions (one or two words, key word highlighted), trim dead air, a cart/"link below" CTA, "AI-generated"
label. QA: transcribe the speech (Whisper) and check for ad-libbed claims; product text not garbled; no second face;
the product doesn't jump between hands.
