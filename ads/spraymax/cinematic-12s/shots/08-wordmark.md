# Shot 08: wordmark

Part of one Seedance 2.5 multi-shot generation (`prompt-seedance-12s.md`). Rules: `reference/ai-video-playbook.md`.

## Plan

- **Brand / campaign:** Spraymax / cinematic-12s
- **Job in the edit:** Name the brand
- **On screen:** 1 s, 9–10 s
- **The shot:** Macro across the front label: the indigo Spraymax wordmark running down the bottle in shallow focus, cold light grazing the print, the far side falling into shadow.
- **Real-crew test:** a tabletop / macro studio (motion-control slider, strip lights, a hidden pump rig).
- **Product:** the real bottle; label must match the product sheet (lock in post if it drifts)
- **People:** none
- **Camera (one move):** 100 mm macro at an angle, holds still
- **Light:** Cold strip grazing from the right
- **What moves (one action):** Nothing; a still beat before the end
- **Sound (post):** Low hum

## Pipeline

- **Layout frame:** `frames/F8.jpg` (Blender, `video/blender/film_shots.py --shot F8`), sent as Image 9
- **Product truth:** Image 1, `refs/01-product-sheet.jpg` (real photos)
- **Motion:** Seedance 2.5, reference-to-video, one 12 s generation for all nine shots

## Prompt line

> Macro across the front of the label of <Subject 1>, framed as in Image 9: the indigo wordmark running down the bottle in shallow focus, a cold light grazing across the printed surface, the far side falling into shadow. The camera holds still.

## Pass criteria

1. One camera move, no morph into the next shot (hard cut at 10 s)
2. Bottle proportions and label match the product sheet
3. No visible light fixture, no mirror floor, no text other than the label

## Takes

| Take | Model / mode | Cost | Scorecard (1–9) | Total | Usable range | Verdict | Failures |
|---|---|---|---|---|---|---|---|
