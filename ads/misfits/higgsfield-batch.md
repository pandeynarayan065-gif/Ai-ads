# Higgsfield Ultra batch (bought 14 Nov 2026, sale price $79)

- Unlimited Seedance 2.5 / 2.5 Flash for 14 days: up to 20 s, 720p, only on the higgsfield.ai website (not via MCP/API).
  Unlimited images (Nano Banana Pro, Seedream 5.0 Pro, GPT Image 2.5/2.6 at 2K) for 60 days.
- Renews at $129/month. **Cancel before the renewal date** if not continuing.
- Workflow: Claude writes the prompt here; Narayan pastes it on higgsfield.ai (Seedance 2.5, references uploaded in the
  order given = Image 1, Image 2), downloads the clip into the folder below; Claude QAs, upscales (Real-ESRGAN, free),
  adds sound and end cards.
- Settings for every job: Seedance 2.5, 720p, 9:16, audio on, duration as listed (max 20 s).

| # | Job | Prompt (paste the whole file) | References, in order | Length | Save the clip to |
|---|---|---|---|---|---|
| 1 | Avrana game-cutscene ad | `ads/misfits/clients/avrana/demo-game-cutscene/prompt-seedance-18s.md` | 04.jpg (back), 03.jpg (front) | 18 s | `ads/misfits/clients/avrana/demo-game-cutscene/takes/` |
| 2 | Avrana 6 macro shots (cuff, knit, ink, emblem, ash, hem) | `ads/misfits/clients/avrana/demo-death-glory/prompt-seedance-6s-macros.md` | 04.jpg, 03.jpg | 6 s | `ads/misfits/clients/avrana/demo-death-glory/takes/` |
| 3 | Jose's 7 videos (15-day plan) | written one by one once Jose picks designs | that design's back + front photos | 15-20 s | `ads/misfits/clients/avrana/content-engine/` |
| 4 | Jewellery demos for Ranchi/Delhi shops | `ads/misfits/jewellery-demo/prompt-seedance-12s.md` as the base, one per shop's piece | the shop's product photo + a crop | 12-15 s | `ads/misfits/jewellery-demo/<shop>/` |
