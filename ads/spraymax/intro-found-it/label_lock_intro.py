#!/usr/bin/env python3
"""Lock the real Spraymax label onto the bottle in the intro take (clips/20261103-104914-1.mp4).

Seedance drew a lavender wordmark, a pale band and garbled small lines. Per frame:

1. Track: the AI label's own texture (wordmark + band) in reference frame REF is registered to every other
   frame with OpenCV ECC (full homography), always against REF, so nothing drifts. Frames where it can't lock
   (the bottle still tiny at the top of the frame) keep the AI pixels, with a short crossfade into the lock.
2. Wrap: in REF's coordinates the bottle is a cylinder (axis, radius, label bottom edge measured from the AI
   band), and the flat label art (label-hires.jpg) is wrapped round it at the AI print's own scale.
3. Light: the frame is pulled back into REF coordinates and the AI bottle's paper/plastic colour is measured
   on a grid across and along the bottle (its ink skipped), so the torch falloff, the cylinder shading and the
   cool cast carry onto the real print. Glove pixels (dark, unsaturated) are never painted.
4. Match: the print is softened and given the frame's own noise so it doesn't read as a sticker.

  python3 ads/spraymax/intro-found-it/label_lock_intro.py <clip.mp4> <out.mp4> [--scale 3] [--qa <dir>]

--scale renders onto a clip that is --scale times the 720x1280 take (e.g. the 2160x3840 Real-ESRGAN upscale);
the tracking always runs on the 720x1280 take, given with --track <take.mp4> in that case.
"""
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / "video/assets/label-hires.jpg"      # 5612x3820, 4x label-flat.jpg
ART_SCALE = 4.0                                    # hires px per label-flat px
# label-flat.jpg layout (px): front-panel centre, wordmark top, label height (measured)
ART_X0, ART_WM_TOP, ART_H = 701.0, 48.0, 955.0

W, H = 720, 1280
REF = 72                                           # 3.0 s: bottle large, label clear, no glove on it
# REF geometry, measured from the AI band (minAreaRect) and cross profiles of the bottle
REF_BOTTOM = np.array([406.1, 787.4])              # centre of the label's bottom edge (band's far edge)
REF_A = np.array([-0.819, -0.573])                 # unit vector along the axis, toward the cap
REF_R = 33.0                                       # bottle radius, px
LOCK_FROM = 52                                     # earlier, the bottle is tiny and the chained track drifts


def read(path, w, h):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(path), "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)


def bottle_coords(shape, s, bottom, a, r):
    """u (px along the axis from the label's bottom edge toward the cap) and v (across, -r..r) for every pixel of
    an image `s` times the 720x1280 take, in REF geometry."""
    hh, ww = shape
    yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
    px, py = (xx + 0.5) / s - 0.5 - bottom[0], (yy + 0.5) / s - 0.5 - bottom[1]
    n = np.array([-a[1], a[0]])
    return px * a[0] + py * a[1], px * n[0] + py * n[1]


def fit_k(ref_bgr):
    """Image px per label-flat px, from the AI wordmark's extent along the axis (its top = the art's wordmark top)."""
    hsv = cv2.cvtColor(ref_bgr, cv2.COLOR_BGR2HSV).astype(int)
    wm = (hsv[..., 0] >= 119) & (hsv[..., 0] <= 150) & (hsv[..., 1] > 50)
    u, v = bottle_coords((H, W), 1, REF_BOTTOM, REF_A, REF_R)
    sel = wm & (np.abs(v) < REF_R * 0.8) & (u > 0) & (u < 200)
    top = np.percentile(u[sel], 99.5)
    return top / (ART_H - ART_WM_TOP), top


def ecc_affine(tpl, img, mask, init):
    """Affine ECC, coarse (half size) then full; init is a 2x3 warp at full size."""
    crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 80, 1e-5)
    w = init.copy()
    w[:, 2] *= 0.5
    t2, i2 = cv2.resize(tpl, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA), \
        cv2.resize(img, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
    m2 = cv2.resize(mask, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_NEAREST)
    try:
        _, w = cv2.findTransformECC(t2, i2, w, cv2.MOTION_AFFINE, crit, m2, 3)
        w[:, 2] *= 2
    except cv2.error:                                   # a thin mask can fail at half size: go straight to full
        w = init.copy()
    return cv2.findTransformECC(tpl, img, w, cv2.MOTION_AFFINE, crit, mask, 5)


def label_pts(us, k):
    """Points on the label (REF coords) at axial positions us (fractions of the label length) and v = +-0.8 r."""
    n = np.array([-REF_A[1], REF_A[0]])
    return np.array([REF_BOTTOM + REF_A * (f * ART_H * k) + n * d for f in us for d in (-0.8 * REF_R, 0.8 * REF_R)],
                    np.float32)


def track(frames, k):
    """Warp (3x3) REF -> frame n for every frame, or None where it can't lock.

    The label's lower half (band end) and upper half (wordmark end) are each tracked with affine ECC (OpenCV's
    homography ECC diverges here) and joined into one homography through 8 points, which carries the perspective
    taper when the cap end lifts. Each half must land near its constant-velocity guess, and the two must agree
    with their last offset (the band end wins; the glove covers the wordmark end late in the shot). Tracking is
    against REF until it fails, then re-anchors on the last good frame (chained, so only a little drift)."""
    g = [cv2.GaussianBlur(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), 1.0) for f in frames]
    u, v = bottle_coords((H, W), 1, REF_BOTTOM, REF_A, REF_R)
    L = (ART_H - 10) * k
    core = np.abs(v) < REF_R * 0.85
    ref_masks = {"low": (core & (u > -4) & (u < 0.5 * L)).astype(np.uint8),
                 "up": (core & (u > 0.35 * L) & (u < 0.85 * L)).astype(np.uint8)}
    pts = {"low": label_pts((0.0, 0.42), k), "up": label_pts((0.58, 1.0), k)}
    A3 = lambda w: np.vstack([w, [0, 0, 1]]).astype(np.float64)  # noqa: E731
    Hs, cc = [None] * len(frames), [0.0] * len(frames)
    Hs[REF], cc[REF] = np.eye(3, dtype=np.float32), 1.0

    def anchor_masks(a):
        Ha = Hs[a].astype(np.float64)
        return {m: (cv2.warpPerspective(ref_masks[m], Ha, (W, H), flags=cv2.INTER_NEAREST) > 0).astype(np.uint8)
                for m in ref_masks}

    for step in (1, -1):
        # per half: the affine REF -> frame (as 3x3), and the one before it
        cur = {m: np.eye(3) for m in ref_masks}
        prev = {m: np.eye(3) for m in ref_masks}
        anchor, amasks = REF, dict(ref_masks)
        n = REF + step
        retried = False
        while 0 <= n < len(frames):
            Ha = np.eye(3) if anchor == REF else Hs[anchor].astype(np.float64)
            guess = {m: cur[m] @ np.linalg.inv(prev[m]) @ cur[m] for m in ref_masks}      # REF -> n
            res = {}
            for m in ref_masks:
                # ECC from the anchor frame: init = guess composed with REF -> anchor inverse
                init = (guess[m] @ np.linalg.inv(cur_anchor[m]))[:2].astype(np.float32) if anchor != REF else \
                    guess[m][:2].astype(np.float32)
                try:
                    c, w = ecc_affine(g[anchor], g[n], amasks[m], init)
                    res[m] = (c, A3(w) @ (cur_anchor[m] if anchor != REF else np.eye(3)))
                except cv2.error:
                    res[m] = (-1.0, None)
            ok = {m: res[m][0] >= 0.6 for m in ref_masks}
            for m in ref_masks:
                if ok[m] and np.abs(cv2.perspectiveTransform(pts[m][None], res[m][1])[0]
                                    - cv2.perspectiveTransform(pts[m][None], guess[m])[0]).max() > 18:
                    ok[m] = False
            rel = cur["up"] @ np.linalg.inv(cur["low"])
            if ok["low"] and ok["up"]:
                pred = cv2.perspectiveTransform(pts["up"][None], rel @ res["low"][1])[0]
                if np.abs(cv2.perspectiveTransform(pts["up"][None], res["up"][1])[0] - pred).max() > 5:
                    ok["up"] = False
            if not any(ok.values()):
                last = n - step
                if not retried and last != anchor and Hs[last] is not None:
                    anchor, retried = last, True                      # re-anchor on the last good frame
                    amasks = anchor_masks(anchor)
                    cur_anchor = dict(cur)
                    print(f"  frame {n}: re-anchoring on frame {anchor}")
                    continue
                print(f"  tracking stops at frame {n}: ECC low {res['low'][0]:.3f}, up {res['up'][0]:.3f}")
                break
            retried = False
            new = {}
            if ok["low"] and ok["up"]:
                new = {m: res[m][1] for m in ref_masks}
            elif ok["low"]:
                new = {"low": res["low"][1], "up": rel @ res["low"][1]}
            else:
                new = {"up": res["up"][1], "low": np.linalg.inv(rel) @ res["up"][1]}
            prev, cur = cur, new
            dst = np.vstack([cv2.perspectiveTransform(pts["low"][None], cur["low"])[0],
                             cv2.perspectiveTransform(pts["up"][None], cur["up"])[0]])
            Hn, _ = cv2.findHomography(np.vstack([pts["low"], pts["up"]]), dst, 0)
            corners = cv2.perspectiveTransform(label_pts((0.0, 1.0), k)[None], Hn)[0]
            if corners[:, 0].min() < 2 or corners[:, 1].min() < 2 or corners[:, 0].max() > W - 3 or corners[:, 1].max() > H - 3:
                print(f"  tracking stops at frame {n}: label leaves the frame")
                break
            Hs[n], cc[n] = Hn.astype(np.float32), max(res["low"][0], res["up"][0])
            n += step
    return Hs, cc


def main():
    a = sys.argv[1:]
    src, dst = a[0], a[1]
    s = int(a[a.index("--scale") + 1]) if "--scale" in a else 1
    take = a[a.index("--track") + 1] if "--track" in a else src
    qa = Path(a[a.index("--qa") + 1]) if "--qa" in a else None
    small = read(take, W, H)
    rate = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=r_frame_rate",
                           "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip()

    k, wm_top = fit_k(small[REF])
    print(f"k = {k:.4f} image px per label-flat px (wordmark top at u = {wm_top:.1f} px); "
          f"label {ART_H * k:.1f} px long, bottle radius {REF_R} px")
    Hs, cc = track(small, k)
    Hs = [h if (h is not None and i >= LOCK_FROM) else None for i, h in enumerate(Hs)]
    locked = [i for i, h in enumerate(Hs) if h is not None]
    print(f"locked frames {locked[0]}-{locked[-1]} ({len(locked)}), ECC min {min(cc[i] for i in locked):.3f}")

    # --- the label, rendered once in REF coordinates (a crop round the bottle) at output scale s ---------------
    art = cv2.imread(str(ART)).astype(np.float32) / 255
    paper_art = np.median(art[1200:2400, 1900:2300].reshape(-1, 3), axis=0)      # the art's white paper
    edge_px = int(8 * ART_SCALE)                                                  # the file's thin border lines
    art[:edge_px], art[-edge_px:] = paper_art, paper_art
    # the side panels' tiny text only reads as dots at this size: half its contrast
    side = np.ones(art.shape[1], np.float32)
    side[:int((ART_X0 - 240) * ART_SCALE)] = 0.5
    side[int((ART_X0 + 240) * ART_SCALE):] = 0.5
    art = paper_art + (art - paper_art) * side[None, :, None]
    corners = label_pts((0.0, 1.0), k)
    pad = REF_R + 12
    bx0, by0 = int(corners[:, 0].min() - pad), int(corners[:, 1].min() - pad)
    bx1, by1 = int(corners[:, 0].max() + pad), int(corners[:, 1].max() + pad)
    cw, ch = (bx1 - bx0) * s, (by1 - by0) * s
    T = np.array([[1, 0, bx0 * s], [0, 1, by0 * s], [0, 0, 1]], np.float64)     # crop -> REF (out scale)
    yy, xx = np.mgrid[0:ch, 0:cw].astype(np.float32)
    px, py = (xx + bx0 * s + 0.5) / s - 0.5 - REF_BOTTOM[0], (yy + by0 * s + 0.5) / s - 0.5 - REF_BOTTOM[1]
    nrm = np.array([-REF_A[1], REF_A[0]])
    u, v = px * REF_A[0] + py * REF_A[1], px * nrm[0] + py * nrm[1]
    inside = np.abs(v) < REF_R
    theta = np.arcsin(np.clip(v / REF_R, -0.9999, 0.9999))
    ax = (ART_X0 + theta * REF_R / k) * ART_SCALE
    ay = (ART_H - u / k) * ART_SCALE
    on_label = inside & (ay >= 0) & (ay <= ART_H * ART_SCALE - 1)
    blur_px = ART_SCALE / (k * s) * 0.45                              # pre-filter the hires art to the output pixel
    art_soft = cv2.GaussianBlur(art, (0, 0), max(0.3, blur_px))
    label = cv2.remap(art_soft, ax.astype(np.float32), ay.astype(np.float32), cv2.INTER_LINEAR,
                      borderMode=cv2.BORDER_REPLICATE)
    del art, art_soft
    reflect = label / paper_art                                       # 1 = white paper
    edge = np.clip((REF_R - np.abs(v)) * s / 1.2, 0, 1)               # fade over the cylinder's last ~1.2 px
    ends = np.clip(np.minimum(ay, ART_H * ART_SCALE - ay) / (ART_SCALE * 1.2 / k / s), 0, 1)
    paint_ref = (on_label * edge * ends).astype(np.float32)

    # light grid (v bins across, u bins along), from the AI's paper / plastic
    NV, NU = 14, 8
    u0, u1 = -0.25 * REF_R, ART_H * k + 0.15 * REF_R
    ub = np.clip(((u - u0) / (u1 - u0) * NU).astype(int), 0, NU - 1)
    vb = np.clip(((v + REF_R) / (2 * REF_R) * NV).astype(int), 0, NV - 1)
    band_lo = (ART_H - 700) * k                                       # the band and the small line sit below this
    bins = ub * NV + vb
    bottle_band = inside & (u > u0) & (u < u1) & (np.abs(v) < REF_R * 0.97) & ~((u > 0) & (u < band_lo))
    Lx = np.clip((v + REF_R) / (2 * REF_R) * NV * 16 - 0.5, 0, NV * 16 - 1).astype(np.float32)
    Ly = np.clip((u - u0) / (u1 - u0) * NU * 16 - 0.5, 0, NU * 16 - 1).astype(np.float32)

    lock_w = np.zeros(len(Hs), np.float32)
    for i in locked:
        lock_w[i] = 1.0
    for j, i in enumerate(locked[:4]):                                # crossfade into the lock
        lock_w[i] = (j + 1) / 5
    S = np.diag([s, s, 1]).astype(np.float64)
    Si = np.diag([1 / s, 1 / s, 1]).astype(np.float64)
    hs, ws = H * s, W * s
    dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{ws}x{hs}",
                            "-r", rate, "-i", "-", "-c:v", "libx264", "-crf", "12", "-preset", "slow", "-pix_fmt", "yuv420p",
                            dst], stdin=subprocess.PIPE)
    fsize = ws * hs * 3
    i = 0
    while True:
        buf = dec.stdout.read(fsize)
        if len(buf) < fsize:
            break
        f = np.frombuffer(buf, np.uint8).reshape(hs, ws, 3)
        if i >= len(Hs) or lock_w[i] == 0:
            enc.stdin.write(f.tobytes())
            i += 1
            continue
        Hn = S @ Hs[i].astype(np.float64) @ Si @ T                    # crop (out scale) -> frame i (out scale)
        back = cv2.warpPerspective(f, Hn, (cw, ch), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                                   borderMode=cv2.BORDER_REPLICATE)
        hsv = cv2.cvtColor(back, cv2.COLOR_BGR2HSV)
        back = back.astype(np.float32) / 255
        lum = back.mean(2)
        cand = bottle_band & (hsv[..., 1] < 60)
        light = np.zeros((NU * NV, 3), np.float32)
        valid = np.zeros(NU * NV, bool)
        cb, cpx = bins[cand], back[cand]
        order = np.argsort(cb, kind="stable")
        cb, cpx = cb[order], cpx[order]
        starts = np.searchsorted(cb, np.arange(NU * NV + 1))
        for b in range(NU * NV):
            px_ = cpx[starts[b]:starts[b + 1]]
            if len(px_) >= 4 * s * s:
                l = px_.mean(1)
                light[b] = np.median(px_[l >= np.percentile(l, 40)], axis=0)  # skip the AI's ink and specks
                valid[b] = True
        light, valid = light.reshape(NU, NV, 3), valid.reshape(NU, NV)
        for bv in range(NV):                                          # fill along u (under the band)
            idx = np.nonzero(valid[:, bv])[0]
            if len(idx):
                for c in range(3):
                    light[:, bv, c] = np.interp(np.arange(NU), idx, light[idx, bv, c])
        colok = valid.any(0)
        idx = np.nonzero(colok)[0]
        for bu in range(NU):                                          # and across v if a column was empty
            for c in range(3):
                light[bu, :, c] = np.interp(np.arange(NV), idx, light[bu, idx, c])
        light = cv2.GaussianBlur(light, (3, 3), 0.7)
        Lmap = cv2.remap(cv2.resize(light, (NV * 16, NU * 16), interpolation=cv2.INTER_CUBIC), Lx, Ly, cv2.INTER_LINEAR)
        new = reflect * Lmap
        g = cv2.GaussianBlur(lum, (0, 0), 1.2 * s)                    # the frame's own noise, on its paper
        res_n = (lum - g)[cand]
        noise = min(0.02, 0.8 * 1.4826 * np.median(np.abs(res_n - np.median(res_n)))) if len(res_n) > 50 else 0.006
        nz = cv2.GaussianBlur(np.random.default_rng(i).standard_normal((ch, cw)).astype(np.float32), (0, 0), 0.6 * s)
        nz *= noise / max(1e-4, nz.std())
        new = new + nz[..., None]
        glove = ((lum < 0.30) & (hsv[..., 1] < 110)).astype(np.uint8)  # never paint over the glove
        glove = cv2.dilate(glove, np.ones((3 * s, 3 * s), np.uint8))
        glove = cv2.GaussianBlur(glove.astype(np.float32), (0, 0), 0.8 * s)
        mask_ref = paint_ref * (1 - np.clip(glove * 1.5, 0, 1)) * lock_w[i]
        comp = cv2.warpPerspective(np.clip(new, 0, 1), Hn, (ws, hs), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        mk = cv2.warpPerspective(mask_ref, Hn, (ws, hs), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        ys, xs = np.nonzero(mk > 0)
        o = f.copy()
        if len(ys):
            y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
            m3 = mk[y0:y1, x0:x1, None]
            o[y0:y1, x0:x1] = np.clip((f[y0:y1, x0:x1].astype(np.float32) / 255 * (1 - m3) + comp[y0:y1, x0:x1] * m3)
                                      * 255 + 0.5, 0, 255).astype(np.uint8)
        enc.stdin.write(o.tobytes())
        if qa and i % 6 == 0:
            qa.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(qa / f"f{i:03d}.jpg"), np.hstack([f, o]))
        i += 1
    enc.stdin.close()
    enc.wait()
    dec.wait()
    print(f"wrote {dst}: {i} frames, label locked on {len(locked)} (from frame {locked[0]})")


if __name__ == "__main__":
    main()
