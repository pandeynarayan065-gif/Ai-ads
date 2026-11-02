# Shot 09: packshot

Part of one Seedance 2.5 multi-shot generation (`prompt-seedance-12s.md`). Rules: `reference/ai-video-playbook.md`.

## Plan

- **Brand / campaign:** Spraymax / cinematic-12s
- **Job in the edit:** Pack and end card
- **On screen:** 2 s, 10–12 s
- **The shot:** Wide: the capped bottle left of centre on a deep indigo matte surface, a long hard shadow raking right, the top half left dark for the end card (added in post: logo, BORN IN HIMACHAL, spraymax.in).
- **Real-crew test:** a tabletop / macro studio (motion-control slider, strip lights, a hidden pump rig).
- **Product:** the real bottle; label must match the product sheet (lock in post if it drifts)
- **People:** none
- **Camera (one move):** 85 mm just above the surface, very slow push-in
- **Light:** Hard silver spot from low left; indigo rim
- **What moves (one action):** Nothing but the camera
- **Sound (post):** One soft low boom, then silence

## Pipeline

- **Layout frame:** `frames/F9.jpg` (Blender, `video/blender/film_shots.py --shot F9`), sent as Image 10
- **Product truth:** Image 1, `refs/01-product-sheet.jpg` (real photos)
- **Motion:** Seedance 2.5, reference-to-video, one 12 s generation for all nine shots

## Prompt line

> Wide packshot framed as in Image 10. <Subject 1> with its overcap on stands left of centre on a deep indigo matte surface, label to camera, a long hard shadow raking away to the right, the upper half of the frame left in empty darkness. The camera pushes in very slowly, almost imperceptibly.

## Pass criteria

1. One camera move, no morph into the next shot (hard cut at 12 s)
2. Bottle proportions and label match the product sheet
3. No visible light fixture, no mirror floor, no text other than the label

## Takes

| Take | Model / mode | Cost | Scorecard (1–9) | Total | Usable range | Verdict | Failures |
|---|---|---|---|---|---|---|---|
