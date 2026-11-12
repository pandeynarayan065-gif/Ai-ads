# Status (updated 12 Nov 2026)

Open work, newest first. Each project's `plan.md` has the details; finished masters sit in the project folder.

## Client: Avrana (Jose, US print-on-demand streetwear via Apliiq)

- **Death & Glory demo film: final.** `ads/misfits/clients/avrana/demo-death-glory/avrana-death-glory-film.mp4`
  (1080p) and `-4k.mp4` (4K, 67 MB); the 120 MB 4K master `-4k-master.mp4` stays local (over GitHub's 100 MB cap).
  Mixed-order macro cut, 17 shots, Narayan's soundtrack (`soundtrack/soundtrack.m4a`). Pipeline: `deflicker_subject.py`
  -> `scripts/esrgan_upscale.py` -> `recut_macros.py` -> `finish_film.py`. Log: `ads/misfits/clients/avrana/prompt-log.md`.
- **Pitch site live:** https://misfits-avrana.vercel.app (custom player, 4K download). Redeploy with
  `deploy_site.py <scratchpad>/avrana-live`; repo copy in `pitch-site/index.html`.
- **Deal on the table:** Jose offered $200 for 15 days. Proposed: 7 x 15 s videos + free statics, $100 upfront, rolls
  into $399 first month, then $599/mo. Seedance 2.5 at 720p ~ $54 for 7 with retries (then free Real-ESRGAN to 4K).
- **Not generated yet:** the 6 real macro shots (cuff, knit, hem...) in `prompt-seedance-6s-macros.md` (378 kie cr).
  kie balance 27 credits. Higgsfield MCP (Seedance 2.5 among its models) is now connected: check its trial terms
  and commercial use before client work.
- Call prep and store findings: `ads/misfits/clients/avrana/call-prep.md`.

## Portfolio spec ads ("3 demo ai ads ... 12 seconds", up to 5 in total)

1. **Red Bull**: done. `ads/redbull-spec/cinematic-12s/redbull-cinematic-12s.mp4` (1080p) and `-4k.mp4`.
   Possible extra: an end card, only if Narayan asks.
2. **Samsung Galaxy Z Fold8 Ultra**: done (v5 cut). `ads/samsung-spec/fold8-ultra-12s/samsung-fold8-ultra-spec.mp4`
   (1080p) and `-4k.mp4`, 14.6 s, visuals only: iPhone Duo opener 2.6 s, chrome logo shot graded to Star White, the
   film, clean spec supers; no-text versions `-notext.mp4` and `-notext-4k.mp4`. Rebuild with `make_masters.sh`. Caption: "Spec ad. Not affiliated with Samsung or Apple."
3. **Ad 3: Jean Paul Gaultier Ultra Male** (`ads/jpg-spec/ultra-male-12s/plan.md`): done: `jpg-ultra-male-spec.mp4` (1080p) and `-4k.mp4`, 12.4 s, spray shot replaced by the lavender gust (v4). Caption: "Spec ad. Not affiliated with Jean Paul Gaultier."

## Paused

- **Misfits portfolio packaging** (`brand/misfits/portfolio/make_portfolio.py`): Narayan said "Wait stop everything".
  He also said "Noir acid was selected rn", but `brand/misfits/tokens.css` still defaults to Midnight/Volt: confirm
  with him before switching.
