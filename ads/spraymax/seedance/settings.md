# Spraymax: Seedance 2.5 product film (15 s)

Built on the structure of a Higgsfield Seedance 2.5 demo (a perfume brand's product film from one reference sheet
and one timestamped prompt):
- product truth first;
- hard cuts only;
- a global look;
- a "never render" list;
- 12 timed shots alternating product and ingredient macros.

Adapted to Spraymax:
- **Ingredients from the label:** Himalayan sea salt, sea water, aloe vera, plus a faceless hair-texture macro.
- **The pump mists, never drips.**
- **Vertical 9:16, 15 s.**

| Setting | Value |
|---|---|
| Model | Seedance 2.5, reference-to-video (not first-frame mode: the two can't be combined) |
| Reference | `product-sheet.jpg` (real photos: front, pump side, nozzle, flat label). Name it `sheet` on Higgsfield; on API providers replace `@sheet` with that provider's tag (`@Image 1` on Segmind, `@Image1` on fal, `Image 1` on BytePlus) |
| Prompt | `prompt-seedance-15s.md` (passes `scripts/prompt_lint.py --kind seedance --faceless`) |
| Aspect / length | 9:16, 15 s |
| Resolution | Draft at 480p to check the shots, final at 720p (or 1080p if the budget allows) |
| Audio | Off if the provider allows it, or keep it (the prompt asks for no music or voices); the music is added in Instagram |
| Cost | ~$3.50 per 15 s take at 720p (~$1.55 at 480p, ~$8.50 at 1080p); about 3 takes, so **~$10** per finished film |

## After the render

- Check the label against `product-sheet.jpg` frame by frame. Lock it with `scripts/label_lock_*.py` where
  the small lines garble.
- Check that the mist never turns into a liquid stream and that no hand or face appears.
- Score the take on `reference/ai-video-qa.md` and log it in `ads/spraymax/prompt-log.md`.
