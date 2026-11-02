# Shot 04: mist

Part of one Seedance 2.5 multi-shot generation (`prompt-seedance-12s.md`). Rules: `reference/ai-video-playbook.md`.

## Plan

- **Brand / campaign:** Spraymax / cinematic-12s
- **Job in the edit:** Product action: what it does
- **On screen:** 2 s, 4–6 s
- **The shot:** Side macro of the pump head, cap off. A fine cone of mist bursts sideways out of the nozzle, backlit ice blue, tight at the nozzle and blooming wide before it thins into the black. Mist, never liquid.
- **Real-crew test:** a tabletop / macro studio (motion-control slider, strip lights, a hidden pump rig).
- **Product:** the real bottle; label must match the product sheet (lock in post if it drifts)
- **People:** none
- **Camera (one move):** 100 mm macro, locked off, slow motion
- **Light:** Ice-blue back light through the mist; soft cold key on the pump
- **What moves (one action):** The mist bursts and blooms
- **Sound (post):** Sharp pump hiss, airy trail

## Pipeline

- **Layout frame:** `frames/F4.jpg` (Blender, `video/blender/film_shots.py --shot F4`), sent as Image 5
- **Product truth:** Image 1, `refs/01-product-sheet.jpg` (real photos)
- **Motion:** Seedance 2.5, reference-to-video, one 12 s generation for all nine shots

## Prompt line

> Macro side view of the pump head of <Subject 1>, overcap removed, nozzle pointing right, framed as in Image 5. Locked-off camera, slow motion. A fine cone of mist bursts sideways out of the nozzle hole, backlit ice blue so every droplet catches the light, tight at the nozzle and blooming wide, soft and translucent before thinning into black.

## Pass criteria

1. One camera move, no morph into the next shot (hard cut at 6 s)
2. Mist only: airborne droplets, no stream, no drips
3. No visible light fixture, no mirror floor, no text other than the label

## Takes

| Take | Model / mode | Cost | Scorecard (1–9) | Total | Usable range | Verdict | Failures |
|---|---|---|---|---|---|---|---|
