# Spraymax: "What's bro carrying" (recreating the reference format)

**Reference:** Instagram reel `DfBDm5NPc5-`, a men's skincare brand (not ours). 12.05 s, 9:16, 30 fps.
**Budget:** $0. The hook is shot on a phone, the product half is rendered in Blender with the real label,
and the edit is made with ffmpeg and Python. No AI credits are needed.

## 1. How the reference works

| Time | What happens | Why it works |
|---|---|---|
| 0.00–4.43 | **Hook, real phone footage.** A guy in black crosses the street with a duffel. A POV hand stops him, he unzips the bag, and it's packed with the product. The hand pulls one bottle out toward the camera. Snapchat-style caption bar the whole time: "What's is bro carrying". | Looks like a creator clip, not an ad. A real person and real street, so nothing reads as AI. The question makes people watch to the reveal. The bag full of product is the joke: he's obsessed. |
| 4.43 | **Beat drop + hard cut** from the bottle in his hand to a 3D bottle at the same tilt. | The music drop does the transition. The match cut ties the real bottle to the 3D one. |
| 4.43–12.05 | **3D product montage**, 9 shots, one per beat (~0.68 s): tilted bottle with a light sweep, macro on the label, pump with a drop, dropper on a flower petal, bubbles, pump silhouette, dropper, bottle among bubbles, product range on a shelf. | Openly stylised 3D in a single brand colour (purple + a red accent); it never pretends to be real. Fast, on the beat, with exact product details. |

**Audio:** a bass-heavy track. Hits every ~0.33 s in the hook, a build from 2.0 s, the drop at 4.42 s, then a hit
every ~0.68 s (~88 BPM). Every cut in the 3D half lands on one: 5.13, 5.80, 7.07, 7.80, 8.47, 9.13, 9.80, 10.50.

**Why it isn't slop:** the "real" part is actually real, and the 3D part is honestly 3D. That's the split our
K2 film didn't have: there, AI imitated reality and looked fake.

## 2. Spraymax version

The same beats and timing. Purple + red becomes Spraymax indigo, with Himalayan-salt pink and ocean blue as the
accents (the brand story: sea salt, Himalaya).

### Hook (0.00–4.43): real phone footage, 4 beats

| # | Time | Shot | Notes |
|---|---|---|---|
| H1 | 0.00–1.10 | Wide, phone at chest height: a guy in a plain black tee walks toward camera across a busy Indian street (market road, college gate, metro exit), gym duffel in hand | Caption bar on from frame 1. Faceless option: frame him from the shoulders down |
| H2 | 1.10–2.30 | POV: the camera person's hand comes into frame, palm out, and stops him | Keep walking toward him; a slight shake is fine |
| H3 | 2.30–3.90 | Close, looking down into the bag: he unzips the duffel and it's packed with Spraymax bottles | 12–15 bottles, labels up and facing the camera |
| H4 | 3.90–4.43 | The POV hand pulls out one bottle and holds it toward the lens, **tilted top-right about 28°**, label to camera | This frame match-cuts into 3D shot C1. Hold it still for the last 5 frames |

Caption: **"What's bro carrying"**, white on a translucent black bar across the frame at ~44% height, as in
the reference. Hinglish option: **"Bhai bag mein kya hai 😭"**.

### Product half (4.43–12.05): Blender, real label, $0

| # | Time | Shot | Colour |
|---|---|---|---|
| C1 | 4.43–5.13 | Bottle tilted ~28° in an indigo void; a strip light sweeps across the label; slow push-in | Indigo |
| C2 | 5.13–5.80 | Extreme close-up sliding down the "Spraymax" wordmark, shallow focus, dutch angle | Indigo |
| C3 | 5.80–7.07 | Cap off: the pump dips, and a burst of mist crosses the frame, backlit | Indigo |
| C4 | 7.07–7.80 | A pink Himalayan salt crystal with water beads on a wet black floor; a drop falls past | Salt pink |
| C5 | 7.80–8.47 | Air bubbles rising through ocean-blue water | Ocean |
| C6 | 8.47–9.13 | Low-angle silhouette of the pump and ribbed collar, turning; rim light crawls over the ribs | Indigo |
| C7 | 9.13–9.80 | Salt crystals tumbling through warm light | Salt pink |
| C8 | 9.80–10.50 | The bottle among floating water drops, push-in | Indigo |
| C9 | 10.50–12.05 | The bottle on a glossy black floor, indigo glow, push-in. End card over it: wordmark + spraymax.in | Indigo |

Source: `video/blender/carry_shots.py`. The real label comes from a 4× rebuild with the clean wordmark
(`video/blender/label_hires.py`).

## 3. Phone shoot list for the hook (about 30 minutes)

- **Props:** 12–15 Spraymax bottles (or 6–8 on top of filler), with their caps on and labels up. A plain black
  gym duffel.
- **Talent:** a guy with good textured hair (the product's result). Plain black tee and black trousers.
- **Phone:** 1080p or 4K at **30 fps**, main 1× lens, vertical. Lock exposure on his face or the street. Use
  daylight, but not harsh midday sun.
- **Takes:** shoot H1–H4 as **one continuous take**, 3–5 times. One take keeps it feeling real; we cut it in
  the edit. Then shoot 2–3 extra takes of just H3–H4 (the bag and the pull-out), in case the bottles need
  rearranging.
- **The key frame:** the last ~0.2 s of H4. Bottle in hand, tilted top-right, label sharp and facing the lens,
  filling about a third of the frame height.
- **Sound:** keep the phone audio (street ambience, the zip). The music is added in Instagram.

## 4. If there's no shoot: an AI hook (not recommended)

Nano Banana Pro stills plus Veo 3.1 Fast, 2 clips (H1+H2 and H3+H4): about 166 credits (~$0.83) per attempt.
This is the playbook's highest-risk recipe: a hand, a bag of 15 bottles with labels, and a pull-out, so expect
garbled labels and 2–3 attempts. A real 30-minute phone shoot is cheaper and can't look like AI.

## 5. Music

The reference's track is a trending sound. Post the reel with that sound (or another trending one) chosen
**inside Instagram**, so it's licensed and the reel can be found through the sound. The draft edit uses the
reference audio only as a temporary track for timing; don't publish that file. A version with no music (SFX
only) is exported to post.
