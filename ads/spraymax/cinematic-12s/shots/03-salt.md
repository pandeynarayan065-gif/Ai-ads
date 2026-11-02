# Shot 03: salt

Part of one Seedance 2.5 multi-shot generation (`prompt-seedance-12s.md`). Rules: `reference/ai-video-playbook.md`.

## Plan

- **Brand / campaign:** Spraymax / cinematic-12s
- **Job in the edit:** Ingredient: Himalayan sea salt (from the label)
- **On screen:** 1 s, 3–4 s
- **The shot:** Extreme macro of raw pale-pink Himalayan salt with beads of sea water, glowing pink from behind. The only warm colour in the film.
- **Real-crew test:** a tabletop / macro studio (motion-control slider, strip lights, a hidden pump rig).
- **Product:** not in shot
- **People:** none
- **Camera (one move):** 100 mm macro, holds nearly still (micro drift)
- **Light:** Warm back light through the salt; small cold key catching the beads
- **What moves (one action):** A bead rolls down a facet
- **Sound (post):** One soft water drip

## Pipeline

- **Layout frame:** `frames/F3.jpg` (Blender, `video/blender/film_shots.py --shot F3`), sent as Image 4
- **Product truth:** Image 1, `refs/01-product-sheet.jpg` (real photos)
- **Motion:** Seedance 2.5, reference-to-video, one 12 s generation for all nine shots

## Prompt line

> Extreme macro of a raw chunk of pale pink Himalayan rock salt with frosted, cleaved facets and small beads of sea water clinging to its edges, framed as in Image 4, glowing soft pink from a light behind it against black. The camera holds nearly still with a micro drift.

## Pass criteria

1. One camera move, no morph into the next shot (hard cut at 4 s)
2. Reads as real footage, not 3D
3. No visible light fixture, no mirror floor, no text other than the label

## Takes

| Take | Model / mode | Cost | Scorecard (1–9) | Total | Usable range | Verdict | Failures |
|---|---|---|---|---|---|---|---|
