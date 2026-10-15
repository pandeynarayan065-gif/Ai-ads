#!/usr/bin/env python3
"""Put the label's two small text lines back, exactly as printed, in the v2 studio hero clip.

Veo kept the v2 first frame's label (sticker edges, wordmark, wave panel, FOR ALL HAIR TYPES) through its own
push-in, but redrew the two small lines wrong ("Instont Hoir Volume & Testure", and the volume line garbled).

- The label is followed frame to frame with optical flow on its own print (similarity: scale + shift + a little
  roll), chained forward from frame 0, where its geometry is known exactly (build_first_v2.py: axis x 542.5,
  radius 168.8 px, 0.855 px per art row, sticker top y 661).
- Each line is drawn from the real label art (label-flat.jpg) wrapped round the bottle at that frame's scale, so it
  stays sharp through the zoom; its position is refined against Veo's own (garbled) line by matching.
- Veo's garbled strokes are taken out (thin dark strokes on the paper / thin light strokes on the wave panel,
  filled from around them) and the real line is printed in the colour Veo gives its own print there in that frame;
  water drops over the line stay on top (only Veo's text strokes are replaced, the rest of the pixel is kept).

  python3 ads/spraymax/studio-hero/fix_text_v2.py clips/hero-v2-8s.mp4 out.mp4
"""
import subprocess
import sys

import cv2
import numpy as np

src, out_path = sys.argv[1], sys.argv[2]
ONLY = [int(v) for v in sys.argv[3].split(",")] if len(sys.argv) > 3 else None

ART = cv2.imread("brand/spraymax/assets/label-flat.jpg").astype(np.float32)
U_C, XC0, R0, K0, TOP0 = 702.0, 542.5, 168.8, 0.855, 661.0         # frame-0 geometry of the label
# the two lines in art coordinates (v rows, u columns) and how they are printed
LINES = [dict(name="small", v0=656, v1=692, u0=536, u1=866, dark=True),     # Instant Hair Volume & Texture
         dict(name="volume", v0=862, v1=892, u0=600, u1=806, dark=False)]   # 100ml/3.38fl.oz.

cap = cv2.VideoCapture(src)
fps = cap.get(cv2.CAP_PROP_FPS)
frames = []
while True:
    ok, f = cap.read()
    if not ok:
        break
    frames.append(f)
N = len(frames)
H, W = frames[0].shape[:2]
gray = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]


def art_to_f0(u, v):
    x = XC0 + R0 * np.sin((u - U_C) * K0 / R0)
    y = TOP0 + v * K0
    return x, y


# ---- track the label: frame-to-frame similarity on its own print, chained from frame 0 ----
S = np.zeros((N, 3, 3))
S[0] = np.eye(3)
lab_poly0 = np.array([art_to_f0(u, v) for u, v in ((520, 60), (884, 60), (884, 940), (520, 940))], np.float64)
lk = dict(winSize=(21, 21), maxLevel=4, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 40, 0.01))
res_max = 0.0
for i in range(1, N):
    poly = (np.c_[lab_poly0, np.ones(4)] @ S[i - 1].T)[:, :2]
    msk = np.zeros((H, W), np.uint8)
    cv2.fillPoly(msk, [np.round(poly).astype(np.int32)], 255)
    p0 = cv2.goodFeaturesToTrack(gray[i - 1], 500, 0.004, 5, mask=msk)
    M_ = None
    if p0 is not None and len(p0) >= 10:
        p1, s1, _ = cv2.calcOpticalFlowPyrLK(gray[i - 1], gray[i], p0, None, **lk)
        pb, s2, _ = cv2.calcOpticalFlowPyrLK(gray[i], gray[i - 1], p1, None, **lk)
        good = (s1.ravel() == 1) & (s2.ravel() == 1) & (np.linalg.norm((p0 - pb).reshape(-1, 2), axis=1) < 0.6)
        if good.sum() >= 10:
            M_, inl = cv2.estimateAffinePartial2D(p0.reshape(-1, 2)[good], p1.reshape(-1, 2)[good],
                                                  method=cv2.RANSAC, ransacReprojThreshold=1.0)
    step = np.vstack([M_, [0, 0, 1]]) if M_ is not None else np.eye(3)
    S[i] = step @ S[i - 1]
# smooth the chain a little (the camera moves smoothly)
par = np.array([[s_[0, 0], s_[1, 0], s_[0, 2], s_[1, 2]] for s_ in S])
for c in range(4):
    par[:, c] = cv2.GaussianBlur(np.pad(par[:, c], 4, mode="edge").reshape(-1, 1), (1, 0), 1.0).ravel()[4:-4]
for i in range(N):
    a_, b_, tx, ty = par[i]
    S[i] = np.array([[a_, -b_, tx], [b_, a_, ty], [0, 0, 1]])
zoom = np.hypot(par[:, 0], par[:, 1])
print(f"label scale: x{zoom[0]:.2f} -> x{zoom[-1]:.2f}, roll {np.degrees(np.arctan2(par[-1, 1], par[-1, 0])):+.2f} deg")


def render_line(L, i, dx=0.0, dy=0.0):
    """The real line, in frame i: (x0, y0, coverage alpha, box) or None when it is out of frame."""
    us = np.array([L["u0"], L["u1"], L["u1"], L["u0"]], float)
    vs = np.array([L["v0"], L["v0"], L["v1"], L["v1"]], float)
    pts = np.c_[np.array(art_to_f0(us, vs)).T, np.ones(4)] @ S[i].T
    x0, y0 = int(np.floor(pts[:, 0].min())) - 4, int(np.floor(pts[:, 1].min())) - 4
    x1, y1 = int(np.ceil(pts[:, 0].max())) + 5, int(np.ceil(pts[:, 1].max())) + 5
    if x0 < 2 or y0 < 2 or x1 > W - 2 or y1 > H - 2:
        return None
    gx, gy = np.meshgrid(np.arange(x0, x1, dtype=np.float64) - dx, np.arange(y0, y1, dtype=np.float64) - dy)
    Si = np.linalg.inv(S[i])
    fx = Si[0, 0] * gx + Si[0, 1] * gy + Si[0, 2]
    fy = Si[1, 0] * gx + Si[1, 1] * gy + Si[1, 2]
    u = (U_C + (R0 / K0) * np.arcsin(np.clip((fx - XC0) / R0, -1, 1))).astype(np.float32)
    v = ((fy - TOP0) / K0).astype(np.float32)
    A = cv2.remap(ART, u, v, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    Ag = A.mean(axis=2)
    if L["dark"]:                                                # dark print on white paper
        alpha = np.clip((235 - Ag) / 150, 0, 1)
    else:                                                        # white print on the wave photo
        bgv = cv2.morphologyEx(Ag, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
        alpha = np.clip((Ag - bgv - 25) / 90, 0, 1)
    inside = (u >= L["u0"]) & (u <= L["u1"]) & (v >= L["v0"]) & (v <= L["v1"])
    alpha = alpha * inside
    return x0, y0, alpha.astype(np.float32), (x0, y0, x1, y1)


def fix_line(frame, L, i, weight=1.0, measure_only=False):
    r = render_line(L, i)
    if r is None:
        return frame, None
    x0, y0, alpha, (x0b, y0b, x1b, y1b) = r
    reg = frame[y0b:y1b, x0b:x1b].astype(np.float32)
    g = reg.mean(axis=2)
    sc = zoom[i]
    ksz = max(5, int(round(5 * sc)) | 1)
    # refine the position: match the real line against Veo's line (both as stroke maps)
    if L["dark"]:
        veo_str = cv2.morphologyEx(g, cv2.MORPH_BLACKHAT, np.ones((ksz, ksz), np.uint8))
    else:
        veo_str = cv2.morphologyEx(g, cv2.MORPH_TOPHAT, np.ones((ksz, ksz), np.uint8))
    best = (-2, 0, 0)
    P = int(3 + 3 * sc)
    pad = np.pad(alpha, P)
    for dy in range(-P, P + 1, 1):
        for dx in range(-P, P + 1, 1):
            a_s = pad[P - dy:P - dy + alpha.shape[0], P - dx:P - dx + alpha.shape[1]]
            c = np.corrcoef(a_s.ravel(), veo_str.ravel())[0, 1]
            if c > best[0]:
                best = (c, dx, dy)
    _, dx, dy = best
    if measure_only:
        return frame, best
    alpha = pad[P - dy:P - dy + alpha.shape[0], P - dx:P - dx + alpha.shape[1]]
    # match Veo's focus there: the blur that makes the real line's strokes look most like Veo's
    best_b = (-2, 0.0)
    for sg in (0.0, 0.6, 1.0, 1.5, 2.2, 3.0, 4.0):
        a_b = cv2.GaussianBlur(alpha, (0, 0), sg) if sg else alpha
        c = np.corrcoef(a_b.ravel(), veo_str.ravel())[0, 1]
        if c > best_b[0] + 0.003:
            best_b = (c, sg)
    if best_b[1]:
        alpha = cv2.GaussianBlur(alpha, (0, 0), best_b[1])
    # Veo's strokes out
    thr = 14 if L["dark"] else 18
    strokes = (veo_str > thr).astype(np.uint8)
    strokes = cv2.dilate(strokes, np.ones((3, 3), np.uint8))
    strokes[:2], strokes[-2:], strokes[:, :2], strokes[:, -2:] = 0, 0, 0, 0
    clean = cv2.inpaint(np.clip(reg, 0, 255).astype(np.uint8), strokes, 3, cv2.INPAINT_TELEA).astype(np.float32)
    # ink colour: Veo's own print here this frame (its darkest / brightest stroke pixels, not the soft edges)
    sel = veo_str > thr * 1.6
    if sel.sum() > 10:
        vals = reg[sel]
        lum = vals.mean(axis=1)
        ink = (vals[lum <= np.percentile(lum, 20)] if L["dark"] else vals[lum >= np.percentile(lum, 80)]).mean(axis=0)
    else:
        ink = np.array([40, 40, 40], np.float32) if L["dark"] else np.array([235, 235, 235], np.float32)
    a3 = alpha[..., None]
    new = clean * (1 - a3) + ink[None, None, :] * a3
    out = frame.astype(np.float32)
    out[y0b:y1b, x0b:x1b] = reg * (1 - weight) + new * weight
    return np.clip(out, 0, 255).round().astype(np.uint8), (best[0], dx, dy, best_b[1])


# pass 1: how well Veo's own line still matches the real one (low while water runs over the label)
corr = {L["name"]: np.full(N, np.nan) for L in LINES}
for i, f in enumerate(frames):
    for L in LINES:
        _, info = fix_line(f, L, i, measure_only=True)
        if info is not None:
            corr[L["name"]][i] = info[0]
weights = {}
for L in LINES:
    c = corr[L["name"]].copy()
    c = np.where(np.isnan(c), -1, c)
    w = np.clip((c - 0.30) / 0.15, 0, 1)                      # clear below 0.30, full above 0.45
    w = np.minimum(w, np.minimum.accumulate(np.r_[w[1:], 1])[:N] * 0 + w)
    k = np.ones(5) / 5                                        # no popping: ease in and out over a few frames
    w = np.convolve(np.pad(np.minimum(w, np.convolve(np.pad(w, 2, mode="edge"), np.ones(5), "valid") / 5), 2,
                           mode="edge"), k, "valid")
    weights[L["name"]] = w
    print(f"{L['name']}: printed in {int((w > 0.99).sum())} frames, faded in {int(((w > 0) & (w <= 0.99)).sum())}, "
          f"left to Veo/water in {int((w <= 0).sum())}")

enc = None if ONLY else subprocess.Popen(
    ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
     "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p", out_path], stdin=subprocess.PIPE)
for i, f in enumerate(frames):
    if ONLY and i not in ONLY:
        continue
    out = f
    for L in LINES:
        wgt = float(weights[L["name"]][i])
        if wgt > 0.01:
            out, _ = fix_line(out, L, i, weight=wgt)
    if ONLY:
        cv2.imwrite(f"{out_path}-f{i}.png", out)
    else:
        enc.stdin.write(out.tobytes())
if enc:
    enc.stdin.close()
    if enc.wait() != 0:
        raise SystemExit("ffmpeg failed")
np.save(out_path + "-corr.npy", np.array([corr[L["name"]] for L in LINES]))
