#!/usr/bin/env python3
"""Generate ad images with kie.ai (Nano Banana Pro by default).

The API key is read from the KIE_API_KEY environment variable (or a
gitignored `.env` file in the repo root). Never commit the key.

Usage:
  python3 scripts/kie_generate.py credits
  python3 scripts/kie_generate.py image --prompt-file <prompt.md> --out <dir> \
      [--aspect 4:5] [--resolution 2K] [--ref product.jpg --ref logo.png] [--yes]
  python3 scripts/kie_generate.py video --prompt-file <motion.md> --out <dir> \
      [--image first-frame.jpg] [--model veo3_fast] [--aspect 9:16] \
      [--resolution 1080p] [--duration 8] [--mode frames|reference] [--yes]
  python3 scripts/kie_generate.py seedance --prompt-file <prompt.md> --out <dir> \
      [--ref sheet.jpg --ref layout-1.jpg ...] | [--first-frame f.jpg [--last-frame l.jpg]] \
      [--resolution 720p] [--aspect 9:16] [--duration 12] [--audio] [--draft] [--yes]
  python3 scripts/kie_generate.py seedance-final --draft-task-id <id> --duration 12 --out <dir> [--yes]

Without --yes, `image` and `video` only print what they would send and spend nothing.
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
            result = json.loads(data["resultJson"])
            nested = result.get("data") or {}
            return (result.get("resultUrls") or result.get("result_urls")
                    or nested.get("result_urls") or nested.get("resultUrls"))
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


def cmd_video(args):
    prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()
    images = args.image or []
    body = {
        "model": "veo-3-1",
        "input": {
            "prompt": prompt,
            "model": args.model,
            "aspect_ratio": args.aspect,
            "resolution": args.resolution,
            "duration": args.duration,
        },
    }
    if images:
        if args.mode == "reference":
            if not 1 <= len(images) <= 3 or args.duration != 8:
                sys.exit("Reference mode needs 1-3 --image references and --duration 8.")
            body["input"]["generation_type"] = "REFERENCE_2_VIDEO"
        else:
            body["input"]["generation_type"] = "FIRST_AND_LAST_FRAMES_2_VIDEO"
    print(f"Model: veo-3-1 / {args.model} | aspect {args.aspect} | {args.resolution} | {args.duration}s")
    label = "References" if args.mode == "reference" else "Frames"
    print(f"{label}: {images or 'none (text to video)'}")
    print(f"Prompt ({len(prompt)} chars):\n{prompt}\n")
    if not args.yes:
        print("Dry run — nothing sent, no credits spent. Re-run with --yes to generate.")
        return

    before = credits()
    print(f"Credits before: {before}")
    if images:
        body["input"]["image_urls"] = [upload(Path(i)) if not i.startswith("http") else i for i in images]
    task_id = request("POST", f"{API}/api/v1/jobs/createTask", body)["taskId"]
    print(f"Task: {task_id}")
    urls = wait_for(task_id, timeout=1500)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    for i, url in enumerate(urls, 1):
        dest = out / f"{stamp}-{i}.mp4"
        urllib.request.urlretrieve(url, dest)
        print(f"Saved {dest}")
    (out / f"{stamp}.json").write_text(json.dumps(
        {"task_id": task_id, "request": body, "result_urls": urls}, indent=2))
    print(f"Credits after: {credits()} (was {before})")


# Seedance 2.5 on kie, credits per second of output, no video input (kie.ai/seedance-2-5, checked 2026-11-02).
# Reference images and audio add no billable seconds. Draft mode is 480p; the final from a draft is 1080p.
SEEDANCE_RATE = {"480p": 28, "720p": 63, "1080p": 158}


def run_video_task(body, out, before, timeout=2400):
    task_id = request("POST", f"{API}/api/v1/jobs/createTask", body)["taskId"]
    print(f"Task: {task_id}", flush=True)
    urls = wait_for(task_id, timeout=timeout)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    for i, url in enumerate(urls, 1):
        dest = out / f"{stamp}-{i}.mp4"
        urllib.request.urlretrieve(url, dest)
        print(f"Saved {dest}")
    (out / f"{stamp}.json").write_text(json.dumps(
        {"task_id": task_id, "request": body, "result_urls": urls}, indent=2))
    print(f"Credits after: {credits()} (was {before})")


def cmd_seedance(args):
    prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()
    refs = args.ref or []
    if refs and args.first_frame:
        sys.exit("Seedance can't combine --ref images with --first-frame (kie rejects the request).")
    res = "480p" if args.draft else args.resolution
    inp = {"prompt": prompt, "resolution": res, "aspect_ratio": args.aspect, "duration": args.duration,
           "generate_audio": args.audio}
    if args.draft:
        inp["draft"] = True
    body = {"model": "bytedance/seedance-2-5", "input": inp}
    cost = SEEDANCE_RATE[res] * args.duration
    print(f"Model: bytedance/seedance-2-5 | {res}{' draft' if args.draft else ''} | {args.aspect} | "
          f"{args.duration}s | audio {'on' if args.audio else 'off'}")
    print(f"Estimated cost: {cost} credits (${cost * 0.005:.2f})")
    print(f"References (Image 1, 2, ... in this order): {refs or 'none'}")
    if args.first_frame:
        print(f"First frame: {args.first_frame}  Last frame: {args.last_frame or 'none'}")
    print(f"Prompt ({len(prompt)} chars):\n{prompt}\n")
    if not args.yes:
        print("Dry run — nothing sent, no credits spent. Re-run with --yes to generate.")
        return
    before = credits()
    print(f"Credits before: {before}")
    if before < cost:
        sys.exit(f"Not enough credits: {before} < {cost}.")
    up = lambda x: x if x.startswith("http") else upload(Path(x))  # noqa: E731
    if refs:
        inp["reference_image_urls"] = [up(r) for r in refs]
    if args.first_frame:
        inp["first_frame_url"] = up(args.first_frame)
        if args.last_frame:
            inp["last_frame_url"] = up(args.last_frame)
    run_video_task(body, args.out, before)


def cmd_seedance_final(args):
    body = {"model": "bytedance/seedance-2-5-draft",
            "input": {"draft_task_id": args.draft_task_id, "resolution": "1080p"}}
    cost = SEEDANCE_RATE["1080p"] * args.duration
    print(f"Final 1080p from draft {args.draft_task_id} | estimated cost {cost} credits (${cost * 0.005:.2f}) "
          "(kie doesn't publish a separate draft-final price; this assumes the 1080p rate)")
    if not args.yes:
        print("Dry run — nothing sent, no credits spent. Re-run with --yes to generate.")
        return
    before = credits()
    print(f"Credits before: {before}")
    run_video_task(body, args.out, before)


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
    vid = sub.add_parser("video")
    vid.add_argument("--prompt-file", required=True)
    vid.add_argument("--out", required=True)
    vid.add_argument("--image", action="append", help="first (and optional last) frame, or a reference image, path or URL")
    vid.add_argument("--mode", default="frames", choices=["frames", "reference"],
                     help="frames: images are first/last frames; reference: images are product references (1-3)")
    vid.add_argument("--model", default="veo3_fast", choices=["veo3_fast", "veo3_lite", "veo3"])
    vid.add_argument("--aspect", default="9:16", choices=["9:16", "16:9", "Auto"])
    vid.add_argument("--resolution", default="1080p", choices=["720p", "1080p", "4k"])
    vid.add_argument("--duration", type=int, default=8, choices=[4, 6, 8])
    vid.add_argument("--yes", action="store_true", help="actually generate and spend credits")
    vid.set_defaults(func=cmd_video)
    sd = sub.add_parser("seedance")
    sd.add_argument("--prompt-file", required=True)
    sd.add_argument("--out", required=True)
    sd.add_argument("--ref", action="append", help="reference image path or URL, in Image 1, 2, ... order (max 30)")
    sd.add_argument("--first-frame", help="first frame (not with --ref)")
    sd.add_argument("--last-frame", help="last frame (needs --first-frame)")
    sd.add_argument("--resolution", default="720p", choices=["480p", "720p", "1080p"])
    sd.add_argument("--aspect", default="9:16", choices=["9:16", "16:9", "1:1", "3:4", "4:3", "21:9", "adaptive"])
    sd.add_argument("--duration", type=int, default=12, help="4-30 s")
    sd.add_argument("--audio", action="store_true", help="generate audio (off by default; we add sound in post)")
    sd.add_argument("--draft", action="store_true", help="480p draft; finish it with seedance-final at 1080p")
    sd.add_argument("--yes", action="store_true", help="actually generate and spend credits")
    sd.set_defaults(func=cmd_seedance)
    sf = sub.add_parser("seedance-final")
    sf.add_argument("--draft-task-id", required=True)
    sf.add_argument("--duration", type=int, required=True, help="the draft's duration, for the cost estimate")
    sf.add_argument("--out", required=True)
    sf.add_argument("--yes", action="store_true", help="actually generate and spend credits")
    sf.set_defaults(func=cmd_seedance_final)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
