# Installed skills (from Joey Mulcahy's "Complete Claude Skill Bank", 9 Nov 2026)

Source: joeymulcahyguides.notion.site/the-complete-claude-skill-bank. Reviewed before install: the scripts only call
fal.ai (FAL_KEY from .env) and download their results; no other network use.

| Command | What it does | Model (fal.ai) | Their stated cost |
|---|---|---|---|
| /packshot | phone photo -> studio packshot / flat-lay | Nano Banana 2 | ~ $0.12 / image |
| /product-shoot | your product into a reference scene (+ optional lighting ref) | GPT Image 2.5 | ~ $0.12 / image |
| /model | consistent brand model: headshot + full body | Nano Banana 2 | ~ $0.24 / model |
| /model-product-shoot | model + product in a reference scene | GPT Image 2.5 | ~ $0.12 / image |
| /add-motion | animate a still, 3-12 s | Kling 3.0 Pro | ~ $0.11-0.17 / s |
| /product-video | UGC: selfie review, unboxing, try-on, GRWM, ASMR, up to 30 s | Seedance 2.5 | ~ $0.47 / s at 720p |

Not installable (not Claude skills): Static Ad (behind a YouTube video), Recasting and Cinematic Brand Videos
(Figma Weave workflows).

Setup: `pip install fal-client requests`; put `FAL_KEY=...` in `.env` at the repo root (gitignored), or, in a cloud
session, save it as a network credential for fal.ai. They write to `brands/<brand>/...` (our brand files live in
`brand/`). Our CLAUDE.md rules still apply: show the prompt and cost and wait for OK before spending.
