# Shot 02: blade

Part of one Seedance 2.5 multi-shot generation (`prompt-seedance-12s.md`). Rules: `reference/ai-video-playbook.md`.

## Plan

- **Brand / campaign:** Spraymax / cinematic-12s
- **Job in the edit:** Reveal the shape
- **On screen:** 1 s, 2–3 s
- **The shot:** Low three-quarter view of the capped bottle, almost in silhouette. One thin silver highlight runs down its right edge.
- **Real-crew test:** a tabletop / macro studio (motion-control slider, strip lights, a hidden pump rig).
- **Product:** the real bottle; label must match the product sheet (lock in post if it drifts)
- **People:** none
- **Camera (one move):** 85 mm, low angle, creeps upward toward the collar
- **Light:** One hard silver strip from behind on the right; faint cool bounce at the base
- **What moves (one action):** The highlight slides along the edge as the camera rises
- **Sound (post):** Deep soft whoosh

## Pipeline

- **Layout frame:** `frames/F2.jpg` (Blender, `video/blender/film_shots.py --shot F2`), sent as Image 3
- **Product truth:** Image 1, `refs/01-product-sheet.jpg` (real photos)
- **Motion:** Seedance 2.5, reference-to-video, one 12 s generation for all nine shots

## Prompt line

> Low three-quarter view of <Subject 1> with its overcap on, nearly in silhouette against black, framed as in Image 3. One thin silver highlight runs down the bottle's right edge and nothing else is lit. The camera creeps slowly upward toward the collar.

## Pass criteria

1. One camera move, no morph into the next shot (hard cut at 3 s)
2. Bottle proportions and label match the product sheet
3. No visible light fixture, no mirror floor, no text other than the label

## Takes

| Take | Model / mode | Cost | Scorecard (1–9) | Total | Usable range | Verdict | Failures |
|---|---|---|---|---|---|---|---|
