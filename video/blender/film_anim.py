"""Animate one film_shots.py shot for the 3D animatic: the camera moves the way the Higgsfield perfume film's
camera moves (measured with optical flow, reference/creators/higgsfield-seedance-ex-nihilo.md), and the shot's
own hook (film_shots.ANIM) runs across the shot: a light sweep, the pump rising, a bead running, the mist bursting.

  python video/blender/film_anim.py --shot F1 --frames 29 --out <dir> [--push 0.12] [--lat 0.0] [--rise 0.0]
         [--hook sweep] [--samples 16] [--res-scale 50]

push: fraction of the camera-to-focus distance travelled forward; lat / rise: metres along the camera's right / up.
Writes <dir>/<shot>_0000.png ...
"""
import math
import sys
from pathlib import Path

import bpy  # noqa: I001

sys.path.insert(0, str(Path(__file__).resolve().parent))
import carry_shots as cs  # noqa: E402
import film_shots as fs  # noqa: E402
from mathutils import Vector  # noqa: E402

CAMERA_HOOKS = {"orbit"}            # hooks that move the camera themselves (keyframed so motion blur works)


def arg(a, name, default, cast=str):
    return cast(a[a.index(name) + 1]) if name in a else default


def smooth(t):
    return t * t * (3 - 2 * t)


def main():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    shot = arg(a, "--shot", None)
    n = arg(a, "--frames", 24, int)
    out = Path(arg(a, "--out", "."))
    push, lat, rise = arg(a, "--push", 0.0, float), arg(a, "--lat", 0.0, float), arg(a, "--rise", 0.0, float)
    hook = arg(a, "--hook", None)
    sc = cs.setup(arg(a, "--samples", 16, int), arg(a, "--res-scale", 50, int))
    sc.render.fps = 24
    fs.SHOTS[shot](sc)
    for ob in bpy.data.objects:
        if ob.type == "LIGHT":
            ob.visible_camera = False
    cam = sc.camera
    loc0 = cam.location.copy()
    rot0 = cam.rotation_euler.copy()
    focus0 = cam.data.dof.focus_distance
    m = rot0.to_matrix()
    fwd, right, up = m @ Vector((0, 0, -1)), m @ Vector((1, 0, 0)), m @ Vector((0, 1, 0))
    sc.frame_start, sc.frame_end = 1, n
    # pass 1: keyframe the camera for every frame (motion blur needs the path)
    for i in range(n):
        t = i / max(n - 1, 1)
        sc.frame_set(i + 1)
        if hook in CAMERA_HOOKS:
            fs.ANIM[hook](t)
        else:
            d = push * focus0 * smooth(t)
            cam.location = loc0 + fwd * d + right * (lat * t) + up * (rise * t)
            cam.rotation_euler = rot0
            cam.data.dof.focus_distance = focus0 - d
        cam.keyframe_insert("location")
        cam.keyframe_insert("rotation_euler")
        cam.data.dof.keyframe_insert("focus_distance")
    # pass 2: run the shot's own hook and render each frame
    out.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        t = i / max(n - 1, 1)
        if hook and hook not in CAMERA_HOOKS:
            fs.ANIM[hook](t)
        sc.frame_set(i + 1)
        sc.render.filepath = str(out / f"{shot}_{i:04d}.png")
        bpy.ops.render.render(write_still=True)
    print("wrote", n, "frames of", shot)


if __name__ == "__main__":
    main()
