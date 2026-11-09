# /add-motion

Turns any still into a short product film, 3 to 12 seconds (Kling 3.0 Pro via fal.ai, about $0.11 per second, $0.17 with audio).

## Install

1. Drop this `add-motion` folder into your project at `.claude/skills/add-motion/`
2. Add your fal.ai key to a `.env` file in the project root:
   ```
   FAL_KEY=your-fal-key-here
   ```
3. Install the two Python packages once:
   ```
   pip install fal-client requests
   ```
4. Open the project in Claude Code (or Cowork) and type `/add-motion`

Claude asks for everything it needs, sets up your `brands/your-brand/` folder if you don't have one yet, and saves every output there.
