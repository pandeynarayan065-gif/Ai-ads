#!/usr/bin/env python3
"""Lint an image/video generation prompt before any credits are spent.

Usage:
  python3 scripts/prompt_lint.py <prompt.md> [...] [--kind still|i2v|ref|seedance] [--faceless] [--sd 2.0|2.5]

--kind (guessed from the file name when left out: prompt-* = still, motion-* = i2v, *seedance* = seedance):
  still     keyframe / product still (Nano Banana Pro)
  i2v       image-to-video from a first frame (Veo 3.1): motion only, the picture is already given
  t2v       text-to-video, no images (Veo): describe the whole scene, one moment
  ref       video from reference images, no first frame (Veo ingredients)
  seedance  Seedance 2.x four-block prompt (asset mapping, summary, timed shots, constants)
--faceless  the brand needs faceless people: fail if a person appears without a face rule
--sd        Seedance version (default 2.5); 2.0 ignores timestamps and only follows "Shot N"

FAIL = fix before the dry run. WARN = look again. Exit code 1 if anything fails.
The rules and their sources are in reference/ai-video-playbook.md.
"""
import argparse
import re
import sys
from pathlib import Path

NEG = r"\b(no|not|never|without|avoid|nor|isn't|don't|doesn't|zero)\b"

# quality-word stacks push towards glossy stock/CGI (Higgsfield, FOOH, fal); "3D render" reads as CGI
HYPE = [r"masterpiece", r"best quality", r"\b(8|16)k\b", r"hyper-?realistic", r"ultra[- ]detailed", r"ultra ?hd",
        r"trending on artstation", r"octane", r"unreal engine", r"3d render", r"\bcgi\b", r"award[- ]winning",
        r"\bstunning\b", r"\bepic\b"]
# things no crew could film read as CGI (our zero-g and tethys shots; abstract morphs fail in every model)
MAGIC = [r"gravity (switches|turns) off", r"zero[- ]?g(ravity)?\b", r"levitat", r"float(s|ing)? (up|upward|in the air|in mid-?air)",
         r"transforms? into", r"\bmorph", r"materiali[sz]", r"dissolves into", r"disintegrat", r"teleport",
         r"\bportal\b", r"magical?ly", r"shatters into", r"reassembl", r"assembles itself", r"comes to life",
         r"hardens into", r"turns (in)?to (stone|rock|snow|ice|gold|dust|sand|crystal)", r"the (story|history) of"]
MAYBE_MAGIC = [r"turns into", r"\bfloating\b", r"wells up", r"rises out of", r"emerges from", r"forms (a|an|the)\b"]
# camera move families: more than one per shot destabilises the shot (Seedance docs; practitioners for Veo)
MOVES = {
    "push/pull": r"push(es)?[- ]in|pull(s|ing)?[- ](back|out)|dolly(ing)? (in|out|forward|back)|zoom(s|ing)? (in|out)|"
                 r"(camera|lens|helicopter|drone) (slowly )?(moves?|creeps?|drifts?) (slowly )?(closer|in\b|toward|forward)",
    "pan": r"\bpan(s|ning)?\b|whip[- ]pan",
    "tilt": r"\btilt(s|ing)? (up|down)",
    "orbit": r"\borbit(s|ing)?\b|arc shot|\barcs? around|circles? (around|the)|rotates? around",
    "truck/track": r"\btruck(s|ing)? (left|right)|tracking shot|\btracks?\b (along|with|left|right)|follows? (him|her|the)",
    "crane/rise": r"\bcrane\b|pedestal|camera (rises|lifts|descends|drops)|rising gently|gentle rise|\brises? gently",
}
CAMERA_SAID = r"static|locked[- ]off|locked camera|tripod|holds? (still|its distance)|camera stays|does not move|" \
              r"still camera|handheld|hand-held"
CHAIN = r"\bthen\b|\bnext,|after that|\bfinally\b|\bsuddenly\b"
COLOURS = r"\b(white|black|indigo|navy|pink|red|blue|grey|gray|golden|orange|salmon|charcoal|green|yellow|amber|" \
          r"silver|cream|beige)\b"
MATERIALS = r"\b(plastic|glass|wool|slate|marble|metal|chrome|frosted|matte|glossy|ribbed|knit)\b"
PERSON = r"\b(man|woman|he|she|his|her|person|guy|girl|boy|climber|mountaineer|people)\b"
FACE_RULE = r"\bfaces?\b|faceless|from behind|back of (his|her) head|never turns|cropped (below|above)|hands only"
WATER_AUDIO = r"\b(water|wave|waves|splash\w*|bubbl\w*|echo\w*|drip\w*|pour\w*|ocean|sea)\b"


def unnegated(pattern, text):
    """Matches of pattern not preceded within a few words by a negation ('no zoom', 'never floats')."""
    hits = []
    for m in re.finditer(pattern, text, flags=re.I):
        before = text[max(0, m.start() - 40):m.start()]
        clause = re.split(r"[.;:!?\n]", before)[-1]
        if not re.search(NEG, clause, flags=re.I):
            hits.append(m.group(0))
    return hits


def split_shots(text):
    """Shot blocks: 'Shot 1', '0-3 seconds', '[1s-4s]', '[00:00-00:02]'. One block if none."""
    marks = list(re.finditer(r"(?im)^\s*(\*\*)?(shot \d+|\[?\d+(\.\d+)?\s*s?\s*[-–]\s*\d+(\.\d+)?\s*(s|sec|seconds)\]?|"
                             r"\[\d\d:\d\d\s*[-–]\s*\d\d:\d\d\])", text))
    if not marks:
        return [("whole prompt", text)]
    blocks = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        blocks.append((m.group(2).strip(), text[m.start():end]))
    return blocks


def lint(path, kind, faceless, sd):
    raw = Path(path).read_text()
    text = "\n".join(l for l in raw.splitlines() if not l.lstrip().startswith("#"))  # headings are notes, not prompt
    words = len(re.findall(r"[\w'’-]+", text))
    fails, warns = [], []

    for p in HYPE:
        for h in unnegated(p, text):
            fails.append(f'hype word "{h}": name a real camera, lens, light and materials instead')
    for p in MAGIC:
        for h in unnegated(p, text):
            fails.append(f'"{h}": nothing a real crew could film. Magic and transformations read as CGI; '
                         f"use a real physical event (pour, splash, gust, press)")
    for p in MAYBE_MAGIC:
        for h in unnegated(p, text):
            warns.append(f'"{h}": could a real crew film this? If it is a transformation, it will read as CGI')

    shots = split_shots(text) if kind == "seedance" else [("whole prompt", text)]
    for name, block in shots:
        if kind == "still":
            break
        fams = sorted({f for f, p in MOVES.items() if unnegated(p, block)})
        where = "" if name == "whole prompt" else f"{name}: "
        if len(fams) > 1:
            (fails if kind == "seedance" or len(fams) > 2 else warns).append(
                f"{where}{len(fams)} camera moves ({', '.join(fams)}): one move per shot")
        if not fams and not re.search(CAMERA_SAID, block, flags=re.I):
            warns.append(f"{where}no camera move and no 'static/locked-off': say what the camera does "
                         f"(Veo leaves it still)")
        n_chain = len(unnegated(CHAIN, block))
        if n_chain > 2:
            warns.append(f"{where}{n_chain} 'then/next/finally' steps: one moment per clip, split the rest into shots")
        if kind == "seedance":
            sw = len(re.findall(r"[\w'’-]+", block))
            if name != "whole prompt" and sw > 110:
                warns.append(f"{name}: {sw} words; keep each shot to ~60-100, later instructions get dropped")

    quoted = re.findall(r'"([^"\n]{1,80})"|“([^”\n]{1,80})”', text)
    q_words = sum(len((a or b).split()) for a, b in quoted)
    if kind == "still":
        if words > 300:
            warns.append(f"{words} words: Nano Banana wants a clear paragraph, not an essay; cut what the refs already show")
        if q_words > 8:
            warns.append(f"{q_words} words in quotes: small text comes out garbled; keep in-image text to a headline "
                         f"+ CTA and lock the label in post")
        if not re.search(r"9:16|4:5|1:1|16:9|vertical|portrait format|square", text, flags=re.I):
            warns.append("no aspect ratio in the prompt (also pass --aspect)")
        if not re.search(r"\d+ ?mm|lens|phone|camera|f/\d|macro", text, flags=re.I):
            warns.append("no camera/lens: say what it was shot on (e.g. 50mm, phone wide lens, 100mm macro)")
        if not re.search(r"light|sun|window|softbox|daylight|overcast", text, flags=re.I):
            warns.append("no light source: name it and its direction")
        if re.search(r"bottle|product|jar|tube|can\b", text, flags=re.I) and \
                not re.search(r"\d+ ?cm|as tall as|the size of|hand'?s? (width|length)|fits in|palm|scale", text, flags=re.I):
            warns.append("no scale anchor: give the real size (cm) and compare it with a hand or head")
        if not re.search(r"image \d|reference|first image|second image", text, flags=re.I):
            warns.append("no reference images named: say which image is the product and what to take from it")
    else:
        if q_words:
            warns.append(f"{len(quoted)} quoted strings: video models render quoted words as captions or garbled "
                         f"labels. The label comes from the first frame/refs and is locked in post; write dialogue "
                         f"as 'He says: ...'")
    if kind == "i2v":
        if words > 180:
            fails.append(f"{words} words: image-to-video prompts are motion only; the first frame already shows the "
                         f"scene (aim for 40-100)")
        elif words > 100:
            warns.append(f"{words} words: aim for 40-100 (motion, camera, sound)")
        look = len(re.findall(COLOURS, text, flags=re.I)) + len(re.findall(MATERIALS, text, flags=re.I))
        if look > 6:
            warns.append(f"{look} colour/material words: you're re-describing the picture; say 'the bottle', "
                         f"'the man' and describe only what moves")
    if kind in ("ref", "t2v") and words > 220:
        warns.append(f"{words} words: keep it under ~200, one moment per clip; extra detail gets dropped or muddled")
    if kind == "seedance":
        if not re.search(r"image ?\d|@image|<image", text, flags=re.I):
            warns.append("no asset mapping: open with 'Image 1 is ..., use it for ...'")
        if not re.search(r"subtitle", text, flags=re.I):
            warns.append("add 'Keep it subtitle-free.'")
        if sd == "2.0" and re.search(r"\d+\s*[-–]\s*\d+\s*(s|sec|seconds)\b|\[\d+s", text, flags=re.I):
            warns.append("Seedance 2.0 ignores timestamps: use 'Shot 1: ... Shot 2: ...'")
        for m in re.finditer(r"(?i)\b(sound|audio|sfx)\b[^.\n]*(\.[^.\n]*)?", text):
            if unnegated(WATER_AUDIO, m.group(0)):
                warns.append("water/wave/echo words in the sound line make Seedance audio bubble or whistle; "
                             "ask for no BGM and add liquid SFX in post")
                break
    if faceless and unnegated(PERSON, text) and not re.search(FACE_RULE, text, flags=re.I):
        fails.append("a person appears with no face rule: say 'seen from behind, face never visible' (or crop to hands)")

    return words, fails, warns


def guess_kind(path):
    name = Path(path).name
    if name.startswith("prompt-"):
        return "still"
    if "seedance" in name:
        return "seedance"
    return "i2v"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--kind", choices=["still", "i2v", "t2v", "ref", "seedance"])
    ap.add_argument("--faceless", action="store_true")
    ap.add_argument("--sd", default="2.5", choices=["2.0", "2.5"])
    args = ap.parse_args()
    bad = False
    for f in args.files:
        kind = args.kind or guess_kind(f)
        words, fails, warns = lint(f, kind, args.faceless, args.sd)
        status = "FAIL" if fails else ("WARN" if warns else "PASS")
        print(f"{status}  {f}  [{kind}, {words} words]")
        for m in dict.fromkeys(fails):
            print(f"   FAIL  {m}")
        for m in dict.fromkeys(warns):
            print(f"   warn  {m}")
        bad |= bool(fails)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
