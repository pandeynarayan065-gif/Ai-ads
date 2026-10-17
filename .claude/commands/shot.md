---
description: Plan, prompt, QA and generate one AI video shot using the playbook
argument-hint: <brand> <campaign> <shot idea>
---
Make one AI shot: $ARGUMENTS

1. Read `reference/ai-video-playbook.md`, `reference/ai-video-qa.md`, the brand file,
   `brand/<brand>/product-lock.md` and `ads/<brand>/prompt-log.md`. Read the campaign's `edit-plan.md` too, if
   there is one.
2. **Gate 0 (concept).** Write the shot in one sentence: camera, subject, one action, place, light.
   Run the real-crew test, and check it against the "Avoid" column of the playbook's shot recipes and against
   the prompt log.
   - If it fails, say why in one line and offer the nearest real-world version.
   - If the job, length, product visibility or faceless approach is unclear, ask me before going on.
3. **Shot card.** Copy `ads/_shot-template.md` to `ads/<brand>/<campaign>/shots/<nn>-<slug>.md` and fill in
   every line, including the shot-specific pass criteria and the budget.
4. **Prompts.** Write them from the playbook templates (section 5):
   - `prompt-<nn>-still.md` for the keyframe, unless it's a pure environment shot;
   - `motion-<nn>.md` for the motion.
   Copy the product block word for word. Name a role for every reference image. Image-to-video prompts
   describe motion, camera and sound only.
5. **Lint.** Run `python3 scripts/prompt_lint.py <files> --kind <kind> [--faceless]`. Fix every FAIL. Fix
   each warning, or note on the card why it's fine.
6. **Spend gate.** Run `python3 scripts/kie_generate.py credits`, then a dry run (no `--yes`). Show me:
   - the final prompt in full;
   - the refs and the role of each;
   - the model, mode and cost;
   - the pass criteria.
   Then **stop and wait**. Only add `--yes` after I approve that exact prompt. If the balance won't cover it, say
   so; don't switch models to fit the balance without asking.
7. **Still QA (gate 2).** After a still is generated, compare it at full size with the real product photo
   scaled to the same width.
   - Check proportions, scale, the known AI errors from the product lock, light, faces and stray text.
   - Fix small things in post: label lock, cleanup, exact 1080x1920 JPEG.
   - If proportions or scale are wrong, propose one Nano Banana edit (back to step 6). Don't animate a
     failing still.
8. **Motion.** Repeat steps 5–6 for the motion prompt, with the checked still as the first frame.
9. **Clip QA (gate 3).** Scrub the clip frame by frame and score it 0/1/2 on the scorecard.
   - Log each failure with a timestamp and mark the usable range.
   - Show me a contact sheet of the usable range.
   - Recommend one of three:
     - keep, and list the post fixes;
     - a second take with exactly one change, and why;
     - reject the concept.
10. **Post.** Apply the fixes from the playbook's toolbox and write a `*-notes.txt` next to the clip with the
    commands used.
11. **Log.** Fill in the takes table on the shot card. Add a row to `ads/<brand>/prompt-log.md` with the model,
    lint result, verdict (in my words if I gave one), what happened and the rule it gave us.
12. Commit and push. Never print or commit API keys.
