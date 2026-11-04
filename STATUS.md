# Status (updated 4 Nov 2026)

Open work, newest first. Each project's `plan.md` has the details; finished masters sit in the project folder.

## Portfolio spec ads ("3 demo ai ads ... 12 seconds", up to 5 in total)

1. **Red Bull**: done. `ads/redbull-spec/cinematic-12s/redbull-cinematic-12s.mp4` (1080p) and `-4k.mp4`.
   Possible extra: an end card, only if Narayan asks.
2. **Samsung Galaxy Z Fold8 Ultra**: cut approved as v5 (`ads/samsung-spec/fold8-ultra-12s/takes/preview-v5-1080.mp4`,
   14.6 s): iPhone Duo opener 2.6 s, chrome logo shot graded to Star White, the film, clean spec supers.
   Next: the 4K master, in progress: `make_masters.sh` (re-runnable from scratch, see SETUP.md). ESRGAN 4x of `takes/edit-v1-720.mp4` and of opener frames 0-64
   (`takes/20261104-203734-1.mp4`), then `add_opener.py` -> `grade_logo_shot.py --from 62` ->
   `ads/spraymax/cinematic-12s/finish_film.py --no-card --size 1080x1920` and `2160x3840` -> strip audio ->
   `hud_overlay.py --offset 62` -> `samsung-fold8-ultra-spec.mp4` and `-4k.mp4`.
   Caption it "Spec ad. Not affiliated with Samsung or Apple."
3. **Ad 3**: not chosen yet; ask Narayan.

## Paused

- **Misfits portfolio packaging** (`brand/misfits/portfolio/make_portfolio.py`): Narayan said "Wait stop everything".
  He also said "Noir acid was selected rn", but `brand/misfits/tokens.css` still defaults to Midnight/Volt: confirm
  with him before switching.
