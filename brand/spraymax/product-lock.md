# Spraymax product lock

The fixed description of the bottle. Copy it **word for word** into still prompts and reference-video prompts,
and never reword it between shots. Image-to-video prompts don't use it: there the bottle is just "the bottle".

## Facts (from the real bottle photos)

- 100 ml. About 14 cm tall including the pump, about 3.8 cm wide. [VERIFY: measure. `himalayan-launch/poster-plan.md`
  used 15.5 cm.] In a hand it is about as long as the hand from the base of the palm to the fingertips.
- Body: a slim cylinder with a rounded shoulder, made of smooth, slightly greyish off-white opaque plastic
  with a soft sheen.
- Collar: matte white and finely ribbed.
- Pump head: a small, smooth white actuator. The nozzle is a **small round hole flush in the side of the head**,
  not a tube.
- **The nozzle faces the same way as the back label.** When someone sprays their hair, the front label faces
  away from their head. Filming from behind the person therefore shows the front wordmark.
- Overcap: clear, lightly frosted plastic. The white pump shows through it. The cap is off whenever someone is
  spraying.
- Label: a printed wrap-around sticker. Its top edge sits just below the shoulder, and a band of bare white
  plastic shows below its bottom edge at the base.
  - The indigo "Spraymax" wordmark runs down the bottle, reading **top to bottom**.
  - The small line "Instant Hair Volume & Texture".
  - A band at the bottom with a dark navy photo of real ocean waves, carrying "FOR ALL HAIR TYPES" and
    "100ml/3.38fl.oz." in white.
- Back label: ingredients and a caution block (small text). Never needs to be readable.

## Reference images and their roles (`brand/spraymax/assets/`)

| File | Use it for | Notes |
|---|---|---|
| `bottle-ref-clean.jpg` | Shape, proportions, front label (studio packshots) | Clean front view; best "image 1" for packshots. Also the overlay for proportion QA |
| `bottle-real-hand-close.jpg` | Bottle held in a hand: grip, scale, real plastic | Real photo, front label, cap on |
| `pump-side-real.jpg` | The pump head from the side and the ribbed collar | Fixes the "nasal-spray tube" error |
| `pump-front-real.jpg` | The nozzle hole, and which way it faces | The back label shows on the nozzle side |
| `label-front-panel.jpg` | Front label layout | For still refs. Wording is locked in post anyway |
| `label-flat.jpg` | Full flat label art | Post-production label lock only, not a generation ref |
| `bottle-front-render.jpg` | Label layout only | A render. Don't use it as a realism ref |
| `logo-wide.png` | End cards in post | Never ask a model to draw it |

## Block for still prompts (Nano Banana Pro)

> Take the bottle from image 1 exactly as it is: a slim 100 ml bottle about 14 cm tall, with a rounded
> shoulder, made of smooth, slightly greyish off-white opaque plastic with a soft sheen; a matte white, finely
> ribbed collar; a small smooth white pump head with a tiny round nozzle hole in its side[, under a clear,
> lightly frosted overcap]. A white wrap-around label with the indigo wordmark running down the bottle and a
> dark navy ocean-wave photo band at the base, exactly as in image 1, with bare white plastic showing below
> the band.

Drop the bracketed part when the cap is off. End the prompt with: "Ensure the bottle's shape, proportions,
cap, collar and label remain completely unchanged from image 1."

## Block for Seedance 2.5

> Image 1 is the real Spraymax bottle from the front: use it for the exact shape, colours and label. Image 2
> is its pump from the side: use it for the pump head and the ribbed collar. Define the slim off-white bottle
> with the ribbed collar and the vertical indigo wordmark in Image 1 as <Subject 1>.

Constants line: "<Subject 1> keeps its exact shape, size, label and colours from Image 1; no new reflections."

## What the models get wrong with this bottle (check at still QA)

| Error | Seen in | Fix |
|---|---|---|
| Pump drawn as a nasal-spray tube, or mist already coming out | Ocean still | Use `pump-side-real.jpg` as a ref. Fix in post (`spray-ocean-fix.py`) |
| Smooth collar instead of ribbed | Ocean still | Ref plus post fix |
| Wordmark reads bottom to top; "TTFES"; a different band photo | Ocean still | `label_lock_still.py` / `label_lock_handheld.py` |
| Bottle 13–17% too long for its width | Ocean still, drop | Measure against `bottle-ref-clean.jpg` at the same width |
| Bottle oversized next to a hand (23–27 cm) | Ocean still v1 | Scale anchor in the prompt. Resize edit if it still happens |
| Squat proportions; no gap below the label; label not visible as a sticker | Gemini mockup, studio hero v1 | Rebuild the first frame at real proportions (`build_first_v2.py`) |
| Milky overcap instead of clear | Studio hero | `clear_cap.py` |
| Small lines ("Instant Hair…", "100ml/3.38…") garbled or mirrored | Every clip | `fix_text_v2.py`, label lock |
| Bottle swells when a hand passes over it | Reveal (mitt wipe) | Never move a hand over the bottle |
| Label paste looks like a flat sticker with a yellow tint | First ocean lock | `label_lock_handheld.py` (per-pixel light, taper, chroma to the scene's white) |
