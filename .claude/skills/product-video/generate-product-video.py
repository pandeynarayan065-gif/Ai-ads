#!/usr/bin/env python3
"""
generate-product-video.py — One-shot product video pipeline (Seedance 2.5).

Reads an agent-authored prompt from product-video-spec.json and dispatches it
verbatim to bytedance/seedance-2.5/reference-to-video along with the product image(s)
as references. No prompt assembly here —
the prompt is authored by the agent in the /product-video skill flow.

References (drive @Image1/@Image2... in the prompt, in this order):
  Image1..N   = product image(s) (product_image: one path or a list)
  then        = outfit image(s) for a styled model (outfit_images: the garment
                product shots from the styled model's style-spec.json), if any

No image of a person is ever uploaded. Seedance rejects any photoreal face as
"may contain likenesses of real people", AI-generated faces included, so the
model's identity is written into the prompt from their characteristics sheet
(models/<name>/characteristics.md). A reference video is never uploaded either.

Usage (run from project root):
  python3 .claude/skills/product-video/generate-product-video.py brands/[brand]/generation/product-video/[output-name]

Reads product-video-spec.json from the output folder.

Defaults if absent from spec: duration=15, resolution=720p, aspect_ratio=9:16.

Output:
  [output-name]_v1.mp4 (auto-increments on each run)

Pricing (Seedance 2.5, image references only, audio included):
  480p:  ~$0.22/sec
  720p:  ~$0.47/sec
  1080p: ~$1.05/sec (token billing scales with pixels × duration)

Duration: 4-30 seconds, the model's native limit. Nothing longer is allowed.
"""

import argparse
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

VIDEO_MODEL = "bytedance/seedance-2.5/reference-to-video"

VALID_RESOLUTIONS = {"480p", "720p", "1080p"}
MIN_DURATION, MAX_DURATION = 4, 30  # Seedance 2.5 native limit
VALID_DURATIONS = set(range(MIN_DURATION, MAX_DURATION + 1))
PRICE_PER_SEC = {"480p": 0.22, "720p": 0.47, "1080p": 1.05}
VALID_ASPECT_RATIOS = {"auto", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"}


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
    resp = requests.get(url, timeout=600)
    resp.raise_for_status()
    dest.write_bytes(resp.content)


def _claim_next_version(output_dir: Path, stem: str, ext: str) -> Path:
    """Atomically reserve the next `{stem}_v{N}{ext}` path under output_dir.

    Uses O_CREAT | O_EXCL so two parallel callers can never claim the same N —
    the loser sees FileExistsError and bumps to N+1. Leaves a 0-byte placeholder
    that the caller overwrites when it writes the real output.
    """
    version = 1
    while True:
        candidate = output_dir / f"{stem}_v{version}{ext}"
        try:
            fd = os.open(candidate, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            os.close(fd)
            return candidate
        except FileExistsError:
            version += 1


# ---------------------------------------------------------------------------
# Video generation
# ---------------------------------------------------------------------------

LIKENESS_HINTS = ("likeness", "real people", "private information")


def _paths(raw) -> list:
    if not raw:
        return []
    return [Path(p) for p in raw] if isinstance(raw, list) else [Path(raw)]


def generate_video(output_dir: Path, spec: dict) -> None:
    output_name   = spec.get("output_name", output_dir.name)
    product_images = _paths(spec.get("product_image"))
    outfit_images  = _paths(spec.get("outfit_images"))
    prompt        = spec.get("prompt", "").strip()
    resolution    = spec.get("resolution", "720p")
    aspect_ratio  = spec.get("aspect_ratio", "9:16")
    duration_raw  = spec.get("duration", 15)

    if not prompt:
        sys.exit(
            "Error: spec['prompt'] is missing or empty. "
            "The prompt must be authored by the agent in the /product-video flow "
            "and written verbatim into product-video-spec.json."
        )
    if not product_images:
        sys.exit("Error: spec['product_image'] is missing. Add the product image path.")

    try:
        duration = int(duration_raw)
    except (TypeError, ValueError):
        sys.exit(f"Error: duration must be an integer {MIN_DURATION}-{MAX_DURATION}, got {duration_raw!r}.")
    if duration not in VALID_DURATIONS:
        sys.exit(f"Error: duration must be an integer {MIN_DURATION}-{MAX_DURATION} (Seedance 2.5's limit), got {duration}.")
    if resolution not in VALID_RESOLUTIONS:
        sys.exit(f"Error: resolution must be one of {sorted(VALID_RESOLUTIONS)}, got {resolution!r}.")
    if aspect_ratio not in VALID_ASPECT_RATIOS:
        sys.exit(f"Error: aspect_ratio must be one of {sorted(VALID_ASPECT_RATIOS)}, got {aspect_ratio!r}.")

    for image in product_images + outfit_images:
        if not image.exists():
            sys.exit(f"Error: reference image not found: {image}")

    (output_dir / "video-prompt.txt").write_text(prompt)

    print(f"\n{output_name} — product video (Seedance 2.5)")
    print("Uploading reference images (no images of people: identity is in the prompt)...")

    image_urls = []
    for image in product_images:
        image_urls.append(_upload(image, f"product: {image.name} (Image {len(image_urls) + 1})"))
    for image in outfit_images:
        image_urls.append(_upload(image, f"outfit: {image.name} (Image {len(image_urls) + 1})"))

    print(f"\nGenerating {duration}s video at {resolution} {aspect_ratio} (Seedance 2.5, ~${duration * PRICE_PER_SEC[resolution]:.2f})...")
    try:
        result = fal_client.run(
            VIDEO_MODEL,
            arguments={
                "prompt": prompt,
                "image_urls": image_urls,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "duration": str(duration),
                "generate_audio": True,
            },
        )
    except Exception as exc:  # fal raises several error types; the message says which problem it is
        msg = str(exc)
        if any(h in msg.lower() for h in LIKENESS_HINTS):
            sys.exit(
                "Error: Seedance rejected a reference image as showing a real person, so nothing was made "
                "and nothing was charged.\nProduct and outfit images must not show a person or a face. "
                "Use a packshot-style image of the product on its own, then run again."
            )
        sys.exit(f"Error: Seedance didn't make the video: {msg[:500]}")

    video = result.get("video", {})
    video_url = video.get("url") if isinstance(video, dict) else None
    if not video_url:
        sys.exit("Error: no video returned from FAL.")

    out_path = _claim_next_version(output_dir, output_name, ".mp4")
    print("  Downloading video...", end=" ", flush=True)
    try:
        _download(video_url, out_path)
    except BaseException:
        out_path.unlink(missing_ok=True)
        raise
    print("✓")
    print(f"\nDone. Output → {out_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Product video pipeline (Seedance 2.5).")
    parser.add_argument(
        "output_dir",
        help="Path to the output folder (e.g. brands/[brand]/generation/product-video/jade-paris-tshirt)",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    spec_path  = output_dir / "product-video-spec.json"

    if not spec_path.exists():
        sys.exit(f"Error: product-video-spec.json not found at {spec_path}")

    with open(spec_path) as f:
        spec = json.load(f)

    check_fal_key()
    generate_video(output_dir, spec)


if __name__ == "__main__":
    main()
