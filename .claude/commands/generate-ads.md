---
description: Generate ads for every platform in a brief
argument-hint: <path to brief>
---
Generate ads for the brief: $ARGUMENTS

1. Read the brief, the brand file it references, `reference/platform-specs.md`,
   `reference/frameworks.md` and `reference/output-format.md`.
2. If the goal, offer, audience or platforms are missing, ask me before writing.
3. For each checked platform write `ads/<brand-slug>/<campaign-slug>/<platform>.md` following the
   output format. Each variation uses a different angle, labelled in its heading.
   - For tiktok (and Reels if requested) add a 15–30s script: Hook (0–2s), Body, CTA, with on-screen text.
   - For visual platforms include a **Visual:** line and an **Image prompt:** line.
4. Follow every rule in CLAUDE.md — especially: no invented facts, mark anything uncertain `[VERIFY]`.
5. Run `python3 scripts/check_limits.py ads/<brand-slug>/<campaign-slug>/` and fix every
   over-limit field, then re-run until it passes.
6. Finish with a short table: platform, file, number of variations, and your top pick per platform with a one-line reason.
