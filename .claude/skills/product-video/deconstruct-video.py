#!/usr/bin/env python3
"""
deconstruct-video.py — Read a reference video into a rebuildable breakdown for /product-video.

The reference is an analysis input only. It is read for its setting, its
structure and its words, then rebuilt with your own model and product.
It is never uploaded to the video model and never rendered.

Two modes (run from the project root):

  --check <video> [--start S --end E]
      Reads the clip's length from the file (no install needed for .mp4/.mov/.m4v),
      and prints a JSON manifest: length, the section that would be read, the
      cost, the expected wait, whether a saved breakdown already exists, and
      whether the clip is over the 30-second limit. Spends nothing, needs no key.

  <video> --out <dir> [--start S --end E]
      Reads the clip (or the chosen section) with fal-ai/video-understanding and
      writes deconstruction.json + deconstruction.md into <dir>. The breakdown is
      also saved beside the clip, so a second brief from the same clip costs nothing.

Clips longer than 30 seconds (Seedance 2.5's native limit) are refused unless a
--start/--end section of 30 seconds or less is given. With ffmpeg installed the
section is cut before upload; without it, the whole clip is uploaded and the
reader is told to break down only that section.

Exit codes: 0 ok | 2 usage | 3 over the limit, pick a section | 4 file problem
            5 the read failed
"""

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ENDPOINT = "fal-ai/video-understanding"
MAX_SECONDS = 30               # Seedance 2.5 native limit; nothing longer is rebuilt
PRICE_PER_5_SEC = 0.01         # fal pricing: $0.01 per 5 seconds of video
WAIT_BASE_SEC = 30             # expected wait: base + per-second-of-video (measured: 10s clip read in 57s)
WAIT_PER_VIDEO_SEC = 3
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".webm", ".gif"}

PROMPT = """You are a short-form video ad analyst. Deconstruct this video so it can be rebuilt with a DIFFERENT person, a different product and a rewritten script, while keeping what makes it work.

Return ONLY a JSON object (no markdown fences, no prose around it) with exactly these keys:
{
  "durationSec": number,            // total length in seconds
  "format": string,                 // closest archetype: selfie-review | unboxing | try-on | lifestyle-demo | asmr-product | talking-head | product-demo | podcast-two-shot | other
  "setting": string,                // the environment in concrete detail (location, surfaces, lighting source and direction, props). This is PRESERVED in the rebuild.
  "character": string,              // the on-camera person in concrete detail: apparent age, build, hair, wardrobe, vibe. Described so a casting director could deliberately cast a DIFFERENT person.
  "pacing": string,                 // the rhythm and energy: cut speed, talking cadence, where the energy rises, the talking structure that carries the clip
  "transcript": string,             // every spoken line, as close to verbatim as you can, in order. Empty string if no dialogue.
  "hook": string,                   // the first 1-3 seconds: what grabs attention
  "productMoment": string,          // where and how the product (if any) is shown or mentioned. Empty string if none.
  "beats": [                        // timecoded shot list covering the FULL duration
    { "timecode": "0-3s", "shot": "camera angle / framing / movement", "action": "what happens", "dialogue": "spoken line if any, else empty" }
  ]
}

Rules: describe only what is actually visible or audible, do not invent. Keep the transcript faithful. Do not use an em dash anywhere."""


# ---------------------------------------------------------------------------
# Length, without installing anything
# ---------------------------------------------------------------------------

def _mp4_duration(path: Path):
    """Seconds from the moov/mvhd box of an MP4/MOV/M4V file, or None."""
    def boxes(f, start, end):
        pos = start
        while pos + 8 <= end:
            f.seek(pos)
            header = f.read(8)
            if len(header) < 8:
                return
            size, kind = struct.unpack(">I4s", header)
            head = 8
            if size == 1:
                size = struct.unpack(">Q", f.read(8))[0]
                head = 16
            elif size == 0:
                size = end - pos
            if size < head:
                return
            yield kind, pos + head, pos + size
            pos += size

    try:
        end = path.stat().st_size
        with open(path, "rb") as f:
            for kind, body, stop in boxes(f, 0, end):
                if kind != b"moov":
                    continue
                for sub, sbody, _ in boxes(f, body, stop):
                    if sub != b"mvhd":
                        continue
                    f.seek(sbody)
                    version = f.read(1)[0]
                    if version == 1:
                        f.seek(sbody + 20)
                        timescale, duration = struct.unpack(">IQ", f.read(12))
                    else:
                        f.seek(sbody + 12)
                        timescale, duration = struct.unpack(">II", f.read(8))
                    return duration / timescale if timescale else None
    except (OSError, struct.error, IndexError):
        return None
    return None


def video_length(path: Path):
    seconds = _mp4_duration(path)
    if seconds:
        return round(seconds, 2)
    if shutil.which("ffprobe"):
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
            capture_output=True, text=True,
        )
        try:
            return round(float(out.stdout.strip()), 2)
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_env_file() -> None:
    if os.environ.get("FAL_KEY"):
        return
    search = Path.cwd()
    for _ in range(5):
        env_file = search / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key not in os.environ:
                        os.environ[key] = val
            return
        parent = search.parent
        if parent == search:
            break
        search = parent


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _cache_path(path: Path, start, end) -> Path:
    section = "" if start is None else f".{_fmt(start)}-{_fmt(end)}s"
    return path.with_name(f"{path.name}{section}.deconstruction.json")


def _fmt(x: float) -> str:
    return f"{x:g}"


def _plan(path: Path, start, end):
    """Everything the user is told before anything is spent."""
    length = video_length(path)
    plan = {
        "file": str(path),
        "length_sec": length,
        "limit_sec": MAX_SECONDS,
        "section": None,
        "read_sec": length,
        "over_limit": bool(length and length > MAX_SECONDS),
        "ffmpeg": bool(shutil.which("ffmpeg")),
        "cost_usd": None,
        "expected_wait_sec": None,
        "saved_breakdown": None,
    }
    if start is not None:
        plan["section"] = [start, end]
        plan["over_limit"] = (end - start) > MAX_SECONDS
        # Without ffmpeg the whole clip is uploaded, so the whole clip is billed.
        plan["read_sec"] = (end - start) if plan["ffmpeg"] else length
    if plan["read_sec"]:
        plan["cost_usd"] = round(math.ceil(plan["read_sec"] / 5) * PRICE_PER_5_SEC, 2)
        plan["expected_wait_sec"] = int(WAIT_BASE_SEC + WAIT_PER_VIDEO_SEC * plan["read_sec"])
    cache = _cache_path(path, start, end)
    if cache.exists():
        try:
            if json.loads(cache.read_text()).get("sha256") == _sha(path):
                plan["saved_breakdown"] = str(cache)
                plan["cost_usd"] = 0.0
                plan["expected_wait_sec"] = 0
        except (OSError, ValueError):
            pass
    return plan


def _strip_fences(s: str) -> str:
    t = s.strip()
    fence = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", t, re.I)
    if fence:
        return fence.group(1).strip()
    first, last = t.find("{"), t.rfind("}")
    if first != -1 and last > first:
        return t[first:last + 1]
    return t


def _coerce(raw) -> dict:
    o = raw if isinstance(raw, dict) else {}
    s = lambda v: v.strip() if isinstance(v, str) else ""
    beats = []
    for b in o.get("beats") or []:
        b = b if isinstance(b, dict) else {}
        beat = {k: s(b.get(k)) for k in ("timecode", "shot", "action", "dialogue")}
        if any(beat.values()):
            beats.append(beat)
    try:
        duration = float(o.get("durationSec")) if o.get("durationSec") is not None else None
    except (TypeError, ValueError):
        duration = None
    return {
        "durationSec": duration,
        "format": s(o.get("format")),
        "setting": s(o.get("setting")),
        "character": s(o.get("character")),
        "pacing": s(o.get("pacing")),
        "transcript": s(o.get("transcript")),
        "hook": s(o.get("hook")),
        "productMoment": s(o.get("productMoment")),
        "beats": beats,
    }


def to_text(d: dict) -> str:
    if d.get("summary") and not (d.get("setting") or d.get("beats")):
        return f"# Reference video breakdown (unstructured)\n\n{d['summary']}\n"
    lines = ["# Reference video breakdown"]
    if d.get("durationSec"):
        lines.append(f"Length: {_fmt(d['durationSec'])}s")
    if d.get("format"):
        lines.append(f"Closest format: {d['format']}")
    if d.get("setting"):
        lines.append(f"\n## Setting (keep this)\n{d['setting']}")
    if d.get("character"):
        lines.append(f"\n## Original person (replaced by your model, never described in the prompt)\n{d['character']}")
    if d.get("pacing"):
        lines.append(f"\n## Pacing and talking structure (keep this)\n{d['pacing']}")
    if d.get("hook"):
        lines.append(f"\n## Hook\n{d['hook']}")
    if d.get("productMoment"):
        lines.append(f"\n## Product moment\n{d['productMoment']}")
    if d.get("transcript"):
        lines.append(f"\n## Original transcript (rewrite, keep the cadence)\n{d['transcript']}")
    if d.get("beats"):
        lines.append("\n## Beats (keep the count and rhythm)")
        for b in d["beats"]:
            bits = " | ".join(x for x in (b["timecode"], b["shot"], b["action"]) if x)
            lines.append(f"- {bits}" + (f'  ("{b["dialogue"]}")' if b["dialogue"] else ""))
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def read_video(path: Path, out_dir: Path, start, end) -> None:
    plan = _plan(path, start, end)
    if plan["over_limit"]:
        print(json.dumps(plan, indent=2))
        print(f"Error: the {'section' if start is not None else 'clip'} is over {MAX_SECONDS}s. "
              "Ask the user which part to use, then pass --start and --end.", file=sys.stderr)
        sys.exit(3)

    out_dir.mkdir(parents=True, exist_ok=True)
    cache = _cache_path(path, start, end)

    if plan["saved_breakdown"]:
        data = json.loads(cache.read_text())["deconstruction"]
        print(f"Using the saved breakdown: {cache} (nothing spent)")
    else:
        try:
            import fal_client
        except ImportError as exc:
            sys.exit(
                f"Error: missing dependency '{exc.name}'.\n"
                "Install the project requirements first, from the project root:\n"
                "  pip install fal-client requests"
            )
        _load_env_file()
        if not os.environ.get("FAL_KEY"):
            sys.exit("Error: FAL_KEY not found. Add it to .env at the project root.")

        prompt = PROMPT
        upload = path
        tmp = None
        if start is not None:
            if plan["ffmpeg"]:
                tmp = Path(tempfile.mkdtemp()) / f"section{path.suffix or '.mp4'}"
                cut = subprocess.run(
                    ["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", _fmt(start), "-to", _fmt(end),
                     "-i", str(path), "-c:v", "libx264", "-preset", "veryfast", "-c:a", "aac", str(tmp)],
                    capture_output=True, text=True,
                )
                if cut.returncode != 0:
                    sys.exit(f"Error: couldn't cut the section with ffmpeg: {cut.stderr.strip()[:300]}")
                upload = tmp
            else:
                prompt += (f"\n\nOnly break down the section from {_fmt(start)}s to {_fmt(end)}s. "
                           f"Ignore everything outside it. Write timecodes relative to {_fmt(start)}s, "
                           "so the section starts at 0s.")

        print(f"Reading {plan['read_sec']}s of video (~${plan['cost_usd']:.2f}, "
              f"usually about {plan['expected_wait_sec']}s)...")
        began = time.time()
        try:
            url = fal_client.upload_file(str(upload))
            res = fal_client.subscribe(ENDPOINT, arguments={
                "video_url": url, "prompt": prompt, "detailed_analysis": True,
            })
        except Exception as exc:  # fal raises several error types; any of them means the read failed
            print(f"Error: the video read failed: {exc}", file=sys.stderr)
            sys.exit(5)
        finally:
            if tmp:
                shutil.rmtree(tmp.parent, ignore_errors=True)
        output = (res or {}).get("output", "") if isinstance(res, dict) else ""
        if not output.strip():
            print("Error: the video read returned nothing.", file=sys.stderr)
            sys.exit(5)
        print(f"Read in {int(time.time() - began)}s.")

        try:
            data = _coerce(json.loads(_strip_fences(output)))
            if not (data["setting"] or data["character"] or data["beats"] or data["transcript"]):
                raise ValueError("empty")
        except (ValueError, json.JSONDecodeError):
            # Unusable JSON: keep the raw narrative so the analysis is never lost.
            data = {"summary": output.strip(), "setting": "", "character": "", "pacing": "",
                    "transcript": "", "beats": []}
        try:
            cache.write_text(json.dumps({"sha256": _sha(path), "section": plan["section"],
                                         "deconstruction": data}, indent=2))
        except OSError:
            pass  # saving beside the clip is a convenience; the run's own copy below is what counts

    (out_dir / "deconstruction.json").write_text(json.dumps(
        {"source": str(path), "section": plan["section"], "deconstruction": data}, indent=2))
    text = to_text(data)
    (out_dir / "deconstruction.md").write_text(text)
    print(f"\nSaved → {out_dir / 'deconstruction.md'}\n")
    print(text)


def main():
    ap = argparse.ArgumentParser(description="Read a reference video for /product-video.")
    ap.add_argument("video", help="Path to the reference video")
    ap.add_argument("--check", action="store_true", help="Report length, cost and wait; spend nothing")
    ap.add_argument("--out", help="Output folder for deconstruction.json / deconstruction.md")
    ap.add_argument("--start", type=float, help="Section start, in seconds")
    ap.add_argument("--end", type=float, help="Section end, in seconds")
    args = ap.parse_args()

    path = Path(args.video)
    if not path.is_file():
        print(f"Error: video not found: {path}", file=sys.stderr)
        sys.exit(4)
    if path.suffix.lower() not in VIDEO_EXTS:
        print(f"Error: unsupported file type {path.suffix!r}. Use one of: {', '.join(sorted(VIDEO_EXTS))}",
              file=sys.stderr)
        sys.exit(4)
    if (args.start is None) != (args.end is None):
        ap.error("--start and --end go together")
    if args.start is not None and not (0 <= args.start < args.end):
        ap.error("--start must be at least 0 and before --end")

    if args.check:
        plan = _plan(path, args.start, args.end)
        print(json.dumps(plan, indent=2))
        sys.exit(3 if plan["over_limit"] else 0)
    if not args.out:
        ap.error("--out is required unless --check is used")
    read_video(path, Path(args.out), args.start, args.end)


if __name__ == "__main__":
    main()
