# AI Product Video Playbook

The repeatable way to make AI product shots for ads in this repo. Use `/shot` to run it.
It is built from Google's and ByteDance's own prompt guides, published breakdowns from agencies and creators,
and what failed or worked on our Spraymax shoots. Sources are linked at the bottom and in
`reference/ai-video-examples.md`. That file has verbatim prompts from real campaigns.

Files that go with it:
- `ads/_shot-template.md`: the shot card. Fill one in per shot before writing any prompt.
- `reference/ai-video-qa.md`: the gates and the scorecard each still and clip must pass.
- `scripts/prompt_lint.py`: checks a prompt against the rules below. Run it before every dry run.
- `brand/<brand>/product-lock.md`: the product's fixed description, reference roles and known AI errors.
- `ads/<brand>/prompt-log.md`: every take, its verdict and the rule it taught us.

---

## 1. Why our earlier prompts underdelivered

`scripts/prompt_lint.py` run over our Spraymax prompts (details in `ads/spraymax/prompt-log.md`):

1. **We re-described the whole picture in image-to-video.** Our first-frame motion prompts ran 330–410 words
   and restated the bottle, label, light and set. Google's guidance for image-to-video is "prompt for motion
   only". Re-describing the subject, background or lighting "confuses the model and leads to poor results".
   Now: 40–100 words covering the camera, the one thing that moves, and the sound. Call the product "the bottle".
2. **We asked for magic.** Zero-g drops and a sea turning into mountains ("Both lowk ass bro"). No crew could
   film them, so they read as CGI. Every shot the user kept was a real event: wind, a dropped bottle, a wave, a
   splash, snow melting. Now: **the real-crew test** (section 2, rule 1).
3. **We asked the models for text.** Every model garbled the small label lines. We fixed them in post anyway.
   Now: never ask a model to write words. The label comes from the reference or first frame and is locked in post.
4. **Stills had no scale anchors.** The ocean bottle came out 23–27 cm tall next to a hand, and the studio
   mockup was squat. We caught both only after spending video credits on them. Now: give real size against a
   hand or head in the still prompt, and pass **still QA** before any animation.
5. **One take per shot, judged by feel.** Pros report about 20 generations per usable clip (Kalshi: 300–400
   generations for 15 clips). We can do far fewer because we fix in post, but only if we plan for 2–3 takes and
   score them against written pass criteria.
6. **Stacked camera moves and actions.** "Push in while rising", "then… then… then". Veo often ignored the
   camera entirely (hero v1 moved 2–3%). Now: one camera move, named first, and one action per clip.

## 2. The ten rules

1. **Real-crew test.** Every shot must be something a real crew could film in a day: a real camera, real
   water, real wind, the real bottle. If it needs VFX to exist, redesign it.
2. **One shot = one camera move + one action + one physical cause.** Split anything else into separate shots.
3. **Still first, then animate.** Product or person shots start from a checked keyframe still. Pure
   environment shots (ridge, sea, salt macro) can go straight to text-to-video.
4. **Image-to-video prompts describe motion only:** camera, what moves, sound. Not what's already in the frame.
5. **The product is described once, in one fixed block** (`brand/<brand>/product-lock.md`), used word for word
   in stills and reference-video prompts. Don't rename "the slim white bottle" as "the cylindrical container".
6. **No words from the model.** No labels, supers, CTAs or end cards. Those are done in post (label lock,
   `end_screen.py`).
7. **Keep the label side calm.** No orbits past ~30°, no full spins, no hands sliding over the label, no thrown
   or tumbling product, and no new reflections. These are what break lettering and shape.
8. **Name the camera, lens, light source and materials.** Never stack hype words ("8K, masterpiece,
   hyper-realistic, 3D render").
9. **Write pass criteria before generating.** Score every take blind on the scorecard. Log failures with
   timestamps.
10. **Spend in order: cheapest check first.** Lint (free) → dry run (free) → still (18 cr) → still QA →
    clip (65+ cr). The user approves each exact prompt before `--yes`.

## 3. Pipeline

| # | Step | Output | Gate |
|---|---|---|---|
| 0 | **Edit plan**: music, beat map, shot list. Each shot has a job (hook, product truth, use, texture, payoff) and an on-screen length (usually 0.6–1.5 s in a 15 s reel). | `ads/<brand>/<campaign>/edit-plan.md` | Every shot passes the real-crew test |
| 1 | **Shot card** per shot | `shots/<nn>-<slug>.md` | All fields filled, pass criteria written |
| 2 | **Keyframe still** (Nano Banana Pro + real product refs) | `prompt-<nn>-still.md`, `images/` | `prompt_lint.py` → dry run → user OK |
| 3 | **Still QA**: proportions, scale, label side, details, light, faces | QA notes on the card | Pass `ai-video-qa.md` gate 2 |
| 4 | **Fix the still in post**: label lock, cleanup, exact 1080x1920 JPEG | `images/<nn>-first.jpg` | Overlay vs real product |
| 5 | **Motion prompt** (template below) | `motion-<nn>.md` | `prompt_lint.py` → dry run → user OK |
| 6 | **Generate** 1 take, score it, decide on take 2 | `clips/` | Scorecard ≥ 14/18, no zeros |
| 7 | **Fix the clip in post**: label lock, cap, sky, push-in, sharpening | `clips/<nn>-final.mp4` | Frame-by-frame scrub |
| 8 | **Edit**: cut on beats, take only the best 1–3 s of each clip, real SFX, end card | `edit/` | Watch on a phone, sound on and off |
| 9 | **Log** the verdict and lesson | `ads/<brand>/prompt-log.md` | |

We only use 1–3 s of each 8 s clip. Judge a take by its best 2 seconds, not by the whole clip.

## 4. Which model for which job

| Job | Model (provider) | Mode | Cost | Notes |
|---|---|---|---|---|
| Keyframe still, product in a scene | Nano Banana Pro (kie) | image + up to 8 refs | 18 cr ($0.09) at 2K | Best at keeping a product from refs; edits well |
| Fix a still: scale, pose, end frame | Nano Banana Pro edit (kie) | the still as input | 18 cr | "Edit, don't re-roll": one change per edit |
| Animate a checked still | Veo 3.1 Fast (kie) | first frame | 65 cr ($0.33) / 8 s 1080p | Good physics and water; makes audio; tends to leave the camera still and "interpret" (adds water nobody asked for) |
| Environment, no product | Veo 3.1 Fast (kie) | text-to-video | 65 cr | Ridge, salt and sea shots all came out usable |
| Product from photos, no still | Veo 3.1 Fast (kie) | reference (1–3 refs, 8 s) | 65 cr | Drop shot. Refs on a plain background; text-only product details drift |
| Literal control, timed beats, product held in a hand | Seedance 2.5 (Segmind or kie) | references **or** first frame (not both) | Segmind 8 s: $1.91 at 720p, $4.70 at 1080p. kie: 63 cr/s at 720p (~$2.52 / 8 s) | "More literal" than Veo; holds bottle shape, label geometry and colour in hand. Draft at 480p first. No script yet: needs `SEGMIND_API_KEY` in the environment settings |

Use Veo 3.1 Fast for cheap single-moment shots. Use Seedance 2.5 when the product must stay exactly put in a
hand, or the shot needs timed beats.

## 5. Prompt templates

Fill the `[slots]`. Copy the product block from `brand/<brand>/product-lock.md`. Run `scripts/prompt_lint.py`
on the file before the dry run.

### 5.1 Keyframe still: Nano Banana Pro with references (`prompt-<nn>-still.md`)

Google's product template plus reference roles. Write it as prose, about 120–250 words.

```
Create a vertical 9:16 [unretouched photo / frame from handheld phone footage / studio product photograph]
for a [brand category] ad. Image 1 is the real [product] from the front, image 2 [its pump from the side],
image 3 [the flat label]. Take the bottle from image 1 exactly as it is: [PRODUCT LOCK BLOCK].

[Subject + action in one or two sentences, e.g. "A man seen only from behind holds the bottle beside his
ear, about to spray his hair; his face is turned away and never visible."]

[Place + context in one or two sentences.]

Scale: the bottle is [14 cm] tall, about [the length of his hand from wrist to fingertip]; [it sits a hand's
width from his hair, level with his ear, not closer to the camera than his head].

Light: [named source and direction, e.g. "hard, cold sunlight from the upper left, behind him, rims his hair
and the left edge of the bottle"]. True daylight colour.

Camera: [shot on / lens / height / distance, e.g. "phone wide lens just behind his right shoulder, slightly
below head height"]. [Focus]. Fine natural grain, real-world imperfections. The bottle has the same grain,
sharpness and contrast as everything else in the frame.

Ensure the bottle's shape, proportions, cap, collar and label remain completely unchanged from image 1.
```

Rules:
- Pick the reference photo whose angle matches the shot. Don't ask for a new angle and "unchanged" in the
  same prompt; the two pull against each other.
- At most ~8 words of quoted text in the whole prompt. The label is locked in post anyway.
- One change per edit when fixing a still: "Using the provided image, change only [X]. Keep everything else
  exactly the same, preserving the original style, lighting and composition."
- Always pass `--aspect 9:16` as well as writing it in the prompt. With several refs, the model may copy the
  last ref's aspect.

### 5.2 End frame for first/last-frame shots: Nano Banana Pro edit

```
Take this exact picture as the base. Keep the exact same [product], framing, camera angle, lighting and
background. Only change: [one or two things, e.g. "the water around the base is now a high splash crown at
the height of the label"]. Do not change anything else.
```

### 5.3 Motion from a first frame: Veo 3.1 (`motion-<nn>.md`)

40–100 words. Order: camera, action with its cause, what stays still, sound.

```
[Shot type / rig], single continuous shot: [ONE camera move with speed and end point, or "locked-off"].
[The one thing that moves, with its physical cause and timing, e.g. "At one second his index finger presses
the pump once; a short burst of fine mist shoots sideways into his hair and the wind carries it off."]
[What stays fixed, e.g. "The bottle stays raised beside his head, label to camera; his face stays turned
to the sea."] [Speed: real-time / slow motion, shot at 240 fps.]
SFX: [specific sounds]. No music, no voices.
```

- Say "the bottle", "the man", "the salt". Never restate colours, materials or label text.
- Veo tends to keep the camera static. Make the move the first words. If it still doesn't move, use
  `push_in.py` in post (we did this for zero-g and tethys).
- Dialogue in colon form: `He says: ...`. Never quoted.
- kie quirk: send the first frame as an **exact 1080x1920 JPEG**. A 1536x2752 PNG gave three uncharged 500
  errors.

### 5.4 Video from references, no first frame: Veo 3.1 ingredients

Up to 3 refs on plain backgrounds, 8 s only. Describe the whole scene. Use the product block. 120–200 words.

```
Using the provided images of the [product] (image 1 front, image 2 side, image 3 label), create [shot type,
rig, lens]: [scene in one sentence]. [The one action and its cause.] [Camera: one move.] The [product]
stays exactly as in the images: [PRODUCT LOCK BLOCK, short form]. [Light: named source.] [Look: true colour,
fine grain, real physics.]
SFX: [...]. No music, no voices.
```

### 5.5 Seedance 2.5: four blocks (`motion-<nn>-seedance.md`)

From ByteDance's official 2.5 guide. Use timestamps in whole seconds with no gaps. Seedance **2.0** ignores
timestamps, so write "Shot 1: … Shot 2: …" for it. One camera move per shot. 60–100 words per shot.

```
Image 1 is the real [product] from the front: use it for the exact shape, colours and label. Image 2 is
[the pump from the side]: use it for the pump. Image 3 is [a scene/light reference]: use it only for the
lighting. Define the [2–3 stable features, e.g. "slim white bottle with the clear overcap and the vertical
indigo wordmark"] in Image 1 as <Subject 1>.

[One-sentence summary: Subject + Location + Event + Style + Camera movement.]

0-3 seconds: [framing, e.g. close-up, eye level, locked-off camera]. [Action.]
3-6 seconds: [framing + one move]. [Action.]
6-8 seconds: [framing]. [Action / end on the product, label to camera.]

Throughout: <Subject 1> keeps its exact shape, size, label and colours from Image 1; no new reflections;
neutral white balance, fine film grain, real physics. Keep it subtitle-free. No other logos. No BGM; only
[action sounds].
```

- `first_frame` and reference images can't be combined in one request. For an exact start, use
  first-frame mode with a motion-only prompt (as in 5.3) instead.
- Water, wave or echo words in the sound line cause bubbling or whistling audio. Ask for no BGM and add water
  SFX in post.
- Downsize refs to the output resolution or smaller, as standard JPEG (`ffmpeg -pix_fmt yuvj420p`).
- 1080p output is 10-bit H.265. Transcode it to 8-bit H.264 before editing.
- Draft at 480p (`draft: true`). The 1080p final reuses the draft's prompt, refs and seed. Draft IDs stay valid
  for 7 days.

## 6. Shot recipes: what to ask for

Risk = how often the shot comes back unusable.

| Shot | Risk | Camera | What moves | Avoid |
|---|---|---|---|---|
| **Hero packshot** | Low | Slow push-in or a lateral truck of 15° or less, motion-control | One practical event: water splashes up round the base, a light sweeps across, droplets bead | Orbits, spins, product moving, "3D render" |
| **Macro texture** (salt, beads, mist) | Low | Locked-off or very slow push, 100 mm macro | One natural process: snow melts, a drop lands, mist drifts | Many processes at once |
| **Liquid / splash** | Medium | Locked-off, "shot at 240 fps, played back at normal speed" | Real cause: bottle dropped into a tank, water poured over it | Water passing through the product, bending plastic, tumbling |
| **Product in use** (spray into hair) | High | Handheld, holds its distance, behind the shoulder | One press, mist sideways into hair, wind takes it | No still first, hand over the label, bottle held up "to camera", nozzle at the sky |
| **Hair / lifestyle**, faceless | Medium | Handheld from behind or the side, or a slow push | Wind or a gust in the hair, a helmet off, a hand through the hair | Turning toward camera (check every frame), before/after stories |
| **Environment** (ridge, sea, salt) | Low | One move: helicopter drift, slow push, locked-off | Wind, spindrift, waves | Asking for an exact rig (Veo made a rope-mate view, not a helicopter) |
| **Transition / match cut** | Medium | First + last frame, same framing and light | One change between the two frames | Different crop or light between the frames (it morphs). Often cheaper as an edit cut |
| **End card / text** | n/a | Never AI | n/a | Made in post (`end_screen.py`) |

## 7. Vocabulary

**Camera moves** (pick one): push-in, pull back, truck left/right, pan, tilt up/down, crane up, orbit/arc
(small), handheld follow, locked-off. For anything niche, write the term plus what it does ("rack focus: the
focus shifts from the salt to the bottle").

**Rigs and lenses that ground the look:**
- "motion-control camera rig", "handheld phone footage", "helicopter aerial", "tripod";
- "100 mm macro lens", "35 mm lens at f/2.8", "phone wide lens";
- "shot at 240 fps, played back at normal speed".

**Light:** name the source and its side ("soft key from the front left, hard rim from behind right", "low
hard sun from the side", "overcast daylight"). Also say "true colour, no golden tint". Models drift to a warm
golden grade.

**Words that help:**
- a named camera or film ("shot on ARRI Alexa 35", "Kodak Portra 400 look"), "fine film grain";
- "real-world imperfections", "slight motion softness";
- specific materials ("semi-matte off-white plastic", "frosted polypropylene cap");
- "neutral white balance", "visible skin texture, no smoothing";
- "no new reflections", "real physics, not CGI".

**Words that hurt:**
- "8K", "masterpiece", "best quality", "hyper-realistic", "ultra-detailed";
- "3D render", "CGI", "Octane", "award-winning", "stunning", "epic";
- vague energy words ("dynamic", "cinematic angles");
- any unspecified material, which defaults to gloss.

**Faceless (brand rule):** "seen only from behind; we see the back of his head, his ear and his hair, never
his face; he never turns toward the camera". Or crop to the hands.

## 8. Sound

- Veo's audio is a placeholder. The edit uses the music plus a few chosen SFX taken from the clips: the
  splash, the wave, the pump hiss.
- Always say what you want to hear: `SFX: ...` plus "no music, no voices". If you say nothing, the model adds
  a car-advert score.
- In Seedance, don't put water words in the sound line (see 5.5).

## 9. Fix toolbox (post)

| Problem | Tool |
|---|---|
| Label garbled on a still | `scripts/label_lock_still.py` |
| Label garbled, bottle upright or moving in water | `scripts/label_lock_upright.py` (`--track-flow` for optical-flow tracking) |
| Label garbled, small bottle in a hand, needs real light and taper | `scripts/label_lock_handheld.py` |
| Wrapping flat label art onto a cylinder | `scripts/label_wrap.py` |
| Milky cap should be clear | `ads/spraymax/studio-hero/clear_cap.py` |
| Small label lines garbled while tracking | `ads/spraymax/studio-hero/fix_text_v2.py` |
| Streaks or artifacts in the sky | `scripts/clean_sky.py` |
| Sea colour or grade | `scripts/sea_grade.py` |
| Camera didn't move | `ads/spraymax/studio-hero/push_in.py` |
| Soft shots, 60 fps duplicate frames | `ads/spraymax/k2-15s/enhance_export.py` |
| Beat-cut edit with SFX mix | `ads/spraymax/k2-15s/edit_k2_15s.py` |
| End card | `ads/spraymax/k2-15s/end_screen.py` |

The label lock covers the bottle's exact wording. Fix the shape, the scale, faces and motion with a new take
or a still edit. Post can't fix them.

## 10. Sources

**Official:**
- Veo 3.1 prompting guide (Google Cloud): https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-veo-3-1
- Vertex video prompt guide: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/video/video-gen-prompt-guide
- Vertex image-to-video ("prompt for motion only"): https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/generate-videos-from-an-image
- Vertex video best practices: https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/best-practice
- Gemini API Veo docs: https://ai.google.dev/gemini-api/docs/veo
- Nano Banana image generation docs: https://ai.google.dev/gemini-api/docs/image-generation
- Nano Banana prompting guide (Google Cloud): https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-nano-banana
- Nano Banana Pro prompting tips: https://blog.google/products-and-platforms/products/gemini/prompting-tips-nano-banana-pro/
- Seedance 2.5 prompt guide (BytePlus): https://docs.byteplus.com/en/docs/ModelArk/2607689
- Seedance 2.0 prompt guide (BytePlus): https://docs.byteplus.com/en/docs/modelark/seedance-2-0-prompt-guide

**Practitioners:**
- FOOH TirTir spec ad: https://www.fooh.com/blog/tirtir-murakami-ai-spec-ad
- FOOH SKIMS spec ad: https://www.fooh.com/blog/skims-toothpaste-ai-ad
- FOOH Kaufland hybrid campaign: https://www.fooh.com/blog/kaufland-ice-ice-baby-hybrid-ai-campaign
- Masonry model test for product ads: https://masonry.so/blog/best-ai-video-model-for-product-ads
- astorie, Seedance 2.5 vs Veo 3.1: https://astorie.ai/blog/seedance-2-5-vs-veo-3-1
- hermoso, Veo vs Seedance vs Kling: https://hermoso.ai/blog/veo-vs-seedance-vs-kling/
- hermoso, why AI ads look fake: https://hermoso.ai/blog/why-ai-ads-look-fake
- fal Seedance prompting guide: https://fal.ai/learn/tools/seedance-2-0-prompting-guide
- Higgsfield on prompt mistakes: https://higgsfield.ai/blog/ai-video-prompt-mistakes
- Kalshi NBA Finals ad: https://getcoai.com/news/kalshis-nba-finals-ad-costs-just-2k-using-googles-ai-video-tool/
