# Spraymax: 12 s cinematic film (Seedance 2.5)

**Brief (Narayan, 2026-11-02):** "create the 12 second pure cinematic masterpiece but first give me a pdf with actual
shots rendered with 3d to give me an idea of what each shot will look like and I need 1080p 9:16". Budget about
$7 of kie credits. Then: "Only use seedance 2.5".

**Look:** the Higgsfield Seedance "Ex Nihilo" product film (`reference/creators/higgsfield-seedance-ex-nihilo.md`)
in Spraymax's colours:
- black void;
- ice-blue and silver-white light, deep ocean-blue washes (never purple);
- the pink Himalayan salt the only warm note;
- one hard light per shot;
- hard cuts.

## Feedback on storyboard v1 (partners Anirudh and Ishaan, WhatsApp, 2 Nov) and what changed in v2

| Feedback | v2 |
|---|---|
| "Bas ye jyada hi detailed hai" (too detailed) | One full frame and one line per page, phone-shaped pages; the tech details live here |
| "Real bottle aisi nahi hai" (the real bottle isn't like this) | Milky semi-matte plastic, matte pump and collar, matched to Narayan's real-bottle video; nozzle on the back-label side |
| "Purple kyu? Blue honi chahiye" | All violet washes and rims are now deep ocean blue; "no purple or violet light" in the prompt |
| Narayan: no POV, macro, multi-pack, smoke or water splash? Usage, spray on the hand? | New shots: crown splash, smoke, first-person spray onto the palm, sea-water beads macro, five-bottle lineup |

## Steps

1. **3D storyboard frames:** `video/blender/film_shots.py --shot <id>` renders 1080x1920 frames, with the real
   bottle and label. The POV frame (F12) is Narayan's video frame plus the 3D mist (`make_pov.py`, from F15).
2. **Storyboard PDF:** `build_storyboard.py --frames <dir>` builds `storyboard.pdf`, `shots/*.md` (one card per
   shot) and `refs/` (the Seedance references).
3. **One Seedance 2.5 generation** (reference-to-video, 9:16, 12 s, audio off), using `prompt-seedance-12s.md`
   (lint PASS, `--kind seedance --faceless`):
   - Image 1 is `refs/01-product-sheet.jpg` (from `product-sheet-v2.jpg`): Narayan's low-light front photo, the
     pump side, the nozzle and the flat label. This is the product truth.
   - Images 2–11 are `refs/02-layout-F1.jpg` … `11-layout-F9.jpg`: one per shot, used for framing, angle and
     light only.
4. **QA every shot** (`reference/ai-video-qa.md`):
   - the label matches the real bottle (lock it in post if it drifts);
   - the mist never turns into liquid;
   - no light fixtures, glossy studio floors or faces; hands only in shot 5;
   - blue light, never purple.
5. **Fix a failed shot:** regenerate only that shot as a 4 s clip (the minimum length) and cut it in.
6. **Finish:**
   - upscale to 1080x1920 if generated at 720p;
   - grade, grain, SFX and music;
   - end card in post: logo, BORN IN HIMACHAL, spraymax.in.

## Shots (v2)

| # | Frame | Time | Shot | Type |
|---|---|---|---|---|
| 1 | F1 | 0–1 s | A hard light sweeps across the ribbed collar | Macro |
| 2 | F10 | 1–2 s | Dark sea water erupts in a crown round the bottle | Elemental water |
| 3 | F3 | 2–3 s | Pink Himalayan salt tumbles through one cold beam | Ingredient |
| 4 | F11 | 3–4 s | Cold smoke rolls in and curls round the bottle | Smoke |
| 5 | F12 | 4–6 s | First person: one press, a fine mist settles on the open palm | POV, use |
| 6 | F4 | 6–7 s | The mist bursts out of the nozzle, backlit ice blue | Macro |
| 7 | F13 | 7–8 s | Sea-water beads on the label, one runs down over the wordmark | Macro |
| 8 | F5 | 8–9 s | A night swell rises toward the lens under a cold moon | Elemental water |
| 9 | F14 | 9–10 s | Five bottles staggered back into the dark | Multi-pack |
| 10 | F9 | 10–12 s | Packshot on deep blue, long shadow, end card | Packshot |

## Budget (kie, Seedance 2.5, per second of output; 1 credit = $0.005)

Rates: 480p 28 cr, 720p 63 cr, 1080p 158 cr. Reference images are free. Balance on the old account: 2,037 cr.

| Option | Credits | Cost | Note |
|---|---|---|---|
| **A · 720p, upscaled to 1080x1920** (recommended) | 756 | $3.78 | Leaves room for two 4 s single-shot fixes (1,260 cr, $6.30 in all) |
| B · native 1080p | 1,896 | $9.48 | Over the $7 budget. One take, no fixes possible (141 cr left) |
| C · 480p draft, then 1080p from the draft | ~2,232 | ~$11.16 | More than the balance; kie lists no price for the draft-to-1080p step |

**Status:** v1 sent 2 Nov (feedback above). v2 storyboard being built. Waiting for A or B. Nothing spent.

## Commands

```bash
KEY="$(grep '^KIE_API_KEY_PREV=' .env | cut -d= -f2- | tr -d "\"'")"
REFS=$(ls ads/spraymax/cinematic-12s/refs/*.jpg | sed 's/^/--ref /')
# dry run (prints the request and the cost; spends nothing)
KIE_API_KEY="$KEY" python3 scripts/kie_generate.py seedance --prompt-file ads/spraymax/cinematic-12s/prompt-seedance-12s.md \
  --out ads/spraymax/cinematic-12s/takes --resolution 720p --aspect 9:16 --duration 12 $REFS
# after approval: the same command with --yes
```
