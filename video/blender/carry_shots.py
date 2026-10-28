"""Spraymax "What's bro carrying": the 3D product half (Blender / Cycles, CPU, 30 fps, 1080x1920).

Follows the CGI half of the reference reel beat for beat: after the street hook, nine macro product shots
cut on a ~0.68 s beat. The reference's purple + red becomes Spraymax indigo with two accents from the
brand story, Himalayan salt pink and ocean blue. The bottle carries the real label (4x rebuild with the
clean wordmark, see label_hires.py), so the print is exact in every frame.

  C1 tilt     bottle tilted in an indigo void, a strip light sweeps across the label (match cut from the hand)
  C2 macro    extreme close-up sliding down the wordmark, shallow focus, dutch angle
  C3 pump     cap off, the pump dips, a burst of mist, backlit
  C4 salt     pink salt crystal with water beads, a drop falls past
  C5 bubbles  air bubbles rising through ocean-blue water
  C6 collar   low-angle silhouette of the pump and ribbed collar, turning
  C7 falling  salt crystals tumbling through warm light
  C8 drops    bottle among floating water drops, push-in
  C9 end      bottle on a glossy floor, indigo glow, push-in, top kept clear for the end card

  python video/blender/carry_shots.py --shot C1 --out DIR [--frames 1,12] [--samples 32] [--res-scale 100]
(run with the venv python that has `bpy`; label: python3 video/blender/label_hires.py first)
"""
import math
import random
import sys
from pathlib import Path

import bpy  # noqa: I001
import bmesh
import numpy as np
from mathutils import Quaternion, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spraymax_scene import area_light, make_bottle, principled, r, z  # noqa: E402
import k2_shots as k2  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
LABEL = ROOT / "video/assets/label-hires.jpg"
FPS = 30
TOP = z(800)                       # cap top (m), bottle standing on z=0
MID = 0.08

# frames per shot = the reference's cut points on its beat grid (+2 handle frames)
LENGTHS = {"C1": 23, "C2": 22, "C3": 40, "C4": 24, "C5": 22, "C6": 22, "C7": 22, "C8": 23, "C9": 48}

# linear-RGB palettes: (deep, glow). Near-black with one tight glow, like the reference's purple void.
INDIGO = ((0.0006, 0.0003, 0.004), (0.10, 0.035, 0.85))
OCEAN = ((0.0, 0.0008, 0.003), (0.02, 0.20, 0.55))
SALT = ((0.003, 0.0004, 0.0008), (0.95, 0.24, 0.10))


# ---------------------------------------------------------------- helpers
def setup(samples, res):
    sc = k2.setup(samples, res)
    sc.render.fps = FPS
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.cycles.transmission_bounces = 8
    sc.cycles.max_bounces = 10
    sc.render.use_persistent_data = True               # keep the BVH/textures between frames
    return sc


def cam_make(lens=85.0, fstop=2.8):
    cd = bpy.data.cameras.new("Cam")
    cd.lens = lens
    cd.sensor_fit = "VERTICAL"
    cd.sensor_width = cd.sensor_height = 36.0
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = fstop
    cam = bpy.data.objects.new("Cam", cd)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    return cam


def look(cam, pos, target, roll=0.0, focus=None):
    """Place the camera at pos looking at target, rolled (deg) about its view axis."""
    cam.location = Vector(pos)
    d = Vector(target) - cam.location
    q = d.to_track_quat("-Z", "Y") @ Quaternion((0, 0, 1), math.radians(roll))
    cam.rotation_euler = q.to_euler()
    cam.data.dof.focus_distance = focus if focus is not None else d.length


def focus_on(pos, target, point):
    """Focus distance (along the view axis) that puts a world point exactly in focus."""
    fwd = (Vector(target) - Vector(pos)).normalized()
    return (Vector(point) - Vector(pos)).dot(fwd)


def vis_h(lens, dist):
    """Visible frame height (m) at a distance for a vertical 36 mm sensor."""
    return 36.0 / lens * dist


def lerp(a, b, t):
    return a + (b - a) * t


ease, ease_out = k2.ease, k2.ease_out


def bottle(cap=True):
    """Bottle on a pivot at mid-height (so tilts and turns happen about its centre)."""
    root, R = make_bottle(with_cap=cap, label_art=LABEL)
    piv = bpy.data.objects.new("Pivot", None)
    bpy.context.collection.objects.link(piv)
    piv.location = (0, 0, MID)
    root.parent = piv
    root.location = (0, 0, -MID)
    return piv, root, R


def void(pal, glow_z, glow_x=0.0, radius=0.15, y=1.0, strength=1.0):
    """Emissive backdrop: near-black with one soft glow (1/e radius in metres) at (glow_x, glow_z). The
    camera only sees ~0.4-0.6 m of it, so the glow must be small to leave dark around it. Seen by the
    camera and in reflections, but it doesn't light the scene diffusely, so the product keeps its contrast."""
    falloff = 1.0 / radius ** 2
    deep, glow = pal
    bpy.ops.mesh.primitive_plane_add(size=4.0, location=(0, y, 0.6), rotation=(math.pi / 2, 0, 0))
    bd = bpy.context.object
    m = bpy.data.materials.new("Void")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])

    def op(kind, a, b):
        n_ = nt.nodes.new("ShaderNodeMath")
        n_.operation = kind
        for i, v in enumerate((a, b)):
            if isinstance(v, (int, float)):
                n_.inputs[i].default_value = v
            else:
                nt.links.new(v, n_.inputs[i])
        return n_.outputs[0]
    dx = op("SUBTRACT", sep.outputs[0], glow_x)
    dy = op("SUBTRACT", sep.outputs[1], glow_z - 0.6)
    d2 = op("ADD", op("MULTIPLY", dx, dx), op("MULTIPLY", dy, dy))
    g = op("EXPONENT", op("MULTIPLY", d2, -falloff), 0)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = (*deep, 1)
    mix.inputs[7].default_value = (*glow, 1)
    nt.links.new(g, mix.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = strength
    nt.links.new(mix.outputs[2], em.inputs["Color"])
    nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    bd.data.materials.append(m)
    bd.visible_diffuse = False
    return bd


SPH = {}


def unit_sphere(sub):
    if sub not in SPH:
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
        SPH[sub] = (np.array([v.co[:] for v in bm.verts], np.float32),
                    np.array([[v.index for v in f.verts] for f in bm.faces], np.int64))
        bm.free()
    return SPH[sub]


def set_spheres(ob, centers, radii, sub=3, squash=None):
    """Rebuild a mesh of smooth spheres (subdivided enough for macro); squash=(axis vectors, factors)."""
    V, F = unit_sphere(sub)
    centers = np.asarray(centers, np.float32)
    radii = np.asarray(radii, np.float32)
    n = len(centers)
    me = ob.data
    me.clear_geometry()
    if n == 0:
        return
    base = np.repeat(V[None], n, 0) * radii[:, None, None]
    if squash is not None:
        axes, fac = squash
        along = (base * axes[:, None, :]).sum(2, keepdims=True)
        base = base + along * axes[:, None, :] * (fac[:, None, None] - 1)
    verts = (base + centers[:, None, :]).reshape(-1, 3)
    faces = (F[None] + (np.arange(n) * len(V))[:, None, None]).reshape(-1, 3)
    me.from_pydata(verts.tolist(), [], faces.tolist())
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    me.update()


def water_mat(name="Water", ior=1.33):
    m = principled(name, (1, 1, 1), rough=0.0, transmission=1.0, ior=ior)
    return m


def spheres(name, mat, centers, radii, sub=3, squash=None):
    """One mesh of many smooth spheres (fast to rebuild every frame)."""
    ob = k2.points_mesh(name, mat)
    set_spheres(ob, centers, radii, sub, squash)
    return ob


def wet_floor(color=(0.002, 0.002, 0.004), rough=0.12):
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
    f = bpy.context.object
    f.data.materials.append(principled("WetFloor", color, rough=rough, coat=0.8))
    return f


def strip(name, loc, target, length, width, energy, color=(1, 1, 1)):
    l = area_light(name, loc, (0, 0, 0), width, energy, color, size_y=length)
    k2.aim(l, target)
    return l


def salt_mat(glow=0.6):
    """Raw pink rock salt: uneven pale-pink to salmon with white veins, frosted, translucent, glowing inside."""
    m = principled("PinkSalt", (0.95, 0.52, 0.42), rough=0.5, transmission=0.25, ior=1.54, sss=0.6,
                   emission=((1.0, 0.36, 0.2), glow))
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.25)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.6
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.35, (0.80, 0.22, 0.14, 1)
    els[1].position, els[1].color = 0.62, (0.97, 0.70, 0.62, 1)
    e = els.new(0.78)
    e.color = (1.0, 0.95, 0.93, 1)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Subsurface Radius"])
    fine = nt.nodes.new("ShaderNodeTexNoise")
    fine.inputs["Scale"].default_value = 60.0
    fine.inputs["Detail"].default_value = 6.0
    nt.links.new(tc.outputs["Object"], fine.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.02
    nt.links.new(fine.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    rough = nt.nodes.new("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value = 0.3
    rough.inputs["To Max"].default_value = 0.7
    nt.links.new(fine.outputs["Fac"], rough.inputs["Value"])
    nt.links.new(rough.outputs["Result"], b.inputs["Roughness"])
    return m


def crystal_mesh(name, size, mat, seed):
    """An irregular salt chunk: the convex hull of random points (cleaved facets), bevelled edges,
    subdivided a little so the bump and colour noise read at macro distance."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    for _ in range(26):
        v = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized() * rnd.uniform(0.7, 1.1)
        bm.verts.new(v)
    bmesh.ops.convex_hull(bm, input=bm.verts[:])
    bmesh.ops.bevel(bm, geom=bm.edges[:] + bm.verts[:], offset=0.04, segments=2, affect="EDGES")
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=1, use_grid_fill=True)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.scale = (size * rnd.uniform(0.9, 1.3), size * rnd.uniform(0.8, 1.1), size * rnd.uniform(0.7, 1.0))
    o.data.materials.append(mat)
    return o


# ---------------------------------------------------------------- shots
VIOLET = (0.5, 0.36, 1.0)


def shot_C1(sc):
    """Tilt: bottle tipped ~28 deg in an indigo void; a strip light sweeps across the label; slow push."""
    zc = 0.6 + MID
    void(INDIGO, glow_z=zc + 0.10, glow_x=0.08, radius=0.10, strength=0.8)
    piv, root, R = bottle(cap=True)
    piv.location = (0, 0, zc)
    sweep = strip("Sweep", (-0.3, -0.32, zc + 0.05), (0, 0, zc), 0.7, 0.03, 14, (1.0, 1.0, 1.0))
    key = area_light("Key", (-0.35, -0.35, zc + 0.2), (0, 0, 0), 0.25, 1.2, (0.92, 0.93, 1.0))
    k2.aim(key, (0, 0, zc))
    strip("RimR", (0.22, 0.20, zc + 0.05), (0, 0, zc), 0.6, 0.03, 18, VIOLET)
    strip("RimL", (-0.22, 0.20, zc), (0, 0, zc), 0.6, 0.03, 10, (0.4, 0.35, 1.0))
    cam = cam_make(85, 4.0)
    n = LENGTHS["C1"]

    def at(f):
        t = (f - 1) / (n - 1)
        piv.rotation_euler = (0, math.radians(28), math.radians(lerp(-24, -12, ease(t))))
        d = lerp(0.42, 0.36, ease(t))
        look(cam, (0.0, -d, zc + 0.01), (0.004, 0, zc + 0.012), focus=d - R)
        sweep.location = (lerp(-0.34, 0.30, ease(t)), -0.30, zc + 0.05)
        k2.aim(sweep, (0, 0, zc))
    return at, n


def shot_C2(sc):
    """Macro: extreme close-up sliding down the wordmark, f/2.2, dutch angle; the curve falls into dark."""
    void(INDIGO, glow_z=0.11, glow_x=0.10, radius=0.08, strength=0.8)
    piv, root, R = bottle(cap=True)
    strip("Key", (-0.16, -0.14, 0.11), (0, 0, 0.07), 0.25, 0.03, 1.2, (1.0, 0.98, 0.96))
    strip("RimR", (0.14, 0.06, 0.10), (0, 0, 0.07), 0.3, 0.02, 10, VIOLET)
    cam = cam_make(100, 2.8)
    n = LENGTHS["C2"]
    d = 0.20                                              # ~72 mm of label visible top to bottom

    def at(f):
        t = (f - 1) / (n - 1)
        zc = lerp(0.080, 0.056, ease(t))
        a = math.radians(lerp(18, 12, ease(t)))
        pos = Vector((d * math.sin(a), -d * math.cos(a), zc + 0.006))
        mark = Vector((0.0, -R, zc))                       # the wordmark, on the front of the label
        look(cam, pos, (0.0, -R * 0.4, zc), roll=-22, focus=focus_on(pos, (0.0, -R * 0.4, zc), mark))
    return at, n


def shot_C3(sc):
    """Pump: cap off, the actuator dips, a slow-motion burst of mist crosses the frame, backlit."""
    void(INDIGO, glow_z=0.17, glow_x=0.14, radius=0.09, strength=0.8)
    piv, root, R = bottle(cap=False)
    yaw = math.radians(90)                                # nozzle points to camera right
    piv.rotation_euler = (0, 0, yaw)
    act = [o for o in root.children if o.name.startswith(("Actuator", "Cylinder"))]
    act0 = {o.name: o.location.copy() for o in act}
    key = area_light("Key", (-0.30, -0.30, 0.25), (0, 0, 0), 0.25, 0.8, (0.88, 0.9, 1.0))
    k2.aim(key, (0, 0, 0.14))
    back = area_light("Back", (0.14, 0.30, 0.17), (0, 0, 0), 0.10, 45, (1.0, 1.0, 1.0))
    k2.aim(back, (0.07, 0, 0.15))
    strip("RimL", (-0.16, 0.18, 0.16), (0, 0, 0.14), 0.3, 0.02, 10, VIOLET)
    cam = cam_make(100, 4.0)
    mist_m = bpy.data.materials.new("Mist")
    mist_m.use_nodes = True
    mb = mist_m.node_tree.nodes["Principled BSDF"]
    mb.inputs["Base Color"].default_value = (1, 1, 1, 1)
    mb.inputs["Roughness"].default_value = 0.25
    mb.inputs["Alpha"].default_value = 0.45
    mist = k2.points_mesh("Mist", mist_m)
    rng = np.random.default_rng(3)
    N = 50000
    te = rng.uniform(0, 0.55, N)                           # emission times after the press (s)
    spd = rng.uniform(0.20, 0.50, N)
    half = math.radians(14)
    th, ph = np.sqrt(rng.uniform(0, 1, N)) * half, rng.uniform(0, 2 * math.pi, N)
    local = np.stack([np.sin(th) * np.cos(ph), -np.cos(th), np.sin(th) * np.sin(ph)], 1)
    c, s_ = math.cos(yaw), math.sin(yaw)
    R3 = np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1]])
    dirs = local @ R3.T
    nz = R3 @ np.array([0, -r(160), 0])
    nozzle = np.array([nz[0], nz[1], z(870)])
    size = rng.uniform(0.00003, 0.00008, N)
    tau = 0.30
    drift = rng.normal(0, 0.004, (N, 3))
    press = 6
    n = LENGTHS["C3"]

    def at(f):
        dz = -0.0025 * (ease((f - press) / 3) - ease((f - press - 10) / 5))
        for o in act:
            o.location = act0[o.name] + Vector((0, 0, dz))
        tt_all = (f - press - 2) / FPS - te
        live = (tt_all > 0) & (tt_all < 3.0)
        tt = tt_all[live]
        dist = spd[live] * tau * (1 - np.exp(-tt / tau))
        vel = (spd[live] * np.exp(-tt / tau))[:, None] * dirs[live]
        pos = nozzle + dirs[live] * dist[:, None] + drift[live] * tt[:, None] + np.array([0, 0, -0.02]) * tt[:, None] ** 2
        k2.set_points(mist, pos.astype(np.float32), (size[live] * (1 + 0.8 * tt)).astype(np.float32), vel, stretch=0.012)
        t = (f - 1) / (n - 1)
        dcam = lerp(0.215, 0.20, ease(t))
        look(cam, (0.0, -dcam, 0.145), (0.022, 0, 0.138), focus=dcam - r(160))
    return at, n


def shot_C4(sc):
    """Salt: a raw pink Himalayan salt chunk with water beads on a wet black floor; a drop falls past."""
    void(SALT, glow_z=0.07, radius=0.07, strength=0.7)
    wet_floor()
    m = salt_mat(0.12)
    hero = crystal_mesh("Hero", 0.021, m, seed=7)
    hero.location = (0, 0, 0.017)
    hero.rotation_euler = (0.3, 0.5, 0.2)
    rnd = random.Random(3)
    for i in range(9):
        o = crystal_mesh(f"S{i}", rnd.uniform(0.003, 0.007), m, seed=20 + i)
        a = rnd.uniform(0, 2 * math.pi)
        rr = rnd.uniform(0.035, 0.09)                    # around and behind the chunk, never in front
        o.location = (rr * math.cos(a), abs(rr * math.sin(a)) * 0.8 + 0.01, 0.003)
        o.rotation_euler = (rnd.uniform(0, 6), rnd.uniform(0, 6), rnd.uniform(0, 6))
    bpy.context.view_layer.update()
    # water beads: ray-cast onto the chunk's upper faces, flattened along the surface normal
    water = water_mat()
    inv = hero.matrix_world.inverted()
    nmat = hero.matrix_world.to_3x3().inverted().transposed()
    cs, rs, ax = [], [], []
    for _ in range(600):
        th = rnd.uniform(0, 2 * math.pi)
        el = rnd.uniform(0.1, 1.3)
        dirw = Vector((math.cos(th) * math.cos(el), math.sin(th) * math.cos(el), math.sin(el)))
        ok, loc, nrm, _ = hero.ray_cast(inv @ (hero.location + dirw * 0.1), (inv.to_3x3() @ -dirw).normalized())
        if not ok:
            continue
        nw = (nmat @ nrm).normalized()
        rad = rnd.uniform(0.0005, 0.0016) if rnd.random() < 0.85 else rnd.uniform(0.0018, 0.003)
        cs.append(tuple(hero.matrix_world @ loc + nw * rad * 0.3))
        rs.append(rad)
        ax.append(tuple(nw))
        if len(cs) >= 60:
            break
    spheres("Beads", water, cs, rs, sub=3, squash=(np.array(ax, np.float32), np.full(len(cs), 0.55, np.float32)))
    drop = spheres("Drop", water, [(0, 0, 1)], [0.0022])
    back = area_light("Back", (0.04, 0.22, 0.09), (0, 0, 0), 0.06, 7, (1.0, 0.55, 0.35))
    k2.aim(back, (0, 0, 0.02))
    back.visible_glossy = False                          # glow through the salt, no panel in the wet floor
    key = area_light("Key", (-0.2, -0.18, 0.16), (0, 0, 0), 0.12, 0.6, (0.9, 0.92, 1.0))
    k2.aim(key, (0, 0, 0.02))
    strip("Rim", (0.18, 0.02, 0.10), (0, 0, 0.02), 0.25, 0.02, 4, (1.0, 0.7, 0.6))
    cam = cam_make(100, 3.2)
    n = LENGTHS["C4"]

    def at(f):
        t = (f - 1) / (n - 1)
        a = math.radians(lerp(-10, 6, ease(t)))
        d = 0.24
        look(cam, (d * math.sin(a), -d * math.cos(a), 0.05), (0, 0, 0.022), focus=d - 0.012)
        tz = max((f - 3) / FPS, 0)
        zz = 0.105 - 0.6 * tz ** 2 - 0.12 * tz                 # slow-motion fall, in front of the chunk
        set_spheres(drop, [(-0.016, -0.014, zz)], [0.0022], 3,
                    (np.array([[0, 0, 1]], np.float32), np.array([1.3], np.float32)))
    return at, n


def shot_C5(sc):
    """Bubbles: streams of air bubbles rising through ocean-blue water, surface glow above, f/2.8."""
    void(OCEAN, glow_z=0.30, radius=0.14, strength=0.9)
    rng = np.random.default_rng(5)
    cs, rad, vup, ph = [], [], [], []
    for sx in (-0.022, 0.004, 0.024):                     # three streams near the focus plane (frame is ~70 mm wide)
        for k in range(26):
            cs.append((sx + rng.normal(0, 0.002), rng.uniform(0.27, 0.31), -0.08 + k * 0.009 + rng.uniform(0, 0.004)))
            rr = rng.uniform(0.0012, 0.0035)
            rad.append(rr)
    for _ in range(70):                                    # loose bubbles in front and behind (bokeh)
        cs.append((rng.uniform(-0.12, 0.12), rng.uniform(0.4, 0.75),
                   rng.uniform(-0.25, 0.25)))
        rad.append(rng.uniform(0.001, 0.0035))
    cs, rad = np.array(cs, np.float32), np.array(rad, np.float32)
    vup = 0.06 + 6.0 * rad + rng.uniform(0, 0.01, len(rad))    # bigger bubbles rise faster (slow motion)
    ph = rng.uniform(0, 6.28, len(rad))
    bub = spheres("Bubbles", water_mat("Air", ior=0.75), cs, rad, sub=3)
    top = area_light("Surface", (0, 0.3, 0.5), (0, 0, 0), 0.6, 20, (0.6, 0.85, 1.0))
    k2.aim(top, (0, 0.3, 0))
    strip("RimL", (-0.25, 0.32, 0.02), (0, 0.3, 0.02), 0.6, 0.04, 25, (0.4, 0.75, 1.0))
    strip("RimR", (0.25, 0.32, 0.02), (0, 0.3, 0.02), 0.6, 0.04, 25, (0.4, 0.75, 1.0))
    cam = cam_make(85, 2.8)
    look(cam, (0, -0.02, 0.02), (0, 0.4, 0.02), focus=0.31)
    n = LENGTHS["C5"]

    def at(f):
        t = (f - 1) / FPS
        pos = cs.copy()
        pos[:, 2] = cs[:, 2] + vup * t
        pos[:, 0] += 0.0015 * np.sin(t * 14 + ph)
        wob = 1 + 0.12 * np.sin(t * 20 + ph)
        set_spheres(bub, pos, rad, 3, (np.tile(np.array([[0, 0, 1]], np.float32), (len(rad), 1)), (0.85 * wob).astype(np.float32)))
    return at, n


def shot_C6(sc):
    """Collar: low-angle silhouette of the pump and ribbed collar against a violet glow, slowly turning."""
    void(INDIGO, glow_z=0.36, radius=0.09, strength=1.1)
    piv, root, R = bottle(cap=False)
    strip("RimL", (-0.10, 0.14, 0.14), (0, 0, 0.13), 0.3, 0.02, 12, VIOLET)
    strip("RimR", (0.10, 0.14, 0.14), (0, 0, 0.13), 0.3, 0.02, 12, VIOLET)
    key = area_light("Key", (-0.2, -0.2, 0.05), (0, 0, 0), 0.1, 0.2, (0.8, 0.82, 1.0))
    k2.aim(key, (0, 0, 0.13))
    cam = cam_make(100, 5.6)
    n = LENGTHS["C6"]

    def at(f):
        t = (f - 1) / (n - 1)
        piv.rotation_euler = (0, 0, math.radians(lerp(-10, 14, t)))
        d = lerp(0.215, 0.20, ease(t))
        pos, tgt = Vector((0.01, -d, 0.095)), (0.0, 0, 0.142)
        look(cam, pos, tgt, roll=14, focus=focus_on(pos, tgt, Vector((0.0, -r(244), 0.124))))
    return at, n


def shot_C7(sc):
    """Falling salt: pink rock-salt chunks tumbling through warm backlight in slow motion."""
    void(SALT, glow_z=0.06, radius=0.10, strength=0.8)
    m = salt_mat(0.1)
    rnd = random.Random(11)
    objs = []
    for i in range(40):
        near = rnd.random() < 0.8
        o = crystal_mesh(f"F{i}", rnd.uniform(0.003, 0.009), m, seed=100 + i)
        y = rnd.uniform(0.27, 0.33) if near else rnd.uniform(0.42, 0.7)
        p = Vector((rnd.uniform(-0.055, 0.055), y, rnd.uniform(-0.02, 0.16)))
        objs.append((o, p, rnd.uniform(0.04, 0.09), Vector((rnd.uniform(-3, 3), rnd.uniform(-3, 3), rnd.uniform(-3, 3)))))
    back = area_light("Back", (0, 0.8, 0.08), (0, 0, 0), 0.4, 25, (1.0, 0.55, 0.32))
    k2.aim(back, (0, 0.3, 0.05))
    key = area_light("Key", (-0.3, -0.05, 0.25), (0, 0, 0), 0.2, 1.2, (0.9, 0.9, 1.0))
    k2.aim(key, (0, 0.3, 0.05))
    cam = cam_make(85, 2.4)
    look(cam, (0, -0.02, 0.06), (0, 0.35, 0.06), focus=0.32)
    n = LENGTHS["C7"]

    def at(f):
        t = (f - 1) / FPS
        for o, p, v, w in objs:
            o.location = (p.x, p.y, p.z - v * t)
            o.rotation_euler = (w.x * t * 0.4, w.y * t * 0.4, w.z * t * 0.4)
    return at, n


def shot_C8(sc):
    """Drops: bottle with its clear cap among floating water drops, slow push-in."""
    void(INDIGO, glow_z=0.14, radius=0.12, strength=0.8)
    piv, root, R = bottle(cap=True)
    rng = np.random.default_rng(8)
    M = 160
    ang = rng.uniform(0, 2 * math.pi, M)
    rr = rng.uniform(R + 0.012, 0.13, M)
    p0 = np.stack([rr * np.cos(ang), rr * np.sin(ang) * 1.2, rng.uniform(-0.02, 0.19, M)], 1)
    p0 = p0[np.hypot(p0[:, 0], p0[:, 1]) > R + 0.01].astype(np.float32)
    M = len(p0)
    rad = np.where(rng.random(M) < 0.75, rng.uniform(0.0012, 0.0035, M), rng.uniform(0.004, 0.008, M)).astype(np.float32)
    vel = rng.normal(0, 0.004, (M, 3)).astype(np.float32)
    drops = spheres("Drops", water_mat(), p0, rad, sub=3)
    key = area_light("Key", (-0.55, -0.25, 0.2), (0, 0, 0), 0.15, 2.0, (0.95, 0.95, 1.0))
    k2.aim(key, (0, 0, 0.08))
    strip("Spec", (0.12, -0.5, 0.1), (0, 0, 0.08), 0.5, 0.02, 4, (1.0, 1.0, 1.0))
    strip("RimL", (-0.3, 0.25, 0.2), (0, 0, 0.09), 0.5, 0.04, 18, VIOLET)
    strip("RimR", (0.3, 0.25, 0.2), (0, 0, 0.09), 0.5, 0.04, 18, VIOLET)
    cam = cam_make(85, 4.0)
    n = LENGTHS["C8"]

    def at(f):
        t = (f - 1) / FPS
        set_spheres(drops, p0 + vel * t, rad, 3)
        d = lerp(0.56, 0.47, ease((f - 1) / (n - 1)))
        look(cam, (0, -d, 0.085), (0, 0, 0.085), focus=d - R)
    return at, n


def shot_C9(sc):
    """End: bottle on a glossy black floor, indigo glow behind, slow push-in; top of frame left for type."""
    void(INDIGO, glow_z=0.16, radius=0.13, strength=0.8)
    wet_floor(rough=0.06)
    piv, root, R = bottle(cap=True)
    key = area_light("Key", (-0.6, -0.3, 0.25), (0, 0, 0), 0.18, 4, (0.95, 0.95, 1.0))
    k2.aim(key, (0, 0, 0.08))
    strip("Spec", (0.15, -0.6, 0.1), (0, 0, 0.08), 0.6, 0.02, 6, (1.0, 1.0, 1.0))
    strip("RimL", (-0.32, 0.3, 0.22), (0, 0, 0.09), 0.6, 0.05, 35, VIOLET)
    strip("RimR", (0.32, 0.3, 0.22), (0, 0, 0.09), 0.6, 0.05, 35, VIOLET)
    cam = cam_make(85, 4.0)
    n = LENGTHS["C9"]

    def at(f):
        t = ease((f - 1) / (n - 1))
        d = lerp(0.80, 0.72, t)                         # bottle ~900 -> 1000 px tall
        h = vis_h(85, d)
        aim_z = 0.08 + (1150 - 960) / 1920 * h          # bottle centre ~190 px below frame centre
        look(cam, (0, -d, 0.065), (0, 0, aim_z), focus=d - R)
    return at, n


SHOTS = {k: globals()[f"shot_{k}"] for k in LENGTHS}


def main():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    shot = a[a.index("--shot") + 1]
    out = Path(a[a.index("--out") + 1])
    samples = int(a[a.index("--samples") + 1]) if "--samples" in a else 32
    res = int(a[a.index("--res-scale") + 1]) if "--res-scale" in a else 100
    sc = setup(samples, res)
    at, n = SHOTS[shot](sc)
    for ob in bpy.data.objects:                         # lights light the scene but never show as panels
        if ob.type == "LIGHT":
            ob.visible_camera = False
    frames = [int(x) for x in a[a.index("--frames") + 1].split(",")] if "--frames" in a else range(1, n + 1)
    out.mkdir(parents=True, exist_ok=True)
    for f in frames:
        path = out / f"{shot}_{f:04d}.png"
        if "--skip-existing" in a and path.exists():
            continue
        sc.frame_set(f)
        at(f)
        sc.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        print("frame", shot, f, flush=True)


if __name__ == "__main__":
    main()
