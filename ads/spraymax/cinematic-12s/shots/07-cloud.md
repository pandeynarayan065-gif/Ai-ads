# Shot 07: cloud

Part of one Seedance 2.5 multi-shot generation (`prompt-seedance-12s.md`). Rules: `reference/ai-video-playbook.md`.

## Plan

- **Brand / campaign:** Spraymax / cinematic-12s
- **Job in the edit:** Texture: lightweight, airy finish
- **On screen:** 1 s, 8–9 s
- **The shot:** A soft cloud of fine mist hanging in a single hard beam of cold light, droplets glinting as it spreads up and to the right.
- **Real-crew test:** a tabletop / macro studio (motion-control slider, strip lights, a hidden pump rig).
- **Product:** not in shot
- **People:** none
- **Camera (one move):** 85 mm, locked off, slow motion
- **Light:** One hard ice-blue beam from behind on the right
- **What moves (one action):** The cloud spreads and drifts
- **Sound (post):** Airy hiss fading out

## Pipeline

- **Layout frame:** `frames/F7.jpg` (Blender, `video/blender/film_shots.py --shot F7`), sent as Image 8
- **Product truth:** Image 1, `refs/01-product-sheet.jpg` (real photos)
- **Motion:** Seedance 2.5, reference-to-video, one 12 s generation for all nine shots

## Prompt line

> A soft cloud of fine mist hangs in a single hard beam of cold light in black space, framed as in Image 8, the droplets glinting as the cloud slowly spreads up and to the right. Locked-off camera.

## Pass criteria

1. One camera move, no morph into the next shot (hard cut at 9 s)
2. Mist only: airborne droplets, no stream, no drips
3. No visible light fixture, no mirror floor, no text other than the label

## Takes

| Take | Model / mode | Cost | Scorecard (1–9) | Total | Usable range | Verdict | Failures |
|---|---|---|---|---|---|---|---|
