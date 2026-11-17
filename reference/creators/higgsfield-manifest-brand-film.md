# Higgsfield "Manifest" — 68 s brand film, Seedance 2.5 (Higgsfield's own read-only project brief)

**Source:** https://higgsfield.ai/generate?projectId=e3dc6c3d-4374-459f-b051-9f7965a48363&brief=1 (from
@higgsfield.commercials, "Manifest (Brand Film)"), sent by Narayan on 17 Nov 2026. Read with the headless browser
(no login): the brief, every shot prompt, the asset metadata and Higgsfield's cost table.

**What it is:** "You think you're too late? You're right on time." One voice speaks to anyone afraid the moment to
start making things has passed, then follows people who started anyway. Fear is cold, blue and fast (whispers,
racing clock hands, closing doors); the answer is warm and patient (a childhood, a first heartbreak, long nights, a
finished work). Higgsfield appears only "at the point where the tools catch up with the person".

## Facts we can use (measured)

- **Model:** every video shot is Seedance 2.5 on Higgsfield (`job_set_type: seedance_2_5`); stills/elements from
  Soul (text2image_soul_v2) and Seedream 5.0 Pro. Shots delivered at **1080p 4:3 (1440×1080)** and **4K 4:3
  (2880×2160)**; one 720p 16:9. Typical generations: 4–6 s single shots, 10–14 s multi-shot.
- **Higgsfield Seedance 2.5 price (17 Nov 2026, Higgsfield credits per second of output):** 480p 3, 720p 7, 1080p 16,
  4K 28. Seedance 2.5 Flash: 480p 2, 720p 5. Kling upscale of a Seedance clip to 1080p: 4/s. ($ per Higgsfield credit
  depends on the plan [VERIFY].)
- **Workflow:** "Shots were explored as 480p drafts, then regenerated at 1080p and 4K once the action held."
- **Elements:** each recurring person, room and object is a reusable Element (character sheet, location, prop) used
  as a reference token `<<<id>>>`; the Canvas groups cast and locations by role.
- **Prompt assistant:** "GENZILLA 3.2" (Higgsfield's tool) helped write every prompt.

## The prompt method (their words)

> "Each prompt opens with the one thing that must not fail, then fixes the film look, the subject, the light, the
> main action, the camera and a second-by-second timeline, and ends with sound and a list of explicit failure
> conditions. Wording that pulls the model the wrong way is replaced before generation: in a shot full of birds the
> camera 'rises straight upward' because 'crane' is also a bird."

## What the prompts do (patterns, with verbatim lines)

1. **One-job references, said twice.** "<<<id>>> is a photographic STYLE reference only: match its film texture,
   colour separation, optical softness and natural material rendering. The scene and camera movement are defined
   below." / "= the location only" / "= the older son's clothes only" / "@image1 = the angle and composition of shot 1
   only … the reference's colours, g[rade] …" (ignored).
2. **A film-stock look block** instead of quality words: "A real analog 35mm film photograph, shot on a Contax G2
   with Kodak Portra 400 colour negative film pushed one stop and scanned … on a Frontier scanner … coarse organic film
   grain … strongest in the shadows and midtones … milky lifted blacks … red-orange halation … green-cyan cast in the
   shadows … No digital sharpness, no HDR, no noise reduction, no clean CGI surfaces." Night look: "Kodak Vision3 500T".
3. **The camera move is named, profiled and fenced.** "Perform one deliberate DOWNWARD TILT from a nearly stationary
   camera position. The movement is clearly noticeable immediately, then progressively decelerates into a gentle
   settle … the upper tip exits through the top edge, the base rises within the frame … Complete the tilt during the
   first three seconds and let the final second settle … Fixed focal length and camera height. This is a downward tilt,
   not a sideways tracking reveal, push-in, zoom or orbit."
4. **Lenses as field of view + mm:** "63-degree diagonal field of view (35 mm)", "18-degree … (135 mm)".
5. **Exact cut counts:** "Exactly two hard cuts, at 0:03 and 0:07." / "STRICTLY 2 SHOTS, one hard cut at 6.5 s and
   nowhere else." / "Exactly four hard cuts, one every second".
6. **Second-by-second timeline inside one shot** ("0.0–1.3s — REAL-TIME FALL AND VIOLENT BREAKAGE. … 1.3–5.0s —
   SLOW-MOTION REVERSE PLAYBACK."), with the first frame defined ("FIRST FRAME: the clock is already falling fast …
   Start immediately on the final instant of the fall, without a slow hovering descent").
7. **Physics as rules plus explicit failure conditions:** "Everything begins breaking at the ground-contact point,
   never in midair … no melting, disappearing fragments, orbiting debris or magical glow. Never reveal the source or
   destination of the fall." Materials pinned: "hard and brittle, not rubberized or flexible".
8. **People and continuity:** "Exactly three people, three clearly different faces, each person exactly once"; "always
   on the left of frame"; "The faces are the brightest things in every frame. All three shots share one colour and
   grade, so the cuts read as one continuous moment." A match cut is written across two shots of one generation.
9. **Handheld documentary written as a person:** "one real documentary operator holding the camera in his bare hands:
   a constant natural shake, his breathing and footsteps in the frame, quick searching reframes that overshoot and come
   back, the horizon tipping a few degrees and correcting … focus breathing and hunting before it lands".
10. **Stillness stated as "Moving things in this video: zero."** for the painting inserts.
11. **Sound as an exact list:** "SOUND — Exactly this: … No music." Generated sound kept in the mix; music, the two
    titles and the logo are post.
12. **Story first:** an earlier cut "went straight to the makers at work … but the film had no arc"; rebuilt as a hook
    of doubt → a life in five lines → the makers and their endings.

## Adopt / Avoid

**Adopt (now in `reference/seedance-rules.md` and the crew):**
- Open every shot with **the one thing that must not fail**; end with **per-shot failure conditions**.
- **Name the camera move, give its speed profile and what enters/exits frame, and negate the moves it is not.**
- **Exact cut count and times** in the hard-cuts block (we lost a cut in 12 s runs).
- **Scrub words the model can misread** in context (crane → "rises straight upward" near birds; "screen print" vs
  a screen).
- Lenses as field of view + mm when the framing matters; "Moving things: zero" for still inserts.
- **Drafts at 480p, keepers regenerated at 1080p/4K** (kie: `--draft` + `seedance-final`; Higgsfield: regenerate).
- Elements-style reuse: one character/location/prop reference per recurring thing, one job each.

**Avoid / adapt:**
- Their people are full-face characters; our brands are faceless by default. Their reverse-playback clock is a VFX
  event (fine as a brand-film device; for products keep the real-crew test).
- Their 4:3 native frame doesn't fit our 9:16 deliverables; their 35 mm analog look suits brand films more than
  crisp product macros. Choose it per brief.
- Long prompts (their single shots run 600–900 words for 4–6 s). Our multi-shot runs stay under ~8,000 characters.
