---
name: product-video
description: Run when the user wants a product video, a creator-style video of a model talking about, holding or using a product, wants to rebuild a reference video with their own model and product, or uses the /product-video command. Starts from a short concept brief ("model unboxes product", "gym selfie review", "ASMR try-on") or from a reference video the user drops in, which is read for its setting, structure and script, then rebuilt with the brand's model and product and a rewritten script. Generates a multi-shot Seedance 2.5 prompt; only product (and outfit) images are uploaded, and the model is written into the prompt from their characteristics sheet, because Seedance rejects photos of people. Defaults 720p / 15s / 9:16, up to 30s. Output saved under the active brand folder.
---

# Product Video

> **Folders**: before writing anything, create any folder this skill writes to with `mkdir -p` (all paths live under `brands/[brand-name]/`).


One-shot pipeline with two starting points:

- **A concept**: the user gives a short brief and you build the video from it.
- **A reference video**: the user drops in a video that works (theirs, a competitor's, anything). `deconstruct-video.py` reads it into a breakdown (setting, pacing, hook, beats, transcript) and you rebuild it: same setting, same structure, the brand's own model and product, and a rewritten script.

Either way you author a Seedance 2.5 multi-shot prompt using the **Prompt Construction Framework** below, write it to the spec, and `generate-product-video.py` sends it to `bytedance/seedance-2.5/reference-to-video` with the product image (and, for a styled model, the outfit's product images) as references.

**No image of a person is ever uploaded.** Seedance rejects any photoreal face as a possible "likeness of a real person", AI-generated models included, so the model's look is written into the prompt from their characteristics sheet instead.

Defaults: **720p / 15s / 9:16**. All three overridable. **Duration is 4–30 seconds, Seedance 2.5's native limit. Nothing longer is ever made.**

**Prerequisite:** The user needs a model created with `/model` (a headshot, full body and characteristics sheet) and at least one clean product image with no person in it.

Output saved to `./brands/[brand-name]/generation/product-video/[output-name]/`.

---

## Step 1 — Select brand

Scan `./brands/` for brand subfolders.

- **One brand found:** use it. Confirm: "Using brand: [name]"
- **Multiple brands:** list and ask which
- **None:** ask the user for their brand name, slug it (lowercase, hyphens, no spaces) and create `brands/[brand-name]/intelligence/product-images/`. Ask them to drop a few clean product photos (product only, no people) into that folder.

---

## Step 2 — Select model

Ask: "Use a **styled** model (outfit applied) or **unstyled** model (plain casting)?"

**Styled:** list `./brands/[brand]/generation/styled/` and read `style-spec.json` for `model_dir`, `product_images` (the garments) and `notes`. Look at the latest styled image so you can describe the outfit as it was styled. The garment product images go in the spec's `outfit_images`, so Seedance sees the real clothes.

**Unstyled:** list `./brands/[brand]/generation/models/`. You choose an outfit that suits the concept and write it into the prompt.

Either way, read the model's `characteristics.md` (or the `characteristics` field in `model-spec.json`). That sheet is the model's identity in this skill: Step 9 writes it into the prompt. Look at `headshot.png` too, to add anything the sheet misses, but never upload it.

If `styled/` is empty, go straight to **Unstyled**. If there are no models at all: "No models found. Run `/model` first to create one."

---

## Step 3 — Select product

Ask: "Which product should the video feature?"

Check `./brands/[brand]/intelligence/product-images/`. If not found, check `products.json`, try to download from the brand site, or ask the user to drop/paste the image.

---

## Step 4 — Starting point

Ask: "Do you want to start from **a concept** (describe the video in a line or two) or from **a reference video** (drop in a video you want rebuilt with your model and product)?"

- **Concept** → Step 4A.
- **Reference video** → Step 4B. If the user already attached or named a video, skip the question and go straight to 4B.

---

## Step 4A — Concept brief

Ask the user a single open question:

> "Describe the concept in one or two lines — what kind of video do you want? Examples:
> - 'sofia unboxes the magnesium on her desk'
> - 'gym selfie review while warming up'
> - 'ASMR top-down try-on of the running socks'
> - 'kitchen demo of the bottle'
> - 'walking down the street showing off the cap'"

Then Step 5.

---

## Step 4B — Reference video

**Standing rule: the reference is an analysis input, never an asset.** It is read for its setting, structure and words. It is never uploaded to the video model, its person is never copied, and its script is never reused word for word.

### 1. Get the file

Ask the user to drop the video into `brands/[brand]/generation/product-video/uploads/`, or to give its path. Accepted: `.mp4 .mov .m4v .webm .gif`.

- A file elsewhere on their computer: copy it into that uploads folder first, so the breakdown can be saved beside it.
- A link (TikTok, Instagram, an ad library): the skill can't download it. Ask the user to save the video file and drop it in.

### 2. Tell them the length, cost and wait, before anything runs

```bash
python3 .claude/skills/product-video/deconstruct-video.py brands/[brand]/generation/product-video/uploads/[file] --check
```

This spends nothing and needs no key. It prints `length_sec`, `over_limit`, `cost_usd`, `expected_wait_sec`, `ffmpeg` and `saved_breakdown`.

- **Over 30 seconds** (`over_limit: true`, exit code 3): don't read anything yet. Tell the user the length and that product videos max out at 30 seconds, and ask which part to rebuild ("from 0:12 to 0:35", "the first 20 seconds"). Turn the answer into seconds, keep it to 30 or less, and run `--check` again with `--start S --end E`. If `ffmpeg` is `false`, the whole clip is uploaded and only that part is read, and the cost covers the whole clip. The check already accounts for this.
- **Length unknown** (`length_sec: null`, usually a `.webm` on a machine without ffmpeg): ask the user roughly how long it is. If it's over 30 seconds, ask which part, as above.
- **`saved_breakdown` set**: this clip (and section) was read before. Reusing it costs nothing and needs no wait.

Then tell the user, in one message, and wait for a yes:

> "That video is **[length]s**. Reading [it / 0:12–0:35] takes about **[expected wait]** and costs about **$[cost]**. Go ahead?"

### 3. Pick the output name, then read it

Pick the output name now (Step 8's rules, using a short hint from the reference) and read the video into that folder:

```bash
python3 .claude/skills/product-video/deconstruct-video.py brands/[brand]/generation/product-video/uploads/[file] --out brands/[brand]/generation/product-video/[output-name] [--start S --end E]
```

It writes `deconstruction.json` and `deconstruction.md` into the output folder, saves a copy beside the clip, and prints the breakdown. Exit 5 means the read failed: say so in one line and ask the user to describe the reference instead, then carry on from their description. Never invent a breakdown.

### 4. Read it back

Show the user a short read-back and confirm before writing anything:

- the closest format and the length
- the setting you'll keep
- the hook and the number of beats
- the original script in brief, and where the product moment falls

Then the rebuild follows **the three rules**:

1. **Same setting.** Keep the location, the lighting source and direction, the surfaces and the props. The new clip should feel shot in the same place.
2. **The brand's model, never the original person.** Identity comes only from the model's characteristics sheet. Never describe the original person's face, hair or distinguishing features in the prompt. For an unstyled model, choose an outfit that suits the setting and differs from the original's.
3. **Same structure, new words.** Keep the beat count, the rhythm, the talking cadence and where the hook lands. Rewrite every line in the brand's voice (if `brands/[brand]/intelligence/brand-voice.md` exists, read it and respect its banned words and compliance rules). The product slots into the moment the original builds to, as a genuine reaction, never a feature list. If the original had no dialogue, keep it dialogue-free and let sound carry it.

Use the breakdown's format as the format (Step 5) and its setting as the scene paragraph. The script is Path 4 in Step 6. The duration defaults to the read length rounded to a whole second (4–30). Then continue from Step 5.

---

## Step 5 — Confirm format

If the brief (or the breakdown's format) matches one of these common patterns we've tuned for, use it as the scaffold. Otherwise use `custom` and build the prompt from the **Prompt Construction Framework** directly — the framework is format-agnostic and handles any concept.

| Format | When | Structure |
|---|---|---|
| `selfie-review` | Model talks to camera about the product. | iPhone front/back camera mix, 3–4 dialogue beats, casual show-a-friend energy. |
| `unboxing` | "unbox", "reveal", "opens the package", desk shot. | Overhead top-down, hands only, ASMR cardboard/tissue/reveal beats, minimal or no dialogue. |
| `try-on` | Clothing, accessories, "try-on haul", "GRWM". | Full-length mirror, jump cuts between outfit stages, confident poses. |
| `lifestyle-demo` | "gym", "court", "kitchen", "while running" — using product in an environment. | Mix of selfie + action shots, props phone, demonstrates use. |
| `asmr-product` | "ASMR", "tactile", "satisfying", no model dialogue. | Close-up tactile, slow deliberate movements, amplified sound. |
| `custom` | Anything that doesn't fit the above — mukbang, driving vlog, get-ready-with-me variants, dual-creator skits, anything. | Author the prompt directly from the Prompt Construction Framework — pick camera approach, beat structure, and dialogue style based on the concept itself. |

If the brief clearly matches one of the first 5, confirm it. If it doesn't, use `custom` — don't force-fit.

---

## Step 6 — Script

From a reference video, Path 4 is the default: say you'll rewrite the reference's script, and offer Paths 1–3 instead.

From a concept, ask:

> "Three options for the script:
> 1. Paste your own
> 2. I'll write one based on the concept
> 3. I'll write one grounded in the product's landing page (paste the URL)"

- **Path 1** — use verbatim
- **Path 2** — write short fragmented lines (2–4 for 15s, scale with length), casual show-a-friend tone, no marketing speak
- **Path 3** — fetch the URL, extract 1–2 concrete benefits, write the script with those benefits surfaced naturally. If the user can't find a URL, fall back to Path 2
- **Path 4** (reference video) — rewrite the breakdown's transcript line for line: same number of spoken beats, same cadence, new words in the brand's voice, the product at the product moment

For dialogue-free formats (`unboxing`, `asmr-product`, or any concept or reference where the model isn't speaking): script is optional. Many of the best examples have zero dialogue.

---

## Step 7 — Technical params

Ask in one message with defaults (from a reference, the duration default is the read length):

> "Defaults: **15s / 720p / 9:16**. Override any of:
> - Duration (4–30s)
> - Resolution (480p / 720p / 1080p)
> - Aspect ratio (9:16 / 16:9 / 1:1 / 4:3 / 3:4 / 21:9 / auto)"

Never accept more than 30 seconds. If the user asks for longer, say Seedance 2.5 tops out at 30 seconds and ask which part of the idea to keep.

---

## Step 8 — Output name

Slug from model + product + 1–2 word concept hint:
- `sofia-magnesium-desk-asmr`
- `marcus-cap-urban-walk`
- `jade-bottle-kitchen-review`

---

## Step 9 — Generate the prompt

Using the **Prompt Construction Framework** (below), author the full Seedance 2.5 prompt. Show it to the user inline, then write it verbatim to the spec.

Spec format — `brands/[brand]/generation/product-video/[output-name]/product-video-spec.json`:

```json
{
  "output_name": "sofia-magnesium-desk-asmr",
  "brand": "acme",
  "model_type": "styled",
  "model_dir": "brands/acme/generation/models/sofia",
  "styled_dir": "brands/acme/generation/styled/sofia-allblack-athletic",
  "product_image": "brands/acme/intelligence/product-images/ultra-magnesium-01.jpg",
  "outfit_images": ["brands/acme/intelligence/product-images/allblack-athletic-set-01.jpg"],
  "concept": "ASMR top-down unboxing of the magnesium sachets on a wooden desk",
  "format": "unboxing",
  "reference_video": null,
  "reference_section": null,
  "script": "",
  "prompt": "<the full prompt you authored>",
  "duration": 15,
  "resolution": "720p",
  "aspect_ratio": "9:16"
}
```

From a reference video, set `reference_video` to the clip's path, `reference_section` to `[start, end]` in seconds (or `null` for the whole clip), and `concept` to a one-line summary of the rebuild. Both fields are a record only: the script never uploads the reference.

The `format` field is freeform — use one of the archetype names if it fits, or any short descriptor (`custom`, `mukbang-review`, `driving-vlog`, etc.). It's descriptive metadata; nothing downstream validates it.

For `unstyled`, set `styled_dir: null`, leave out `outfit_images`, and put the outfit description directly in the prompt text. `model_dir` and `styled_dir` are a record only: nothing from them is uploaded.

Product and outfit images must show the product alone, with no person or face in them (a packshot, not a lifestyle shot), or Seedance rejects the request.

---

## Step 10 — Run

Before running, tell the user the cost and wait for a yes:

| Resolution | Cost per second | 15s | 30s |
|---|---|---|---|
| 480p | ~\$0.22 | ~\$3.30 | ~\$6.60 |
| 720p | ~\$0.47 | ~\$7.05 | ~\$14.10 |
| 1080p | ~\$1.05 | ~\$15.75 | ~\$31.50 |

Audio is included. Suggest 480p for a first look at a new idea: same prompt, a fraction of the cost.

```bash
python3 .claude/skills/product-video/generate-product-video.py brands/[brand]/generation/product-video/[output-name]
```

Reference upload order is positional (the script enforces this — drives `@Image1/@Image2/...`): the product image(s) first, then any outfit images.

If the script says Seedance rejected an image as showing a real person, nothing was made and nothing was charged. Swap that product or outfit image for one with no person in it and run again.

---

## Step 11 — Present + iterate

Tell the user the path: `brands/[brand]/generation/product-video/[output-name]/[output-name]_v1.mp4`

Offer:
- **Regenerate** — same spec, new run, auto-increments `_v2.mp4`
- **Adjust prompt** — edit any field in the spec (`concept`, `script`, `prompt`, `duration`, etc.) and regenerate
- **Rewrite prompt** — change the concept/format, I'll author a new prompt
- **Another take on the reference** — same breakdown (no new read, no cost), a different script or setting tweak

Each run auto-increments — previous outputs are never overwritten.

---

# Prompt Construction Framework

Every prompt you author follows this structure. Distilled from working Seedance UGC-style examples and the official Seedance prompting guide.

## Structure (in order)

### (a) Opening style line — one sentence

`Vertical [aspect_ratio] [format] UGC [product category] [activity], shot on iPhone [camera type], [lighting], [energy], casual "[one-line vibe quote]" vibe, real skin tones, no filters, no color grading.`

Examples:
- `Vertical 9:16 selfie-style UGC running-socks review, shot on iPhone front and back camera mix, bright natural daylight, casual "showing a friend my new socks" vibe, real skin tones, no filters.`
- `Vertical 9:16 ASMR unboxing of the magnesium sachets, top-down overhead camera, warm soft natural light from a window on the left, slow deliberate hands-only movements, no filters.`

### (b) Scene paragraph — concrete environment

Specific location, lighting source/direction, surfaces, props in frame. Avoid abstract descriptors. Ground it in a real place.

Good: `A bright living room with warm window light from the left, clean wooden floor, a folded exercise mat behind her, a half-drunk water bottle on the side table.`

Bad: `A nice indoor space with good lighting.`

### (c) Subject + Product paragraph — the model in words, the product by tag

- **The model, from their characteristics sheet:** one or two sentences carrying every identity trait on the sheet — apparent age, sex, ethnicity, skin tone, face shape, eyes, brows, nose, lips, freckles or facial hair, hair colour and style, build. Concrete and specific, the same wording every time this model is used, so they read as the same person across videos.
- **The outfit:** for **styled**, describe the outfit as styled and tag its images — e.g., "She is wearing the set shown in @Image2." For **unstyled**, describe an outfit that suits the concept.
- **The product:** name it briefly and let the reference carry all visual detail — e.g., "She is holding @Image1, the blush stick shown in @Image1."

**Do NOT describe the product's visual appearance** — no colors, no packaging details, no branding text, no finish descriptions. The reference image is the ground truth; adding visual descriptors will conflict with what Seedance sees in the image and produce an off-brand product render.

### (d) Action sequence — multi-shot with explicit timecodes

Break duration into timecoded beats: 2–3 for short clips, 3–5 for 15s, up to 7 for 30s. For 30s: `0–4s / 4–9s / 9–15s / 15–21s / 21–26s / 26–30s`. For 20s: `0–3s / 3–8s / 8–14s / 14–20s`. For 15s: `0–3s / 3–7s / 7–11s / 11–15s`. For 8s: `0–2s / 2–5s / 5–8s`. For 4s: `0–2s / 2–4s`. Any other length: divide it proportionally the same way.

From a reference video, mirror its beats instead: the same count, the same order, and timecodes scaled to the chosen duration.

Each beat must include:
- **Camera angle/movement** — "front camera close-up", "switches to back camera", "overhead top-down", "low angle from the floor", "props phone against the wall, steps back to show full body"
- **Physical action** — what hands/body do with the product
- **Dialogue (in quotes)** if applicable — see dialogue principles
- **Product interaction** — rotate, tilt to catch light, tap, hold up to lens, fill the frame, etc.

Use the working format:
```
0–3s — Hook: [camera] [action]. "[dialogue]"
3–7s — Detail: [camera switch] [action] [product moment]. "[dialogue]"
7–11s — Demo / Demonstration: [camera change] [action]. "[dialogue]"
11–15s — Final: [camera] [pose] [smile/look]. "[closing line]"
```

### (e) Dialogue principles — what makes UGC sound real, not AI-written

- **Fragmented, not polished** — "Okay so —", "Wait. Wait look at this.", "I cannot stop doing this."
- **Genuine reactions over claims** — describe what they see/feel, not why the product is good
- **Self-aware playfulness** — "WHY is there a duck.", "Is this crazy or—"
- **Pauses and repetition** — "Yeah. Yeah this is the one."
- **Showing-a-friend tone, NOT marketing** — never "this product features X benefit"
- **Deadpan close** — "That's it. That's the review.", "You are welcome."
- **2–4 short lines total** for a 15s clip, about double for 30s. Less is more. From a reference, match its line count.
- For unboxing / ASMR formats: dialogue is often zero — sound design carries it.
- Tone matters more than content. Real UGC has hesitation, half-thoughts, breaths.

### (f) Style closing paragraph — aesthetic + negative cues

Aesthetic line: `Authentic UGC / TikTok aesthetic, real skin tones, natural iPhone HDR, slight handheld micro-shake, natural lens distortion, slight exposure shifts.`

Sound:
- If speaking: `Natural voice and room tone, no music, no sound effects beyond ambient.`
- If ASMR: `Crisp amplified ASMR sounds — cardboard tap, sticker peel, tissue rustle, vinyl figure lifted from foam, [other specific sounds]. No music. Pure ASMR sounds only.`

Negatives (always include):
`No text overlays, no filters, no studio lighting, no over-processed look. The phone, camera, and any mirror reflection of a phone or hands holding a phone must never be visible.`

### (g) Reference tags

Place `@Image1` / `@Image2` inline where they're referenced. Products come first, then outfit images. Seedance binds references by position (the first uploaded image is `@Image1`, etc.) — so the tags only need to be consistent throughout the prompt. The Python script handles the upload order automatically based on `model_type`. A reference video is never uploaded, so never write a `@Video` tag.

---

## Reference example 1 — selfie-review (15s, styled model)

```
Vertical 9:16 selfie-style UGC review of the acme running socks, shot on iPhone front and back camera mix, bright natural daylight from a window, casual "showing a friend my new socks" vibe, real skin tones, no filters, no color grading.

A bright living room — warm light from the left, clean wooden floor, an exercise mat folded against the wall behind her, a water bottle on the side table.

She is a 27-year-old woman of South Asian heritage with warm medium-brown skin, an oval face, almond-shaped dark brown eyes, full natural brows, a straight nose, full lips and a few freckles across her nose; long dark brown hair in loose waves with a centre part; slim athletic build. She is wearing the athletic set shown in @Image2. She is holding @Image1, the running socks shown in @Image1.

0–3s — Hook: She holds @Image1 up to the front camera with one hand, the socks filling the vertical frame, her sleeve visible at the edge. She tilts them slowly so the daylight catches the fabric: "Okay, these just arrived and I am obsessed with the colour."

3–7s — Detail: Switches to the back camera. Brings @Image1 close to the lens — the socks fill the frame, the cushioning texture visible. "Look at the cushion on these — it feels insane."

7–11s — Demo: Props the phone against her bag, steps back. Pulls on one sock, flexes her foot, looks up at the camera with a small laugh: "These are actually so comfortable."

11–15s — Final: Picks the phone back up. Holds @Image1 up beside her face on the front camera, smiles directly into the lens: "Yeah. Yeah these are the ones."

Authentic UGC / TikTok aesthetic, real skin tones, natural iPhone HDR, slight handheld micro-shake, natural lens distortion. Natural voice and room tone, no music, no sound effects beyond ambient. No text overlays, no filters, no studio lighting, no over-processed look. The phone, camera, and any mirror reflection of a phone or hands holding a phone must never be visible.
```

## Reference example 2 — unboxing (15s, hands-only, no dialogue)

```
Vertical 9:16 ASMR unboxing of the acme magnesium sachets, top-down overhead camera looking straight down at a light wooden desk surface, warm soft natural light from a window on the left, slow deliberate hands-only movements, no filters, no color grading.

The desk is light wood. Only hands are visible — female hands, short natural nails, sleeves of a soft sage-green knit sweater. A small ceramic plate and a folded white linen napkin sit to the upper right of the frame.

Only her hands and forearms in the sage sweater sleeves appear in frame, no face. The product is @Image1, the magnesium sachet pack shown in @Image1.

0–4s — Box reveal: The sealed magnesium box sits centered on the wooden desk. Fingers tap the lid three times — satisfying hollow cardboard thuds. Both hands grip the lid and lift it straight up slowly, revealing the foil sachets nestled inside.

4–9s — Sachet pull: One hand reaches in and slowly draws out a single magnesium sachet, holds it at center frame, rotates it gently so the foil catches the warm light. The acme wordmark and the magnesium product name face the lens.

9–13s — Pour ritual: The sachet is torn open at the corner (satisfying crisp tear sound), tipped gently over the ceramic plate so a small mound of magnesium powder pours out, then placed beside it.

13–15s — Final: Hands withdraw. Hold the final composition — open box at top of frame, single sachet, small powder mound on the plate, warm light catching the wood grain.

Cozy ASMR unboxing aesthetic for Xiaohongshu / TikTok. Crisp amplified ASMR sounds — cardboard tap, lid lift, foil sachet handled, sachet tear, powder pour, sachet placed on wood. No music. Pure ASMR sounds only. Warm natural daylight. Slow, satisfying, tactile. No text overlays, no filters, no studio lighting. The phone, camera, and any mirror reflection of a phone or hands holding a phone must never be visible.
```

---

## Notes

- **Prompt is the contract** — you author it, write it to the spec, the Python script passes it through verbatim to Seedance 2.5. No Python-side prompt assembly.
- **No person is ever uploaded** — Seedance rejects photoreal faces, AI models included. The characteristics sheet carries identity in the prompt; references are products first, then outfit images.
- **30 seconds is the ceiling** — Seedance 2.5's native limit. The script refuses anything longer, and a longer reference video is always cut to a part the user picks.
- **Defaults: 720p / 15s / 9:16** — the sweet spot for quality and platform fit (~\$7/clip). 480p is the cheap first look.
- **A reference breakdown is reusable** — it's saved beside the clip in `uploads/`, so a second brief from the same video reads nothing and costs nothing.
- **Each brand has its own** `product-video/` subfolder — multiple brands run independently.
- **Editable spec** — power users can edit any field in `product-video-spec.json` (including `prompt`) and re-run the script directly.
