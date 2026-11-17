---
description: Rerun one stage of the Seedance film crew from the files already in ads/<brand>/<campaign>/film/ (e.g. after you edited one), without redoing the others. Never spends credits.
argument-hint: <stage: research|reverse|story|storyboard|director|dop|prompt|reality|signoff|page> <brand> <campaign> [notes]
---
Rerun one film-crew stage: $ARGUMENTS

1. Read `ads/<brand>/<campaign>/film/00-brief.md` and the stage files the agent depends on:
   research ← brief; story ← 01; storyboard ← 02 (+04 notes); director ← 02, 03 (sign-off: + 05–07); dop ← 03, 04;
   prompt ← 03–05 (+ latest 07); reality ← prompt file, 06; signoff ← all.
2. Spawn the matching agent (`researcher`, `reverse-engineer`, `story-writer`, `storyboard-artist`, `director`,
   `dop`, `prompt-engineer`, `reality-checker`) with the brand, campaign and any notes from the arguments. It
   overwrites its own stage file (reality writes the next round number).
3. Tell Narayan which later stages are now stale (everything downstream of the rerun stage) and offer to rerun them.
4. `page`: rebuild `film/page.md` (lint, credits, dry run, no `--yes`) as in `/film` step 9.
Never run `kie_generate.py` with `--yes`. Commit and push the changed stage files.
