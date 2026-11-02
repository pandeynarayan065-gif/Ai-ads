# Spraymax: 12 s cinematic film (Seedance 2.5)

**Brief (Narayan, 2026-11-02):** "create the 12 second pure cinematic masterpiece but first give me a pdf with actual
shots rendered with 3d to give me an idea of what each shot will look like and I need 1080p 9:16". Budget about
$7 of kie credits. Then: "Only use seedance 2.5".

**Look:** the Higgsfield Seedance "Ex Nihilo" product film (`reference/creators/higgsfield-seedance-ex-nihilo.md`)
in Spraymax's colours:
- black void;
- ice-blue and silver-white light, deep indigo washes;
- the pink Himalayan salt the only warm note;
- one hard light per shot;
- hard cuts.

## Steps

1. **3D storyboard frames:** `video/blender/film_shots.py --shot F1..F9` renders 1080x1920 frames, with the real
   bottle and label.
2. **Storyboard PDF:** `build_storyboard.py` builds `storyboard.pdf`, `shots/*.md` (one card per shot) and
   `refs/` (the Seedance references).
3. **One Seedance 2.5 generation** (reference-to-video, 9:16, 12 s, audio off), using `prompt-seedance-12s.md`
   (lint PASS, `--kind seedance --faceless`):
   - Image 1 is `refs/01-product-sheet.jpg` (from `product-sheet-v2.jpg`): Narayan's low-light front photo, the
     pump side, the nozzle and the flat label. This is the product truth.
   - Images 2–10 are `refs/02-layout-F1.jpg` … `10-layout-F9.jpg`: one per shot, used for framing, angle and
     light only.
4. **QA every shot** (`reference/ai-video-qa.md`):
   - the label matches the real bottle (lock it in post if it drifts);
   - the mist never turns into liquid;
   - no light fixtures, mirror floors, hands or faces.
5. **Fix a failed shot:** regenerate only that shot as a 4 s clip (the minimum length) and cut it in.
6. **Finish:**
   - upscale to 1080x1920 if generated at 720p;
   - grade, grain, SFX and music;
   - end card in post: logo, BORN IN HIMACHAL, spraymax.in.

## Shots

| # | Time | Shot | Camera |
|---|---|---|---|
| F1 | 0–2 s | Macro of the pump and ribbed collar, a light sweeping across the ribs | 100 mm, slow push-in |
| F2 | 2–3 s | Capped bottle in near-silhouette, a silver line down its edge | 85 mm low, creeps up |
| F3 | 3–4 s | Pink Himalayan salt with sea-water beads, glowing from behind | Macro, near still |
| F4 | 4–6 s | The mist bursts sideways from the nozzle, backlit ice blue | Macro, locked off, slow motion |
| F5 | 6–7 s | Night sea, a swell rising toward the lens under a cold moon | 50 mm at the water, still |
| F6 | 7–8 s | The bottle in a black void, an indigo wash blooming behind | 85 mm, slow push-in |
| F7 | 8–9 s | The mist hanging in one hard beam of light | 85 mm, locked off |
| F8 | 9–10 s | Macro across the wordmark, cold grazing light | Macro, still |
| F9 | 10–12 s | Packshot: left of centre on indigo matte, long shadow, dark sky for the end card | 85 mm, very slow push-in |

## Budget (kie, Seedance 2.5, per second of output; 1 credit = $0.005)

Rates: 480p 28 cr, 720p 63 cr, 1080p 158 cr. Reference images are free. Balance on the old account: 2,037 cr.

| Option | Credits | Cost | Note |
|---|---|---|---|
| **A · 720p, upscaled to 1080x1920** (recommended) | 756 | $3.78 | Leaves room for two 4 s single-shot fixes (1,260 cr, $6.30 in all) |
| B · native 1080p | 1,896 | $9.48 | Over the $7 budget. One take, no fixes possible (141 cr left) |
| C · 480p draft, then 1080p from the draft | ~2,232 | ~$11.16 | More than the balance; kie lists no price for the draft-to-1080p step |

**Status:** storyboard sent; waiting for the user to pick A or B. Nothing spent.

## Commands

```bash
KEY="$(grep '^KIE_API_KEY_PREV=' .env | cut -d= -f2- | tr -d "\"'")"
REFS=$(ls ads/spraymax/cinematic-12s/refs/*.jpg | sed 's/^/--ref /')
# dry run (prints the request and the cost; spends nothing)
KIE_API_KEY="$KEY" python3 scripts/kie_generate.py seedance --prompt-file ads/spraymax/cinematic-12s/prompt-seedance-12s.md \
  --out ads/spraymax/cinematic-12s/takes --resolution 720p --aspect 9:16 --duration 12 $REFS
# after approval: the same command with --yes
```
