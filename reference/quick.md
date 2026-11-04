# AI video and stills: quick reference

One page to read instead of the full playbook. Open `reference/ai-video-playbook.md` or `reference/ai-video-qa.md`
only for something this page doesn't cover. For Spraymax, also read `brand/spraymax/preferences.md` and
`brand/spraymax/product-lock.md`.

## Rules that make a shot work

1. **Real-crew test:** only what a real crew could film in a day (real water, wind, light, the real bottle).
2. **One camera move + one action per shot**; Seedance can carry timed beats and hard-cut multi-shot films.
3. **Still first, then animate**, except pure environments or Seedance from reference photos.
4. **Image-to-video prompts describe motion, camera and sound only**, never the picture again.
5. **The product block from the product lock, word for word.** Give each reference image one named job.
6. **Never ask a model for words.** Labels, supers and end cards are done in post.
7. **Lint before every dry run** (`scripts/prompt_lint.py`). Show the exact prompt and cost, and wait for OK.

## Models on kie (`scripts/kie_generate.py`)

| Job | Model / mode | Cost |
|---|---|---|
| Still, or an edit of a frame we have | Nano Banana Pro, 2K | 18 cr |
| Multi-shot film from real product photos | Seedance 2.5, reference images, `[mm:ss.s]` timestamps, hard-cuts rule | 720p 63 cr/s, 480p 28 cr/s, 1080p 158 cr/s |
| Exact start (and end) frame | Seedance 2.5, `--first-frame` (`--last-frame`) with `--aspect adaptive` (9:16 is rejected); refs can't be combined | same |
| Upscale | Real-ESRGAN, local and free (`scripts/esrgan_upscale.py`, ~11 s/frame); Topaz on kie failed 4/4 | free |

1 cr = $0.005.

## Prompts to copy (they worked)

- **Multi-shot perfume-style film, 15 cuts in 12 s:** `ads/spraymax/cinematic-12s/prompt-seedance-12s.md`. Its
  blocks, in order:
  - asset mapping;
  - product truth;
  - summary;
  - hard-cuts rule;
  - real-photography block;
  - global look;
  - never-render list (put before the shots);
  - timestamped shots;
  - "Throughout" line.
- **Ocean/Armani film:** `ads/spraymax/cinematic-12s-ocean/prompt-seedance-12s.md`.
- **Single 4 s POV with the bottle lying down:** `ads/spraymax/intro-found-it/prompt-01-seedance-ref.md`.
- **Nano Banana edit of our own 3D frame into a real photo:** `ads/spraymax/shelf-still/prompt-01-still.md`.

## Lessons (details in `ads/spraymax/prompt-log.md`)

- **Seedance stands the product upright** whatever the text says. Give a reference photographed lying down
  (`brand/spraymax/assets/bottle-real-lying-capleft.jpg`), or a first frame where it already lies.
- **Seedance spells the wordmark right**; the small lines ("Instant Hair...", "100ml/...") come out garbled.
- **A Nano Banana edit of our own render keeps the layout pixel-true.** Fix the small lines there by band position
  (`ads/spraymax/shelf-still/fix_labels.py`). Upscale first, then lay in the text.
- **Full label replacement on a moving AI bottle was rejected** (morphs, lighting reads as pasted). Don't repeat it.
- **Watch the nozzle:** models draw it facing front. The real hole faces the back-label side.
- **Seedance writes fake text on anything that would carry print in life:** a chip lid ("SALOXY SNMAD"), a glove (a
  real brand's star logo), a wingsuit (pseudo-letters). Say "blank" for those surfaces. If it still prints, remake the
  shot from a first frame with the surface wiped blank (`ads/samsung-spec/fold8-ultra-12s/`).
- **A reference used "only for a reflection" gets pasted in flat.** Given Samsung's front+back product photo for the
  Fold8 seen in the iPhone's logo, Seedance faded in a copy of that photo, wallpaper and all. Cut before it shows, or
  describe the reflection in words (a thin violet sliver of an edge) and leave that reference out.
- **Official product photos as refs make the product true** (Apple's iPhone Duo, Samsung's Fold8 camera column).
  Get them with the headless browser from the brand's own site; save them in the project's `refs/`.
- **Text over the film:** clean supers only, on shots long enough to read (`brand/spraymax/preferences.md`).

## QA, cheap version

- **Still:** proportions within ~5% (real bottle 4.13–4.22x taller than wide), cap and collar right, no stray text,
  no face.
- **Clip:** one contact sheet (`ffmpeg ... fps=4,scale=180:-1,tile=8x3`). Score it on the scorecard in
  `reference/ai-video-qa.md` only for a keeper.
- Images for checking: at most 800 px wide, one combined sheet per check.

## Post toolbox

- **Edits:** frame-exact edit (`ads/spraymax/cinematic-12s-ocean/edit_ad2.py`).
- **Match a shot to the next one's colour** (one fixed Lab curve, no masks): `ads/samsung-spec/fold8-ultra-12s/grade_logo_shot.py`.
- **Spec supers:** `ads/samsung-spec/fold8-ultra-12s/hud_overlay.py`.
- **Finish:** grade, grain, end card, size (`ads/spraymax/cinematic-12s/finish_film.py --no-card | --card x,y,w,scrim --size`).
- **End-card overlay:** `ads/spraymax/cinematic-12s-ocean/endcard/make_endcard_overlay.py`.
- **Motion on a still** (push-in, light sweep, glint, dust): `ads/spraymax/shelf-still/animate_shelf.py`.
- **One garbled line on a clip:** `ads/spraymax/cinematic-12s/label_lock.py`.
