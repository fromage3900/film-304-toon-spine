"""Render ONE asset with the trim sheet applied. One invocation per asset.

    blender.exe -b --python Blender/render_one_asset.py -- CAD_WallModule 3

Args after `--`: <asset name> <tile index>
"""
import bpy, os, sys, math, json
from mathutils import Vector

ROOT = r"G:\film-304-toon-spine"
CAD = os.path.join(ROOT, "Film304_Packages", "Office_CAD_Pass_2026-11-17", "01_Modules")
ATLAS = os.path.join(ROOT, "Film304_Packages", "Office_Asset_PBR_Pack_v4.0.0_2026-11-18",
                     "02_TrimSheet", "master_4096x2048")
OUT = os.path.join(ROOT, "Film304_Packages", "Asset_ContactSheet_2026-11-18", "01_Assets")
os.makedirs(OUT, exist_ok=True)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
NAME = argv[0] if argv else "CAD_WallModule"
TILE = int(argv[1]) if len(argv) > 1 else 3
COLS, ROWS = 4, 2

ALBEDO = os.path.join(ATLAS, "T_OfficeTrim_Albedo_4096x2048.png")
NORMAL = os.path.join(ATLAS, "T_OfficeTrim_Normal_4096x2048.png")
ORM = os.path.join(ATLAS, "T_OfficeTrim_ORM_4096x2048.png")
AO = os.path.join(ATLAS, "T_OfficeTrim_AO_4096x2048.png")

u0 = (TILE % COLS) / float(COLS)
v0 = (TILE // COLS) / float(ROWS)
du, dv = 1.0 / COLS, 1.0 / ROWS

scn = bpy.context.scene
scn.render.engine = "CYCLES"
scn.cycles.device = "CPU"
scn.cycles.samples = 20
scn.cycles.use_denoising = False
scn.render.resolution_x = 560
scn.render.resolution_y = 560
scn.render.resolution_percentage = 100
scn.render.image_settings.file_format = "PNG"

world = bpy.data.worlds.new("W")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.42, 0.44, 0.48, 1.0)
bg.inputs[1].default_value = 1.0
scn.world = world
try:
    scn.view_settings.exposure = 1.1
    scn.view_settings.look = "AgX - Medium High Contrast"
except Exception:
    pass

cam_data = bpy.data.cameras.new("C")
cam = bpy.data.objects.new("C", cam_data)
scn.collection.objects.link(cam)
scn.camera = cam

sd = bpy.data.lights.new("S", type="SUN")
sd.energy = 5.5
sd.angle = math.radians(8)
sun = bpy.data.objects.new("S", sd)
sun.rotation_euler = (math.radians(48), 0, math.radians(35))
scn.collection.objects.link(sun)

fd = bpy.data.lights.new("F", type="AREA")
fd.energy = 4000.0
fd.size = 700.0
fill = bpy.data.objects.new("F", fd)
scn.collection.objects.link(fill)

rd = bpy.data.lights.new("R", type="AREA")
rd.energy = 2500.0
rd.size = 600.0
rim = bpy.data.objects.new("R", rd)
scn.collection.objects.link(rim)

mat = bpy.data.materials.new("Trim")
mat.use_nodes = True
nt = mat.node_tree
bsdf = nt.nodes.get("Principled BSDF")
t = nt.nodes.new("ShaderNodeTexImage")
t.image = bpy.data.images.load(ALBEDO)
t.location = (-700, 200)
ao = nt.nodes.new("ShaderNodeTexImage")
ao.image = bpy.data.images.load(AO)
ao.image.colorspace_settings.name = "Non-Color"
ao.location = (-700, -20)
try:
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs["Fac"].default_value = 0.85
except Exception:
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.85
mix.location = (-380, 120)
nt.links.new(t.outputs["Color"], mix.inputs[1] if mix.type == "MIX_RGB" else mix.inputs["A"])
nt.links.new(ao.outputs["Color"], mix.inputs[2] if mix.type == "MIX_RGB" else mix.inputs["B"])
nt.links.new(mix.outputs[0] if mix.type == "MIX_RGB" else mix.outputs["Result"],
             bsdf.inputs["Base Color"])
n = nt.nodes.new("ShaderNodeTexImage")
n.image = bpy.data.images.load(NORMAL)
n.image.colorspace_settings.name = "Non-Color"
n.location = (-500, -120)
nm = nt.nodes.new("ShaderNodeNormalMap")
nm.location = (-250, -120)
nt.links.new(n.outputs["Color"], nm.inputs["Color"])
nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
o = nt.nodes.new("ShaderNodeTexImage")
o.image = bpy.data.images.load(ORM)
o.image.colorspace_settings.name = "Non-Color"
o.location = (-500, -420)
sep = nt.nodes.new("ShaderNodeSeparateColor")
sep.location = (-250, -420)
nt.links.new(o.outputs["Color"], sep.inputs["Color"])
nt.links.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
nt.links.new(sep.outputs["Red"], bsdf.inputs["Metallic"])

path = os.path.join(CAD, NAME + ".fbx")
bpy.ops.import_scene.fbx(filepath=path)
objs = [x for x in bpy.data.objects if x.type == "MESH"]
for ob in objs:
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    uvl = ob.data.uv_layers.active
    if uvl:
        for lp in uvl.data:
            lp.uv[0] = u0 + lp.uv[0] * du
            lp.uv[1] = v0 + lp.uv[1] * dv

bpy.ops.object.select_all(action="DESELECT")
for ob in objs:
    ob.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
if len(objs) > 1:
    bpy.ops.object.join()
obj = bpy.context.view_layer.objects.active

bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
lo = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
hi = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
ctr = (lo + hi) / 2.0
r = (hi - lo).length / 2.0 or 1.0
d = r * 2.6
cam.location = ctr + Vector((d * 0.75, -d * 0.85, d * 0.55))
cam.rotation_euler = (ctr - cam.location).to_track_quat("-Z", "Y").to_euler()
fill.location = ctr + Vector((-r * 1.5, -r * 1.2, r * 2.0))
rim.location = ctr + Vector((r * 1.6, r * 1.4, r * 1.6))
rim.rotation_euler = (ctr - rim.location).to_track_quat("-Z", "Y").to_euler()
fill.rotation_euler = (ctr - fill.location).to_track_quat("-Z", "Y").to_euler()

out = os.path.join(OUT, NAME + ".png")
scn.render.filepath = out
bpy.ops.render.render(write_still=True)
print("RENDERED", NAME, os.path.exists(out), [round(v, 1) for v in obj.dimensions], flush=True)
