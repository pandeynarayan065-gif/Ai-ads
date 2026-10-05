#!/usr/bin/env python3
"""Generate ad images with kie.ai (Nano Banana Pro by default).

The API key is read from the KIE_API_KEY environment variable (or a
gitignored `.env` file in the repo root). Never commit the key.

Usage:
  python3 scripts/kie_generate.py credits
  python3 scripts/kie_generate.py image --prompt-file <prompt.md> --out <dir> \
      [--aspect 4:5] [--resolution 2K] [--ref product.jpg --ref logo.png] [--yes]

Without --yes, `image` only prints what it would send and spends nothing.
Reference images (--ref) can be local files (uploaded to kie.ai first) or URLs.
"""
import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

API = "https://api.kie.ai"
UPLOAD = "https://kieai.redpandaai.co/api/file-stream-upload"
ROOT = Path(__file__).resolve().parent.parent


def api_key():
    key = os.environ.get("KIE_API_KEY")
    env_file = ROOT / ".env"
    if not key and env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.strip().startswith("KIE_API_KEY="):
                key = line.split("=", 1)[1].strip().strip("'\"")
    if not key:
        sys.exit("KIE_API_KEY is not set. Add it as an environment variable (see README).")
    return key


def request(method, url, body=None, headers=None):
    headers = {"Authorization": f"Bearer {api_key()}", **(headers or {})}
    data = None
    if isinstance(body, dict):
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    elif isinstance(body, bytes):
        data = body
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            payload = json.loads(resp.read())
    except urllib.error.HTTPError as err:
        sys.exit(f"HTTP {err.code} from {url}: {err.read().decode(errors='replace')[:500]}")
    if payload.get("code") not in (200, None):
        sys.exit(f"kie.ai error {payload.get('code')}: {payload.get('msg')}")
    return payload.get("data")


def credits():
    return request("GET", f"{API}/api/v1/chat/credit")


def upload(path: Path):
    boundary = uuid.uuid4().hex
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    parts = []
    for name, value in (("uploadPath", "ai-ads/refs"), ("fileName", path.name)):
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
        f"Content-Type: {mime}\r\n\r\n".encode() + path.read_bytes() + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode())
    data = request("POST", UPLOAD, b"".join(parts),
                   {"Content-Type": f"multipart/form-data; boundary={boundary}"})
    return data.get("fileUrl") or data["downloadUrl"]


def wait_for(task_id, timeout=600):
    start = time.time()
    while time.time() - start < timeout:
        data = request("GET", f"{API}/api/v1/jobs/recordInfo?taskId={task_id}")
        state = data.get("state")
        print(f"  state: {state}", flush=True)
        if state == "success":
            return json.loads(data["resultJson"])["resultUrls"]
        if state == "fail":
            sys.exit(f"Generation failed: {data.get('failCode')} {data.get('failMsg')}")
        time.sleep(5)
    sys.exit(f"Timed out; task {task_id} may still finish — check https://kie.ai/logs")


def cmd_credits(_args):
    print(f"Credits remaining: {credits()}")


def cmd_image(args):
    prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()
    refs = args.ref or []
    body = {
        "model": args.model,
        "input": {
            "prompt": prompt,
            "image_input": refs,
            "aspect_ratio": args.aspect,
            "resolution": args.resolution,
            "output_format": "png",
        },
    }
    print(f"Model: {args.model} | aspect {args.aspect} | resolution {args.resolution}")
    print(f"References: {refs or 'none'}")
    print(f"Prompt ({len(prompt)} chars):\n{prompt}\n")
    if not args.yes:
        print("Dry run — nothing sent, no credits spent. Re-run with --yes to generate.")
        return

    before = credits()
    print(f"Credits before: {before}")
    uploaded = [upload(Path(r)) if not r.startswith("http") else r for r in refs]
    body["input"]["image_input"] = uploaded
    task_id = request("POST", f"{API}/api/v1/jobs/createTask", body)["taskId"]
    print(f"Task: {task_id}")
    urls = wait_for(task_id)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    for i, url in enumerate(urls, 1):
        dest = out / f"{stamp}-{i}.png"
        urllib.request.urlretrieve(url, dest)
        print(f"Saved {dest}")
    (out / f"{stamp}.json").write_text(json.dumps(
        {"task_id": task_id, "request": body, "result_urls": urls}, indent=2))
    print(f"Credits after: {credits()} (was {before})")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("credits").set_defaults(func=cmd_credits)
    img = sub.add_parser("image")
    img.add_argument("--prompt-file", required=True)
    img.add_argument("--out", required=True)
    img.add_argument("--model", default="nano-banana-pro")
    img.add_argument("--aspect", default="4:5")
    img.add_argument("--resolution", default="2K", choices=["1K", "2K", "4K"])
    img.add_argument("--ref", action="append", help="reference image path or URL (max 8)")
    img.add_argument("--yes", action="store_true", help="actually generate and spend credits")
    img.set_defaults(func=cmd_image)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
