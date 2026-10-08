"""Spraymax 3D hero shot, built entirely in code with Blender (bpy).

Bottle proportions are measured from brand/spraymax/assets/bottle-blank.png (cap top -> base = 1697 px
-> 160 mm). The real flat label (label-flat.jpg) is UV-wrapped once around the body, front panel facing
the camera. Set: dark indigo cove, a mound of salt crystals, softbox key + rim lights + backdrop glow.

  python video/blender/spraymax_scene.py <out.png> [--samples N] [--res-scale P] [--frame F] [--anim out_dir]
(run with the venv python that has `bpy` installed)
"""
import math
import random
import sys
from pathlib import Path

import bpy  # noqa: I001  (bpy must load before bmesh)
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "brand/spraymax/assets"

PX = 0.160 / 1697.0                    # metres per pixel of the bottle cut-out
Y0 = 790                               # cap top in the cut-out


def z(py):                             # cut-out y (px) -> height above the floor (m)
    return (2487 - py) * PX


def r(px_width):
    return px_width / 2 * PX


# ---------------------------------------------------------------- helpers
def lathe(name, profile, segs=128, rib=None, uv=False):
    """Revolve (radius, height) profile points around Z. rib=(count, depth, z0, z1) adds vertical ribs."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rings = []
    for i in range(segs):
        th = 2 * math.pi * i / segs
        ring = []
        for (rad, h) in profile:
            rr = rad
            if rib and rib[2] <= h <= rib[3]:
                rr = rad + rib[1] * (0.5 + 0.5 * math.cos(rib[0] * th)) ** 3
            ring.append(bm.verts.new((rr * math.cos(th), rr * math.sin(th), h)))
        rings.append(ring)
    bm.verts.ensure_lookup_table()
    uvl = bm.loops.layers.uv.new() if uv else None
    n = len(profile)
    for i in range(segs):
        a, b = rings[i], rings[(i + 1) % segs]
        for j in range(n - 1):
            f = bm.faces.new((a[j], b[j], b[j + 1], a[j + 1]))
            if uv:
                u0, u1 = i / segs, (i + 1) / segs
                v0, v1 = j / (n - 1), (j + 1) / (n - 1)
                for loop, (uu, vv) in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
                    loop[uvl].uv = (uu, vv)
    # caps
    for idx in (0, n - 1):
        if profile[idx][0] > 1e-6:
            bm.faces.new([rings[i][idx] for i in range(segs)][::(1 if idx == n - 1 else -1)])
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob


def principled(name, color, rough=0.3, spec=0.5, transmission=0.0, ior=1.45, coat=0.0, sss=0.0, emission=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["IOR"].default_value = ior
    b.inputs["Transmission Weight"].default_value = transmission
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Subsurface Weight"].default_value = sss
    if emission:
        b.inputs["Emission Color"].default_value = (*emission[0], 1)
        b.inputs["Emission Strength"].default_value = emission[1]
    return m


def area_light(name, loc, rot, size, energy, color=(1, 1, 1), shape="RECTANGLE", size_y=None):
    l = bpy.data.lights.new(name, "AREA")
    l.energy = energy
    l.color = color
    l.shape = shape
    l.size = size
    if size_y:
        l.size_y = size_y
    ob = bpy.data.objects.new(name, l)
    ob.location = loc
    ob.rotation_euler = rot
    bpy.context.collection.objects.link(ob)
    return ob


def aim(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


# ---------------------------------------------------------------- scene
def build(samples=64, res_scale=100):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 8
    sc.cycles.transmission_bounces = 8
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
    sc.render.resolution_percentage = res_scale
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.004, 0.003, 0.02, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    sc.world = world

    # --- bottle body (shoulder -> body -> rounded base), measured from the cut-out
    R = r(436)
    body_prof = [(0.0, 0.0), (R - 0.004, 0.0), (R - 0.0012, 0.0006), (R, 0.003)]
    body_prof += [(R, z(1430)), (R * 0.98, z(1395)), (R * 0.9, z(1355)), (R * 0.75, z(1320)), (r(250), z(1295)), (r(250), z(1285))]
    white = principled("BottleWhite", (0.92, 0.92, 0.94), rough=0.22, coat=0.6, sss=0.05)
    body = lathe("Body", body_prof, segs=160)
    body.data.materials.append(white)

    # --- label: thin open cylinder just outside the body, UV = full wrap, front panel faces -Y
    lab_prof = [(R + 0.00025, z(2400) + k * (z(1470) - z(2400)) / 40) for k in range(41)]
    label = lathe("Label", lab_prof, segs=256, uv=True)
    img = bpy.data.images.load(str(ASSETS / "label-flat.jpg"))
    m = bpy.data.materials.new("LabelMat")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.28
    bsdf.inputs["Coat Weight"].default_value = 0.35
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.extension = "REPEAT"
    uvn = nt.nodes.new("ShaderNodeUVMap")
    mapping = nt.nodes.new("ShaderNodeMapping")
    # crop the 6 px border of the artwork, and rotate so the front panel (u=0.505) sits at theta=-90deg
    W_, H_ = img.size
    sx, sy = (W_ - 12) / W_, (H_ - 12) / H_
    mapping.inputs["Scale"].default_value = (sx, sy, 1)
    mapping.inputs["Location"].default_value = (6 / W_ + (0.505 - 0.75) * sx, 6 / H_, 0)
    nt.links.new(uvn.outputs["UV"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    label.data.materials.append(m)

    # --- ribbed collar, pump ring, actuator, nozzle insert
    plastic = principled("PumpWhite", (0.9, 0.9, 0.92), rough=0.35, sss=0.03)
    col_prof = [(0.0, z(1290)), (r(236), z(1290)), (r(244), z(1284)), (r(244), z(1092)), (r(236), z(1085)), (r(150), z(1085)), (0.0, z(1085))]
    collar = lathe("Collar", col_prof, segs=192, rib=(64, r(10), z(1280), z(1095)))
    collar.data.materials.append(plastic)
    ring = lathe("PumpRing", [(0.0, z(1085)), (r(182), z(1085)), (r(182), z(1010)), (r(170), z(1000)), (0.0, z(1000))], segs=96)
    ring.data.materials.append(plastic)
    act = lathe("Actuator", [(0.0, z(1000)), (r(160), z(1000)), (r(160), z(838)), (r(150), z(826)), (0.0, z(824))], segs=96)
    act.data.materials.append(plastic)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=r(34), depth=0.002, location=(0, -r(160) + 0.0007, z(870)), rotation=(math.pi / 2, 0, 0))
    nozzle = bpy.context.object
    nozzle.data.materials.append(principled("Nozzle", (0.85, 0.82, 0.68), rough=0.5))

    # --- clear overcap (thin shell with real thickness)
    cap_outer = [(0.0, z(800)), (r(196), z(800)), (r(206), z(806)), (r(208), z(1080)), (r(212), z(1088))]
    cap_prof = cap_outer + [(r(198), z(1088)), (r(194), z(1080)), (r(192), z(814)), (r(184), z(810)), (0.0, z(810))]
    cap = lathe("Cap", cap_prof[::-1], segs=128)
    # thin clear plastic: mostly see-through with a Fresnel-weighted gloss, so the pump reads through it
    cm = bpy.data.materials.new("ClearCap")
    cm.use_nodes = True
    cn = cm.node_tree
    cn.nodes.remove(cn.nodes["Principled BSDF"])
    tr = cn.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (0.96, 0.97, 1.0, 1)
    gl = cn.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = 0.04
    lw = cn.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.18
    mix = cn.nodes.new("ShaderNodeMixShader")
    cn.links.new(lw.outputs["Fresnel"], mix.inputs["Fac"])
    cn.links.new(tr.outputs["BSDF"], mix.inputs[1])
    cn.links.new(gl.outputs["BSDF"], mix.inputs[2])
    cn.links.new(mix.outputs["Shader"], cn.nodes["Material Output"].inputs["Surface"])
    cap.data.materials.append(cm)

    bottle = [body, label, collar, ring, act, nozzle, cap]
    root = bpy.data.objects.new("Bottle", None)
    bpy.context.collection.objects.link(root)
    for o in bottle:
        o.parent = root
    root.location = (0, 0, 0.012)       # sits slightly sunk into the salt bed

    # --- set: indigo cove (floor curving up into a backdrop)
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 1.2, 0))
    cove = bpy.context.object
    bm = bmesh.new()
    bm.from_mesh(cove.data)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=60, use_grid_fill=True)
    for v in bm.verts:
        y = v.co.y + 1.2
        if y > 0.35:
            v.co.z = (y - 0.35) ** 2.0 * 0.9
    bm.to_mesh(cove.data)
    bm.free()
    for p in cove.data.polygons:
        p.use_smooth = True
    cove.data.materials.append(principled("Cove", (0.012, 0.008, 0.08), rough=0.45, spec=0.3))

    # --- salt crystal mound: bevelled, randomised cubes, translucent pinkish-white
    salt = principled("Salt", (0.95, 0.92, 0.9), rough=0.5, transmission=0.35, ior=1.54, sss=0.35)
    random.seed(4)
    protos = []
    for k in range(6):                       # a few distinct irregular crystal shapes
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.5)
        p = bpy.context.object
        for v in p.data.vertices:
            v.co *= random.uniform(0.65, 1.25)
        bm = bmesh.new()
        bm.from_mesh(p.data)
        bmesh.ops.planar_faces(bm, faces=bm.faces[:], iterations=2)
        bm.to_mesh(p.data)
        bm.free()
        p.data.materials.append(salt)
        p.hide_render = True
        p.hide_viewport = True
        protos.append(p)
    for i in range(1400):
        rad = abs(random.gauss(0, 0.06)) + 0.03
        ang = random.uniform(0, 2 * math.pi)
        x, y = rad * math.cos(ang), rad * math.sin(ang) * 0.85 + 0.01
        if math.hypot(x, y) < R * 0.92:
            continue
        s_ = random.uniform(0.0025, 0.0075) * (1.25 if rad < 0.05 else 1.0)
        mound = max(0.0, 0.014 - rad * 0.11)
        src = random.choice(protos)
        o = src.copy()
        o.hide_render = False
        o.hide_viewport = False
        o.location = (x, y, mound + s_ * 0.25)
        o.rotation_euler = (random.uniform(0, 6.3), random.uniform(0, 6.3), random.uniform(0, 6.3))
        o.scale = (s_ * random.uniform(0.8, 1.5), s_ * random.uniform(0.7, 1.2), s_ * random.uniform(0.6, 1.1))
        bpy.context.collection.objects.link(o)

    # --- lights
    area_light("Key", (-0.45, -0.5, 0.3), (0, 0, 0), 0.35, 9, (1.0, 0.96, 0.92), size_y=0.5)
    aim(bpy.data.objects["Key"], (0, 0, 0.09))
    area_light("RimL", (-0.3, 0.22, 0.2), (0, 0, 0), 0.04, 14, (0.7, 0.8, 1.0), size_y=0.5)
    aim(bpy.data.objects["RimL"], (0, 0, 0.09))
    area_light("RimR", (0.3, 0.22, 0.2), (0, 0, 0), 0.04, 14, (0.7, 0.8, 1.0), size_y=0.5)
    aim(bpy.data.objects["RimR"], (0, 0, 0.09))
    area_light("Top", (0, -0.05, 0.6), (0, 0, 0), 0.25, 3, (0.95, 0.95, 1.0))
    aim(bpy.data.objects["Top"], (0, 0, 0.1))
    glow = area_light("Glow", (0, 0.55, 0.18), (math.radians(90), 0, 0), 0.25, 6, (0.3, 0.32, 1.0), shape="DISK")
    aim(glow, (0, 2, 0.25))

    # --- camera: ~85 mm, low angle, shallow depth of field on the label
    cam_d = bpy.data.cameras.new("Cam")
    cam_d.lens = 85
    cam_d.sensor_width = 36
    cam_d.dof.use_dof = True
    cam_d.dof.aperture_fstop = 2.8
    cam = bpy.data.objects.new("Cam", cam_d)
    bpy.context.collection.objects.link(cam)
    sc.camera = cam
    cam.location = (0, -0.62, 0.07)
    aim(cam, (0, 0, 0.088))
    cam_d.dof.focus_distance = 0.62 - R
    return sc, cam, root


def animate(sc, cam, root, frames=72):
    """Slow push-in + a quarter turn of the bottle: the hero move for the test clip."""
    sc.frame_start, sc.frame_end = 1, frames
    sc.render.fps = 24
    for f, (d, h, rot) in ((1, (0.80, 0.068, -0.45)), (frames, (0.66, 0.08, 0.0))):
        cam.location = (0, -d, h)
        aim(cam, (0, 0, 0.088))
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)
        cam.data.dof.focus_distance = d - r(436)
        cam.data.dof.keyframe_insert("focus_distance", frame=f)
        root.rotation_euler = (0, 0, rot)
        root.keyframe_insert("rotation_euler", frame=f)


def main():
    args = sys.argv[1:]
    out = args[0]
    samples = int(args[args.index("--samples") + 1]) if "--samples" in args else 64
    res = int(args[args.index("--res-scale") + 1]) if "--res-scale" in args else 100
    sc, cam, root = build(samples, res)
    if "--anim" in args:
        animate(sc, cam, root)
        sc.render.filepath = str(Path(args[args.index("--anim") + 1]) / "f_")
        sc.render.image_settings.file_format = "PNG"
        bpy.ops.render.render(animation=True)
        return
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
