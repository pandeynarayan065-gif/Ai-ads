# Red Bull: 12 s spec film (Misfits portfolio)

Spec ad: not commissioned by, affiliated with or endorsed by Red Bull. Say so wherever it is posted.

- Brief (Narayan, 4 Nov): cinematic product shots of the can, plus Red Bull's world of dangerous sport (F1, freeride
  skiing, moto and more), cinematic ad visuals.
- Ref: `refs/01-redbull-can-official-front.jpg`, Red Bull's official US product image of the 250 ml Energy Drink can (redbull.com,
  collected with a headless browser on 4 Nov), cold, front view. One ref only, so the model can't mix two regional prints.
- Model: Seedance 2.5, reference mode, 720p, 9:16, 12 s, 756 cr. Upscale free with Real-ESRGAN.
- Prompt: `prompt-seedance-12s.md`, in the ad-1 structure (asset map, product truth, summary, hard cuts, real
  photography, global look, never-render, 13 timestamped shots, Throughout).
- Faceless: every athlete in a helmet and goggles, or in silhouette. No readable sponsor text, so nothing garbles.

## Take 1 (4 Nov): kept
- `takes/20261104-192915-1.mp4`: Seedance 2.5, 720p, 12 s, 756 cr. All 13 shots, in order, cut at 1.50 2.67 3.71 4.46
  5.08 5.96 6.50 7.08 7.71 8.54 9.50 10.71 s.
- Right: the can's print, exactly ("Red Bull", the bulls and sun, ENERGY DRINK, "Vitalizes body and mind",
  "250 mL (8.4 FL OZ)"); everyone helmeted, no faces; the F1 shot has no text; real-looking sparks, powder, dust and
  rock.
- Fixed in post (`clean_logos.py` -> `takes/20261104-192915-1_clean.mp4`): a white star logo on the racing gloves
  (9.5-10.7 s), like a real glove brand's mark; red pseudo-letters on the wingsuit (6.5-7.1 s).
- Cut (Narayan, 4 Nov: "Remove this shot"): the cliff dive, frames 185-204 (`edit_redbull.py`); the film is 11.21 s.
- Next: Real-ESRGAN 4x of the cleaned take, then `edit_redbull.py`, then `finish_film.py --no-card` at 1080x1920 and 4K,
  visuals only.
