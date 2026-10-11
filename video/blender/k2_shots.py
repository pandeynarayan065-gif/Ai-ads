"""Spraymax "Shaped by the wind" — 3D shots for the expedition film (Blender / Cycles, CPU).

Shots (24 fps, 1080x1920 delivery, rendered at --res-scale % and upscaled in the edit):
  A  rise    72 f  bottle erupts out of a Himalayan salt bed, floating crystals, rack focus, slow orbit
  B  spray   72 f  cap off, actuator press, backlit slow-motion mist plume
  C  pack   120 f  end card: bottle on salt, falling snow, slow push-in, text space at top

Framing is solved from the bottle's real size (160 mm cap top -> base) so the bottle lands on exact
pixel rows inside the Instagram Reels safe area (top 250 px, bottom 420 px, right 120 px).

  python video/blender/k2_shots.py --shot A --frames 1,36,72 --out DIR [--samples 24] [--res-scale 75]
"""
import math
import random
import sys
from pathlib import Path

import bpy  # noqa: I001
import bmesh
import numpy as np
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spraymax_scene import aim, area_light, lathe, make_bottle, principled, r, z  # noqa: E402

FPS = 24
W, H = 1080, 1920
LENS, SENSOR = 85.0, 36.0                       # sensor fits the 1920 px (vertical) side
VFOV_HALF = math.atan(SENSOR / 2 / LENS)       # 11.95 deg
SINK = 0.012                                   # bottle base sits 12 mm into the salt bed
TOP = SINK + z(800)                            # cap top height above floor (0.172 m)
ACT_TOP = SINK + z(824)                        # actuator top (cap removed)


def solve_frame(top_px, bottom_px, z_top, z_bot):
    """Distance and aim height so world heights z_top/z_bot land on pixel rows top_px/bottom_px."""
    span = (bottom_px - top_px) / H                       # fraction of frame height
    frame_h = (z_top - z_bot) / span                      # metres visible vertically at the subject
    dist = frame_h / 2 / math.tan(VFOV_HALF)
    mid_px = (top_px + bottom_px) / 2
    aim_z = (z_top + z_bot) / 2 - (H / 2 - mid_px) / H * frame_h
    return dist, aim_z


# ---------------------------------------------------------------- scene pieces
def setup(samples, res_scale):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.max_bounces = 6
    sc.cycles.transmission_bounces = 6
    sc.cycles.glossy_bounces = 3
    sc.cycles.diffuse_bounces = 2
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.resolution_percentage = res_scale
    sc.render.fps = FPS
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.render.image_settings.file_format = "PNG"
    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.003, 0.004, 0.008, 1)
    sc.world = world
    return sc


def backdrop(tint=(0.012, 0.018, 0.032), glow=(0.08, 0.11, 0.17), glow_z=0.11):
    """Emissive backdrop 1 m behind the bottle: deep steel blue with a soft radial glow."""
    bpy.ops.mesh.primitive_plane_add(size=3.0, location=(0, 1.0, 0.6), rotation=(math.pi / 2, 0, 0))
    bd = bpy.context.object
    m = bpy.data.materials.new("Backdrop")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    em = nt.nodes.new("ShaderNodeEmission")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mth = nt.nodes.new("ShaderNodeMath")          # radial distance from (0, glow_z) in object space
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    vx = nt.nodes.new("ShaderNodeMath")
    vx.operation = "MULTIPLY"
    nt.links.new(sep.outputs[0], vx.inputs[0])
    nt.links.new(sep.outputs[0], vx.inputs[1])
    vy = nt.nodes.new("ShaderNodeMath")
    vy.operation = "SUBTRACT"
    nt.links.new(sep.outputs[1], vy.inputs[0])
    vy.inputs[1].default_value = glow_z - 0.6
    vy2 = nt.nodes.new("ShaderNodeMath")
    vy2.operation = "MULTIPLY"
    nt.links.new(vy.outputs[0], vy2.inputs[0])
    nt.links.new(vy.outputs[0], vy2.inputs[1])
    mth.operation = "ADD"
    nt.links.new(vx.outputs[0], mth.inputs[0])
    nt.links.new(vy2.outputs[0], mth.inputs[1])
    fall = nt.nodes.new("ShaderNodeMath")
    fall.operation = "EXPONENT"
    neg = nt.nodes.new("ShaderNodeMath")
    neg.operation = "MULTIPLY"
    neg.inputs[1].default_value = -9.0
    nt.links.new(mth.outputs[0], neg.inputs[0])
    nt.links.new(neg.outputs[0], fall.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = (*tint, 1)
    mix.inputs[7].default_value = (*glow, 1)
    nt.links.new(fall.outputs[0], mix.inputs[0])
    nt.links.new(mix.outputs[2], em.inputs["Color"])
    em.inputs["Strength"].default_value = 1.0
    nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    bd.data.materials.append(m)
    return bd


def floor():
    bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, 0))
    f = bpy.context.object
    m = principled("Floor", (0.004, 0.0045, 0.006), rough=0.95)
    m.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.05
    f.data.materials.append(m)
    return f


SALT = None
PROTOS = []


def crystal_protos(n=6, seed=4):
    global SALT
    SALT = principled("Salt", (0.95, 0.93, 0.92), rough=0.42, transmission=0.45, ior=1.54, sss=0.3)
    rnd = random.Random(seed)
    for _ in range(n):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.5)
        p = bpy.context.object
        for v in p.data.vertices:
            v.co *= rnd.uniform(0.65, 1.25)
        bm = bmesh.new()
        bm.from_mesh(p.data)
        bmesh.ops.planar_faces(bm, faces=bm.faces[:], iterations=2)
        bm.to_mesh(p.data)
        bm.free()
        p.data.materials.append(SALT)
        p.hide_render = True
        PROTOS.append(p)


def crystal(loc, size, rnd):
    o = rnd.choice(PROTOS).copy()
    o.hide_render = False
    o.location = loc
    o.rotation_euler = (rnd.uniform(0, 6.3), rnd.uniform(0, 6.3), rnd.uniform(0, 6.3))
    o.scale = (size * rnd.uniform(0.8, 1.5), size * rnd.uniform(0.7, 1.2), size * rnd.uniform(0.6, 1.1))
    bpy.context.collection.objects.link(o)
    return o


def salt_bed(R, n=1800, seed=5):
    """Mound of crystals around the bottle. Returns list of (obj, radius_from_axis)."""
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        rad = abs(rnd.gauss(0, 0.075)) + R * 0.95
        ang = rnd.uniform(0, 2 * math.pi)
        x, y = rad * math.cos(ang), rad * math.sin(ang) * 0.9
        s = rnd.uniform(0.0025, 0.008) * (1.3 if rad < R + 0.03 else 1.0)
        h = max(0.0, 0.018 - (rad - R) * 0.16)
        out.append((crystal((x, y, h + s * 0.25), s, rnd), rad, ang))
    return out


def unit_ico():
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    v = np.array([vv.co[:] for vv in bm.verts], np.float32)
    f = [[vv.index for vv in face.verts] for face in bm.faces]
    bm.free()
    return v, f


ICO_V, ICO_F = None, None


def points_mesh(name, mat):
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    me.materials.append(mat)
    return ob


def set_points(ob, centers, radii, vel=None, stretch=0.0):
    """Rebuild a mesh of small icospheres; optional stretch along velocity (fake motion blur)."""
    global ICO_V, ICO_F
    if ICO_V is None:
        ICO_V, ICO_F = unit_ico()
    n = len(centers)
    me = ob.data
    me.clear_geometry()
    if n == 0:
        return
    base = np.repeat(ICO_V[None], n, 0) * radii[:, None, None]
    if vel is not None and stretch > 0:
        sp = np.linalg.norm(vel, axis=1) + 1e-9
        d = vel / sp[:, None]
        L = 1 + np.clip(sp * stretch, 0, 6)
        proj = (base @ np.ones(3))  # placeholder to keep shapes
        along = (base * d[:, None, :]).sum(2, keepdims=True)
        base = base + along * d[:, None, :] * (L[:, None, None] - 1)
    verts = (base + centers[:, None, :]).reshape(-1, 3)
    faces = (np.array(ICO_F)[None] + (np.arange(n) * len(ICO_V))[:, None, None]).reshape(-1, 3)
    me.from_pydata(verts.tolist(), [], faces.tolist())
    for p in me.polygons:
        p.use_smooth = True
    me.update()


def camera(dist, height, aim_z, az_deg=0.0, fstop=2.8, focus=None):
    cd = bpy.data.cameras.new("Cam")
    cd.lens, cd.sensor_width, cd.sensor_fit = LENS, SENSOR, "VERTICAL"
    cd.sensor_height = SENSOR
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = fstop
    cam = bpy.data.objects.new("Cam", cd)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    place_cam(cam, dist, height, aim_z, az_deg, focus)
    return cam


def place_cam(cam, dist, height, aim_z, az_deg=0.0, focus=None, aim_x=0.0):
    a = math.radians(az_deg)
    cam.location = (dist * math.sin(a), -dist * math.cos(a), height)
    aim(cam, (aim_x, 0, aim_z))
    cam.data.dof.focus_distance = focus if focus is not None else dist - r(436)


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


# ---------------------------------------------------------------- shots
def shot_A(sc):
    """Rise: bottle erupts from the salt bed; floating crystals in front rack-focus to the label."""
    backdrop(glow=(0.09, 0.11, 0.16))
    floor()
    crystal_protos()
    root, R = make_bottle(with_cap=True)
    bed = salt_bed(R)
    rnd = random.Random(9)
    floating = []
    for _ in range(200):     # crystals drifting in the air between camera and bottle (snow -> salt match)
        near = rnd.random() < 0.45
        y = rnd.uniform(-0.455, -0.43) if near else rnd.uniform(-0.30, 0.05)   # near band = focus plane at frame 1
        spread = 0.06 if near else 0.12
        x, zz = rnd.uniform(-spread, spread), rnd.uniform(0.03, 0.17) if near else rnd.uniform(0.0, 0.26)
        o = crystal((x, y, zz), rnd.uniform(0.0012, 0.0028), rnd)
        floating.append((o, Vector((x, y, zz)), rnd.uniform(0.004, 0.012), rnd.uniform(0, 6.28)))
    # light: cold key front-left, warm sunrise rim back-left (continuity from the summit shot), cool rim right
    k = area_light("Key", (-0.45, -0.5, 0.32), (0, 0, 0), 0.4, 7, (0.86, 0.92, 1.0), size_y=0.5)
    aim(k, (0, 0, 0.09))
    w = area_light("RimWarm", (-0.32, 0.30, 0.22), (0, 0, 0), 0.05, 26, (1.0, 0.72, 0.42), size_y=0.6)
    aim(w, (0, 0, 0.09))
    c = area_light("RimCool", (0.32, 0.30, 0.22), (0, 0, 0), 0.05, 16, (0.7, 0.82, 1.0), size_y=0.6)
    aim(c, (0, 0, 0.09))
    d0, a0 = solve_frame(330, 1430, TOP, SINK)            # final framing: bottle 1100 px tall, safe area
    cam = camera(d0, 0.06, a0, fstop=2.8)
    burst = [(o, o.location.copy(), rad, ang) for (o, rad, ang) in bed if rad < R + 0.035]

    def at(f):
        t = (f - 1) / FPS
        p = ease_out((f - 6) / 54)                         # rise from frame 6 to 60
        root.location = (0, 0, SINK - 0.19 * (1 - p))
        root.rotation_euler = (0, 0, math.radians(-25 * (1 - ease(f / 72))))
        tb = max(0.0, (f - 8) / FPS)                      # crystals kicked out as the bottle breaks through
        g = 9.81 * 0.35                                   # slowed gravity (slow-motion feel)
        for o, p0, rad, ang in burst:
            v_out = 0.10 + 0.25 * ((hash(o.name) % 100) / 100)
            v_up = 0.12 + 0.22 * ((hash(o.name[::-1]) % 100) / 100)
            dz = max(-p0.z + 0.002, v_up * tb - 0.5 * g * tb * tb)
            o.location = (p0.x + math.cos(ang) * v_out * tb * 0.6, p0.y + math.sin(ang) * v_out * tb * 0.6, p0.z + dz)
        for o, p0, sp, ph in floating:
            o.location = (p0.x + 0.01 * math.sin(t * 0.7 + ph), p0.y, p0.z - sp * t)
        az = -8 + 16 * ease(f / 72)
        dist = d0 * (1.06 - 0.06 * ease(f / 72))
        place_cam(cam, dist, 0.06, a0, az)
        bpy.context.view_layer.update()
        fwd = cam.matrix_world.to_3x3() @ Vector((0, 0, -1))
        near = (Vector((0, -0.4425, 0.10)) - cam.location).dot(fwd)        # depth of the foreground crystal band
        label = (Vector((0, -r(436), 0.09)) - cam.location).dot(fwd)       # depth of the label front
        cam.data.dof.focus_distance = near + (label - near) * ease((f - 10) / 34)   # rack focus crystals -> label
    return at, 72


def shot_B(sc):
    """Spray: cap off, actuator press, slow-motion mist plume, strong backlight through the plume."""
    backdrop(tint=(0.012, 0.018, 0.032), glow=(0.10, 0.14, 0.22), glow_z=0.16)
    floor()
    crystal_protos()
    root, R = make_bottle(with_cap=False)
    root.location = (0, 0, SINK)
    salt_bed(R, n=900)
    yaw = math.radians(90)                               # nozzle points to camera right: plume crosses the frame
    root.rotation_euler = (0, 0, yaw)
    act = [o for o in root.children if o.name.startswith(("Actuator", "Cylinder"))]
    act0 = {o.name: o.location.copy() for o in act}
    # lights: soft cold key front-left; hard white backlight behind the plume (forward scatter)
    k = area_light("Key", (-0.45, -0.40, 0.30), (0, 0, 0), 0.40, 4, (0.88, 0.93, 1.0), size_y=0.5)
    aim(k, (0, 0, 0.13))
    bl = area_light("Back", (0.16, 0.35, 0.20), (0, 0, 0), 0.10, 45, (1.0, 1.0, 1.0))
    aim(bl, (0.08, 0, 0.15))
    rim = area_light("Rim", (-0.25, 0.30, 0.24), (0, 0, 0), 0.05, 12, (0.75, 0.85, 1.0), size_y=0.5)
    aim(rim, (0, 0, 0.12))
    # macro framing: actuator top at 760 px, bottle shoulder (z 1355) at 1500 px; nozzle sits left of centre
    d0, a0 = solve_frame(880, 1880, ACT_TOP, SINK + z(1440))   # label top just below the frame edge
    cam = camera(d0, 0.15, a0, fstop=5.6)
    place_cam(cam, d0, 0.15, a0, 0, aim_x=0.016)
    # mist droplets
    # semi-transparent droplets: overlapping drops build up into soft haze like real mist
    mist_m = bpy.data.materials.new("Mist")
    mist_m.use_nodes = True
    mn = mist_m.node_tree
    mb = mn.nodes["Principled BSDF"]
    mb.inputs["Base Color"].default_value = (1, 1, 1, 1)
    mb.inputs["Roughness"].default_value = 0.25
    mb.inputs["Alpha"].default_value = 0.45
    mist = points_mesh("Mist", mist_m)
    rnd = np.random.default_rng(3)
    N = 60000
    te = rnd.uniform(0, 1.0, N)                          # emit times (s) after the press
    spd = rnd.uniform(0.18, 0.45, N)                      # slow-motion launch speed (m/s)
    half = math.radians(14)
    th, ph = np.sqrt(rnd.uniform(0, 1, N)) * half, rnd.uniform(0, 2 * math.pi, N)
    local = np.stack([np.sin(th) * np.cos(ph), -np.cos(th), np.sin(th) * np.sin(ph)], 1)   # around -Y
    R3 = np.array(Matrix.Rotation(yaw, 3, "Z"))
    dirs = local @ R3.T
    nz = R3 @ np.array([0, -r(160), 0])
    nozzle = np.array([nz[0], nz[1], SINK + z(870)])
    size = rnd.uniform(0.00003, 0.00008, N)
    tau = 0.30                                            # drag time constant (slowed)
    drift = rnd.normal(0, 0.004, (N, 3))
    press = 10                                            # frame of the press

    def at(f):
        dz = -0.0025 * (ease((f - press) / 4) - ease((f - press - 12) / 6))
        for o in act:
            o.location = act0[o.name] + Vector((0, 0, dz))
        t = (f - press - 2) / FPS - te
        live = (t > 0) & (t < 3.0)
        tt = np.clip(t[live], 0, None)
        dist_ = spd[live] * tau * (1 - np.exp(-tt / tau))
        vel = (spd[live] * np.exp(-tt / tau))[:, None] * dirs[live]
        pos = nozzle + dirs[live] * dist_[:, None] + drift[live] * tt[:, None] + np.array([0, 0, -0.02]) * tt[:, None] ** 2
        grow = 1 + 0.8 * tt                                # droplets spread and fade as mist
        set_points(mist, pos.astype(np.float32), (size[live] * grow).astype(np.float32), vel, stretch=0.012)
        place_cam(cam, d0 * (1.03 - 0.03 * ease(f / 72)), 0.15, a0, -4 + 8 * ease(f / 72), aim_x=0.016)
    return at, 72


def shot_C(sc):
    """End card: bottle on salt, falling snow, slow push-in; top 300-600 px kept clear for type."""
    backdrop(tint=(0.025, 0.03, 0.075), glow=(0.16, 0.18, 0.36), glow_z=0.08)
    floor()
    crystal_protos()
    root, R = make_bottle(with_cap=True)
    root.location = (0, 0, SINK)
    salt_bed(R)
    k = area_light("Key", (-0.45, -0.5, 0.32), (0, 0, 0), 0.4, 7, (0.88, 0.93, 1.0), size_y=0.5)
    aim(k, (0, 0, 0.09))
    w = area_light("RimWarm", (-0.32, 0.30, 0.22), (0, 0, 0), 0.05, 18, (1.0, 0.76, 0.5), size_y=0.6)
    aim(w, (0, 0, 0.09))
    c = area_light("RimCool", (0.32, 0.30, 0.22), (0, 0, 0), 0.05, 16, (0.7, 0.82, 1.0), size_y=0.6)
    aim(c, (0, 0, 0.09))
    d1, a1 = solve_frame(700, 1480, TOP, SINK)            # end of push-in: bottle 780 px, top at 700 px
    cam = camera(d1 * 1.08, 0.065, a1, fstop=3.2)
    snow_m = principled("Snow", (1, 1, 1), rough=0.6, sss=0.4)
    snow = points_mesh("Snow", snow_m)
    rnd = np.random.default_rng(11)
    M = 700
    p0 = np.stack([rnd.uniform(-0.25, 0.25, M), rnd.uniform(-0.5, 0.25, M), rnd.uniform(0, 0.45, M)], 1)
    vfall = rnd.uniform(0.02, 0.05, M)
    sz = rnd.uniform(0.0006, 0.0016, M)
    ph = rnd.uniform(0, 6.28, M)

    def at(f):
        t = (f - 1) / FPS
        pos = p0.copy()
        pos[:, 2] = (p0[:, 2] - vfall * t) % 0.45
        pos[:, 0] += 0.006 * np.sin(t * 1.1 + ph)
        set_points(snow, pos.astype(np.float32), sz.astype(np.float32))
        place_cam(cam, d1 * (1.08 - 0.08 * ease(f / 120)), 0.065, a1)
    return at, 120


SHOTS = {"A": shot_A, "B": shot_B, "C": shot_C}


def main():
    a = sys.argv[1:]
    shot = a[a.index("--shot") + 1]
    out = Path(a[a.index("--out") + 1])
    samples = int(a[a.index("--samples") + 1]) if "--samples" in a else 24
    res = int(a[a.index("--res-scale") + 1]) if "--res-scale" in a else 75
    sc = setup(samples, res)
    at, nframes = SHOTS[shot](sc)
    frames = [int(x) for x in a[a.index("--frames") + 1].split(",")] if "--frames" in a else range(1, nframes + 1)
    out.mkdir(parents=True, exist_ok=True)
    skip = "--skip-existing" in a
    for f in frames:
        if skip and (out / f"{shot}_{f:04d}.png").exists():
            continue
        sc.frame_set(f)
        at(f)
        sc.render.filepath = str(out / f"{shot}_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        print("frame", shot, f, flush=True)


if __name__ == "__main__":
    main()
