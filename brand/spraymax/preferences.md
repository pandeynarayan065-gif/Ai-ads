# Spraymax: Narayan's standing preferences

What Narayan has asked for, approved and rejected across the cinematic-ad sessions (Oct–Nov 2026). Read this before
any Spraymax video or image work, so a fresh session starts where the last one ended. Add to it when he gives a new
standing rule.

## Look and content

- **Ultra-real and premium, never "AI slop".** Every shot must read as real footage (playbook rule 1).
- **The real bottle, 1:1.** Real shape and proportions, ribbed collar, clear overcap, the real label. No invented
  claims anywhere, including text a model makes up on a label (e.g. "100% ...", "98% ...").
- **Faceless.** Hands, boots, a silhouette or the back of a body are fine; never a face.
- **Blue, not purple.** The partner pushed back on purple ("Purple kyu he colour scheme"); the cinematic ads went
  Spraymax blue and the shelf still too ("go blue"). Ask before using purple.
- **9:16, 1080x1920**, plus a 4K (2160x3840) master when it matters.
- Style references he likes: the Higgsfield "Ex Nihilo" blue perfume film (hard cuts, perfume grammar), the
  Giorgio Armani ocean ad (bottle falling into the sea, underwater, wreck, sunset), GoPro POV at night.

## Video

- **Video model: Seedance 2.5 only** ("Only use seedance 2.5 dude"). Stills: Nano Banana Pro (Veo is video only).
- **No slow-motion or frozen endings.** "The endshot is stupid and lasts too long": end shots run in real time and stay
  short. A hero end card is ~1.75 s of real footage with the lockup fading in.
- **End cards only when asked.** He has asked for visuals-only cuts ("Just give 12s worth of cinematic visuals").
- **Keep every shot he has approved** in a re-cut unless he says drop it ("why did you remove the dark rock shot").
- **Label fixes on moving shots must not look pasted.** He rejected a full label replacement on a moving clip
  ("looks slapped on", "it lowk morphs and the lighting is distinguishable", "u lowk ruined it more than the
  original"). Prefer Seedance's own label over a fix that reads as a sticker. On stills, replacing only the garbled
  small lines with the real ones worked (`ads/spraymax/shelf-still/fix_labels.py`).
- When he says **"stop"**, stop at once: end the running work and change nothing more.
- **Edits must hold continuity.** A cut between two shots of the same object must match in colour and finish; he
  calls a mismatch "sloppy" ("Cc the chrome shot to make it look like the 1st phone": "Cc" = colour-correct). One
  fixed grade per shot, no masks: `ads/samsung-spec/fold8-ultra-12s/grade_logo_shot.py`.

## On-screen text (spec supers, HUD)

- **Clean, never "slop".** He rejected a busy HUD (dark boxes, scrambled glyphs, mono + sans fonts, shot numbers,
  brackets, ticks, a new position every shot). What works: one typeface (Inter), one baseline and margin, a hairline
  that draws out, the label and the value wiping on, a soft shadow instead of a box, and only on shots long enough to
  read (>= ~0.6 s, or one super over two short shots). `ads/samsung-spec/fold8-ultra-12s/hud_overlay.py`.
- Every number from the brand's official page; no comparative claims about rivals.

## End-card lockup

White Spraymax logo, "BORN IN HIMACHAL", then "spraymax.in", animated (blur-in logo, tracking-in tagline, URL rise):
`ads/spraymax/cinematic-12s-ocean/endcard/make_endcard_overlay.py`. On a bright sky, add a soft top scrim.

## Money

- kie credits are scarce: show the exact prompt and cost, and wait for his OK before `--yes` (CLAUDE.md).
- Free first: Real-ESRGAN for upscales (`scripts/esrgan_upscale.py`), post fixes, re-cuts of existing takes.
