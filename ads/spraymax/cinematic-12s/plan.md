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

## Shots (v3): the perfume film's grammar, shot for shot

Narayan, 3 Nov: "there's no shots and motions like the ones that was in the blue perfume shot". v2 had drifted
into static, centred shots at a slower pace. v3 copies the reference's cut (measured in
`reference/creators/higgsfield-seedance-ex-nihilo.md`) and keeps every requested type (POV and use, macro,
multi-pack, smoke, water splash). The preview is a moving 3D animatic (`build_animatic.py` →
`animatic-v3.mp4`) because a PDF can't show camera moves.

| # | Frame | Time (s) | Shot | Move (from the reference) |
|---|---|---|---|---|
| 1 | F1 | 0.0-1.2 | Light sweeps round the ribbed collar | push-in |
| 2 | F16 | 1.2-1.8 | Pink salt chunks meeting in sea mist, blue backdrop (= citrus) | drift |
| 3 | F17 | 1.8-2.4 | Aloe rosette from above (= the blossom) | drift |
| 4 | F18 | 2.4-3.0 | Pump and collar rise out of the aloe's heart (= cap in the blossom) | push-in |
| 5 | F19 | 3.0-3.7 | Cold smoke curl | drift through |
| 6 | F6 | 3.7-4.8 | Bottle, deep blue bloom rising behind | push-in |
| 7 | F20 | 4.8-5.6 | Macro on the wave band (= the base text) | push-in |
| 8 | F21 | 5.6-6.2 | A bead of sea water runs down (= the liquid strand; never from the nozzle) | locked, drop moves |
| 9 | F22 | 6.2-6.8 | Fast rack across the collar ribs (= the glass ridges) | fast track, motion blur |
| 10 | F2 | 6.8-7.4 | Near-silhouette, silver edge | rise + push |
| 11 | F23 | 7.4-8.1 | Five bottles, light through the gaps (= the wood shards) | lateral drift |
| 12 | F12 | 8.1-8.8 | POV: one press, mist onto the palm | handheld hold |
| 13 | F10 | 8.8-9.4 | Crown splash round the bottle | locked, slow motion |
| 14 | F4 | 9.4-10.0 | Mist burst from the side nozzle | locked, slow motion |
| 15 | F9 | 10.0-12.0 | Packshot + logo, BORN IN HIMACHAL | near-still push |

Seedance: Image 1 is the product sheet; Images 2-16 are the layout frames, one per shot. Duration 12 s.

## Budget (kie, Seedance 2.5, per second of output; 1 credit = $0.005)

Rates: 480p 28 cr, 720p 63 cr, 1080p 158 cr. Reference images are free. Balance on the old account: 2,037 cr.

| Option | Credits | Cost | Note |
|---|---|---|---|
| **A · 720p, upscaled to 1080x1920** (recommended) | 756 | $3.78 | Leaves room for two 4 s single-shot fixes (1,260 cr, $6.30 in all) |
| B · native 1080p | 1,896 | $9.48 | Over the $7 budget. One take, no fixes possible (141 cr left) |
| C · 480p draft, then 1080p from the draft | ~2,232 | ~$11.16 | More than the balance; kie lists no price for the draft-to-1080p step |

**Status:** v1 and v2 sent; v3 (perfume grammar plus animatic) being built. Waiting for A or B. Nothing spent.

## Commands

```bash
KEY="$(grep '^KIE_API_KEY_PREV=' .env | cut -d= -f2- | tr -d "\"'")"
REFS=$(ls ads/spraymax/cinematic-12s/refs/*.jpg | sed 's/^/--ref /')
# dry run (prints the request and the cost; spends nothing)
KIE_API_KEY="$KEY" python3 scripts/kie_generate.py seedance --prompt-file ads/spraymax/cinematic-12s/prompt-seedance-12s.md \
  --out ads/spraymax/cinematic-12s/takes --resolution 720p --aspect 9:16 --duration 12 $REFS
# after approval: the same command with --yes
```
