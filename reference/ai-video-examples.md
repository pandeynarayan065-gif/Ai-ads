# AI Product Ad Prompts: real examples

Part A has verbatim prompts from official guides and published campaigns. Each has its source link and what
to take from it. Part B has our own Spraymax shots rewritten under `reference/ai-video-playbook.md`; all of
them pass `scripts/prompt_lint.py`.

"Verbatim" means copied exactly as the source printed it. Some sources mark their own excerpts with "…".

---

## Part A: from the source

### Image-to-video product lock (Kling 2.6, passed a model test; Kling O3 failed by inventing side copy)

> Animate the supplied fictional NORTHLINE VITAMIN C 30 ML source as a restrained ecommerce product-ad loop. The
> bottle remains upright, centered, stationary, and completely visible while the camera makes one very slow
> subtle push-in with a small clockwise parallax move. Preserve exactly one bottle; the clear cylindrical body
> and cap; silver stepped pump and centered nozzle; orange liquid color and level; white rectangular label;
> exact NORTHLINE, VITAMIN C, and 30 ML text; proportions, edges, reflections, shadow, and light-gray studio
> background. Keep the front label readable throughout. Add no hand, person, prop, ingredient, droplet,
> splash, mist, bubble, extra text, logo, claim, product part, cap movement, dispensing, liquid movement, cut,
> transition, or scene change. No audio. Treat the result as a review candidate, not factual primary product
> footage.

Source: https://masonry.so/blog/best-ai-video-model-for-product-ads

**Take from it:** one slow camera move, a full "preserve" list, and an explicit "add no…" list. The model that
moved more invented copy on the label side.

### Cosmetic compact reveal (FOOH spec ad, Kling 3.0)

> Luxury beauty product film of the exact referenced red TIRTIR cushion compact with Murakami-inspired
> artwork. The compact starts fully closed, standing upright and front-facing. Then the lid slowly flips open
> smoothly on its bottom hinge, revealing the cushion foundation inside. Keep the exact same product design,
> shape, glossy red material, logo placement, artwork, proportions, and camera angle as the reference images.
> No redesign, no deformation, no extra elements. Soft premium studio lighting, realistic reflections, precise
> hinge motion, elegant controlled opening, high-end skincare campaign aesthetic, hyper-realistic. Static
> camera, only the compact moves.

Source: https://www.fooh.com/blog/tirtir-murakami-ai-spec-ad. Their other motion prompts in the same ad were
just "slow zoom in" and "cinematic zoom-out, natural movement."

**Take from it:** one mechanical action (a hinge), a lock clause, and "static camera, only the product moves".

### End frame made by editing the start frame (FOOH SKIMS, Nano Banana Pro)

> Take this exact picture as the base. Keep the exact same design, typography, layout, lighting, camera
> angle, and background. Only change: Add two more identical SKIMS tubes so there are 3 total. Make sure the
> original tube stays in the middle, perfectly centered… Do not change anything else about the design, type,
> logo placement, micro text, graphics, or materials.

Then the first-to-last-frame motion prompt (Kling 3.0):

> Start with a tight framing on the center tube. Fast cinematic push-in while the camera slightly moves from
> right to left, stabilized, premium product-commercial style. The center tube performs a clean slow 360°
> rotation on its vertical axis while staying perfectly centered… They settle into an evenly spaced lineup of
> three tubes facing forward. Keep the same lighting, background, design and typography. No extra objects.

Source: https://www.fooh.com/blog/skims-toothpaste-ai-ad

**Take from it:** "Take this exact picture as the base… Only change:" is how to make a last frame that won't
morph. (A full 360° spin works for a plain tube. Our wrap-around label would break.)

### Google's product photo template (Nano Banana)

> A high-resolution, studio-lit product photograph of a minimalist ceramic coffee mug in matte black,
> presented on a polished concrete surface. The lighting is a three-point softbox setup designed to create
> soft, diffused highlights and eliminate harsh shadows. The camera angle is a slightly elevated 45-degree
> shot to showcase its clean lines. Ultra-realistic, with sharp focus on the steam rising from the coffee.
> Square image.

Source: https://developers.googleblog.com/en/how-to-prompt-gemini-2-5-flash-image-generation-for-the-best-results/

**Take from it:** the slot order: product, surface, named light setup and its purpose, angle and why, focus
point, aspect.

### Keeping one part unchanged during an edit (Nano Banana, official)

> Take the first image of the woman with brown hair, blue eyes, and a neutral expression. Add the logo from
> the second image onto her black t-shirt. Ensure the woman's face and features remain completely unchanged.
> The logo should look like it's naturally printed on the fabric, following the folds of the shirt.

Source: https://ai.google.dev/gemini-api/docs/image-generation

**Take from it:** describe what must survive the edit in detail, then say "remain completely unchanged", and
say how the new element should sit physically.

### Combining two references (Nano Banana, official)

> Create a professional e-commerce fashion photo. Take the blue floral dress from the first image and let the
> woman from the second image wear it. Generate a realistic, full-body shot of the woman wearing the dress,
> with the lighting and shadows adjusted to match the outdoor environment.

Source: https://ai.google.dev/gemini-api/docs/image-generation

**Take from it:** "Take X from the first image… the second image…", plus asking for light and shadows to match
the new scene. That last part is what stops the "pasted sticker" look.

### Localizing a product shot (Nano Banana Pro, official)

> Create a poster ad for a sparkling water called 'Aura Fizz'. The setting is a London street at dusk with
> neon lights. The tagline should be "Taste the Aura". The can design should be minimalist. Make the aspect
> ratio 16:9.

Follow-up turn:

> Localize this concept to a Mexico setting, keep the can exactly the same, making sure to include translation

Source: https://deepmind.google/models/gemini-image/pro/

**Take from it:** change the scene in a follow-up edit instead of re-rolling from scratch.

### Tactile action with sound (Veo, official)

> A handheld shot follows a wok as it's expertly flicked, sending vibrant, sizzling vegetables tumbling over
> themselves in a flash of motion and steam. Audio: a metallic clank and a sharp whoosh.

Source: https://deepmind.google/models/veo/

**Take from it:** camera, one physical action, and two concrete sounds. That's the whole prompt.

### Macro liquid (Veo, official)

> An extreme close-up of a single, glistening drop of rain as it lands on the petal of a vibrant red rose,
> causing the petal to tremble slightly

Source: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/video/video-gen-prompt-guide

**Take from it:** one event and its physical consequence ("causing the petal to tremble").

### Google's prompt anatomy, annotated (Veo, official)

> Close up shot (composition) of melting icicles (subject) on a frozen rock wall (context) with cool blue tones
> (ambiance), zoomed in (camera motion) maintaining close-up detail of water drips (action).

Source: https://ai.google.dev/gemini-api/docs/veo

### Product reference plus a negative prompt (Veo, Google cookbook)

> A caricatural commercial video for this backpack. The actor puts on the backpack, jumps on his motorbike
> and starts off with a bang and an epic music

Negative prompt: `ugly, low quality, static, weird physics`

Source: https://github.com/google-gemini/cookbook/blob/main/quickstarts/Get_started_Veo.ipynb

**Take from it:** in Veo's negative field, list nouns ("static, weird physics"), not "no …".

### Perfume on wet marble (fal ran it on both Seedance 2.0 and Veo 3.1)

> A matte black perfume bottle sits on a slab of wet marble. A single drop of water falls onto the marble
> surface in slow motion, sending a tiny ripple outward. Camera pushes in tight on the bottle's engraved logo
> as golden light sweeps across the glass. The sharp tap of the water drop hitting stone, then silence.

Source: https://fal.ai/learn/tools/seedance-2-0-vs-veo-3-1

**Take from it:** the hero-packshot recipe: still product, one small water event, one push-in, one light move.

### Liquid hero shot (fal, Seedance 2.0)

> A hero spot for a canned sparkling grapefruit soda. The chilled can sits on a wet black stone slab, beads of
> condensation sliding down the aluminium, then a hand enters frame and pops the tab with a sharp hiss as a
> fine spray lifts off the opening. The camera holds a tight macro on the can and pushes in slowly as the
> spray settles, studio lighting with a hard rim light catching the water droplets and the brushed metal.
> Clean premium product-ad look, cool desaturated grade with the grapefruit-pink label staying vivid. Once the
> can settles, the words "CRACK SOMETHING BRIGHT" fade up in the lower third in a tight modern sans-serif.
> Audio: the crisp pop of the tab, the fizz settling, a single low bass note, no voiceover.

Source: https://fal.ai/learn/tools/seedance-2-0-prompting-guide

**Take from it:** the physical action (a tab pop, then spray) and the named light (a hard rim on droplets and
metal). We'd still put the supers in post, not in the prompt.

### Product in a hand (Seedance 2.0, official)

> In a warm-toned home setting, present the thermos shown in the reference image in a medium shot. Then
> smoothly push the camera into a close-up of the thermos. Next, a hand naturally enters the frame off-screen,
> gently grips the thermos body and picks it up. The camera follows the slight rotating motion of the hand to
> showcase the thermos.

Source: https://docs.byteplus.com/en/docs/modelark/seedance-2-0-prompt-guide

### Turntable loop (Seedance 2.5, official API sample; the same image is the first and last frame)

> A strawberry sandwich cookie slowly completes one full rotation while the camera moves smoothly around it
> and keeps the product centered.

Source: https://docs.byteplus.com/en/docs/modelark/seedance-2-5

### Multi-angle product reference (Seedance 2.0, official; 3 product photos as refs)

> Use the cameras featured in Image 1, Image 2 and Image 3. Replace the original background with a white one,
> and place the cameras on a white table. The camera first focuses on the cameras in close-up, then slowly
> rotates 360° with the cameras as the main subject, clearly displaying the front, sides and back of each
> camera.

Source: https://docs.byteplus.com/en/docs/modelark/seedance-2-0-prompt-guide

**Take from it:** a full rotation is only safe when the refs show every side.

### Before and after: hype words vs camera language (Higgsfield)

- Before: "Very cinematic, emotional, 4k, hyperrealistic, best quality"
- After: "Photoreal, shot on ARRI Alexa 35, natural grain"

Source: https://higgsfield.ai/blog/ai-video-prompt-mistakes

### Mirror-lid fix (Cutout.pro, Seedance 2.0)

> Gentle parallax tilt 12°, clockwise micro-orbit, preserve logo sharp, soft bloom 8%

A mirror lid made the model invent a room in its reflection. Adding "no new reflections" fixed it.

Source: https://www.cutout.pro/learn/blog-seedance-2-0-product-promo-packshot-to-video/

### What not to copy

- "A bottle spins through the air as the camera circles it": rotation plus orbit plus reflections destroys the
  label (veo3gen).
- Hedra's perfume prompt asks for a "high-end 3D render", and the output reads as CGI:
  https://www.hedra.com/examples/gold-perfume-bottle-camera-iris-kling-v3-pro
- A 15-second timed template run at an 8-second setting drops beats (Magic Hour shampoo template).
- Before/after haircare storyboards: ad platforms reject them.
- "$100K JSON ad" prompt packs: no test shows JSON beats clear prose. JSON only helps as an internal checklist
  that you turn into prose.

---

## Part B: our Spraymax shots, rewritten under the rules

### Ocean spray: Veo 3.1 Fast, first frame (was 399 words; now 99)

```
Handheld phone shot from just behind his right shoulder, single continuous shot; the camera holds its
distance. At one second his index finger presses the pump once: a short burst of fine mist shoots sideways
into his hair and the sea wind tears it away. At three seconds a swell explodes against the rocks behind him
and he presses once more. The bottle stays raised beside his head, label to the camera; his face stays turned
to the sea. Real-time speed, slight handheld shake.
SFX: the boom of the wave, wind, two short pump hisses. No music, no voices.
```

### Studio hero: Veo 3.1 Fast, first frame (was 411 words; now 79)

```
Motion-control camera, single continuous shot: a slow, steady push-in from the full bottle to its upper half,
ending on the wordmark. The bottle stays perfectly still. Water splashes up around its base in slow motion,
shot at 240 fps: droplets rise, hang at the top of their arc and fall back, a few drift past the lens, and
beads settle on the bottle. The lighting stays constant.
SFX: a deep splash on stone, droplets pattering. No music, no voices.
```

### Studio hero keyframe: Nano Banana Pro, refs = `bottle-ref-clean.jpg`, `pump-side-real.jpg`

```
Create a vertical 9:16 studio product photograph for a premium men's hair-styling ad. Image 1 is the real
bottle from the front; image 2 is its pump from the side. Take the bottle from image 1 exactly as it is: a slim
100 ml bottle about 14 cm tall, with a rounded shoulder, made of smooth, slightly greyish off-white opaque
plastic with a soft sheen; a matte white, finely ribbed collar; a small smooth white pump head with a tiny
round nozzle hole in its side, under a clear, lightly frosted overcap. A white wrap-around label with the
indigo wordmark running down the bottle and a dark navy ocean-wave photo band at the base, exactly as in
image 1, with bare white plastic showing below the band.

The bottle stands upright on a wet black slate slab resting on a block of raw pink Himalayan salt, against a
dark charcoal backdrop. Scale: the slab is about 20 cm wide, so the bottle stands a little shorter than the
slab is wide.

Light: a soft key light from the front left draws a long highlight down the left of the bottle; a hard rim
light from behind right outlines it; the salt glows warm pink-orange from a light inside it.

Camera: 100 mm lens at f/8, level with the middle of the bottle, front-on. Fine film grain, true colour, the
bottle as sharp and grainy as the slate.

Ensure the bottle's shape, proportions, cap, collar and label remain completely unchanged from image 1.
```

### Studio splash: Seedance 2.5, references (Image 1 `bottle-ref-clean.jpg`, Image 2 `pump-side-real.jpg`, Image 3 a set/light still)

```
Image 1 is the real Spraymax bottle from the front: use it for the exact shape, colours and label. Image 2 is
its pump from the side: use it for the pump head and the ribbed collar. Image 3 is a dark studio with a pink
salt block: use it only for the set and the lighting. Define the slim off-white bottle with the ribbed collar
and the vertical indigo wordmark in Image 1 as <Subject 1>.

<Subject 1> stands on wet black slate on a glowing pink salt block in a dark studio while clear water splashes
around it in slow motion; premium haircare commercial; motion-control push-in.

0-3 seconds: medium close-up, eye level, locked-off camera. A pour of clear water lands on the slate behind
<Subject 1> and splashes up around its base in slow motion; droplets catch the rim light.
3-6 seconds: the camera pushes in slowly to the upper half of <Subject 1>. Droplets fall back and bead on the
bottle; a few drift past the lens.
6-8 seconds: close-up on the wordmark, locked-off. Water beads run slowly down the label.

Throughout: <Subject 1> keeps its exact shape, size, label and colours from Image 1; no new reflections; soft
key light from the front left, hard rim light from behind right; neutral white balance, fine film grain, real
physics. Keep it subtitle-free. No other logos. Sound: no BGM; a low whoosh only.
```

The splash sound is added in the edit, because water words in Seedance's sound line cause audio artifacts.
