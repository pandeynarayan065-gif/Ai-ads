# /model

Creates a consistent model for your brand: a matched headshot and full-body casting image (Nano Banana 2 via fal.ai, about $0.24 per model).

## Install

1. Drop this `model` folder into your project at `.claude/skills/model/`
2. Add your fal.ai key to a `.env` file in the project root:
   ```
   FAL_KEY=your-fal-key-here
   ```
3. Install the two Python packages once:
   ```
   pip install fal-client requests
   ```
4. Open the project in Claude Code (or Cowork) and type `/model`

Claude asks for everything it needs, sets up your `brands/your-brand/` folder if you don't have one yet, and saves every output there.
