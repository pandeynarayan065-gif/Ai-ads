# Samsung Galaxy Z Fold8 Ultra: 12 s spec film (Misfits portfolio)

Spec ad: not commissioned by, affiliated with or endorsed by Samsung. Say so wherever it is posted. The opening shows
Apple's logo on an iPhone Duo: a trademark of another company, used in a comparative way (Narayan's call).

- Brief (Narayan, 4 Nov): open on the newly launched iPhone foldable; the reflection in its Apple logo reveals the
  Galaxy Z Fold8 Ultra as we push in; cut to the product; cinematic, informative shots breaking down each component.
- Names: Samsung Galaxy Z Fold8 Ultra (launched 22 July 2026). Apple's foldable: reported as "iPhone Duo"
  (Gurman, 9 Sep 2026). [VERIFY Apple's official name before posting]
- Official facts (samsung.com/us/smartphones/galaxy-z-fold8-ultra, read 4 Nov 2026), for spec supers in post only:
  - screens: 6.5" closed, 8.0" open; 4.1 mm thin, 215 g;
  - Armor FlexHinge; Armor Aluminum frame; Flex Titanium layer; Gorilla Glass Victus 2;
  - cameras: 200 MP wide, 50 MP ultra-wide, 10 MP 3x telephoto, up to 30x digital zoom;
  - Snapdragon 8 Elite Gen 5 for Galaxy; 5000 mAh; 3000 nits peak.
- Refs (all official, from samsung.com/us product and buy pages, collected with a headless browser on 4 Nov):
  1. `refs/01-fold8-ultra-front-back-violet.jpg`: closed, front and back, Violet Shadow (shape, colour, camera column);
  2. `refs/02-fold8-ultra-hinge-side.jpg`: side view folded (hinge, frame, thickness);
  3. `refs/03-fold8-ultra-half-open-back.jpg`: half open from the back (opening, thinness).
- The cameras are a vertical column of three at the top-left of the back (the half-open photo made them look like a row).
- Model: Seedance 2.5, reference mode, 720p, 9:16, 12 s, 756 cr.
- Screens show only an abstract gradient: no UI or text from the model. Spec text is added in post.

## Take 1 (4 Nov): kept, with the chip shot remade
- `takes/20261104-194336-1.mp4`: Seedance 2.5, 720p, 12 s, 756 cr, three official refs. All 13 shots, in order:
  - the Apple logo with the Fold8 reflected;
  - the reveal, with the vertical camera column right;
  - lens macro; two-hand unfold (ribbon wallpaper, no UI); hinge;
  - parts flat lay; camera module; chip; battery; display layers;
  - open flat; fold shut; hero packshot.
- The chip shot (6.62-7.38 s) printed fake text on the lid ("SALOXY SNMAD..."). Two clean-up tries failed (lid mask
  merged with the gold traces). Narayan: "Remake shot". Remake `takes/20261104-195802-1.mp4`: Seedance 2.5 first frame,
  4 s, 252 cr, from `images/chip-first-frame-1080x1920.jpg` (the take's chip frame with the lid wiped blank), prompt
  `motion-chip-remake.md`. The lid stayed blank; a light line sweeps across it.
- kie rule learned: Seedance 2.5 first-frame tasks need `--aspect adaptive` (9:16 is rejected with a 422, uncharged).
- Edit: `edit_samsung.py` swaps in remake frames 36-53 for take frames 159-176 -> `takes/edit-v1-720.mp4` (289 frames).
- Next: Real-ESRGAN 4x of the edit, `finish_film.py --no-card` at 1080x1920 and 4K, visuals only; spec supers in post
  from the official facts above.

## Opener and spec HUD (4 Nov)
- Narayan: open on the real iPhone Duo, push in to its Apple logo, Fold8 Ultra in the reflection; add Jarvis-style
  animated spec text on the component shots.
- Opener: `prompt-opener-seedance-4s.md`, Seedance 2.5 reference mode, 4 s, 720p, 252 cr. Refs: Apple's official
  iPhone Duo photos (`refs/04-...`, `refs/05-...`, Star White) and `refs/01-...` for the reflection. Plan: it replaces
  shot 1 (frames 0-37) so the film stays about 12 s. Awaiting approval.
- HUD: `hud_overlay.py`, run last on the finished film. Official specs only: 200MP/50MP/10MP 3x, Armor FlexHinge,
  up to 30x digital zoom, Snapdragon 8 Elite Gen 5 for Galaxy, 5000 mAh, Flex Titanium, Gorilla Glass Victus 2,
  8.0" / 3000 nits peak, 4.1 mm / 215 g. Preview `takes/preview-hud-1080.mp4` (Lanczos 1080p, not the final upscale).
