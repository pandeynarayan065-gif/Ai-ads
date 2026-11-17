---
description: Run the Seedance 2.5 film crew and show one page with the storyboard, final prompt, lint, cost and risks. Modes - quick (one insert shot, ~3 min), fast (default film, ~6-8 min), full (all 8 stages incl. web research and director review). Never spends credits.
argument-hint: <brand> <campaign> <idea> [quick|fast|full] [length s] [reference files]
---
Run the film crew for: $ARGUMENTS

Every Seedance 2.5 generation goes through this crew. Spawn each agent by its name (`subagent_type`). Agents in
`.claude/agents/` register when a session starts: if one isn't found (files added mid-session), spawn
`general-purpose` with "You are the film crew's `<name>` agent. Read `.claude/agents/<name>.md` and follow it exactly."
Their shared rulebook is `reference/seedance-rules.md`. Work folder: `ads/<brand>/<campaign>/film/`.

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

## Modes (Narayan: "FASTER BRO AM NOT GONNA WAIT THIS LONG FOR EACH GENERATION")
Pick the lightest mode that fits; say which one you used on the page.

| Mode | When | Stages | Time |
|---|---|---|---|
| `quick` | One shot or a 4–6 s insert into an existing film | prompt-engineer (writes a 3-line shot plan + the prompt) → reality-checker (1 round; 1 rewrite max) → spend gate | ~3 min |
| `fast` (default) | A new film for a brand we already know | storyboard-artist (story + shots + light/lens columns in one file) → prompt-engineer → reality-checker (≤2 rounds) → spend gate; director signs off in parallel with the spend gate | ~6–8 min |
| `full` | New brand, new category, or Narayan asks for research | every stage below | ~15–20 min |

In `fast`, the storyboard artist writes `03-storyboard.md` with the hook and the one feeling at the top and a light/lens
column, so `02-story.md` and `05-dop.md` are skipped; the prompt engineer reads the DoP choices from the storyboard.
In `quick`, the prompt engineer works from the brief, the existing film's prompt and the rulebook, and writes the plan at
the top of `06-prompt.md`. Reference decoding (`reverse-engineer` job a) runs in parallel in any mode when Narayan gives
references.

## Speed
- Independent stages run in parallel (research ∥ reverse; director review ∥ DoP). Spawn them in one message.
- Only `full` searches the web; `quick` and `fast` work from the rulebook and `reference/creators/`.
- Give each agent a one-paragraph prompt (brand, campaign, folder, what's different); its file holds the rules. Start
  every spawn prompt with "Read reference/seedance-rules.md first" (the storyboard artist skipped it once and planned
  a first frame inside a reference run).
- Lighter stages (researcher, story, storyboard, DoP) run on a faster model; prompt engineer, reality checker,
  director and reverse engineer keep the main model.

## Full mode, stage by stage

## 1. Research ∥ reverse (parallel)
Spawn in one message, in the background:
- `researcher` → `film/01-research.md` (and any `reference/creators/` study, official refs in `refs/`).
- `reverse-engineer` job (a), only if reference videos/frames were given → `film/00-reverse.md`.
Wait for both.

## 2. Story → 3. Storyboard → 4. Director review
Run in order: `story-writer` → `storyboard-artist` → `director` (review). If the director says REVISE, run
`storyboard-artist` once more with the notes, then `director` again. A second REVISE: stop and show Narayan both.

## 5. DoP (in parallel with the director review) → 6. Prompt → 7. Reality loop
Speed: start `dop` on `03-storyboard.md` in the same message as the `director` review; if the director says REVISE,
rerun `dop` only after the revised storyboard. Then `prompt-engineer` (v1) → `reality-checker` (round 1). On FAIL: `prompt-engineer` (v2, applies every fix) →
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
