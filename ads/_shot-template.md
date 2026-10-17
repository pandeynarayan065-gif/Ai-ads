# Shot <nn>: <slug>

Copy to `ads/<brand>/<campaign>/shots/<nn>-<slug>.md`. Fill in every line before writing a prompt.
Rules: `reference/ai-video-playbook.md`. Gates: `reference/ai-video-qa.md`.

## Plan

- **Brand / campaign:**
- **Job in the edit:** hook / product truth / use / texture / payoff (pick one)
- **On screen:** <seconds> s, from <beat> to <beat>
- **The shot in one sentence:** [camera] on [subject] [doing one action] in [place], [light].
- **Real-crew test:** how would a real crew film it? (rig, location, practical effect). If they couldn't,
  redesign the shot.
- **Recipe** (playbook section 6): hero packshot / macro / liquid / in use / lifestyle / environment / transition
- **Product:** shown? which side faces the camera? label: must be exact (lock in post) / not required to read
- **Scale anchor:** e.g. "bottle 14 cm, about a hand long, a hand's width from his ear"
- **People:** none / faceless how (from behind / cropped below the eyes / hands only)
- **Camera (one move):** rig + lens + height + distance + the move (or locked-off) + where it ends
- **What moves (one action):** the action, its physical cause and its timing
- **Must stay fixed:**
- **Sound:** the SFX we'll want in the edit

## Pipeline

- **Keyframe:** Nano Banana Pro / none (text-to-video). Refs and their roles:
  - image 1:
  - image 2:
- **Still fixes in post:**
- **Motion:** Veo 3.1 Fast first frame / Veo ingredients / Seedance 2.5 refs / Seedance 2.5 first frame / text-to-video
- **Clip fixes in post:**

## Prompts

| File | Lint | Dry run shown | User approved |
|---|---|---|---|
| `prompt-<nn>-still.md` | PASS / WARN (why OK) | yes | <date> |
| `motion-<nn>.md` | | | |

## Budget

- Credits per take: still <18> + clip <65> = <83>
- Takes planned: <2>
- Balance before: <n>

## Pass criteria (specific to this shot)

1. e.g. "the bottle stays the real size; no swelling in any frame"
2. e.g. "the pump dips and the mist goes sideways into the hair within 0.5 s"
3. e.g. "the face is never visible from 0.5 s to 3.5 s"

## Takes

| Take | Model / mode | Cost | Scorecard (1–9) | Total | Usable range | Verdict | Failures (with timestamps) |
|---|---|---|---|---|---|---|---|
| 1 | | | 2 2 1 2 1 2 2 2 1 | 15 | 1.2–3.4 s | keep / retake / reject | |

## Lesson for the prompt log

One line: what worked or failed, and the rule it gives us.
