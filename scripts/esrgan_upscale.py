#!/usr/bin/env python3
"""Free local AI upscale of a video with Real-ESRGAN (realesr-general-x4v3, BSD-3, xinntao/Real-ESRGAN), CPU.

The network (SRVGGNetCompact) is written out here so no basicsr/realesrgan packages are needed: only torch and
the weights file (https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth).

  python scripts/esrgan_upscale.py <in.mp4> <out.mp4> --weights realesr-general-x4v3.pth [--size 2160x3840]
         [--frames 0-287] [--tile 0]

Runs the 4x model on every frame, then resizes (Lanczos) to --size. Writes a high-quality H.264 (crf 12) video
with the input's frame rate; audio is not copied (the finish adds it).
"""
import subprocess
import sys
import time

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F


class SRVGGNetCompact(nn.Module):
    """Real-ESRGAN's compact VGG-style network (as in basicsr.archs.srvgg_arch)."""

    def __init__(self, num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=32, upscale=4):
        super().__init__()
        self.upscale = upscale
        body = [nn.Conv2d(num_in_ch, num_feat, 3, 1, 1), nn.PReLU(num_parameters=num_feat)]
        for _ in range(num_conv):
            body += [nn.Conv2d(num_feat, num_feat, 3, 1, 1), nn.PReLU(num_parameters=num_feat)]
        body.append(nn.Conv2d(num_feat, num_out_ch * upscale * upscale, 3, 1, 1))
        self.body = nn.ModuleList(body)
        self.upsampler = nn.PixelShuffle(upscale)

    def forward(self, x):
        out = x
        for layer in self.body:
            out = layer(out)
        out = self.upsampler(out)
        return out + F.interpolate(x, scale_factor=self.upscale, mode="nearest")


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                          "stream=width,height,r_frame_rate", "-of", "csv=p=0", path], capture_output=True, text=True)
    w, h, r = out.stdout.strip().split(",")
    return int(w), int(h), r


def main():
    a = sys.argv[1:]
    src, dst = a[0], a[1]
    weights = a[a.index("--weights") + 1]
    ow, oh = (int(v) for v in (a[a.index("--size") + 1] if "--size" in a else "2160x3840").split("x"))
    torch.set_num_threads(max(1, torch.get_num_threads()))
    net = SRVGGNetCompact()
    sd = torch.load(weights, map_location="cpu")
    net.load_state_dict(sd.get("params", sd.get("params_ema", sd)))
    net.eval()
    w, h, rate = probe(src)
    dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{ow}x{oh}",
                            "-r", rate, "-i", "-", "-c:v", "libx264", "-crf", "12", "-preset", "slow", "-pix_fmt", "yuv420p",
                            dst], stdin=subprocess.PIPE)
    n, t0 = 0, time.time()
    fsize = w * h * 3
    with torch.inference_mode():
        while True:
            buf = dec.stdout.read(fsize)
            if len(buf) < fsize:
                break
            x = torch.from_numpy(np.frombuffer(buf, np.uint8).reshape(h, w, 3).copy()).permute(2, 0, 1)[None].float() / 255
            y = net(x).clamp(0, 1)
            y = F.interpolate(y, size=(oh, ow), mode="bicubic", align_corners=False, antialias=True).clamp(0, 1)
            enc.stdin.write((y[0].permute(1, 2, 0).numpy() * 255 + 0.5).astype(np.uint8).tobytes())
            n += 1
            if n % 12 == 0:
                print(f"{n} frames, {(time.time() - t0) / n:.1f} s/frame", flush=True)
    enc.stdin.close()
    enc.wait()
    dec.wait()
    print(f"wrote {dst}: {n} frames in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
