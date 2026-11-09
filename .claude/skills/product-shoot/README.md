# /product-shoot

Puts your product into any scene from a reference photo, with an optional second photo to match the lighting (GPT Image 2.5 via fal.ai, about $0.12 per image).

## Install

1. Drop this `product-shoot` folder into your project at `.claude/skills/product-shoot/`
2. Add your fal.ai key to a `.env` file in the project root:
   ```
   FAL_KEY=your-fal-key-here
   ```
3. Install the two Python packages once:
   ```
   pip install fal-client requests
   ```
4. Open the project in Claude Code and type `/product-shoot`

Claude asks for everything it needs, sets up your `brands/your-brand/` folder if you don't have one yet, and saves every output there.
