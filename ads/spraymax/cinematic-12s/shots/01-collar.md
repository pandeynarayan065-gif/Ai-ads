# Shot 01: collar

Part of one Seedance 2.5 multi-shot generation (`prompt-seedance-12s.md`). Rules: `reference/ai-video-playbook.md`.

## Plan

- **Brand / campaign:** Spraymax / cinematic-12s
- **Job in the edit:** Hook: a mystery close-up before the bottle is revealed
- **On screen:** 2 s, 0–2 s
- **The shot:** Extreme macro of the pump head and the ribbed collar, cap off. A narrow hard white light sweeps right to left across the ribs and lights them one by one; the left side stays in shadow.
- **Real-crew test:** a tabletop / macro studio (motion-control slider, strip lights, a hidden pump rig).
- **Product:** the real bottle; label must match the product sheet (lock in post if it drifts)
- **People:** none
- **Camera (one move):** 100 mm macro, very slow push-in
- **Light:** One hard cold-white strip from the right, grazing; faint indigo rim
- **What moves (one action):** The light sweeps across the ribs
- **Sound (post):** Sub-bass swell, cold air hiss

## Pipeline

- **Layout frame:** `frames/F1.jpg` (Blender, `video/blender/film_shots.py --shot F1`), sent as Image 2
- **Product truth:** Image 1, `refs/01-product-sheet.jpg` (real photos)
- **Motion:** Seedance 2.5, reference-to-video, one 12 s generation for all nine shots

## Prompt line

> Extreme macro of the pump head and the ribbed collar of <Subject 1>, overcap removed, against pure black, framed as in Image 2. The camera pushes in very slowly while a narrow hard white light sweeps from right to left across the collar, catching the ribs one by one; the left side of the collar stays in near-total shadow.

## Pass criteria

1. One camera move, no morph into the next shot (hard cut at 2 s)
2. Bottle proportions and label match the product sheet
3. No visible light fixture, no mirror floor, no text other than the label

## Takes

| Take | Model / mode | Cost | Scorecard (1–9) | Total | Usable range | Verdict | Failures |
|---|---|---|---|---|---|---|---|
