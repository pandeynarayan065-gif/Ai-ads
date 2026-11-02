# Shot 06: bloom

Part of one Seedance 2.5 multi-shot generation (`prompt-seedance-12s.md`). Rules: `reference/ai-video-playbook.md`.

## Plan

- **Brand / campaign:** Spraymax / cinematic-12s
- **Job in the edit:** Brand colour moment
- **On screen:** 1 s, 7–8 s
- **The shot:** The bottle in a black void, a little left of centre, label to camera, with a broad soft indigo wash blooming behind it from no visible source.
- **Real-crew test:** a tabletop / macro studio (motion-control slider, strip lights, a hidden pump rig).
- **Product:** the real bottle; label must match the product sheet (lock in post if it drifts)
- **People:** none
- **Camera (one move):** 85 mm at label height, slow push-in
- **Light:** Soft silver light from high right; indigo rim on the left
- **What moves (one action):** The indigo wash rises
- **Sound (post):** Rising low drone

## Pipeline

- **Layout frame:** `frames/F6.jpg` (Blender, `video/blender/film_shots.py --shot F6`), sent as Image 7
- **Product truth:** Image 1, `refs/01-product-sheet.jpg` (real photos)
- **Motion:** Seedance 2.5, reference-to-video, one 12 s generation for all nine shots

## Prompt line

> <Subject 1> with its overcap on stands a little left of centre in a black void, label to camera, framed as in Image 7, a broad soft wash of deep indigo light blooming behind it from an unseen source. The camera pushes in slowly.

## Pass criteria

1. One camera move, no morph into the next shot (hard cut at 8 s)
2. Bottle proportions and label match the product sheet
3. No visible light fixture, no mirror floor, no text other than the label

## Takes

| Take | Model / mode | Cost | Scorecard (1–9) | Total | Usable range | Verdict | Failures |
|---|---|---|---|---|---|---|---|
