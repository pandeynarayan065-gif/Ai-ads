"""Misfits reel #2, "The last one doesn't fit" — Blender scene, built and rendered from this script.
A dark tray of 16 square pockets. 15 grey tiles drop in, one by one, faster and faster, each landing flush.
The 16th tile is lime: it lands rotated -14 degrees (the logo's misfit angle), can't drop in, and sits proud of
the tray, glowing. One continuous camera move, no cuts. Text and sound are added in post (post.py).

Usage: blender -b -P scene.py -- <out_dir> [engine=cycles|eevee] [samples=32] [frames=a-b] [scale=100]
Writes <out_dir>/frames/####.png and <out_dir>/timing.json (land times for the sound design)."""
import bpy, bmesh, json, math, os, sys
from mathutils import Vector, Euler

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(argv[0] if argv else "out")
opt = dict(a.split("=", 1) for a in argv[1:])
ENGINE, SAMPLES, SCALE = opt.get("engine", "cycles"), int(opt.get("samples", 32)), int(opt.get("scale", 100))
FPS, DUR = 30, 8.6
NF = round(FPS * DUR)

INK, LIME = (0.0024, 0.0027, 0.0033), (0.258, 0.651, 0.059)    # linear: #08090b, #8bd346
def srgb(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple((v / 12.92) if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c)

# ---------------- reset ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = FPS; sc.frame_start, sc.frame_end = 1, NF
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, SCALE

def mat(name, base, rough=0.4, coat=0.0, emit=None, estr=0.0, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Coat Roughness"].default_value = 0.08
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = estr
    return m

def rounded_box(name, sx, sy, sz, bevel, segs=5):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.object; o.name = name; o.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply(scale=True)
    b = o.modifiers.new("bevel", "BEVEL"); b.width = bevel; b.segments = segs; b.limit_method = "ANGLE"
    bpy.ops.object.shade_smooth(); o.data.shade_smooth() if hasattr(o.data, "shade_smooth") else None
    return o

# ---------------- tray ----------------
N, PITCH, T, H = 4, 1.16, 1.0, 0.32          # 4x4 pockets, tile size 1.0, tray/tile height
W = N * PITCH + 0.34
tray = rounded_box("tray", W, W, H, 0.06)
tray.location.z = H / 2
for i in range(N):
    for j in range(N):
        bpy.ops.mesh.primitive_cube_add(size=1, location=((i - 1.5) * PITCH, (j - 1.5) * PITCH, H / 2 + 0.06))
        cut = bpy.context.object; cut.scale = (T + 0.05, T + 0.05, H)
        bo = tray.modifiers.new(f"b{i}{j}", "BOOLEAN"); bo.object = cut; bo.operation = "DIFFERENCE"; bo.solver = "FAST"
        cut.hide_render = cut.hide_viewport = True
# put bevel last so pocket edges get rounded too
bev = tray.modifiers["bevel"]; tray.modifiers.move(0, len(tray.modifiers) - 1)
tray.data.materials.append(mat("tray", srgb("#141519"), rough=0.55, coat=0.15))

bpy.ops.mesh.primitive_plane_add(size=60); floor = bpy.context.object
floor.data.materials.append(mat("floor", srgb("#050506"), rough=0.85))

# ---------------- tiles ----------------
grey = [mat(f"grey{k}", srgb(h), rough=0.28, coat=0.35) for k, h in enumerate(["#3b3f46", "#40444b", "#363a40"])]
lime = mat("lime", srgb("#8bd346"), rough=0.22, coat=0.5, emit=srgb("#6fd11a"), estr=0.0)
TH = H - 0.04                                  # tile height; top sits flush with the tray when seated
slots = [(i, j) for j in range(N) for i in range(N)]
MIS = (3, 3)                                   # top-right pocket: same place as the logo's misfit
order = [s for s in slots if s != MIS]
# deterministic shuffle so the pattern feels random but repeatable
order = sorted(order, key=lambda s: (s[0] * 7 + s[1] * 13) % 16)
# drop times: start slow, accelerate (satisfying rhythm), then a pause before the misfit
times, t, gap = [], 0.3, 0.42
for k in range(len(order)):
    times.append(round(t, 3)); t += gap; gap = max(0.13, gap * 0.86)
T_MIS = round(times[-1] + 1.05, 3)             # tension pause
FALL = 0.34                                    # seconds from drop height to landing
DROP_Z = 4.2

def key_tile(o, slot, t_land, misfit=False):
    x, y = (slot[0] - 1.5) * PITCH, (slot[1] - 1.5) * PITCH
    seat = 0.04 + TH / 2 + 0.02                # resting z inside the pocket (flush top)
    if misfit:
        seat = H + TH / 2 + 0.005              # rests on the rim, proud of the tray
    t0 = t_land - FALL
    def k(tt, z, rz=0.0, rx=0.0, ry=0.0):
        f = 1 + tt * FPS
        o.location = (x, y, z); o.keyframe_insert("location", frame=f)
        o.rotation_euler = (rx, ry, rz); o.keyframe_insert("rotation_euler", frame=f)
    if not misfit:
        spin = math.radians(((slot[0] * 5 + slot[1] * 3) % 7 - 3) * 6)
        k(t0 - 0.01, DROP_Z + 6)                # parked out of shot
        k(t0, DROP_Z, spin, 0.12, -0.08)
        k(t_land, seat, 0, 0, 0)
        k(t_land + 0.07, seat + 0.035, 0, 0.015, 0)
        k(t_land + 0.14, seat, 0, 0, 0)
    else:
        rz = math.radians(-16)
        k(t0 - 0.25, DROP_Z + 6, rz)
        k(t0 - 0.24, DROP_Z + 1.2, rz + 0.3, 0.3, -0.2)
        k(t_land, seat, rz, 0, 0)
        k(t_land + 0.11, seat + 0.16, rz + 0.04, 0.05, -0.03)
        k(t_land + 0.24, seat, rz, 0, 0)
        k(t_land + 0.32, seat + 0.03, rz, 0, 0)
        k(t_land + 0.40, seat, rz, 0, 0)
    for fc in o.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"
        # falling segment = gravity (ease in), landing = hard stop
        if len(fc.keyframe_points) > 2:
            fc.keyframe_points[1].interpolation = "QUAD"; fc.keyframe_points[1].easing = "EASE_IN"
        if misfit and len(fc.keyframe_points) > 3:
            fc.keyframe_points[2].interpolation = "QUAD"; fc.keyframe_points[2].easing = "EASE_IN"
    o.location = (x, y, DROP_Z + 6)

for n, (slot, tl) in enumerate(zip(order, times)):
    o = rounded_box(f"tile{n}", T - 0.02, T - 0.02, TH, 0.05)
    o.data.materials.append(grey[n % 3]); key_tile(o, slot, tl)
mis = rounded_box("misfit", T - 0.02, T - 0.02, TH, 0.05)
mis.data.materials.append(lime); key_tile(mis, MIS, T_MIS, misfit=True)
# lime emission ramps up as it lands
es = lime.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for tt, v in [(0, 0.6), (T_MIS - 0.2, 0.9), (T_MIS, 6.0), (T_MIS + 0.35, 2.4), (DUR, 2.6)]:
    es.default_value = v; es.keyframe_insert("default_value", frame=1 + tt * FPS)

# ---------------- lights ----------------
def area(name, loc, rot, size, power, col=(1, 1, 1)):
    l = bpy.data.lights.new(name, "AREA"); l.size = size; l.energy = power; l.color = col
    o = bpy.data.objects.new(name, l); o.location = loc; o.rotation_euler = rot; sc.collection.objects.link(o); return l
area("key", (-2.5, -3.5, 7.5), (math.radians(30), math.radians(-18), 0), 4, 520)
area("rim", (1.5, 6.5, 3.2), (math.radians(-65), 0, 0), 6, 650, (0.82, 0.9, 1.0))
pl = bpy.data.lights.new("limeglow", "POINT"); pl.color = (0.55, 0.85, 0.25); pl.shadow_soft_size = 0.5
plo = bpy.data.objects.new("limeglow", pl); plo.location = ((MIS[0] - 1.5) * PITCH, (MIS[1] - 1.5) * PITCH, 1.1)
sc.collection.objects.link(plo)
for tt, v in [(0, 0), (T_MIS - 0.05, 0), (T_MIS, 260), (T_MIS + 0.4, 110), (DUR, 120)]:
    pl.energy = v; pl.keyframe_insert("energy", frame=1 + tt * FPS)

w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (*srgb("#0a0c0d"), 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.2

# ---------------- camera: one continuous move ----------------
cd = bpy.data.cameras.new("cam"); cd.lens = 40; cd.sensor_fit = "VERTICAL"; cd.sensor_height = 24
cam = bpy.data.objects.new("cam", cd); sc.collection.objects.link(cam); sc.camera = cam
tgt = bpy.data.objects.new("tgt", None); sc.collection.objects.link(tgt)
tc = cam.constraints.new("TRACK_TO"); tc.target = tgt; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cd.dof.use_dof = True; cd.dof.focus_object = tgt; cd.dof.aperture_fstop = 5.6
for tt, cl, tl in [(0, (0.0, -10.8, 14.6), (0, 0.9, 0.2)),
                   (T_MIS - 0.4, (0.25, -9.6, 12.8), (0.05, 0.9, 0.2)),
                   (T_MIS + 0.3, (0.35, -8.9, 11.9), (0.1, 1.0, 0.3)),
                   (DUR, (0.45, -8.5, 11.4), (0.1, 1.0, 0.3))]:
    cam.location = cl; cam.keyframe_insert("location", frame=1 + tt * FPS)
    tgt.location = tl; tgt.keyframe_insert("location", frame=1 + tt * FPS)
for o in (cam, tgt):
    for fc in o.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = "BEZIER"; kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"

# ---------------- render settings ----------------
r = sc.render
if ENGINE == "eevee":
    r.engine = "BLENDER_EEVEE_NEXT"; sc.eevee.taa_render_samples = SAMPLES
    sc.eevee.use_raytracing = True
else:
    r.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.max_bounces = 6; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.03
r.motion_blur_shutter = 0.5; r.use_motion_blur = True; r.use_persistent_data = True
sc.view_settings.view_transform = "Khronos PBR Neutral"
r.image_settings.file_format = "PNG"; r.filepath = os.path.join(OUT, "frames", "")
r.film_transparent = False
# glow: compositor glare
sc.use_nodes = True; nt = sc.node_tree; nt.nodes.clear()
rl = nt.nodes.new("CompositorNodeRLayers"); gl = nt.nodes.new("CompositorNodeGlare"); co = nt.nodes.new("CompositorNodeComposite")
gl.glare_type = "FOG_GLOW"; gl.threshold = 0.9; gl.size = 8; gl.quality = "HIGH"; gl.mix = -0.35
nt.links.new(rl.outputs["Image"], gl.inputs["Image"]); nt.links.new(gl.outputs["Image"], co.inputs["Image"])

os.makedirs(OUT, exist_ok=True)
json.dump({"fps": FPS, "dur": DUR, "lands": times, "misfit": T_MIS}, open(os.path.join(OUT, "timing.json"), "w"), indent=1)
if "frames" in opt:
    a, b = map(int, opt["frames"].split("-")); sc.frame_start, sc.frame_end = a, b
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "scene.blend"))
bpy.ops.render.render(animation=True)
