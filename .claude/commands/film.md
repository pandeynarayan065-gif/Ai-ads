---
description: Run the Seedance 2.5 film crew (research → story → storyboard → director → DoP → prompt → reality check → sign-off) and show one page with the storyboard, final prompt, lint, cost and risks. Never spends credits.
argument-hint: <brand> <campaign> <idea> [length s] [reference files]
---
Run the film crew for: $ARGUMENTS

Every Seedance 2.5 generation goes through this crew. The crew is in `.claude/agents/`; their shared rulebook is
`reference/seedance-rules.md`. Work folder: `ads/<brand>/<campaign>/film/`.

## Hard rules (never break)
- **No credits.** The crew never runs `kie_generate.py ... --yes`. You (the main session) only run `credits` and a
  dry run at the end, show the exact prompt, and stop. Generation happens later, only after Narayan says yes to that
  exact prompt.
- Never print or commit API keys. No real people's likeness, no copyrighted characters, no other brands in client
  ads (spec ads of a real brand use its own official photos and are captioned "Spec ad. Not affiliated with …").
- Max **2 rewrite loops** between prompt engineer and reality checker; if round 3 would be needed, stop and ask.
- If Narayan says "stop", stop.

## 0. Brief (you, the main session)
- Parse brand, campaign, idea, length (default 12 s; Seedance runs 4–30 s on kie, ≤20 s on Higgsfield), resolution
  (default 720p on kie), platform (kie default; Higgsfield if he says so) and any reference files.
- Read `brand/<brand>.md` and the brief if one exists (`briefs/*<campaign>*`). If there is no brand file, or the goal,
  audience or platform is unclear, ask before going on (CLAUDE.md).
- Write `film/00-brief.md`: brand, campaign, idea in his words, length, resolution, platform, references (copied into
  `ads/<brand>/<campaign>/refs/` if he attached them), budget = current credits if known, what is in/out.

## 1. Research ∥ reverse (parallel)
Spawn in one message, in the background:
- `researcher` → `film/01-research.md` (and any `reference/creators/` study, official refs in `refs/`).
- `reverse-engineer` job (a), only if reference videos/frames were given → `film/00-reverse.md`.
Wait for both.

## 2. Story → 3. Storyboard → 4. Director review
Run in order: `story-writer` → `storyboard-artist` → `director` (review). If the director says REVISE, run
`storyboard-artist` once more with the notes, then `director` again. A second REVISE: stop and show Narayan both.

## 5. DoP → 6. Prompt → 7. Reality loop
`dop` → `prompt-engineer` (v1) → `reality-checker` (round 1). On FAIL: `prompt-engineer` (v2, applies every fix) →
`reality-checker` (round 2). If round 2 also FAILs, **stop**: show Narayan the open fixes and ask how to proceed
(that is the 2-loop limit).

## 8. Director sign-off
`director` sign-off → `film/08-signoff.md`.

## 9. Spend gate (you)
1. `python3 scripts/prompt_lint.py <prompt> --kind seedance [--faceless]` (record the output).
2. `python3 scripts/kie_generate.py credits`.
3. Dry run, no `--yes`: `python3 scripts/kie_generate.py seedance --prompt-file <prompt> --out ads/<brand>/<campaign>/takes
   --ref <Image 1> [--ref <Image 2> …] --resolution <res> --aspect 9:16 --duration <s>` (first-frame mode: `--first-frame
   <jpg> --aspect adaptive`). For Higgsfield, skip the dry run and give the paste-ready prompt and settings
   (cost per second there is [VERIFY]).
4. Write `film/page.md` and show it to Narayan:
```
# <brand> / <campaign> — ready for your yes
## Storyboard (from 03, as approved)
| # | Time | Shot | Camera | Product |
## Final prompt (exact, in full)
## Refs (in order, with jobs)
## Lint
## Cost: <cr> credits at <res>, <s> s (balance <n> → <n-cost>)
## Risks (from the last reality check + director)
## Say "yes" to generate this exact prompt.
```
Then **stop and wait**. Commit and push the `film/` folder, the prompt and the refs (never `.env`).
