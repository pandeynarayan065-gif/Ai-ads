#!/usr/bin/env python3
"""Check ad copy files against platform character limits.

Usage: python3 scripts/check_limits.py <file-or-directory> [...]

Reads the `platform:` key from each file's front matter and checks every
`- **Field:** text` bullet whose field has a known limit for that platform.
Hard limits fail the run; recommended limits only warn.
Exit code 1 if any hard limit is exceeded.
"""
import re
import sys
from pathlib import Path

# field name (lowercase) -> (limit, hard?)
LIMITS = {
    "google-search": {
        "headline": (30, True),
        "description": (90, True),
        "path 1": (15, True),
        "path 2": (15, True),
    },
    "google-display": {
        "short headline": (30, True),
        "long headline": (90, True),
        "description": (90, True),
        "business name": (25, True),
    },
    "meta": {
        "primary text": (125, False),
        "headline": (40, False),
        "description": (30, False),
    },
    "linkedin": {
        "intro text": (600, True),
        "headline": (200, True),
    },
    "linkedin-rec": {
        "intro text": (150, False),
        "headline": (70, False),
    },
    "tiktok": {
        "ad text": (100, True),
    },
    "x": {
        "post text": (280, True),
    },
}

FIELD_RE = re.compile(r"^\s*[-*]\s+\*\*(?P<field>[^*:]+):\*\*\s*(?P<text>.*)$")
PLATFORM_RE = re.compile(r"^platform:\s*(\S+)\s*$", re.MULTILINE)


def platform_of(content: str):
    if not content.startswith("---"):
        return None
    end = content.find("\n---", 3)
    match = PLATFORM_RE.search(content[3:end if end != -1 else None])
    return match.group(1).strip().lower() if match else None


def check_file(path: Path):
    content = path.read_text(encoding="utf-8")
    platform = platform_of(content)
    if platform is None:
        return 0, 0, [f"  skip: no 'platform:' in front matter"]
    if platform not in LIMITS:
        return 0, 0, [f"  skip: unknown platform '{platform}' (known: {', '.join(k for k in LIMITS if not k.endswith('-rec'))})"]

    rules = [LIMITS[platform]]
    if f"{platform}-rec" in LIMITS:
        rules.append(LIMITS[f"{platform}-rec"])

    errors = warnings = 0
    lines = []
    for lineno, line in enumerate(content.splitlines(), 1):
        match = FIELD_RE.match(line)
        if not match:
            continue
        field = match.group("field").strip().lower()
        text = match.group("text").strip()
        length = len(text)
        for rule in rules:
            if field not in rule:
                continue
            limit, hard = rule[field]
            if length > limit:
                kind = "ERROR" if hard else "warn "
                if hard:
                    errors += 1
                else:
                    warnings += 1
                lines.append(f"  {kind} line {lineno}: {match.group('field').strip()} {length}/{limit} — {text[:60]}")
                break
    return errors, warnings, lines


def iter_files(args):
    for arg in args:
        path = Path(arg)
        if path.is_dir():
            yield from sorted(path.rglob("*.md"))
        elif path.is_file():
            yield path
        else:
            print(f"not found: {arg}", file=sys.stderr)


def main(argv):
    if not argv:
        print(__doc__.strip())
        return 2
    total_errors = total_warnings = 0
    for path in iter_files(argv):
        errors, warnings, lines = check_file(path)
        total_errors += errors
        total_warnings += warnings
        status = "FAIL" if errors else ("ok (warnings)" if warnings else "ok")
        print(f"{path}: {status}")
        for line in lines:
            print(line)
    print(f"\n{total_errors} error(s), {total_warnings} warning(s)")
    return 1 if total_errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
