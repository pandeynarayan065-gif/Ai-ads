# Status (updated 14 Nov 2026)

New chat? Read `HANDOFF.md` first.

Open work, newest first. Each project's `plan.md` has the details; finished masters sit in the project folder.

## Client: Avrana (Jose Guzman, US print-on-demand streetwear via Apliiq)

- **Deal agreed:** 15-day Content Engine, USD 200 (100 now on invoice INV-002, 100 on day 8): 7 video ads 15-30 s,
  7 statics + 2 carousels, calendar, day-15 call. Deliverables: `ads/misfits/clients/avrana/deliverables-15-day.md`.
  Service agreement sent (signed as Anirudh Savaliya; money-back terms, video 1 delivered watermarked until Jose OKs it).
- **Payment: Jose says the first USD 100 is sent** (15 Nov, ~2:42 am IST, Wise to Anirudh's UPI). Confirm it has landed in Kotak (ACH funding can take 1-2 business days). Jose pays via Wise (Wise-to-Wise by Anirudh's email, or UPI from
  Wise). Day 1 = payment received; video 1 due within 24 h after that. Razorpay international applied for (Misfits
  account, purpose code P1007), pending.
- **Death & Glory demo film: final.** `demo-death-glory/avrana-death-glory-film.mp4` (1080p) and `-4k.mp4`; 120 MB
  master `-4k-master.mp4` local only. Live on https://misfits-avrana.vercel.app (`deploy_site.py`).
- **Game-cutscene ad (in progress, on Higgsfield):** `demo-game-cutscene/prompt-seedance-18s-epic-night.md` (2 refs only; night skyline, epic rain-and-backlight look; earlier: `-night-3refs.md`; older day version: `-rooftop-4refs.md`) with
  refs 1 hoodie back, 2 hoodie front, 3 `refs/3-style-reference.jpg`, 4 `refs/4-background-reference.jpg`.
  Takes so far in `demo-game-cutscene/takes/` (both rejected: low-poly toy look, fantasy village). Original
  characters only (no Jin Kazama / Dante likeness: it's a paid client ad).
- **Not generated yet:** 6 macro shots, `demo-death-glory/prompt-seedance-6s-macros.md`.

## Misfits jewellery demo (outreach to jewellery shops in Ranchi and Delhi)

- Done: `ads/misfits/jewellery-demo/misfits-jewellery-demo.mp4` (+ `-4k`), showcase reel
  `misfits-jewellery-showcase.mp4` (+ `-4k`), captions in `captions.md`. End card says "YOUR STORE HERE".

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
