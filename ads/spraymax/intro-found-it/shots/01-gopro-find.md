# Shot 01: gopro-find

Rules: `reference/ai-video-playbook.md`. Gates: `reference/ai-video-qa.md`.

## Plan

- **Brand / campaign:** Spraymax / intro "found it" (the night-find intro from `two-intros/concept.md`, now as POV)
- **Job in the edit:** hook
- **On screen:** 4 s, the whole clip (Narayan: "The whole clip 4 seconds"), cut straight into the film
- **The shot in one sentence:** a chest-mounted GoPro on a man walking a snowy Himalayan trail at night; the
  bottle, lying on its side in the snow, slides into frame from the top as he walks; he crouches and his hand
  lifts it a little; his head torch is the only light.
- **Brief (Narayan, 3 Nov):** a guy recording at night finds a Spraymax bottle lying on the ground; mysterious,
  dark; jungle or snowy mountains; his foot in good footwear and his hand visible; filmed like a GoPro; "the
  bottle not visible at first but then comes into frame as he walks"; "he goes to pick it up"; "picks it up a lil
  bit". Snow chosen over jungle: Himalayan sea salt, Born in Himachal.
- **Real-crew test:** pass. A hiker with a chest-mounted GoPro and a head torch on a snowy trail at night, the
  real bottle placed in the snow, one take.
- **Recipe:** lifestyle / POV find (handheld). Two beats (walk, then crouch and lift), against rule 2's "one
  action": accepted because Seedance handles timed beats and the brief asks for one continuous GoPro take.
  The first and last frames pin both ends, so the model only fills the motion between them.
- **Product:** shown, lying on its side, cap to the left, front label up. Label: must read in the last second;
  lock in post if garbled.
- **Scale anchor:** the bottle is about as long as his hand; his boot toe is in the same frame.
- **People:** hands-and-feet only (POV): his gloved left hand (black insulated glove; Narayan: "The hand can have gloves"), his jacket cuff, his boots. No face can be in frame.
- **Camera (one move):** chest-mount GoPro, ultra-wide, about 120 cm up while walking, dipping to about 60 cm
  as he crouches; the natural walking bob, no pans.
- **What moves:** 0–1.6 s two steps forward, the bottle enters from the top of the frame; 1.6–2.6 s he stops
  and crouches; 2.6–4 s his left hand grips the bottle's shoulder and collar and lifts that end a little, loose
  snow falling off.
- **Must stay fixed:** the bottle's size and shape, cap on, lying on its side (it never stands up), the label
  uncovered, the trail and rocks solid between the two frames.
- **Sound:** boots crunching in snow, wind, a low drone; added in post (audio off at generation).

## Pipeline

- **Keyframes:** Nano Banana Pro, 2K, 9:16. Two stills, because the bottle must not be in the first frame:
  - **end frame first** (`prompt-01-still-end.md`):
    - image 1 `refs/01-bottle-lying-capleft.jpg`: the real bottle lying down, cap left (bottle and label only);
    - image 2 `refs/02-bottle-dark-front.jpg`: the real plastic in low light;
    - image 3 `refs/03-pump-side.jpg`: the pump head and ribbed collar.
  - **then the start frame** (`prompt-01-still-start.md`):
    - image 1: the checked end frame, for the place, light, boots and grade; no bottle, no hand.
- **Still fixes in post:** label lock on the end frame if needed; both frames exported as exact 1080x1920 JPEGs.
- **Motion (what ran):** Seedance 2.5 reference-to-video, 720p, 4 s, audio off (`prompt-01-seedance-ref.md`), Narayan's
  pick ("Go 252") over the stills route. **Planned first:** Seedance 2.5, first + last frame (`motion-01.md`). Playbook lesson: only a
  frame where the bottle already lies stops Seedance standing it up.
- **Clip fixes in post (done):** Real-ESRGAN 4x; label lock (`label_lock_intro.py`, frames 52-96) with the real art in
  Seedance's own layout and light; `finish_film.py` grade and grain; masters `spraymax-intro-found-it-4s.mp4` and
  `-4k.mp4`, visuals only. SFX still to add.

## Prompts

| File | Lint | Dry run shown | User approved |
|---|---|---|---|
| `prompt-01-still-end.md` | WARN: 362 words. About 95 of them are the product block, which must stay word for word; the rest is cut to the frame | yes, 3 Nov | |
| `prompt-01-still-start.md` | PASS, 248 words | yes, 3 Nov | |
| `motion-01.md` | PASS, 94 words | yes, 3 Nov (480p 112 cr / 720p 252 cr) | not used |
| `prompt-01-seedance-ref.md` (what we ran) | PASS, 611 words | yes, 3 Nov (720p 252 cr) | 3 Nov: "Go 252" |

## Budget

- Credits: stills 18 + 18 = 36, plus the clip: 480p 4 s = 112 (total 148) or 720p 4 s = 252 (total 288)
- Takes planned: 1 of each still; 1 clip, with a second 480p take possible
- Balance before: 273 (720p needs at least 15 more credits)

## Pass criteria (specific to this shot)

1. For the first ~1 s the bottle isn't in frame; it slides in from the top by ~1.6 s, already lying in the snow.
2. The bottle stays the real size (about a hand long) and lying on its side; it never stands up; the cap stays on;
   no swelling as the hand closes on it.
3. The gloved hand has five natural fingers, grips the shoulder and collar, never covers the label, and lifts the
   bottle only a few centimetres.
4. No face in any frame: only the hand, the cuff and the boots.
5. Reads as real GoPro night footage: wide-lens distortion, natural walking bob, sensor noise, the head torch
   as the only light, no CGI sheen.
6. No morphing between the two frames: the trail, rocks and boots stay solid.

## Takes

| Take | Model / mode | Cost | Scorecard (1–9) | Total | Usable range | Verdict | Failures (with timestamps) |
|---|---|---|---|---|---|---|---|
| 1 `clips/20261103-104914-1.mp4` | Seedance 2.5, reference-to-video (Image 1 real bottle lying down, Image 2 flat label, Image 3 low-light bottle), 720p, 4 s, no audio | 252 | 1 2 2 2 2 1 2 2 1 | 15 | 0–4.04 s (all) | **keep** | 0–1.25 s a soft dark rectangle at the bottom left (reads as the GoPro's own shadow from the head torch); 1.3–3.2 s the top is a smooth tapered nozzle, not the ribbed collar, pump and clear cap (small in frame; under the glove from 3.2 s); 2.6 s the trampled snow turns granular as the camera gets close; small label lines garbled (wordmark correct). Passed: the bottle lies on its side and never stands up, enters from the top at 1.3 s, boots and black glove natural, five fingers, label uncovered, no face |

## Lesson for the prompt log

Seedance laid the bottle down for the first time when Image 1 was a real photo of it lying down (the three earlier upright failures all used upright refs). Rule: the refs' pose beats the text; for a lying product, give a reference photographed lying down.
Label lock: the real art laid out to scale read as a pasted sticker ("looks slapped on"); laid out in Seedance's own
footprint (band edge to edge, its letter size) and lit by the bottle's own pixels, it blends.
