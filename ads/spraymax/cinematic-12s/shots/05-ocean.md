# Shot 05: ocean

Part of one Seedance 2.5 multi-shot generation (`prompt-seedance-12s.md`). Rules: `reference/ai-video-playbook.md`.

## Plan

- **Brand / campaign:** Spraymax / cinematic-12s
- **Job in the edit:** Origin: sea salt
- **On screen:** 1 s, 6–7 s
- **The shot:** Low over a night ocean. A swell rises toward the lens under a cold moon; a glittering path on the water, fine spray lifting off the crest.
- **Real-crew test:** a tabletop / macro studio (motion-control slider, strip lights, a hidden pump rig) or a water housing at night.
- **Product:** not in shot
- **People:** none
- **Camera (one move):** 50 mm just above the water, holds still
- **Light:** Moonlight from straight ahead
- **What moves (one action):** The swell rises and folds
- **Sound (post):** Deep wave roar, spray hiss (added in post)

## Pipeline

- **Layout frame:** `frames/F5.jpg` (Blender, `video/blender/film_shots.py --shot F5`), sent as Image 6
- **Product truth:** Image 1, `refs/01-product-sheet.jpg` (real photos)
- **Motion:** Seedance 2.5, reference-to-video, one 12 s generation for all nine shots

## Prompt line

> Low over a dark night ocean, framed as in Image 6. A long swell rises toward the camera under a cold moon that lays a glittering path across the water, fine spray lifting off its crest. The camera holds still just above the water.

## Pass criteria

1. One camera move, no morph into the next shot (hard cut at 7 s)
2. Reads as real footage, not 3D
3. No visible light fixture, no mirror floor, no text other than the label

## Takes

| Take | Model / mode | Cost | Scorecard (1–9) | Total | Usable range | Verdict | Failures |
|---|---|---|---|---|---|---|---|
