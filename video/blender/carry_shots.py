"""Spraymax "What's bro carrying": the 3D product half (Blender / Cycles, CPU, 30 fps, 1080x1920).

A shot-for-shot copy of the reference reel's 3D half (same order, timing, framing and measured colours:
purple world, dark-red accents) with the Spraymax bottle and its real label (4x rebuild with the clean
wordmark, see label_hires.py). Where the reference uses a dropper (their product is a serum) ours sprays.

  C1 tilt     bottle tipped ~38 deg in purple haze, a flare on its shoulder, pink specks, rack focus
  C2 macro    the wordmark running across the frame, extreme close-up, glass blobs out of focus in front
  C3 burst    the pump front-on, it fires: a fine-mist burst crosses the frame (a mist pump never drips)
  C4 petals   lilac; orchid petals lower left, our pump leaning in from the right and misting them
  C5 tube     dark red, inside a glass tube of salt water: big and small bubbles rising
  C6 profile  the pump side-on against a purple gradient, a strip of light slides across it
  C7 salt     dark red; a raw pink salt chunk with water beads, our pump misting it
  C8 spheres  the bottle front-on, buried in big purple-lit water spheres, one magnifying the label
  C9 shelf    the Pack of 3 on a glass shelf on steel rods in a purple room; end card above

  python video/blender/carry_shots.py --shot C1 --out DIR [--frames 1,12] [--samples 12] [--res-scale 75]
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
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
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


# ---------------------------------------------------------------- shots (v2: the reference, shot for shot)
# Colours are the reference's own, measured from its frames (sRGB 0-255), rendered with the Standard view
# transform so a backdrop shows exactly the colour asked for. Our white bottle stays white; it is lit low
# so it takes the purple and keeps its shape instead of blowing out.
VIOLET = (0.5, 0.36, 1.0)
LILAC = (0.78, 0.66, 1.0)


def srgb(c):
    """sRGB 0-255 -> linear."""
    def f(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return tuple(f(x) for x in c)


def cyc(stops, z0, z1, glow=None, y=1.0, strength=1.0):
    """Graded emissive backdrop: a colour ramp from world height z0 (pos 0) to z1 (pos 1), plus an optional
    radial glow (rgb, x, z, radius). Seen by the camera and in reflections, never as diffuse light."""
    bpy.ops.mesh.primitive_plane_add(size=6.0, location=(0, y, 0.6), rotation=(math.pi / 2, 0, 0))
    bd = bpy.context.object
    m = bpy.data.materials.new("Cyc")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = z0 - 0.6
    mr.inputs["From Max"].default_value = z1 - 0.6
    mr.clamp = True
    nt.links.new(sep.outputs[1], mr.inputs["Value"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = stops[0][0], (*srgb(stops[0][1]), 1)
    els[1].position, els[1].color = stops[-1][0], (*srgb(stops[-1][1]), 1)
    for pos, col in stops[1:-1]:
        e = els.new(pos)
        e.color = (*srgb(col), 1)
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    col = ramp.outputs["Color"]
    if glow:
        gcol, gx, gz, grad = glow

        def op(kind, a_, b_):
            n_ = nt.nodes.new("ShaderNodeMath")
            n_.operation = kind
            for i, v in enumerate((a_, b_)):
                if isinstance(v, (int, float)):
                    n_.inputs[i].default_value = v
                else:
                    nt.links.new(v, n_.inputs[i])
            return n_.outputs[0]
        dx = op("SUBTRACT", sep.outputs[0], gx)
        dy = op("SUBTRACT", sep.outputs[1], gz - 0.6)
        d2 = op("ADD", op("MULTIPLY", dx, dx), op("MULTIPLY", dy, dy))
        g = op("EXPONENT", op("MULTIPLY", d2, -1.0 / grad ** 2), 0)
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "ADD"
        nt.links.new(g, mix.inputs[0])
        nt.links.new(col, mix.inputs[6])
        mix.inputs[7].default_value = (*srgb(gcol), 1)
        col = mix.outputs[2]
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = strength
    nt.links.new(col, em.inputs["Color"])
    nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    bd.data.materials.append(m)
    bd.visible_diffuse = False
    return bd


def glossy_bottle():
    """Crisper plastic: a clear coat so strip lights draw sharp lines along the bottle."""
    for name, rough, coat in (("BottleWhite", 0.2, 1.0), ("LabelMat", 0.3, 0.8), ("PumpWhite", 0.3, 0.6)):
        m = bpy.data.materials.get(name)
        if m:
            b = m.node_tree.nodes["Principled BSDF"]
            if name != "LabelMat":                         # white plastic reads light grey in a dark studio
                b.inputs["Base Color"].default_value = (0.62, 0.62, 0.66, 1)
            b.inputs["Roughness"].default_value = rough
            b.inputs["Coat Weight"].default_value = coat
            b.inputs["Coat Roughness"].default_value = 0.04


def emissive(name, rgb, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*rgb, 1)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return m


def nozzle_world(root, piv):
    """World position of the nozzle hole and the direction the spray leaves it."""
    bpy.context.view_layer.update()
    mw = root.matrix_world
    pos = mw @ Vector((0, -r(160), z(870)))
    d = (mw.to_3x3() @ Vector((0, -1, 0))).normalized()
    return np.array(pos), np.array(d)


def mist_emitter(origin, direction, press, n=40000, cone=13.0, spd=(0.18, 0.42), dur=0.45, seed=3, bloom=4.0):
    """A burst of fine mist from origin along direction, starting at frame press. Returns update(f).
    Built to look like real atomised spray, not a solid cone: each droplet is faint (they only add up to a
    haze where they crowd), the burst is front-loaded and breaks into a few uneven sub-jets, speeds and sizes
    are spread out (a few heavier droplets fly straighter and further), a slow swirl grows with distance,
    and every droplet shrinks away at the end of its life so the edges thin out."""
    mm = bpy.data.materials.new("Mist")
    mm.use_nodes = True
    mb = mm.node_tree.nodes["Principled BSDF"]
    mb.inputs["Base Color"].default_value = (0.95, 0.96, 1.0, 1)
    mb.inputs["Roughness"].default_value = 0.3
    mb.inputs["Alpha"].default_value = 0.22
    ob = k2.points_mesh("Mist", mm)
    rng = np.random.default_rng(seed)
    te = dur * rng.beta(1.3, 3.0, n)                       # front-loaded burst with a tail
    half = math.radians(cone)
    k = 7                                                  # uneven sub-jets
    jw = rng.dirichlet(np.ones(k) * 0.8)
    jth = np.sqrt(rng.uniform(0, 1, k)) * half * 0.75
    jph = rng.uniform(0, 2 * math.pi, k)
    which = rng.choice(k, n, p=jw)
    th = np.abs(jth[which] + rng.normal(0, half * 0.45, n))
    ph = jph[which] + rng.normal(0, 0.7, n)
    d = direction / np.linalg.norm(direction)
    a_ = np.array([0, 0, 1.0]) if abs(d[2]) < 0.9 else np.array([1.0, 0, 0])
    u = np.cross(d, a_)
    u /= np.linalg.norm(u)
    v = np.cross(d, u)
    dirs = (np.cos(th)[:, None] * d + (np.sin(th) * np.cos(ph))[:, None] * u + (np.sin(th) * np.sin(ph))[:, None] * v)
    mid = 0.5 * (spd[0] + spd[1])
    sp = np.clip(mid * np.exp(rng.normal(0, 0.45, n)), 0.04, 0.8)
    size = 0.00006 * np.exp(rng.normal(0, 0.45, n))
    big = rng.random(n) < 0.03                             # heavier droplets: bigger, less drag
    size[big] *= 2.6
    tau = np.where(big, 0.7, rng.uniform(0.18, 0.32, n))
    life = rng.uniform(0.6, 1.6, n)
    # the plume blooms: each droplet drifts sideways (a random direction across the jet) more and more the
    # further it has flown, so the spray is tight at the nozzle and opens into a big soft cloud at the end
    qa = rng.uniform(0, 2 * math.pi, n)
    qdir = np.cos(qa)[:, None] * u + np.sin(qa)[:, None] * v
    qmag = np.abs(rng.normal(0, 1, n))
    drift = rng.normal(0, 0.003, (n, 3))
    # slow swirl: a few random sinusoidal modes, strength growing with distance from the nozzle
    kv = rng.normal(0, 90, (3, 3))
    om = rng.uniform(2, 6, 3)
    phs = rng.uniform(0, 6.28, 3)

    def update(f):
        tt_all = (f - press) / FPS - te
        live = (tt_all > 0) & (tt_all < life)
        tt = tt_all[live]
        dist = sp[live] * tau[live] * (1 - np.exp(-tt / tau[live]))
        vel = (sp[live] * np.exp(-tt / tau[live]))[:, None] * dirs[live]
        pos = origin + dirs[live] * dist[:, None] + drift[live] * tt[:, None] + np.array([0, 0, -0.025]) * tt[:, None] ** 2
        pos = pos + qdir[live] * (bloom * qmag[live] * dist ** 2 + 0.02 * qmag[live] * tt ** 1.5)[:, None]
        sw = np.stack([np.sin(pos @ kv[i] + om[i] * (f / FPS) + phs[i]) for i in range(3)], 1)
        pos = pos + sw * (0.012 * np.clip(dist / 0.06, 0, 1.5))[:, None]
        fade = np.clip(1 - tt / life[live], 0, 1) ** 0.6
        rad = size[live] * (1 + 1.4 * tt) * fade
        k2.set_points(ob, pos.astype(np.float32), rad.astype(np.float32), vel, stretch=0.010)
    return update
def beads_on(objs, n, rmin, rmax, seed, from_dir=(0, -1, 0.6), spread=0.05, centre=(0, 0, 0)):
    """Water beads sitting on the surfaces of objs (ray-cast from the camera side), flattened on the surface."""
    rnd = random.Random(seed)
    dg = bpy.context.evaluated_depsgraph_get()
    sc = bpy.context.scene
    fd = Vector(from_dir).normalized()
    cs, rs, ax = [], [], []
    names = {o.name for o in objs}
    for _ in range(n * 8):
        o = Vector(centre) + Vector((rnd.uniform(-spread, spread), rnd.uniform(-spread, spread) * 0.3,
                                     rnd.uniform(-spread, spread))) + fd * 0.3
        ok, loc, nrm, _, ob, _ = sc.ray_cast(dg, o, -fd)
        if not ok or ob.name not in names:
            continue
        rad = rnd.uniform(rmin, rmax) if rnd.random() < 0.85 else rnd.uniform(rmax, rmax * 1.8)
        cs.append(tuple(loc + nrm * rad * 0.3))
        rs.append(rad)
        ax.append(tuple(nrm))
        if len(cs) >= n:
            break
    if cs:
        spheres("Beads", water_mat(), cs, rs, sub=3, squash=(np.array(ax, np.float32), np.full(len(cs), 0.55, np.float32)))
    return len(cs)


def petal(name, L, W, cup, curl, mat, seed):
    """An orchid-like petal: a broad, cupped, curling blade with a little thickness."""
    rnd = random.Random(seed)
    nu, nv = 30, 20
    verts, faces = [], []
    for i in range(nu + 1):
        u = i / nu
        w = W * (math.sin(math.pi * u) ** 0.5) * (0.45 + 0.55 * u ** 0.6)
        for j in range(nv + 1):
            vv = -1 + 2 * j / nv
            wav = 0.0015 * math.sin(vv * 7 + seed) * u                 # soft ruffle at the rim
            verts.append((vv * w, u * L, cup * vv * vv * w + curl * u * u * L + wav * abs(vv) ** 2))
    for i in range(nu):
        for j in range(nv):
            a_ = i * (nv + 1) + j
            faces.append((a_, a_ + 1, a_ + nv + 2, a_ + nv + 1))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    so = ob.modifiers.new("Solid", "SOLIDIFY")
    so.thickness = 0.0006
    sub = ob.modifiers.new("Sub", "SUBSURF")
    sub.levels = sub.render_levels = 1
    me.materials.append(mat)
    return ob


def petal_mat():
    m = principled("Petal", (0.42, 0.05, 0.58), rough=0.45, sss=0.6)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.25, 0.9)
    b.inputs["Subsurface Scale"].default_value = 0.003
    b.inputs["Sheen Weight"].default_value = 0.5
    b.inputs["Sheen Tint"].default_value = (0.9, 0.6, 1.0, 1)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wave = nt.nodes.new("ShaderNodeTexNoise")
    wave.inputs["Scale"].default_value = 140.0
    wave.inputs["Detail"].default_value = 4.0
    nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.025
    nt.links.new(wave.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")          # deeper violet veins, lighter magenta between
    ramp.color_ramp.elements[0].color = (0.40, 0.05, 0.58, 1)
    ramp.color_ramp.elements[1].color = (0.55, 0.09, 0.66, 1)
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    return m


def tilted_pump(rot_y_deg, yaw_deg, pos, cap=False):
    """Bottle on its pivot, yawed about its own axis first, then tilted in the picture plane."""
    piv, root, R = bottle(cap=cap)
    piv.rotation_mode = "ZYX"
    piv.rotation_euler = (0, math.radians(rot_y_deg), math.radians(yaw_deg))
    piv.location = pos
    return piv, root, R


def shot_C1(sc):
    """R1: the bottle tipped ~38 deg in purple haze, a flare on its shoulder, pink specks, rack focus."""
    zc = 0.6 + MID
    cyc([(0, (3, 0, 20)), (0.3, (28, 14, 53)), (0.55, (36, 19, 75)), (0.78, (50, 21, 100)), (1, (32, 7, 79))],
        zc - 0.29, zc + 0.29, glow=((40, 18, 90), 0.10, zc + 0.10, 0.12))
    piv, root, R = bottle(cap=True)
    glossy_bottle()
    for name in ("BottleWhite", "PumpWhite"):                # this shot: the bottle reads clean white
        bpy.data.materials[name].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.86, 0.86, 0.9, 1)
    piv.location = (0.006, 0, zc + 0.008)
    strip("RimTop", (0.20, 0.12, zc + 0.14), (0.02, 0, zc + 0.05), 0.4, 0.02, 4, VIOLET)
    strip("RimL", (-0.22, 0.15, zc), (0, 0, zc), 0.5, 0.03, 2.5, VIOLET)
    base = area_light("Base", (-0.10, 0.02, zc - 0.20), (0, 0, 0), 0.06, 3.5, LILAC)
    k2.aim(base, (-0.03, 0, zc - 0.06))
    key = area_light("Key", (-0.12, -0.42, zc + 0.10), (0, 0, 0), 0.5, 1.6, (0.96, 0.94, 1.0))   # big soft front light
    k2.aim(key, (0, 0, zc))
    glint = spheres("Glint", emissive("GlintM", (1.0, 0.85, 1.0), 220), [(0, 0, 0)], [0.0005], sub=2)
    glint.parent = root
    glint.location = (R * 0.62, -R * 0.75, z(1330))
    pink = emissive("Speck", (1.0, 0.25, 0.45), 14)
    rnd = random.Random(4)
    specks = [((rnd.uniform(-0.09, 0.09), rnd.uniform(-0.2, 0.25), zc + rnd.uniform(-0.15, 0.17))) for _ in range(14)]
    spheres("Specks", pink, specks, [rnd.uniform(0.0006, 0.0014) for _ in specks], sub=2)
    cam = cam_make(85, 2.8)
    n = LENGTHS["C1"]

    def at(f):
        t = (f - 1) / (n - 1)
        piv.rotation_euler = (0, math.radians(38), math.radians(lerp(-26, -14, ease(t))))
        d = lerp(0.36, 0.33, ease(t))
        pos = Vector((0.0, -d, zc + 0.01))
        tgt = (0.01, 0, zc + 0.012)
        sharp = focus_on(pos, tgt, Vector((0, -R, zc)))
        look(cam, pos, tgt, focus=lerp(sharp - 0.06, sharp, ease_out((f - 1) / 11)))   # rack focus in
    return at, n


def shot_C2(sc):
    """R2: extreme macro of the wordmark running across the frame; purple glass blobs out of focus in front."""
    cyc([(0, (12, 4, 30)), (0.5, (27, 10, 61)), (1, (29, 8, 68))], -0.25, 0.4)
    piv, root, R = bottle(cap=True)
    glossy_bottle()
    strip("Key", (-0.12, -0.16, 0.14), (0, 0, 0.065), 0.3, 0.04, 0.18, LILAC)
    strip("RimT", (0.0, 0.08, 0.16), (0, 0, 0.07), 0.3, 0.02, 4, VIOLET)
    strip("RimB", (0.0, 0.08, -0.02), (0, 0, 0.06), 0.3, 0.02, 3, VIOLET)
    glass = principled("Blob", (0.75, 0.55, 1.0), rough=0.02, transmission=1.0, ior=1.45)
    blobs = [(-0.010, -0.12, 0.074), (0.009, -0.125, 0.062), (-0.006, -0.13, 0.064), (0.011, -0.118, 0.077)]
    spheres("Blobs", glass, blobs, [0.005, 0.004, 0.0035, 0.003], sub=3)       # out-of-focus glass in front
    cam = cam_make(100, 2.8)
    n = LENGTHS["C2"]
    d = 0.19

    def at(f):
        t = (f - 1) / (n - 1)
        zc = lerp(0.074, 0.062, ease(t))
        pos = Vector((0.004, -d, zc))
        tgt = (0.0, 0, zc)
        look(cam, pos, tgt, roll=-90, focus=focus_on(pos, tgt, Vector((0, -R, zc))))
    return at, n


def shot_C3(sc):
    """R3: the pump front-on and symmetric. Theirs drips (a serum pump); a fine-mist pump never drips, so
    ours fires: the actuator dips and a burst of fine mist comes straight at the lens."""
    cyc([(0, (31, 30, 31)), (0.25, (33, 20, 51)), (0.5, (31, 17, 55)), (0.78, (26, 9, 60)), (1, (17, 3, 43))],
        -0.1, 0.45, glow=((30, 20, 60), 0.0, 0.08, 0.15))
    piv, root, R = bottle(cap=False)
    glossy_bottle()
    pw = bpy.data.materials["PumpWhite"].node_tree.nodes["Principled BSDF"]
    pw.inputs["Coat Weight"].default_value = 0.15             # no neon outline from the backdrop
    pw.inputs["Roughness"].default_value = 0.45
    bw = bpy.data.materials["BottleWhite"].node_tree.nodes["Principled BSDF"]
    bw.inputs["Coat Weight"].default_value = 0.4
    piv.rotation_euler = (0, 0, math.radians(-40))            # nozzle turned 40 deg: the burst crosses the frame
    act = [o for o in root.children if o.name.startswith(("Actuator", "Cylinder"))]
    act0 = {o.name: o.location.copy() for o in act}
    strip("RimL", (-0.12, 0.10, 0.18), (0, 0, 0.14), 0.3, 0.02, 0.7, VIOLET)
    strip("RimR", (0.12, 0.10, 0.18), (0, 0, 0.14), 0.3, 0.02, 0.7, VIOLET)
    top = area_light("Top", (0, -0.06, 0.32), (0, 0, 0), 0.15, 0.5, LILAC)
    k2.aim(top, (0, -0.05, 0.15))
    back = area_light("MistBack", (-0.10, 0.20, 0.17), (0, 0, 0), 0.08, 7, (1.0, 0.95, 1.0))   # backlights the plume
    k2.aim(back, (-0.05, -0.03, 0.15))
    back.visible_glossy = False
    key = area_light("Key", (0, -0.3, 0.2), (0, 0, 0), 0.12, 0.1, LILAC)
    k2.aim(key, (0, 0, 0.14))
    bpy.context.view_layer.update()
    o, dvec = nozzle_world(root, piv)
    press = 10
    mist = mist_emitter(o, dvec, press=press + 1, n=110000, cone=19, spd=(0.35, 0.8), dur=0.55, seed=9)
    cam = cam_make(100, 4.0)
    n = LENGTHS["C3"]

    def at(f):
        t = (f - 1) / (n - 1)
        dz = -0.0025 * (ease((f - press) / 3) - ease((f - press - 9) / 5))
        for ob in act:
            ob.location = act0[ob.name] + Vector((0, 0, dz))
        mist(f)
        d = lerp(0.20, 0.19, ease(t))
        pos = Vector((0, -d, 0.165))
        tgt = (0, 0, 0.133)
        look(cam, pos, tgt, focus=focus_on(pos, tgt, Vector((0, -r(160), 0.15))))
    return at, n


def misting_shot(sc, kind):
    """R4/R7: an organic subject lower left (orchid petals / a salt chunk) with water beads; our pump comes in
    from the right, leaning as someone sprays, and its mist falls on the subject (their dropper, our spray)."""
    if kind == "petals":
        cyc([(0, (98, 36, 139)), (0.35, (90, 44, 131)), (0.6, (106, 71, 148)), (0.82, (120, 95, 149)), (1, (142, 115, 171))],
            -0.35, 0.40)
        pm = petal_mat()
        subj = []
        for x, y, zz, L, W, cup, curl, rz, rx, sd in [(-0.020, 0.00, -0.042, 0.075, 0.046, 0.35, -0.25, 15, 10, 1),
                                                      (-0.040, 0.01, -0.017, 0.070, 0.042, 0.30, -0.20, 60, -5, 2),
                                                      (-0.005, 0.01, -0.052, 0.065, 0.040, 0.40, -0.30, -15, 25, 3),
                                                      (-0.050, 0.02, -0.042, 0.060, 0.038, 0.35, -0.20, 110, 0, 4),
                                                      (-0.025, -0.02, -0.032, 0.050, 0.032, 0.45, -0.35, 40, 35, 5)]:
            p_ = petal(f"Petal{sd}", L, W, cup, curl, pm, sd)
            p_.location = (x, y, zz)
            p_.rotation_euler = (math.radians(rx - 60), 0, math.radians(rz))
            subj.append(p_)
        centre = (-0.03, 0, -0.01)
        key_rgb, back_rgb, rim_rgb = (1.0, 0.9, 1.0), (0.9, 0.7, 1.0), LILAC
        key_e, back_e = 2.0, 5.0
    else:
        cyc([(0, (17, 0, 1)), (0.3, (24, 1, 1)), (0.55, (64, 3, 5)), (0.8, (32, 4, 4)), (1, (38, 6, 6))], -0.35, 0.40)
        m = salt_mat(0.05)
        m.node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = 0.6
        hero = crystal_mesh("Hero", 0.036, m, seed=7)
        hero.location = (-0.03, 0.0, -0.035)
        hero.rotation_euler = (0.3, 0.5, 0.2)
        subj = [hero]
        centre = (-0.03, 0, -0.03)
        key_rgb, back_rgb, rim_rgb = (1.0, 0.5, 0.45), (1.0, 0.15, 0.1), (1.0, 0.35, 0.3)
        key_e, back_e = 0.6, 8.0
    bpy.context.view_layer.update()
    beads_on(subj, 60, 0.0005, 0.0015, seed=11, from_dir=(0.3, -1, 0.6), spread=0.045, centre=centre)
    # upright bottle leaning left 35 deg, nozzle turned to face left: the mist leaves down-left
    tilt = math.radians(-35)
    top = Vector((0.028, 0.0, 0.03))                       # pump head just right of and above centre
    axis = Vector((math.sin(tilt), 0, math.cos(tilt)))
    piv, root, R = tilted_pump(-35, -90, tuple(top - axis * (TOP - MID)), cap=False)
    glossy_bottle()
    o, dvec = nozzle_world(root, piv)
    mist = mist_emitter(o, dvec, press=3, n=90000, cone=19, spd=(0.25, 0.6), dur=0.6, seed=5)
    key = area_light("Key", (-0.15, -0.3, 0.15), (0, 0, 0), 0.25, key_e, key_rgb)
    k2.aim(key, centre)
    back = area_light("Back", (0.0, 0.25, 0.05), (0, 0, 0), 0.2, back_e, back_rgb)
    k2.aim(back, centre)
    back.visible_glossy = False
    strip("Rim", (0.18, 0.05, 0.12), (0.02, 0, 0.0), 0.4, 0.02, 4, rim_rgb)
    glow = area_light("MistBack", (-0.03, 0.18, 0.05), (0, 0, 0), 0.12, 6, (1.0, 0.95, 1.0))   # makes the plume glow
    k2.aim(glow, (-0.01, 0, 0.0))
    glow.visible_glossy = False
    cam = cam_make(85, 4.0)
    n = LENGTHS["C4"] if kind == "petals" else LENGTHS["C7"]

    def at(f):
        t = (f - 1) / (n - 1)
        mist(f)
        pos = Vector((lerp(-0.004, 0.004, ease(t)), -0.36, 0.0))
        tgt = (0.0, 0, -0.008)
        look(cam, pos, tgt, focus=focus_on(pos, tgt, Vector((centre[0] + 0.01, -0.02, centre[2] + 0.01))))
    return at, n


def shot_C4(sc):
    """R4: lilac; violet orchid petals lower left, our pump misting them."""
    return misting_shot(sc, "petals")


def shot_C5(sc):
    """R5: dark red, inside a glass tube of salt water: big bubbles and small ones rising past its walls."""
    cyc([(0, (26, 2, 2)), (0.5, (24, 4, 4)), (1, (15, 2, 2))], -0.4, 0.5, glow=((95, 9, 8), 0.0, 0.05, 0.07))
    # salt water: a plain cylinder (clean normals); the glass wall: a thin shell that only reflects
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=0.0244, depth=1.0, location=(0, 0, 0.05))
    liq = bpy.context.object
    for pl in liq.data.polygons:
        pl.use_smooth = True
    liq.data.materials.append(principled("SaltWater", (0.9, 0.12, 0.1), rough=0.0, transmission=1.0, ior=1.33))
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=0.0256, depth=1.0, location=(0, 0, 0.05), end_fill_type="NOTHING")
    wall = bpy.context.object
    for pl in wall.data.polygons:
        pl.use_smooth = True
    wm = bpy.data.materials.new("TubeWall")
    wm.use_nodes = True
    wn = wm.node_tree
    wn.nodes.remove(wn.nodes["Principled BSDF"])
    tr, gl, lw, mx = (wn.nodes.new(t) for t in ("ShaderNodeBsdfTransparent", "ShaderNodeBsdfGlossy", "ShaderNodeLayerWeight", "ShaderNodeMixShader"))
    gl.inputs["Roughness"].default_value = 0.02
    lw.inputs["Blend"].default_value = 0.25
    wn.links.new(lw.outputs["Fresnel"], mx.inputs["Fac"])
    wn.links.new(tr.outputs["BSDF"], mx.inputs[1])
    wn.links.new(gl.outputs["BSDF"], mx.inputs[2])
    wn.links.new(mx.outputs["Shader"], wn.nodes["Material Output"].inputs["Surface"])
    wall.data.materials.append(wm)
    rng = np.random.default_rng(5)
    cs, rad = [], []
    for rr, cnt in ((0.010, 1), (0.006, 2), (0.003, 7), (0.0015, 14), (0.0008, 22)):
        for _ in range(cnt):
            rlim = 0.0244 - rr * 1.1
            a_ = rng.uniform(math.pi, 2 * math.pi)            # front half of the tube
            rho = rng.uniform(0, rlim)
            cs.append((rho * math.cos(a_), rho * math.sin(a_), rng.uniform(-0.07, 0.11)))
            rad.append(rr * rng.uniform(0.8, 1.2))
    cs[0] = (-0.008, -0.006, 0.035)
    cs, rad = np.array(cs, np.float32), np.array(rad, np.float32)
    vup = 0.008 + 1.5 * rad
    ph = rng.uniform(0, 6.28, len(rad))
    bub = spheres("Bubbles", water_mat("Air", ior=0.75), cs, rad, sub=3)
    back = area_light("Back", (0, 0.3, 0.03), (0, 0, 0), 0.12, 6, (1.0, 0.18, 0.12))
    k2.aim(back, (0, 0, 0.03))
    back.visible_transmission = False                      # light the bubbles, don't show the panel through the tube
    back.visible_glossy = False
    glint = area_light("BubbleKey", (-0.06, -0.22, 0.14), (0, 0, 0), 0.04, 1.2, (1.0, 0.75, 0.7))
    k2.aim(glint, (0, 0, 0.03))
    strip("WallR", (0.12, -0.2, 0.05), (0.02, 0, 0.03), 0.6, 0.01, 8, (1.0, 0.8, 0.8))
    strip("WallL", (-0.15, 0.1, 0.05), (-0.02, 0, 0.03), 0.6, 0.01, 4, (1.0, 0.4, 0.4))
    cam = cam_make(85, 4.0)
    look(cam, (0.004, -0.27, 0.025), (0.004, 0, 0.025), focus=0.27 - 0.006)
    n = LENGTHS["C5"]

    def at(f):
        t = (f - 1) / FPS
        pos = cs.copy()
        pos[:, 2] = cs[:, 2] + vup * t
        pos[:, 0] += 0.0008 * np.sin(t * 8 + ph)
        wob = 1 + 0.06 * np.sin(t * 12 + ph)
        set_spheres(bub, pos, rad, 3, (np.tile(np.array([[0, 0, 1]], np.float32), (len(rad), 1)), (0.92 * wob).astype(np.float32)))
    return at, n


def shot_C6(sc):
    """R6: the pump side-on against a purple gradient that brightens toward the bottom. Theirs has a drop
    at the spout; ours stays clean (a fine-mist pump doesn't drip): a strip of light slides across it."""
    cyc([(0, (129, 79, 154)), (0.25, (91, 41, 151)), (0.5, (41, 14, 84)), (0.75, (14, 0, 55)), (1, (2, 0, 22))],
        -0.25, 0.55)
    piv, root, R = bottle(cap=False)
    glossy_bottle()
    piv.rotation_euler = (0, 0, math.radians(90))          # nozzle points to camera right
    strip("RimL", (-0.12, 0.12, 0.14), (0, 0, 0.13), 0.3, 0.02, 4, VIOLET)
    strip("RimTop", (0.02, 0.10, 0.30), (0, 0, 0.15), 0.2, 0.03, 0.5, LILAC)
    key = area_light("Key", (-0.2, -0.25, 0.12), (0, 0, 0), 0.1, 0.08, LILAC)
    k2.aim(key, (0, 0, 0.13))
    sweep = strip("Sweep", (-0.15, -0.25, 0.14), (0, 0, 0.13), 0.4, 0.015, 0.6, (1.0, 0.95, 1.0))
    cam = cam_make(100, 4.0)
    n = LENGTHS["C6"]

    def at(f):
        t = (f - 1) / (n - 1)
        sweep.location = (lerp(-0.16, 0.16, ease(t)), -0.25, 0.14)
        k2.aim(sweep, (0, 0, 0.13))
        d = lerp(0.215, 0.205, ease(t))
        pos = Vector((0.017, -d, 0.112))                   # pump left of centre, dutch tilt, as theirs
        tgt = (0.017, 0, 0.128)
        look(cam, pos, tgt, roll=-8, focus=focus_on(pos, tgt, Vector((0, -r(160), 0.145))))
    return at, n


def shot_C7(sc):
    """R7: dark red; a raw salt chunk covered in water beads lower left, our pump misting it."""
    return misting_shot(sc, "salt")


def shot_C8(sc):
    """R8: the bottle front-on, buried in big purple-lit water spheres; one sits over the label and magnifies it."""
    cyc([(0, (48, 21, 94)), (0.3, (52, 31, 87)), (0.5, (24, 14, 45)), (0.75, (55, 25, 89)), (1, (44, 14, 102))],
        -0.05, 0.22, strength=2.2)
    piv, root, R = bottle(cap=True)
    glossy_bottle()
    rng = np.random.default_rng(8)
    cs, rs = [(0.0, -R - 0.016, 0.062)], [0.016]
    tries = 0
    while len(cs) < 95 and tries < 20000:
        tries += 1
        rr = rng.uniform(0.007, 0.02)
        p_ = (rng.uniform(-0.085, 0.085), rng.uniform(-0.05, 0.14), rng.uniform(-0.03, 0.2))
        if math.hypot(p_[0], p_[1]) < R + rr + 0.002 and -0.01 < p_[2] < 0.17:
            continue
        if p_[1] < -0.02 and abs(p_[0]) < 0.03 and 0.01 < p_[2] < 0.13:   # keep most of the label clear
            continue
        if any(math.dist(p_, c) < rr + rc for c, rc in zip(cs, rs)):
            continue
        cs.append(p_)
        rs.append(rr)
    cs, rs = np.array(cs, np.float32), np.array(rs, np.float32)
    gel = principled("Gel", (0.72, 0.52, 1.0), rough=0.0, transmission=1.0, ior=1.33)
    balls = spheres("Spheres", gel, cs, rs, sub=3)
    inner = []                                              # tiny air bubbles inside some spheres
    for c, rc in zip(cs, rs):
        for _ in range(int(rng.integers(0, 4))):
            v_ = rng.normal(0, 1, 3)
            v_ = v_ / np.linalg.norm(v_) * rng.uniform(0, 0.6) * rc
            inner.append((c + v_, rng.uniform(0.0006, 0.0018)))
    spheres("Inner", water_mat("AirIn", ior=0.75), [i[0] for i in inner], [i[1] for i in inner], sub=2)
    key = area_light("Key", (-0.3, -0.4, 0.25), (0, 0, 0), 0.3, 1.2, LILAC)
    k2.aim(key, (0, 0, 0.08))
    strip("RimL", (-0.3, 0.25, 0.2), (0, 0, 0.09), 0.5, 0.04, 10, VIOLET)
    strip("RimR", (0.3, 0.25, 0.2), (0, 0, 0.09), 0.5, 0.04, 10, VIOLET)
    top = area_light("Top", (0, 0.0, 0.45), (0, 0, 0), 0.3, 4, LILAC)
    k2.aim(top, (0, 0, 0.1))
    cam = cam_make(85, 4.0)
    n = LENGTHS["C8"]
    t0 = rng.normal(0, 0.003, (len(cs), 3)).astype(np.float32)

    def at(f):
        t = (f - 1) / (n - 1)
        set_spheres(balls, cs + t0 * t, rs, 3)
        d = lerp(0.50, 0.46, ease(t))
        pos = Vector((0, -d, 0.088))
        tgt = (0, 0, 0.086)
        look(cam, pos, tgt, focus=focus_on(pos, tgt, Vector((0, -R, 0.07))))
    return at, n


def shot_C9(sc):
    """R9: a glass shelf on steel rods in a purple room; the Pack of 3 on the middle shelf; end card above."""
    cyc([(0, (131, 75, 182)), (0.2, (92, 50, 147)), (0.45, (29, 13, 55)), (0.62, (64, 42, 100)), (0.72, (20, 10, 35)), (1, (3, 2, 4))],
        -0.30, 0.55, y=0.6)
    metal = principled("Steel", (0.75, 0.72, 0.85), rough=0.25)
    metal.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 1.0
    for x in (-0.2, 0.2):
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.004, depth=1.2, location=(x, 0.05, 0.15))
        bpy.context.object.data.materials.append(metal)
    shelf_m = principled("ShelfGlass", (0.92, 0.88, 1.0), rough=0.05, transmission=1.0, ior=1.5)
    for zz in (0.0, 0.30):
        bpy.ops.mesh.primitive_cube_add(location=(0, 0.02, zz - 0.003))
        sh = bpy.context.object
        sh.scale = (0.21, 0.07, 0.003)
        sh.data.materials.append(shelf_m)
    roots = []
    for x in (-0.07, 0.0, 0.07):
        piv, root, R = bottle(cap=True)
        piv.location = (x, 0.02, MID)
        roots.append(piv)
    glossy_bottle()
    top = area_light("Top", (0, 0.0, 0.28), (0, 0, 0), 0.3, 2.0, LILAC)
    k2.aim(top, (0, 0.02, 0.0))
    strip("RimL", (-0.3, 0.25, 0.1), (0, 0.02, 0.08), 0.5, 0.04, 10, VIOLET)
    strip("RimR", (0.3, 0.25, 0.1), (0, 0.02, 0.08), 0.5, 0.04, 10, VIOLET)
    key = area_light("Key", (-0.2, -0.6, 0.15), (0, 0, 0), 0.3, 0.6, LILAC)
    k2.aim(key, (0, 0, 0.08))
    cam = cam_make(50, 5.6)
    n = LENGTHS["C9"]

    def at(f):
        t = ease((f - 1) / (n - 1))
        d = lerp(1.16, 1.10, t)
        pos = Vector((0, -d, 0.12))
        tgt = (0, 0, 0.12)
        look(cam, pos, tgt, focus=focus_on(pos, tgt, Vector((0, 0.0, 0.08))))
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
