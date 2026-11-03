#!/usr/bin/env python3
"""Lock the real Spraymax label onto the bottle in the intro take (clips/20261103-104914-1.mp4).

Seedance drew a lavender wordmark, a pale band and garbled small lines. Per frame:

1. Track: the AI label's own texture (wordmark + band) in reference frame REF is registered to every other
   frame with OpenCV ECC (full homography), always against REF, so nothing drifts. Frames where it can't lock
   (the bottle still tiny at the top of the frame) keep the AI pixels, with a short crossfade into the lock.
2. Wrap: in REF's coordinates the bottle is a cylinder (axis, radius, label bottom edge measured from the AI
   band), and the flat label art (label-hires.jpg) is wrapped round it at the AI print's own scale.
3. Light: the frame is pulled back into REF coordinates; wherever the AI bottle shows bare paper/plastic, its own
   pixels are the light (shading, highlights, grain), and under its ink the light is filled in from the paper
   around it. The real print is multiplied into that, so the label is the bottle's own surface with the real
   print on it, not a sticker pasted on top. The glove (large dark blobs at the cap end) is never painted.
4. Match: the print is softened to the footage's focus; grain is added only where the light was filled in.

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
    # the side panels' tiny text only reads as a dotted line along the edge at this size: leave it out
    side = np.ones(art.shape[1], np.float32)
    side[:int((ART_X0 - 240) * ART_SCALE)] = 0.0       # Seedance's bottle shows no side-panel print: plain paper
    side[int((ART_X0 + 240) * ART_SCALE):] = 0.0
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
    # --- the real art laid out exactly where Seedance printed its label (measured on REF in bottle coords:
    # band u 1..41.5 and v -32.5..30.5, i.e. edge to edge; wordmark u 53..137.5 with letters ~14 px tall).
    # Along the axis: piecewise-linear from label-flat rows to u. Across: a smooth stretch from the art's column
    # (art px from the front centre) to the angle round the bottle, so the wordmark keeps Seedance's letter size
    # while the band still reaches the edges, as Seedance drew it.
    ALONG_U = np.array([0.0, 41.5, 53.0, 137.5, 144.5])
    ALONG_Y = np.array([ART_H, 690.0, 629.0, ART_WM_TOP, 0.0])
    yb, yw = (ALONG_Y[0] - ALONG_Y[1]) / ALONG_U[1], (ALONG_Y[3] - ALONG_Y[4]) / (ALONG_U[4] - ALONG_U[3])
    ay = np.interp(u, ALONG_U, ALONG_Y)
    ay = np.where(u < 0, ART_H - u * yb, np.where(u > ALONG_U[-1], -(u - ALONG_U[-1]) * yw, ay)) * ART_SCALE
    V_OFF = -1.0                                                      # Seedance's print sits 1 px off the axis
    th_wm, th_band = np.arcsin(7.0 / REF_R), np.arcsin(31.5 / REF_R)  # wordmark half-height, band half-width
    s1 = 55.0 / th_wm                                                 # art px per radian at the centre
    c3 = (th_band * s1 / 233.0) - 1.0                                 # cubic stretch so +-233 art px hits the band edge
    dx_grid = np.linspace(-520, 520, 4161)
    th_grid = dx_grid / s1 * (1 + c3 * (dx_grid / 233.0) ** 2)
    theta = np.arcsin(np.clip((v - V_OFF) / REF_R, -0.9999, 0.9999))
    dx = np.interp(theta, th_grid, dx_grid)
    ax = (ART_X0 + dx) * ART_SCALE
    ay_end = ART_H * ART_SCALE - 1
    bare = 3.0 * yb * ART_SCALE                                       # ~3 px of bare plastic past the label's base edge
    on_label = inside & (ay >= 0) & (ay <= ay_end + bare)                # (covers the AI band where it ran long)
    # where the real band and wordmark land (for matching them to Seedance's look per frame)
    art_band = ((ay > 690 * ART_SCALE) & (ay < 950 * ART_SCALE) & (np.abs(dx) < 233)).astype(np.float32)
    art_wm = ((ay > (ART_WM_TOP - 4) * ART_SCALE) & (ay < 633 * ART_SCALE) & (np.abs(dx) < 60)).astype(np.float32)
    ai_band = inside & (u > 4) & (u < 38) & (np.abs(v - V_OFF) < 0.85 * REF_R)
    ai_wm_zone = (u > 56) & (u < 135) & (np.abs(v - V_OFF) < 8)
    ai_print = inside & (((u > -1.5) & (u < 53)) | ((u > 51) & (u < 140) & (np.abs(v - V_OFF) < 10)))

    def axis_kernel(sig_along, sig_across):
        """Gaussian elongated along the bottle's axis (in REF crop pixels), for filling light under the print
        from the paper beyond it while keeping the shading across the cylinder."""
        rad = int(3 * sig_along)
        yk, xk = np.mgrid[-rad:rad + 1, -rad:rad + 1].astype(np.float32)
        al = xk * REF_A[0] + yk * REF_A[1]
        ac = -xk * REF_A[1] + yk * REF_A[0]
        kk = np.exp(-0.5 * ((al / sig_along) ** 2 + (ac / sig_across) ** 2))
        return kk / kk.sum()
    k_small = axis_kernel(5.0 * s, 1.5 * s)
    k_large = axis_kernel(22.0 * s, 2.0 * s)
    blur_px = ART_SCALE / (k * s) * 0.45 + ART_SCALE / k * 0.18       # anti-alias + match the footage's softness
    art_soft = cv2.GaussianBlur(art, (0, 0), max(0.3, blur_px))
    label = cv2.remap(art_soft, ax.astype(np.float32), ay.astype(np.float32), cv2.INTER_LINEAR,
                      borderMode=cv2.BORDER_REPLICATE)
    del art, art_soft
    reflect = label / paper_art                                       # 1 = white paper
    reflect[ay > ay_end] = 1.0
    edge = np.clip((REF_R - np.abs(v)) * s / 1.2, 0, 1)               # fade over the cylinder's last ~1.2 px
    ends = np.clip(np.minimum(ay, ay_end + bare - ay) / (ART_SCALE * 1.2 / k / s), 0, 1)
    paint_ref = (on_label * edge * ends).astype(np.float32)

    u0, u1 = -0.25 * REF_R, ART_H * k + 0.15 * REF_R                   # where the light is sampled (label + plastic)

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
        # light = the AI bottle's own pixels wherever its bare paper/plastic shows (its shading, highlights and
        # grain, pixel for pixel); under its ink (wordmark, band, small text) it is filled in from the paper
        # around it by normalized convolution, and only there do we add matching grain. The real print is then
        # multiplied into that light, so the paper is literally the bottle's own surface, not a pasted sticker.
        region = inside & (u > u0) & (u < u1)
        # Seedance's ink: its print zones (band, small line, wordmark) plus any thin dark stroke or saturated
        # pixel; soft shading across the bottle is NOT ink (it is compared with its own local blur)
        g3 = cv2.GaussianBlur(lum, (0, 0), 3.0 * s)
        ink = ai_print | (hsv[..., 1] >= 45) | (lum < 0.9 * g3)
        ink = cv2.dilate((region & ink).astype(np.uint8), np.ones((4 * s + 1, 4 * s + 1), np.uint8)) > 0
        paper = region & ~ink
        pm = paper.astype(np.float32)
        def nconv(kern):
            w_ = cv2.filter2D(pm, -1, kern)
            return cv2.filter2D(back * pm[..., None], -1, kern) / np.maximum(w_, 1e-5)[..., None], w_
        f1, w1 = nconv(k_small)
        f2, _ = nconv(k_large)
        fill = np.where((w1 > 0.08)[..., None], f1, f2)
        m_soft = cv2.GaussianBlur(pm, (0, 0), 0.7 * s)[..., None]
        light = m_soft * back + (1 - m_soft) * fill
        # matching grain where the light was filled in: the frame's own noise, measured on its paper
        g = cv2.GaussianBlur(lum, (0, 0), 1.2 * s)
        res_n = (lum - g)[paper]
        noise = min(0.02, 1.4826 * np.median(np.abs(res_n - np.median(res_n)))) if len(res_n) > 50 else 0.006
        nz = cv2.GaussianBlur(np.random.default_rng(i).standard_normal((ch, cw)).astype(np.float32), (0, 0), 0.6 * s)
        nz *= noise / max(1e-4, nz.std())
        new = reflect * light + (nz * (1 - m_soft[..., 0]))[..., None]
        # blend into Seedance's own lighting of its print: the real band takes Seedance's band brightness, contrast
        # and part of its colour cast; the real wordmark keeps its indigo but takes part of Seedance's lightness
        lab_new = cv2.cvtColor(np.clip(new, 0, 1).astype(np.float32), cv2.COLOR_BGR2Lab)
        lab_ai = cv2.cvtColor(back, cv2.COLOR_BGR2Lab)
        rb, ab = art_band > 0.5, ai_band
        if rb.sum() > 50 and ab.sum() > 50:
            mr, sr = lab_new[rb].mean(0), lab_new[rb].std(0)
            ma, sa = lab_ai[ab].mean(0), lab_ai[ab].std(0)
            adj = lab_new.copy()
            gain = np.clip(sa[0] / max(sr[0], 1e-3), 0.7, 1.4) ** 0.6
            adj[..., 0] = mr[0] + (lab_new[..., 0] - mr[0]) * gain + 0.75 * (ma[0] - mr[0])
            adj[..., 1:] = lab_new[..., 1:] + 0.5 * (ma[1:] - mr[1:])
            wb = cv2.GaussianBlur(art_band, (0, 0), 0.8 * s)[..., None]
            lab_new = lab_new * (1 - wb) + adj * wb
        wm_ai = ai_wm_zone & (hsv[..., 1] > 45)
        rw = (art_wm > 0.5) & (lab_new[..., 0] < 60)
        if rw.sum() > 20 and wm_ai.sum() > 20:
            dL = 0.4 * (lab_ai[wm_ai][:, 0].mean() - lab_new[rw][:, 0].mean())
            ww = cv2.GaussianBlur(art_wm, (0, 0), 0.8 * s)
            ink_w = np.clip((90 - lab_new[..., 0]) / 50, 0, 1) * ww      # only the ink, not the paper round it
            lab_new[..., 0] += dL * ink_w
        new = cv2.cvtColor(lab_new, cv2.COLOR_Lab2BGR)
        # never paint over the glove: large dark, unsaturated blobs at the cap end only (the AI's dark print and
        # the shadowed parts of its band are thin or small, and must be painted over)
        glove = ((lum < 0.30) & (hsv[..., 1] < 110) & (u > 0.6 * ART_H * k)).astype(np.uint8)
        glove = cv2.morphologyEx(glove, cv2.MORPH_OPEN, np.ones((7 * s, 7 * s), np.uint8))
        nb, lab_, st_, _ = cv2.connectedComponentsWithStats(glove)
        glove = np.isin(lab_, [b for b in range(1, nb) if st_[b, 4] >= (18 * s) ** 2]).astype(np.uint8)
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
