# 00 Reverse: refs/ref-video-hoodie-reel-20261114.mp4

Probe: 18.08 s, 720x1280, 24 fps, H.264 + AAC 32 kHz stereo. 5 hard cuts by frame difference (3.62, 6.79, 11.33,
16.08 s; no false cuts). Camera from optical flow on the background. Style reference only: its character is not reused.

## Cut list
| # | t (s) | Framing | Subject | Action | Camera move | Light / palette |
|---|---|---|---|---|---|---|
| 1 | 0.00–3.62 | Low angle from his feet, medium-wide; chair arms loom in the foreground, chest print centred | CG hooded man, hood up, seated in a black tufted leather armchair | Talks, one hand gesture (1.5–2.5 s) | Locked-off (zero flow) | Clear sun, deep blue sky; black leather, black fleece, warm white print |
| 2 | 3.62–6.79 | Wide, eye level, symmetrical; chair centred, sky the top third | Same, small in frame on a concrete rooftop with a low parapet; steep hillside of colourful houses behind, hazed | Hand gesture | Locked-off | Sun from frame left, hard shadows; sky blue, sun-bleached concrete, faded pink/ochre/terracotta town |
| 3 | 6.79–11.33 | Tight face close-up under the hood | The character's face | Speaks to camera | Push-in ~15% in the first 1.5 s, then holds with a slight float | Warm side key from frame right, hood shadow; amber skin on black |
| 4 | 11.33–16.08 | Medium, front, head to thigh | Stands up out of the chair, arms loose; chest print centred and sharp | Rises, then stands still | Tilts up with him, then locked | Same sun and town; the print reads close to the official artwork |
| 5 | 16.08–18.08 | Medium from behind → wide | Back to camera, hood up, skull print centred | Walks away toward the parapet and town | Locked-off, slight pull back | Same; ends in real time, no slow-mo |

**Voice** (faster-whisper small.en): "You'll never make it, says the man who quit after one bad week. He's got opinions
about my art. He's never finished a thing. I've been broke, I've been laughed at, I started over twice. Still here.
You met me at a very artistic time of my life." / second, higher voice (~200 Hz vs ~107 Hz): "That hoodie looks sick,
dude, where'd you get it?" / "Get yours at avrana.co." No product claims (no fabric, fit or price). A low bed runs
under the voice.

## What carries the look
- **Place**: a bare concrete rooftop high above a dense, colourful hillside town in haze. Concrete, sky and town
  frame the black hoodie, and it is the only dark mass in the frame.
- **The throne**: a black tufted leather armchair, centred and shot from below. It reads as status and makes the
  chest print the centre of the image.
- **Locked-off poster frames**: the subject moves (sits, stands, walks away), the camera barely does. Symmetry and
  centred print.
- **Hard clear sun**: deep blue sky, crisp shadows, atmospheric haze for depth.
- **Print order**: front print (seated, standing), then the back print as he walks away. The back reveal is the payoff.
- What makes it read **unreal**: game-cinematic CG (smooth skin, plastic leather, uniform sharpness, perfect sky).
  Shots of 3–4.7 s work only because of the voice. For a 12 s silent film we keep the five setups and cut them into
  nine shots of 1.1–1.8 s, shot as real photography.

## Prompt that would make it (for the Avrana Death & Glory hoodie, black)
Refs: Image 1 = `01-…front-official.jpg`, Image 2 = `02-…back-official.jpg`. Leave Image 3 (worn, a real model) out:
a person in a reference invites their likeness. Seedance 2.5, reference-images mode, 720p, 9:16, 12 s, silent.
Not linted yet (the prompt stage runs `prompt_lint.py --kind seedance --faceless`).

```
Image 1 is Avrana's official product photo of the real Death & Glory hoodie in black, front view. Use Image 1 only for the hoodie's shape, hood, pocket and the white chest print; ignore its white background. Image 2 is Avrana's official photo of the same hoodie, back view. Use Image 2 only for the white antlered skull print on the back; ignore its white background. Define the hoodie from Images 1 and 2 as <Subject 1>. <Subject 1> is identical in every shot.

Product truth: <Subject 1> is a black pullover hoodie with a roomy hood, a front kangaroo pocket, long sleeves with ribbed cuffs and a ribbed hem, in matte black cotton-look fleece. On the chest, centred, an ornate white print: the word Avrana in flowing script inside a symmetrical white filigree frame, about as wide as the chest. On the back, centred between the shoulders, a large white print of an antlered deer skull with spreading antlers, as tall as the upper back. The prints are white and slightly cracked-matte like screen print, exactly as in Images 1 and 2. It is worn by an adult man of average build at true size: the chest print spans about the width of his chest, the hem sits at his hips.

A 12-second vertical film: a man in <Subject 1>, hood up, sits in a black leather armchair on a sunlit concrete rooftop high above a colourful hillside town, stands, turns his back and walks to the edge.

Hard cuts only throughout: every shot is a completely separate camera setup. No transitions, no dissolves, no wipes, no fades, no motion carrying across a cut.

Real photography, inherited by every shot: filmed on an ARRI Alexa 35 with 35 mm and 50 mm cinema lenses, in real time, on a real rooftop in real sun and wind. Real fleece, real leather creases, real concrete dust. Natural film grain, gentle lens falloff; no plastic sheen, no over-sharpening.

Global look: hard clear afternoon sun from high frame left, crisp shadows, deep blue cloudless sky, atmospheric haze softening the distant hillside. Palette: sky blue, matte black, sun-bleached grey concrete, and the town's faded pink, ochre, terracotta and cream. The black hoodie is the darkest mass in every frame. Centred, symmetrical, poster-like compositions with open sky.

Never render: any text, letters, numbers, logos, captions or watermarks anywhere other than the two prints from Images 1 and 2, including on walls, signs, roofs, the armchair and the trousers; graffiti; other brands; drawstrings, a zip or extra logos on the hoodie; a face or any part of a face (the man is seen only from the chin down, from behind, or with the hood hiding his head); hands gesturing at the camera; a warped, resized or redrawn print; extra antler points; visible light fixtures; lens flares; slow motion.

[00:00.0] Low angle from the rooftop floor at his feet: the man in <Subject 1> sits square in a black tufted leather armchair, framed from the chin down, the chest print centred and large, the chair's arms looming in the foreground, deep blue sky above. He settles back into the leather. Camera locked-off.

[00:01.4] Wide, eye level, symmetrical: the black armchair centred on a bare concrete rooftop with a low parapet, the man in <Subject 1> seated, head bowed, the hood pulled low so his head is only a black shape; behind him a steep hillside packed with small faded pink, ochre and cream houses fading into haze, the top third clear sky. A gust drags grit across the concrete. Camera locked-off.

[00:02.8] Close side view from behind his left shoulder: the hood of <Subject 1> in profile against the hazy hillside, sun raking across the matte black fleece, his face completely hidden inside the hood. The hood's edge flutters in the wind. Camera pushes in slowly.

[00:03.9] Medium front, framed from the chin down: the man in <Subject 1> pushes up out of the armchair and stands, the chest print rising into the centre of the frame, his hands staying at his sides. Camera tilts up with him, the top edge staying below his chin.

[00:05.4] Medium front, framed from the chin down to the thighs: he stands still before the armchair, arms loose, the chest print of <Subject 1> centred and sharp in hard sun, the hazy town behind. The wind presses the fleece against his chest. Camera locked-off.

[00:06.7] Close-up of the chest print of <Subject 1> filling the frame width, the white filigree frame and script exactly as in Image 1, sun raking across the cracked-matte print and the fleece. The fabric ripples in the wind. Camera pushes in slowly.

[00:07.9] Close from behind: his back fills the frame, hood up, the white antlered skull of <Subject 1> centred between the shoulders exactly as in Image 2, the sun on the fleece. He rolls his shoulders once. Camera locked-off.

[00:09.1] Wide from behind, low: the man in <Subject 1> walks away from the camera across the concrete toward the parapet, the skull print shrinking, the colourful hillside town ahead in haze. Camera locked-off.

[00:10.5] Wide from behind: he stops at the low parapet and stands looking out over the hillside town, back to camera, hood up, the skull print centred, the upper half of the frame open blue sky. He stands still in real time. Camera pushes in slowly.

Throughout: <Subject 1> keeps its exact shape, proportions, black fleece and both white prints from Images 1 and 2 in every shot; the man never turns toward the camera. Keep it subtitle-free, with no captions and no watermark. No music and no voices.
```

## Load-bearing words
1. **"black tufted leather armchair"** (the throne: status, centring)
2. **"bare concrete rooftop high above a … hillside town … fading into haze"** (the place and its depth)
3. **"hard clear afternoon sun … deep blue cloudless sky"** (the light and palette)
4. **"Low angle from the rooftop floor at his feet … framed from the chin down"** (hero framing that stays faceless)
5. **"Camera locked-off" + "centred, symmetrical, poster-like"** (the reel's still, poster-like frames)

Second tier: "the black hoodie is the darkest mass in every frame"; "walks away from the camera … skull print
shrinking" (the payoff). Filler: lens names, "real concrete dust", the palette list after the first three tones.

## Flags (IP, likeness, Seedance risks)
- **IP / likeness:** the reel's character closely resembles a famous fighting-game hero (spiky black fringe, game-
  cinematic render). Don't reuse it, describe it or name it. Our version is faceless, so the look-alike can't come
  back. The reel's voice is generated speech of unknown origin: don't reuse it. "You met me at a very artistic time
  of my life" riffs on a well-known film line (Fight Club): fine as a meme, not for a client ad without Narayan's OK.
  The artist backstory ("I've been broke… started over twice") presents a made-up person as an Avrana artist: not
  for client work (no fake people posing as customers or creators).
- **Image 3 (worn, official)** has a real model in it, and the face hasn't been checked: keep it out of the
  reference set.
- **Seedance: face leak.** The highest risks are shot 2 (wide, head bowed) and shot 4 (standing up with a tilt).
  Both are trimmable; cut any frame where a face shows.
- **Seedance: fake text.** It is likely on the town (signs, graffiti, shop fronts) and may garble the "Avrana"
  script in shot 6 (the chest-print macro). Plan to cut, not fix; the big front print held up well in the reel
  (11–16 s).
- **Seedance: skull redrawn** (extra antler points) in shots 7–10. Image 2 is its only source; check the outline.
- **Seedance: generic hoodie prior** adds drawstrings or a zip. Blocked in Never-render [VERIFY with the real
  garment].
- **Seedance: continuity.** The town and the sun direction may shift between cuts (the reel itself flips the key
  light in shot 3). Fix with one grade per shot in post.
- **Hands:** the reel's talking gestures are dropped; hands stay at his sides (rulebook §4, hands).
- **Ending:** shot 9 must play in real time and short (1.5 s), with no slow-mo. Trim in the edit if Seedance slows it.
