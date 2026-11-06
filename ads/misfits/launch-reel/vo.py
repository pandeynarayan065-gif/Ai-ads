"""Misfits launch reel voiceover with Kokoro (free, open-source, runs locally).
Usage: python3 vo.py <model_dir> [voice]"""
import sys, json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
md = sys.argv[1]; voice = sys.argv[2] if len(sys.argv) > 2 else "am_michael"
LINES = [
    "Every ad in your feed looks the same.",
    "Same look. Same offer. Same flick.",
    "Then one doesn't fit in.",
    "And you just watched this for eight seconds.",
    "Imagine it was your product.",
    "Misfits. Ads that don't fit in.",
    "Comment film, to start yours.",
]
k = Kokoro(f"{md}/kokoro-v1.0.onnx", f"{md}/voices-v1.0.bin")
out = []
for i, t in enumerate(LINES):
    a, sr = k.create(t, voice=voice, speed=1.0, lang="en-us")
    # trim silence
    idx = np.where(np.abs(a) > 0.01)[0]; a = a[max(idx[0]-200,0): idx[-1]+800]
    sf.write(f"vo/line{i}.wav", a, sr); out.append({"text": t, "dur": round(len(a)/sr, 3)})
json.dump(out, open("vo/lines.json", "w"), indent=1); print(json.dumps(out, indent=1))
