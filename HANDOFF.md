# Handoff for a new chat (last updated 14 Nov 2026)

Start here, then `STATUS.md`. Everything below is in this repo on branch `claude/busy-ride-j9nv96`.

## Who and what

- Narayan runs **Misfits** (misfitsagency.in), an AI ad agency; cofounder **Anirudh Savaliya** holds the payment
  accounts (Wise, sole trader). Team on outreach: Daksh.
- Work style Narayan wants: short replies, act fast, show the final prompt and cost before spending, **never run a
  paid test without asking** (CLAUDE.md).

## Tools and money

- **kie.ai** (`scripts/kie_generate.py`, key in env `KIE_API_KEY`): ~159 credits left (1 cr = $0.005). Seedance 2.5:
  480p 28 cr/s, 720p 63 cr/s, 1080p 158 cr/s.
- **Higgsfield Ultra** bought 14 Nov ($79, renews ~14 Dec at **$129: cancel before**). Unlimited Seedance 2.5
  (<=20 s, 720p) for 14 days and unlimited images for 60 days, **only on the higgsfield.ai website**. Workflow:
  Claude writes the prompt + gives refs in order, Narayan generates on the site, sends clips back. MCP connection has
  3,000 credits (separate, costs credits). Plan: `ads/misfits/higgsfield-batch.md`.
- **Free finishing:** Real-ESRGAN 4x upscale (`scripts/esrgan_upscale.py`, needs `pip install torch --index-url
  https://download.pytorch.org/whl/cpu` + weights from github.com/xinntao/Real-ESRGAN releases
  `realesr-general-x4v3.pth`; ~15 s/frame on CPU, run in chunks), ffmpeg finishing scripts per project.
- **Vercel** (token via proxy): lead board (misfits-leads) and Avrana pitch site (misfits-avrana).

## Open work, in order

1. **Avrana game-cutscene ad**: Narayan generating takes on Higgsfield with
   `ads/misfits/clients/avrana/demo-game-cutscene/prompt-seedance-18s-rooftop-4refs.md`; refs in order:
   hoodie back (`product-images/death-amp-glory-hoodie/04.jpg`), hoodie front (`03.jpg`),
   `demo-game-cutscene/refs/3-style-reference.jpg`, `refs/4-background-reference.jpg`. Settings 18 s, 9:16, 720p,
   audio on. When clips arrive: QA, pick best, add subtitles + "Get yours at avrana.co" end card, upscale.
   Product photos are gitignored: re-download with `python3 ads/misfits/clients/avrana/fetch_images.py`.
2. **Jose's 15-day plan** starts when his first $100 lands (not yet as of 14 Nov). Video 1 within 24 h, delivered
   with a light Misfits watermark until he approves or 3 days pass. Then 1 video every 2 days.
3. **Jewellery shop outreach** (Ranchi, Delhi): demo + showcase ready in `ads/misfits/jewellery-demo/`; put each
   shop's name on the end card (`finish_film.py --store "Name"`).
4. Razorpay international for Misfits: submitted, waiting on approval.

## Do not

- Commit lead contact data, card/bank details, the team passcode or client addresses.
- Copy existing game/film characters (Jin Kazama, Dante, etc.) into client ads.
- Spend credits without showing the prompt and cost and getting a yes.
