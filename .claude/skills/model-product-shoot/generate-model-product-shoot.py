#!/usr/bin/env python3
"""
generate-model-product-shoot.py — Model product shoot pipeline (GPT Image 2.5 Sunburst).

Usage (run from project root):
  python3 .claude/skills/model-product-shoot/generate-model-product-shoot.py brands/[brand]/generation/model-product-shoot/[output-name]

Reads model-product-shoot-spec.json from the output folder.
"""

import json
import os
import sys
from pathlib import Path

try:
    import fal_client
    import requests
except ImportError as exc:
    sys.exit(
        f"Error: missing dependency '{exc.name}'.\n"
        "Install the project requirements first, from the project root:\n"
        "  pip install fal-client requests"
    )


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

EDIT_MODEL = "openai/gpt-image-2.5/sunburst/edit"

_SIZE = {
    "1:1":  {"width": 1024, "height": 1024},
    "3:4":  {"width": 1152, "height": 1536},
    "4:5":  {"width": 1229, "height": 1536},
    "4:3":  {"width": 1536, "height": 1152},
    "9:16": {"width": 864,  "height": 1536},
    "16:9": {"width": 1536, "height": 864},
    "2:3":  {"width": 1024, "height": 1536},
}

PROMPT = (
    "Regenerate image 1 by substituting the product with the exact product shown in image 2 "
    "and substituting the model with the one shown in image 3, wearing the clothes shown in image 4.\n\n"
    "--- Instructions ---\n"
    "Image references: Composition, framing and lighting must exactly match image 1. "
    "The model's features must exactly match the model shown in image 3 (excepting clothing, which is shown in image 4). "
    "Product must exactly match image 2.\n"
    "Exact text mapping, maintaining the exact spelling, capitalization and placement hierarchy\n"
    "Maintain the exact proportions of the subject. Recreate the precise clothing items and accessories"
)


def _image_size(aspect_ratio: str) -> dict:
    return _SIZE.get(aspect_ratio, {"width": 768, "height": 1024})


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


_load_env_file()
FAL_KEY = os.environ.get("FAL_KEY", "")


def check_fal_key() -> None:
    if not FAL_KEY:
        sys.exit("Error: FAL_KEY not found. Add it to .env at the project root.")
    os.environ["FAL_KEY"] = FAL_KEY


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _upload(path: Path, label: str) -> str:
    print(f"  Uploading {label}...", end=" ", flush=True)
    url = fal_client.upload_file(str(path))
    print("✓")
    return url


def _download(url: str, dest: Path) -> None:
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    dest.write_bytes(resp.content)


def _next_output_path(output_dir: Path, base: str) -> Path:
    """Atomically claim the next `{base}_v{N}.png` path under output_dir.

    Uses O_CREAT | O_EXCL so two parallel callers can never claim the same N —
    the loser sees FileExistsError and bumps to N+1. Leaves a 0-byte placeholder
    that the caller overwrites when it writes the real output.
    """
    version = 1
    while True:
        candidate = output_dir / f"{base}_v{version}.png"
        try:
            fd = os.open(candidate, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            os.close(fd)
            return candidate
        except FileExistsError:
            version += 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python3 .claude/skills/model-product-shoot/generate-model-product-shoot.py brands/[brand]/generation/model-product-shoot/[output-name]")

    output_dir = Path(sys.argv[1])
    spec_path  = output_dir / "model-product-shoot-spec.json"

    if not spec_path.exists():
        sys.exit(f"Error: model-product-shoot-spec.json not found at {spec_path}")

    with open(spec_path) as f:
        spec = json.load(f)

    output_name      = spec.get("output_name", output_dir.name)
    composition_ref  = Path(spec["composition_reference"])
    product_image    = Path(spec["product_image"])
    model_headshot   = Path(spec["model_headshot"])
    styled_image     = Path(spec["styled_image"])
    aspect_ratio     = spec.get("aspect_ratio", "3:4")
    additional_notes = spec.get("additional_notes", "").strip()

    for label, path in [
        ("composition reference", composition_ref),
        ("product image",         product_image),
        ("model headshot",        model_headshot),
        ("styled image",          styled_image),
    ]:
        if not path.exists():
            sys.exit(f"Error: {label} not found: {path}")

    check_fal_key()

    print(f"\n{output_name} — model product shoot [gpt-image-2.5-sunburst]")
    print("Uploading images...")

    image_urls = [
        _upload(composition_ref, "composition reference (Image 1)"),
        _upload(product_image,   "product (Image 2)"),
        _upload(model_headshot,  "model headshot (Image 3)"),
        _upload(styled_image,    "styled model (Image 4)"),
    ]

    prompt = PROMPT + (f"\n\n{additional_notes}" if additional_notes else "")

    payload = {
        "prompt":        prompt,
        "image_urls":    image_urls,
        "image_size":    _image_size(aspect_ratio),
        "num_images":    1,
        "output_format": "png",
        "quality":       "high",
    }

    print("\nGenerating...")
    result = fal_client.run(EDIT_MODEL, arguments=payload)

    images = result.get("images", [])
    if not images or not images[0].get("url"):
        sys.exit("Error: no image returned from FAL.")

    out_path = _next_output_path(output_dir, output_name)
    try:
        _download(images[0]["url"], out_path)
    except BaseException:
        out_path.unlink(missing_ok=True)
        raise

    print(f"  ✓ {out_path.name}")
    print(f"\nDone. Output → {out_path}")


if __name__ == "__main__":
    main()
