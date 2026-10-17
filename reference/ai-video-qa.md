# AI Video QA: gates and scorecard

Nothing costs credits until gates 0 and 1 pass. No still gets animated until it passes gate 2. No clip goes
into an edit until it scores on gate 3. Record the results on the shot card (`ads/_shot-template.md`).

## Gate 0: concept (before writing a prompt)

- [ ] **Real-crew test:** a real crew could film this in a day, with real water, wind and the real product.
- [ ] One camera move, one action, one physical cause.
- [ ] The shot has a job in the edit (hook, product truth, use, texture or payoff) and a length (0.6–1.5 s).
- [ ] The product is either shown truthfully (right size, right use) or not shown at all.
- [ ] Platform-safe:
  - no before/after;
  - no personal-attribute hooks ("Is your hair thin?");
  - no claims beyond the brand file.
- [ ] Faceless brand: the shot works from behind, from below the eyes, or as hands only.
- [ ] Label is either "must be exact" (plan a post lock) or "not required to read".

## Gate 1: prompt (before the dry run)

- [ ] `python3 scripts/prompt_lint.py <file> [--kind ...] [--faceless]` shows no FAIL. Each warning is fixed or
      has a one-line reason on the card.
- [ ] The product block is copied word for word from `brand/<brand>/product-lock.md` (stills and ref videos only).
- [ ] Every reference image is named with a role ("image 1 is…, use it for…"). It shows the angle the shot needs.
- [ ] Image-to-video: the prompt describes only motion, camera and sound.
- [ ] Credits checked (`kie_generate.py credits`), dry run shown to the user with cost, user approved this exact
      prompt.

## Gate 2: still (before animating; an 18 cr check saves a 65+ cr clip)

Open the still at full size next to the real product photo, scaled to the same body width.

- [ ] **Proportions:** height to width, shoulder, cap and collar within ~5% of the real bottle.
- [ ] **Scale:** the product against a hand or head is believable. A 14 cm bottle is about a hand long. It isn't
      held closer to the lens than the head unless that's intended.
- [ ] **Details the model gets wrong**, from the product-lock list (pump head, ribbed collar, clear cap, wordmark
      direction): note each one and decide how to fix it. Small fixes are done in post; anything bigger needs a
      still edit.
- [ ] **Label side:** faces the camera and isn't covered by fingers. The label's wording will be locked in post.
- [ ] **Light:** one consistent direction on the product, the person and the scene. No golden or yellow cast
      unless asked for. The product has the same grain and sharpness as the rest of the frame (no "sticker" look).
- [ ] **Faces:** none visible (YuNet check plus a look by eye).
- [ ] No stray text, logos, watermarks or lens-flare streaks.
- [ ] Export the first frame as an **exact 1080x1920 JPEG** for Veo on kie.

## Gate 3: clip scorecard (blind, frame by frame)

Scrub the whole clip at full size, frame by frame through spray, splash, turns and occlusion. A check of the
first frame alone misses drift. Score each line **0 / 1 / 2**:

| # | Criterion | 0 = reject | 1 = fixable in post | 2 = good |
|---|---|---|---|---|
| 1 | **Product identity** | Shape, size, cap or collar changes or swells | Small detail off (cap opacity, ribs) | Matches the real product |
| 2 | **Label** | Hands cross it, or it turns away or warps beyond tracking | Garbled but steady (lock in post) | Correct or nearly correct |
| 3 | **Scale & contact** | Product is giant or tiny, or floats without contact or shadow | Slightly off, fixable with a crop | Believable |
| 4 | **Motion physics** | Floaty, magic, wrong direction (e.g. mist going up) | Right but weak or slow | Real weight and cause |
| 5 | **Camera** | Unasked cuts, or a lurch | Static when a move was asked (use `push_in.py`) | The asked move |
| 6 | **Temporal stability** | Parts pop in or out, edges breathe, product morphs | A few bad frames outside the usable range | Clean |
| 7 | **People** | A face visible in the usable range, or broken hands | A face only outside the usable range | Faceless, hands right |
| 8 | **Real look** | Plastic, CGI, glossy stock look | Grade or sharpness fixable | Reads as real footage |
| 9 | **Audio** | Contradicts the picture (and we need it) | Usable after cleanup, or will be replaced | Usable as is |

- **Pass:** no zeros and a total of 14/18 or more. Mark the usable range (e.g. "1.2–3.4 s").
- **Zero on 1, 4, 6 or 7:** reject the take. Re-prompt after reading the failure, don't just re-roll.
- **Log every failure with a timestamp**, e.g. "bottle swells at 1.8 s under the hand", "mist goes up at 1.1 s".
  The log goes on the shot card and in `ads/<brand>/prompt-log.md`.
- **Second take only if** the failure has a clear prompt fix. Change one variable per take.

## Gate 4: edit (before sending)

- [ ] Watched on a phone at full screen, with sound on and with sound off.
- [ ] Every cut lands on the beat. No shot overstays: one idea per 0.6–1.5 s.
- [ ] Reels/TikTok safe zones: nothing important in the bottom ~20% or the right-hand icon strip.
- [ ] Label exact wherever it can be read. End card done in post.
- [ ] No 60 fps duplicate frames (`enhance_export.py`). Loudness levelled.
- [ ] Music rights noted (fine for a portfolio piece; for a paid ad use the platform library or a licence).
