# /product-video

Makes creator-style product videos (unboxings, try-ons, ASMR, selfie reviews, get ready with me) from a one-line concept or from a reference video you want rebuilt with your own model and product. Seedance 2.5 via fal.ai, up to 30 seconds with sound. About $0.47 per second at 720p (a 15 second clip is about $7), or about $0.22 per second at 480p for a cheap first look.

## Before you start

You need a model made with `/model` (headshot, full body and characteristics sheet) and a clean product image with no person in it.

## Install

1. Drop this `product-video` folder into your project at `.claude/skills/product-video/`
2. Add your fal.ai key to a `.env` file in the project root:
   ```
   FAL_KEY=your-fal-key-here
   ```
3. Install the two Python packages once:
   ```
   pip install fal-client requests
   ```
4. Optional: install ffmpeg so only the part of a reference video you pick gets uploaded and read
5. Open the project in Claude Code and type `/product-video`

Claude tells you the cost of every run and waits for your yes before anything is generated.
