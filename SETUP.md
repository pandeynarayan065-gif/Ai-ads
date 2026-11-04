# Setup for a new chat, account or container

Everything the work needs is in this repo except three things that never get committed: the kie.ai key, the local
upscaler and scratch files. A new session (new chat, new Claude account, fresh cloud container) needs only this page.

## 1. The kie.ai key (image and video generation)

- Add `KIE_API_KEY` as an **environment secret** in the Claude Code cloud environment settings (best: it survives
  container resets), or put `KIE_API_KEY=...` in a `.env` file at the repo root (git-ignored; gone after a reset).
- Never paste it in chat, print it or commit it (CLAUDE.md). Credits belong to the kie.ai account, not the Claude one.
- Check: `python3 scripts/kie_generate.py credits`

## 2. Python tools for post (masks, grades, supers)

    pip install -q opencv-python-headless pillow numpy fonttools

ffmpeg, Node and Playwright/Chromium come pre-installed in Claude Code cloud containers.

## 3. Real-ESRGAN upscaler (free, CPU, ~13 s per 720p frame to 4K)

    E=/tmp/esr                                  # any folder outside the repo
    python3 -m venv $E/venv
    $E/venv/bin/pip install -q --index-url https://download.pytorch.org/whl/cpu torch
    $E/venv/bin/pip install -q numpy
    curl -sSL -o $E/realesr-general-x4v3.pth \
      https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth
    $E/venv/bin/python scripts/esrgan_upscale.py in.mp4 out.mp4 --weights $E/realesr-general-x4v3.pth --size 2160x3840

Upscales are scratch files: re-run them from the committed takes; only finished masters go in the repo.

## 4. Where things stand

`STATUS.md`: open work and the next step for each piece. Narayan's standing rules: `brand/spraymax/preferences.md`.
