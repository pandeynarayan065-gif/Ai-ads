"""Spraymax 12 s cinematic film: 3D storyboard frames (Blender / Cycles, 1080x1920).

The Higgsfield Seedance "Ex Nihilo" film structure (reference/creators/higgsfield-seedance-ex-nihilo.md) in
Spraymax's colours: black void, deep indigo and sapphire washes, ice-blue and silver-white light, the pink
Himalayan salt the only warm accent. One hard light per shot, mostly black frame, matte floors only.

Each shot renders one key frame. The product frames (real bottle, real label) double as the first frames
Veo 3.1 animates; the organic shots (salt, ocean, vapour) are previz for Veo text-to-video.

  F1 collar    extreme close-up of the pump and ribbed collar, a hard white light grazing the ribs
  F2 blade     low three-quarter, the capped bottle in near-silhouette, one silver specular blade down its edge
  F3 salt      coarse pink Himalayan salt tumbling through one hard cold beam onto black
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
import re
import sys
from pathlib import Path

import bpy  # noqa: I001
import bmesh
import numpy as np
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import carry_shots as cs  # noqa: E402
import k2_shots as k2  # noqa: E402
from spraymax_scene import area_light, principled, r, z  # noqa: E402

ICE = (0.78, 0.9, 1.0)
SILVER = (0.95, 0.97, 1.0)
INDIGO = (0.12, 0.40, 1.0)                 # was violet; the brand wants blue (Narayan's partners, 2 Nov)
BLACK = [(0, (2, 2, 6)), (1, (1, 3, 10))]


def white_bottle():
    """The real bottle (Narayan's video, 2 Nov): milky, slightly grey-white semi-matte plastic with a soft sheen,
    a matte ribbed collar and a matte pump. Not glossy, not coated."""
    bottle_materials()


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
    cs.cyc(BLACK, -0.1, 0.4, glow=((6, 32, 95), 0.03, 0.15, 0.07))
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
    """Coarse pink Himalayan salt tumbling in slow motion through one hard cold beam, landing on black."""
    cs.cyc(BLACK, -0.2, 0.4)
    matte_floor((3, 3, 5), rough=0.9)
    m = cs.salt_mat(0.04)
    protos = []
    for k in range(10):
        pr = cs.crystal_mesh(f"SaltProto{k}", 1.0, m, seed=30 + k)
        pr.hide_render = True
        protos.append(pr)
    rnd = random.Random(12)

    def chunk(loc, size):
        o = rnd.choice(protos).copy()
        o.hide_render = False
        bpy.context.collection.objects.link(o)
        o.location = loc
        o.rotation_euler = (rnd.uniform(0, 6.3), rnd.uniform(0, 6.3), rnd.uniform(0, 6.3))
        o.scale = (size * rnd.uniform(0.8, 1.3), size * rnd.uniform(0.7, 1.1), size * rnd.uniform(0.6, 1.0))
        return o
    # falling: a loose column, denser in the middle, a few crystals near the lens (bokeh) and far behind
    for _ in range(140):
        x = rnd.gauss(0.0, 0.011)
        y = rnd.gauss(0.0, 0.03)
        zz = rnd.uniform(0.012, 0.15)
        chunk((x, y, zz), rnd.uniform(0.001, 0.0034))
    # landed: a low mound where the column hits the floor
    for _ in range(420):
        rad = abs(rnd.gauss(0, 0.018))
        ang = rnd.uniform(0, 2 * math.pi)
        x, y = rad * math.cos(ang), rad * math.sin(ang)
        size = rnd.uniform(0.0012, 0.004)
        h = max(0.0, 0.009 - rad * 0.35)
        chunk((x, y, h + size * 0.3), size)
    # one hard cold beam from high behind on the right, visible in a faint haze
    beam = spot("Beam", (0.16, 0.30, 0.34), (0, 0, 0.05), 70, ICE, size_deg=11, soft=0.001)
    beam.data.spot_blend = 0.15
    spot("Key", (-0.30, -0.25, 0.12), (0, 0, 0.06), 3, SILVER, size_deg=30, soft=0.02)
    bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 0.1, 0.2))
    haze = bpy.context.object
    hm = bpy.data.materials.new("Haze")
    hm.use_nodes = True
    hn = hm.node_tree
    hn.nodes.remove(hn.nodes["Principled BSDF"])
    pv = hn.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Density"].default_value = 0.06
    pv.inputs["Anisotropy"].default_value = 0.6
    hn.links.new(pv.outputs["Volume"], hn.nodes["Material Output"].inputs["Volume"])
    haze.data.materials.append(hm)
    cam = cs.cam_make(100, 4.0)
    pos, tgt = Vector((0.0, -0.42, 0.055)), (0.0, 0, 0.07)
    cs.look(cam, pos, tgt, focus=cs.focus_on(pos, tgt, Vector((0, 0, 0.07))))


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
    world.node_tree.nodes["Background"].inputs[0].default_value = (*cs.srgb((1, 5, 14)), 1)
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
    cs.cyc([(0, (2, 2, 6)), (1, (2, 2, 7))], -0.4, 0.6, glow=((10, 56, 165), 0.06, 0.16, 0.16))
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
    cs.cyc([(0, (1, 7, 22)), (0.35, (2, 14, 40)), (0.7, (1, 5, 14)), (1, (2, 2, 6))], -0.3, 0.6,
           glow=((5, 31, 90), 0.12, 0.10, 0.25))
    matte_floor((2, 12, 36), rough=0.8)
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



# ---------------------------------------------------------------- v2 shots (variety: splash, smoke, POV, macro, lineup)
def bottle_materials(base=(0.80, 0.81, 0.83)):
    """Real-bottle plastics for every bottle in the scene (each make_bottle call makes its own materials)."""
    for m in bpy.data.materials:
        if not m.node_tree or "Principled BSDF" not in m.node_tree.nodes:
            continue
        b = m.node_tree.nodes["Principled BSDF"]
        if m.name.startswith("BottleWhite"):
            b.inputs["Base Color"].default_value = (*base, 1)
            b.inputs["Roughness"].default_value = 0.42
            b.inputs["Coat Weight"].default_value = 0.12
            b.inputs["Coat Roughness"].default_value = 0.25
            b.inputs["Subsurface Weight"].default_value = 0.3        # milky HDPE: light glows a little through it
            b.inputs["Subsurface Scale"].default_value = 0.003
        elif m.name.startswith("PumpWhite"):
            b.inputs["Base Color"].default_value = (0.84, 0.84, 0.85, 1)
            b.inputs["Roughness"].default_value = 0.55
            b.inputs["Coat Weight"].default_value = 0.0
        elif m.name.startswith("LabelMat"):
            b.inputs["Roughness"].default_value = 0.38
            b.inputs["Coat Weight"].default_value = 0.2
            b.inputs["Coat Roughness"].default_value = 0.2


def crown(R, z0, seed=5, segs=160, rings=14):
    """A crown splash: a thin sheet of water rising and flaring out round the bottle base, jagged rim with spikes."""
    rnd = np.random.default_rng(seed)
    th = np.linspace(0, 2 * np.pi, segs, endpoint=False)
    # rim height: smooth noise plus a few tall spikes
    k = np.arange(1, 7)
    amp = rnd.normal(0, 1, (6,)) / k
    ph = rnd.uniform(0, 6.28, 6)
    top = 0.03 + 0.006 * np.sum(amp[:, None] * np.sin(k[:, None] * th[None] + ph[:, None]), 0)
    spikes = rnd.choice(segs, 34, replace=False)
    for sidx in spikes:
        w = np.exp(-0.5 * ((np.arange(segs) - sidx + segs // 2) % segs - segs // 2) ** 2 / 1.2 ** 2)
        top += w * rnd.uniform(0.004, 0.012)
    bm = bmesh.new()
    grid = []
    for i in range(segs):
        col = []
        for j in range(rings):
            t = j / (rings - 1)
            h = z0 + t * (top[i] - z0)
            rr = R + 0.003 + 0.032 * t ** 1.6
            col.append(bm.verts.new((rr * math.cos(th[i]), rr * math.sin(th[i]), h)))
        grid.append(col)
    for i in range(segs):
        a, b = grid[i], grid[(i + 1) % segs]
        for j in range(rings - 1):
            bm.faces.new((a[j], b[j], b[j + 1], a[j + 1]))
    me = bpy.data.meshes.new("Crown")
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    ob = bpy.data.objects.new("Crown", me)
    bpy.context.collection.objects.link(ob)
    sol = ob.modifiers.new("Solid", "SOLIDIFY")
    sol.thickness = 0.0009
    ob.modifiers.new("Sub", "SUBSURF").levels = 1
    tips = [((R + 0.035) * math.cos(th[i]), (R + 0.035) * math.sin(th[i]), top[i]) for i in spikes]
    return ob, tips


def F10(sc):
    """Elemental: dark sea water erupts in a crown splash round the base of the capped bottle."""
    cs.cyc([(0, (2, 3, 8)), (1, (2, 2, 6))], -0.2, 0.5, glow=((10, 22, 60), 0.0, 0.06, 0.10))
    piv, root, R = cs.bottle(cap=True)
    white_bottle()
    nozzle_to_back(root)
    bpy.ops.mesh.primitive_circle_add(vertices=256, radius=1.5, fill_type="NGON", location=(0, 0, 0.012))
    sea = bpy.context.object
    sea.data.materials.append(principled("DarkSea", cs.srgb((2, 6, 14)), rough=0.08, coat=0.4))
    wm = cs.water_mat("Splash", 1.33)
    wm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.75, 0.88, 1.0, 1)
    wm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.03
    cr, tips = crown(R, 0.012)
    cr.data.materials.append(wm)
    rnd = random.Random(8)
    cen, rad = [], []
    for (x, y, zt) in tips:                                   # a droplet breaking off every spike
        cen.append((x * 1.03, y * 1.03, zt + rnd.uniform(0.002, 0.008)))
        rad.append(rnd.uniform(0.0012, 0.0022))
    for _ in range(160):                                       # spray flung outward and up
        a = rnd.uniform(0, 2 * math.pi)
        d = R + rnd.uniform(0.03, 0.09)
        cen.append((d * math.cos(a), d * math.sin(a), rnd.uniform(0.03, 0.13)))
        rad.append(rnd.uniform(0.0006, 0.0018))
    cs.spheres("Spray", wm, cen, rad, sub=2)
    back = area_light("Back", (0.05, 0.35, 0.22), (0, 0, 0), 0.25, 14, ICE)
    k2.aim(back, (0, 0, 0.05))
    back.visible_glossy = False
    cs.strip("RimR", (0.3, 0.12, 0.14), (0, 0, 0.09), 0.6, 0.01, 3.0, SILVER)
    key = area_light("Key", (-0.3, -0.3, 0.2), (0, 0, 0), 0.2, 0.5, SILVER)
    k2.aim(key, (0, 0, 0.07))
    cam = cs.cam_make(85, 5.6)
    pos, tgt = Vector((0.0, -0.46, 0.035)), (0.0, 0, 0.085)
    cs.look(cam, pos, tgt, focus=cs.focus_on(pos, tgt, Vector((0, -R, 0.05))))


def smoke_points(R, n_steps=90, per_step=1100, seed=3):
    """A cheap smoke simulation: particles emitted low on the left, carried right by a slow draft and a
    divergence-free (curl) noise field, pushed round the bottle. Returns the particle positions."""
    rng = np.random.default_rng(seed)
    # curl of a vector potential made of random sine waves -> swirling, incompressible flow
    modes = 24
    kdir = rng.normal(0, 1, (modes, 3))
    kdir /= np.linalg.norm(kdir, axis=1, keepdims=True)
    kmag = rng.uniform(18, 70, modes)
    kv = kdir * kmag[:, None]
    adir = rng.normal(0, 1, (modes, 3))
    ph = rng.uniform(0, 6.28, modes)
    amp = 0.9 / kmag                                     # big swirls strong, small ones weak
    cross = np.cross(kv, adir)                            # curl(sin(k.p) a) = cos(k.p) (k x a)

    def curl(pts, t):
        arg = pts @ kv.T + ph + t * 1.5
        return (np.cos(arg) * amp) @ cross

    pts = np.zeros((0, 3))
    age = np.zeros(0)
    dt = 1 / 30
    for step in range(n_steps):
        new = np.column_stack([rng.uniform(-0.17, -0.14, per_step), rng.normal(-0.03, 0.012, per_step),
                               rng.uniform(0.02, 0.055, per_step)])
        pts = np.vstack([pts, new])
        age = np.concatenate([age, np.zeros(per_step)])
        v = np.array([0.10, 0.0, 0.004]) + 0.035 * curl(pts, step * dt)
        v[:, 2] += 0.008 * np.clip(age, 0, 1.5)          # lifts a little as it ages
        pts = pts + v * dt
        pts[:, 2] = np.maximum(pts[:, 2], 0.002)          # stays above the floor
        r = np.hypot(pts[:, 0], pts[:, 1])                # round the bottle, not through it
        inside = r < R * 1.05
        pts[inside, 0] *= (R * 1.05) / r[inside]
        pts[inside, 1] *= (R * 1.05) / r[inside]
        age += dt
    keep = rng.random(len(pts)) < np.exp(-age / 2.2)      # older smoke thins out
    return pts[keep]


def F11(sc):
    """Smoke: cold smoke rolls in from the left along the floor and curls round the base of the capped bottle."""
    cs.cyc(BLACK, -0.3, 0.5, glow=((4, 24, 70), 0.04, 0.12, 0.14))
    matte_floor((2, 2, 4), rough=0.9)
    piv, root, R = cs.bottle(cap=True)
    white_bottle()
    nozzle_to_back(root)
    pts = smoke_points(R)
    me = bpy.data.meshes.new("SmokePts")
    me.from_pydata(pts.tolist(), [], [])
    src = bpy.data.objects.new("SmokePts", me)
    bpy.context.collection.objects.link(src)
    m = bpy.data.materials.new("Smoke")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Color"].default_value = (0.82, 0.88, 1.0, 1)
    pv.inputs["Anisotropy"].default_value = 0.35
    pv.inputs["Density"].default_value = 0.9
    nt.links.new(pv.outputs["Volume"], nt.nodes["Material Output"].inputs["Volume"])
    # points -> density volume (Geometry Nodes)
    ng = bpy.data.node_groups.new("SmokeVolume", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi = ng.nodes.new("NodeGroupInput")
    go = ng.nodes.new("NodeGroupOutput")
    m2p = ng.nodes.new("GeometryNodeMeshToPoints")
    p2v = ng.nodes.new("GeometryNodePointsToVolume")
    p2v.inputs["Density"].default_value = 1.0
    if "Voxel Size" in p2v.inputs:
        p2v.inputs["Voxel Size"].default_value = 0.0015
    p2v.inputs["Radius"].default_value = 0.0025
    smat = ng.nodes.new("GeometryNodeSetMaterial")
    smat.inputs["Material"].default_value = m
    ng.links.new(gi.outputs[0], m2p.inputs["Mesh"])
    ng.links.new(m2p.outputs["Points"], p2v.inputs["Points"])
    ng.links.new(p2v.outputs["Volume"], smat.inputs["Geometry"])
    ng.links.new(smat.outputs["Geometry"], go.inputs[0])
    gm = src.modifiers.new("Smoke", "NODES")
    gm.node_group = ng
    sc.cycles.volume_step_rate = 0.6
    spot("Back", (0.15, 0.6, 0.25), (0, 0, 0.03), 90, ICE, size_deg=45, soft=0.02)
    spot("SmokeSide", (-0.5, -0.15, 0.10), (0, 0, 0.03), 10, ICE, size_deg=35, soft=0.02)
    cs.strip("RimL", (-0.28, 0.2, 0.14), (0, 0, 0.09), 0.5, 0.02, 1.4, INDIGO)
    side = area_light("Side", (0.32, -0.05, 0.22), (0, 0, 0), 0.12, 0.5, SILVER)
    k2.aim(side, (0, 0, 0.1))
    cam = cs.cam_make(85, 8.0)
    pos, tgt = Vector((0, -0.55, 0.06)), (0, 0, 0.085)
    cs.look(cam, pos, tgt, focus=cs.focus_on(pos, tgt, Vector((0, -R, 0.08))))
    print("smoke points", len(pts))


def F13(sc):
    """Macro: sea-water beads across the front label, the wordmark under them, cold grazing light."""
    cs.cyc(BLACK, -0.2, 0.4)
    piv, root, R = cs.bottle(cap=True)
    white_bottle()
    nozzle_to_back(root)
    bpy.context.view_layer.update()
    label = [o for o in root.children if o.name.startswith("Label")]
    cs.beads_on(label, 70, 0.0003, 0.0009, seed=21, from_dir=(0.25, -1, 0.1), spread=0.03, centre=(0, 0, 0.06))
    for ob in bpy.data.objects:                              # clear water casts no dark shadow (caustics are off)
        if ob.name.startswith("Beads"):
            ob.visible_shadow = False
    card = area_light("Card", (0.02, -0.12, 0.16), (0, 0, 0), 0.04, 0.1, (0.9, 0.95, 1.0))
    k2.aim(card, (0, 0, 0.066))
    cs.strip("Graze", (0.15, -0.03, 0.08), (0, 0, 0.065), 0.3, 0.006, 0.16, ICE)
    cs.strip("Top", (0.0, -0.06, 0.2), (0, 0, 0.06), 0.15, 0.01, 0.12, SILVER)
    cs.strip("Fill", (-0.15, -0.12, 0.09), (0, 0, 0.065), 0.25, 0.04, 0.04, ICE)
    cam = cs.cam_make(100, 5.6)
    a = math.radians(18)
    pos = Vector((0.15 * math.sin(a), -0.15 * math.cos(a), 0.07))
    tgt = (0.0, -R * 0.5, 0.066)
    cs.look(cam, pos, tgt, focus=cs.focus_on(pos, tgt, Vector((0, -R, 0.066))))


def F14(sc):
    """Multi-pack: five capped bottles staggered back into the dark, the front one sharp."""
    cs.cyc([(0, (1, 4, 12)), (0.5, (2, 10, 30)), (1, (2, 2, 6))], -0.3, 0.6, glow=((4, 24, 70), 0.12, 0.10, 0.25))
    matte_floor((1, 5, 14), rough=0.85)
    for k in range(5):
        piv, root, R = cs.bottle(cap=True)
        nozzle_to_back(root)
        piv.location = (-0.05 + 0.034 * k, 0.10 * k, cs.MID)
    bottle_materials()
    cs.strip("RimR", (0.45, 0.35, 0.2), (0.05, 0.2, 0.08), 1.2, 0.02, 9, SILVER)
    cs.strip("RimL", (-0.35, 0.5, 0.18), (0.05, 0.2, 0.08), 1.2, 0.02, 4, INDIGO)
    key = area_light("Key", (-0.35, -0.3, 0.25), (0, 0, 0), 0.25, 1.2, SILVER)
    k2.aim(key, (0.0, 0.1, 0.08))
    cam = cs.cam_make(85, 2.8)
    pos, tgt = Vector((-0.03, -0.5, 0.075)), (0.0, 0.12, 0.09)
    cs.look(cam, pos, tgt, focus=cs.focus_on(pos, tgt, Vector((-0.05, -0.02, 0.08))))


SHOTS = {k: v for k, v in globals().items() if re.fullmatch(r"F\d+", k) and callable(v)}


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
    sc.frame_set(sc.frame_current)                       # F11 leaves the scene on its smoke frame
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
