---
description: Review a finished Seedance generation with the reverse prompt engineer — score it on the QA scorecard, map each failure to the prompt words that caused it, write the fix and log it in the brand's prompt log.
argument-hint: <video file> <brand> <campaign> [prompt file]
---
Review this take: $ARGUMENTS

1. Find the prompt that made it: the argument, else the `.json` next to the take in `takes/`, else
   `film/06-prompt.md`.
2. Spawn `reverse-engineer` for job (b) with the video, the prompt file, the brand and campaign.
3. Show Narayan, short: the score (n/18, pass/fail), usable ranges, each failure → the prompt words → the fix, and
   the recommendation (keep + post fixes / one 4 s insert / one-change retake / reject the concept). One contact
   sheet ≤800 px wide, no more images.
4. If a retake or insert is recommended, it goes back through `/film-stage prompt` and `/film-stage reality`, then
   the spend gate (credits, dry run, exact prompt, his yes). Never generate from here.
5. Commit and push the review and the prompt-log row.
