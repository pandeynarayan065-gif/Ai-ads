"""Spraymax 12 s cinematic film: 3D storyboard frames (Blender / Cycles, 1080x1920).

The Higgsfield Seedance "Ex Nihilo" film structure (reference/creators/higgsfield-seedance-ex-nihilo.md) in
Spraymax's colours: black void, deep indigo and sapphire washes, ice-blue and silver-white light, the pink
Himalayan salt the only warm accent. One hard light per shot, mostly black frame, matte floors only.

Each shot renders one key frame. The product frames (real bottle, real label) double as the first frames
Veo 3.1 animates; the organic shots (salt, ocean, vapour) are previz for Veo text-to-video.

  F1 collar    extreme close-up of the pump and ribbed collar, a hard white light grazing the ribs
  F2 blade     low three-quarter, the capped bottle in near-silhouette, one silver specular blade down its edge
  F3 salt      raw pink Himalayan salt glowing from inside, sea-water beads on its edges
  F4 mist      the pump fires: a backlit mist burst blooming across the black
  F5 ocean     a night ocean swell under a low cold moon, a glitter path on the water
  F6 bloom     the bottle in a black void, a broad indigo wash blooming behind it
  F7 cloud     the mist a second later: a slow cloud of fine droplets hanging in a hard cold beam
  F8 wordmark  macro down the indigo wordmark, cold light grazing the label
  F9 packshot  wide: the bottle left of centre on a matte indigo surface, a long hard shadow, dark sky for type

  python video/blender/film_shots.py --shot F1 --out frame.png [--samples 48] [--res-scale 100]
"""
import math
import random
import sys
from pathlib import Path

import bpy  # noqa: I001
import numpy as np
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import carry_shots as cs  # noqa: E402
import k2_shots as k2  # noqa: E402
from spraymax_scene import area_light, principled, r, z  # noqa: E402

ICE = (0.78, 0.9, 1.0)
SILVER = (0.95, 0.97, 1.0)
INDIGO = (0.32, 0.25, 1.0)
BLACK = [(0, (2, 2, 6)), (1, (3, 3, 10))]


def white_bottle():
    """Spraymax white reads silver-white: lit low, never flat white, never dull grey."""
    cs.glossy_bottle()
    for name in ("BottleWhite", "PumpWhite"):
        m = bpy.data.materials.get(name)
        if m:
            m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.8, 0.8, 0.84, 1)


def nozzle_to_back(root):
    """On the real bottle the nozzle hole faces the same way as the BACK label (Narayan's photos, 2 Nov 2026);
    make_bottle puts it on the front. Use in every shot that shows the front label."""
    for ob in root.children:
        if ob.data and getattr(ob.data, "materials", None) and any(m and m.name.startswith("Nozzle") for m in ob.data.materials):
            ob.location.y = -ob.location.y
            ob.rotation_euler.x += math.pi


def matte_floor(rgb, rough=0.75):
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
    f = bpy.context.object
    f.data.materials.append(principled("MatteFloor", cs.srgb(rgb), rough=rough))
    return f


def spot(name, loc, target, energy, rgb, size_deg=25, soft=0.002):
    l = bpy.data.lights.new(name, "SPOT")
    l.energy = energy
    l.color = rgb
    l.spot_size = math.radians(size_deg)
    l.spot_blend = 0.3
    l.shadow_soft_size = soft
    ob = bpy.data.objects.new(name, l)
    ob.location = loc
    bpy.context.collection.objects.link(ob)
    k2.aim(ob, target)
    return ob


def focus_hit(pos, tgt):
    """Focus distance to whatever surface the centre of frame actually hits (ray cast)."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    d = (Vector(tgt) - Vector(pos)).normalized()
    hit, loc, *_ = bpy.context.scene.ray_cast(dg, Vector(pos), d)
    return (loc - Vector(pos)).dot(d) if hit else (Vector(tgt) - Vector(pos)).length


# ---------------------------------------------------------------- shots
def F1(sc):
    cs.cyc(BLACK, -0.1, 0.4, glow=((26, 20, 95), 0.03, 0.15, 0.07))
    piv, root, R = cs.bottle(cap=False)
    white_bottle()
    cs.strip("Graze", (0.09, -0.045, 0.126), (0, 0, 0.124), 0.10, 0.003, 0.16, SILVER)  # skims the ribs from the right
    cs.strip("Rim", (-0.06, 0.10, 0.15), (0, 0, 0.14), 0.2, 0.01, 0.08, INDIGO)
    cam = cs.cam_make(100, 32)
    pos, tgt = Vector((-0.003, -0.13, 0.133)), (-0.003, 0, 0.132)
    cs.look(cam, pos, tgt, focus=cs.focus_on(pos, tgt, Vector((0, -r(244), 0.123))))


def F2(sc):
    cs.cyc(BLACK, -0.3, 0.5)
    piv, root, R = cs.bottle(cap=True)
    white_bottle()
    nozzle_to_back(root)
    cs.strip("Blade", (0.34, 0.09, 0.09), (0, 0, 0.085), 0.7, 0.008, 6, SILVER)
    bounce = area_light("Bounce", (-0.05, -0.12, -0.02), (0, 0, 0), 0.06, 0.03, ICE)
    k2.aim(bounce, (0, 0, 0.0))
    cs.strip("Rim", (-0.30, 0.20, 0.12), (0, 0, 0.09), 0.5, 0.01, 0.6, INDIGO)
    cam = cs.cam_make(85, 4.0)
    a = math.radians(-35)
    pos = Vector((0.40 * math.sin(a), -0.40 * math.cos(a), 0.035))
    tgt = (0.0, 0, 0.095)
    cs.look(cam, pos, tgt, focus=cs.focus_on(pos, tgt, Vector((0, -R, 0.08))))


def F3(sc):
    cs.cyc(BLACK, -0.3, 0.4, glow=((40, 8, 14), 0.0, 0.05, 0.12))
    matte_floor((4, 3, 6))
    m = cs.salt_mat(0.08)
    hero = cs.crystal_mesh("Hero", 0.026, m, seed=7)
    hero.location = (0, 0, 0.02)
    hero.rotation_euler = (0.3, 0.5, 0.2)
    bpy.context.view_layer.update()
    low = min((hero.matrix_world @ v.co).z for v in hero.data.vertices)
    hero.location.z -= low + 0.0005
    bpy.context.view_layer.update()
    cs.beads_on([hero], 60, 0.0005, 0.0016, seed=11, from_dir=(0.3, -1, 0.6), spread=0.04, centre=(0, 0, 0.02))
    back = area_light("Back", (0.03, 0.2, 0.06), (0, 0, 0), 0.06, 5, (1.0, 0.62, 0.52))
    k2.aim(back, (0, 0, 0.02))
    back.visible_glossy = False
    key = area_light("Key", (-0.16, -0.14, 0.20), (0, 0, 0), 0.03, 1.2, ICE)
    k2.aim(key, (0, 0, 0.02))
    cam = cs.cam_make(100, 8.0)
    pos, tgt = Vector((-0.025, -0.17, 0.055)), (0, 0, 0.022)
    cs.look(cam, pos, tgt, focus=focus_hit(pos, tgt))


def F4(sc):
    cs.cyc(BLACK, -0.1, 0.45)
    piv, root, R = cs.bottle(cap=False)
    white_bottle()
    piv.rotation_euler = (0, 0, math.radians(90))          # nozzle to camera right
    bpy.context.view_layer.update()
    o, dvec = cs.nozzle_world(root, piv)
    mist = cs.mist_emitter(o, dvec, press=1, n=110000, cone=19, spd=(0.35, 0.8), dur=0.55, seed=9)
    back = area_light("MistBack", (0.16, 0.25, 0.17), (0, 0, 0), 0.10, 30, ICE)
    k2.aim(back, (0.07, 0, 0.15))
    back.visible_glossy = False
    key = area_light("Key", (-0.25, -0.25, 0.22), (0, 0, 0), 0.15, 0.5, SILVER)
    k2.aim(key, (0, 0, 0.14))
    cs.strip("Rim", (-0.14, 0.15, 0.16), (0, 0, 0.14), 0.3, 0.01, 1.5, INDIGO)
    cam = cs.cam_make(100, 5.6)
    pos, tgt = Vector((0.024, -0.40, 0.142)), (0.024, 0, 0.142)
    cs.look(cam, pos, tgt, focus=cs.focus_on(pos, tgt, Vector((0.01, -r(160), 0.15))))
    mist(11)                                                # 8 frames after the press: the plume blooming


def F5(sc):
    world = bpy.context.scene.world
    world.node_tree.nodes["Background"].inputs[0].default_value = (*cs.srgb((3, 4, 14)), 1)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    sea = bpy.context.object
    oc = sea.modifiers.new("Ocean", "OCEAN")
    oc.geometry_mode = "GENERATE"
    oc.repeat_x = oc.repeat_y = 5
    oc.resolution = 14
    oc.spatial_size = 60
    oc.wave_scale = 2.6
    oc.choppiness = 1.5
    oc.wind_velocity = 18
    oc.random_seed = 4
    sea.data.materials.append(principled("Sea", cs.srgb((1, 3, 9)), rough=0.09, coat=0.6))
    bpy.ops.object.shade_smooth()
    moon = bpy.data.lights.new("Moon", "SUN")
    moon.energy = 8.0
    moon.color = ICE
    moon.angle = math.radians(3.0)
    mo = bpy.data.objects.new("Moon", moon)
    bpy.context.collection.objects.link(mo)
    mo.rotation_euler = (math.radians(-68), 0, 0)          # moon ~22 deg up, straight ahead          # low, from behind the swell toward the camera
    bpy.ops.mesh.primitive_uv_sphere_add(radius=5, location=(0, 340, 139))
    disc = bpy.context.object
    disc.data.materials.append(cs.emissive("MoonDisc", (0.85, 0.92, 1.0), 6))
    cam = cs.cam_make(35, 8.0)
    cam.data.clip_end = 1000
    cs.look(cam, (0, 20, 1.2), (0, 80, 9.0), focus=40)


def F6(sc):
    cs.cyc([(0, (2, 2, 6)), (1, (2, 2, 7))], -0.4, 0.6, glow=((44, 30, 165), 0.06, 0.16, 0.16))
    piv, root, R = cs.bottle(cap=True)
    white_bottle()
    nozzle_to_back(root)
    piv.location = (-0.025, 0, cs.MID)
    side = area_light("Side", (0.30, 0.02, 0.22), (0, 0, 0), 0.12, 0.9, SILVER)
    k2.aim(side, (-0.025, 0, 0.10))
    cs.strip("RimL", (-0.28, 0.20, 0.12), (-0.025, 0, 0.09), 0.5, 0.02, 1.6, INDIGO)
    cam = cs.cam_make(85, 4.0)
    pos, tgt = Vector((0, -0.52, 0.07)), (0, 0, 0.095)
    cs.look(cam, pos, tgt, focus=cs.focus_on(pos, tgt, Vector((-0.025, -R, 0.08))))


def F7(sc):
    """The mist a second after the burst: a slow cloud of fine droplets hanging in a hard cold beam."""
    cs.cyc(BLACK, -0.3, 0.5)
    mm = bpy.data.materials.new("Mist")
    mm.use_nodes = True
    mb = mm.node_tree.nodes["Principled BSDF"]
    mb.inputs["Base Color"].default_value = (0.95, 0.96, 1.0, 1)
    mb.inputs["Roughness"].default_value = 0.25
    mb.inputs["Alpha"].default_value = 0.2
    ob = k2.points_mesh("Cloud", mm)
    rng = np.random.default_rng(21)
    n = 70000
    # a plume curling up and to the right, tight where it comes in and opening into soft lobes
    t = rng.beta(1.6, 1.4, n)
    cx = -0.07 + 0.13 * t
    cz = 0.06 + 0.11 * t + 0.025 * np.sin(4.0 * t)
    w = 0.003 + 0.028 * t ** 1.3
    off = rng.standard_t(3, (n, 3)) * w[:, None] * np.array([1.0, 0.8, 1.0])
    curl = 0.012 * t[:, None] * np.stack([np.sin(40 * off[:, 2] + 3), np.zeros(n), np.cos(40 * off[:, 0])], 1)
    pts = np.stack([cx, np.zeros(n), cz], 1) + off + curl
    rad = 0.00008 * np.exp(rng.normal(0, 0.5, n))
    k2.set_points(ob, pts.astype(np.float32), rad.astype(np.float32))
    beam = spot("Beam", (0.40, 0.32, 0.26), (0, 0, 0.12), 140, ICE, size_deg=20, soft=0.002)
    beam.data.spot_blend = 0.4
    spot("Fill", (-0.4, -0.2, 0.2), (0, 0, 0.12), 6, SILVER, size_deg=30, soft=0.01)
    cam = cs.cam_make(85, 2.8)
    pos, tgt = Vector((-0.005, -0.62, 0.12)), (-0.005, 0, 0.12)
    cs.look(cam, pos, tgt, focus=0.62)


def F8(sc):
    cs.cyc(BLACK, -0.2, 0.4)
    piv, root, R = cs.bottle(cap=True)
    white_bottle()
    nozzle_to_back(root)
    cs.strip("Graze", (0.16, 0.03, 0.075), (0, 0, 0.065), 0.3, 0.006, 0.7, ICE)
    cs.strip("Fill", (-0.15, -0.12, 0.09), (0, 0, 0.065), 0.25, 0.04, 0.04, ICE)
    cam = cs.cam_make(100, 4.0)
    a = math.radians(30)
    pos = Vector((0.18 * math.sin(a), -0.18 * math.cos(a), 0.072))
    tgt = (0.0, -R * 0.5, 0.066)
    cs.look(cam, pos, tgt, focus=cs.focus_on(pos, tgt, Vector((0, -R, 0.066))))


def F9(sc):
    cs.cyc([(0, (5, 4, 22)), (0.35, (10, 8, 40)), (0.7, (4, 3, 14)), (1, (2, 2, 6))], -0.3, 0.6,
           glow=((26, 22, 90), 0.12, 0.10, 0.25))
    matte_floor((10, 8, 36), rough=0.8)
    piv, root, R = cs.bottle(cap=True)
    white_bottle()
    nozzle_to_back(root)
    piv.location = (-0.05, 0, cs.MID)
    k = spot("Key", (-0.85, -0.10, 0.24), (0.06, 0, 0.0), 260, SILVER, size_deg=22, soft=0.004)
    k.data.spot_blend = 0.9
    cs.strip("Rim", (0.25, 0.25, 0.15), (-0.05, 0, 0.09), 0.5, 0.02, 2.0, INDIGO)
    cam = cs.cam_make(85, 5.6)
    pos, tgt = Vector((0.04, -1.0, 0.13)), (0.04, 0, 0.15)
    cs.look(cam, pos, tgt, focus=cs.focus_on(pos, tgt, Vector((-0.05, -R, 0.08))))


SHOTS = {f"F{i}": globals()[f"F{i}"] for i in range(1, 10)}


def main():
    a = sys.argv[1:]
    shot = a[a.index("--shot") + 1]
    out = a[a.index("--out") + 1]
    samples = int(a[a.index("--samples") + 1]) if "--samples" in a else 48
    res = int(a[a.index("--res-scale") + 1]) if "--res-scale" in a else 100
    sc = cs.setup(samples, res)
    SHOTS[shot](sc)
    for ob in bpy.data.objects:
        if ob.type == "LIGHT":
            ob.visible_camera = False
    sc.frame_set(1)
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
