"""Office Spider layout - Phase 1: flat aiToon look + Cam_Shot62 framing (v11).

Opens the v09 handoff READ-ONLY, saves a NEW versioned copy (v11), then:
  * retargets Cam_Shot62 so the spider descent (frames 12-48) and the hero
    swatter stay in frame (solved from measured bounding boxes, lens unchanged);
  * replaces each renderable shading group with an aiToon shader:
      - characters/props: flat toon (base colour kept, specular and rim off);
      - backdrop: warm cream toon (keeps the v09 warm read, RGB ~255/244/225);
  * renders Cam_Shot62 at frames 12, 24, 36, 48 with Arnold (960x540).

Never overwrites L_Scene62-66_BS.mb or any earlier v0x scene.

Run:
  "C:\\Program Files\\Autodesk\\Maya2027\\bin\\mayapy.exe" Tools\\apply_aitoon_look.py
"""
import os
import json
import glob
import shutil

os.environ.setdefault("MAYA_MODULE_PATH", r"C:\Program Files\Autodesk\Arnold\Maya2027")

import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds
from maya.api import OpenMaya as om

ROOT = r"G:\film-304-toon-spine"
SRC = os.path.join(ROOT, "Saved", "Scenes", "L_Scene62-66_BS.mb")
OUT = os.path.join(ROOT, "Saved", "Scenes", "L_Scene62-66_BS_v11_aitoon_look.mb")
STILLS = os.path.join(ROOT, "Saved", "Playblasts", "Layout_62-66", "stills")
REPORT = os.path.join(ROOT, "Saved", "Scenes", "layout_62_66_v11_aitoon_look_report.json")
CAM = "Cam_Shot62"
FRAMES = [12, 24, 36, 48]
RES_W, RES_H = 960, 540
WARM_BACKDROP = (1.0, 0.957, 0.882)
BACKDROP_MAT = "Layout_BackdropMat_S"
SWATTER = "Layout_HeroSwatter"
SPIDER_ROOT = "Layout_Spider_Root"

assert os.path.abspath(OUT) != os.path.abspath(SRC), "refusing to overwrite source scene"
report = {"source": SRC, "output": OUT, "steps": []}


def log(step, **kw):
    kw["step"] = step
    report["steps"].append(kw)
    print("STEP", json.dumps(kw, default=str))


cmds.file(SRC, open=True, force=True, ignoreVersion=True)
cmds.loadPlugin("mtoa", quiet=True)
log("opened_source", ok=True)


def world_bb(node):
    return cmds.exactWorldBoundingBox(node)


# ---------------------------------------------------------------- framing ----
keyed = cmds.listConnections(CAM, type="animCurve") or []
shape = cmds.listRelatives(CAM, shapes=True, type="camera")[0]
focal = cmds.getAttr(shape + ".focalLength")
vap_half = cmds.getAttr(shape + ".verticalFilmAperture") * 25.4 / 2.0
hap_half = cmds.getAttr(shape + ".horizontalFilmAperture") * 25.4 / 2.0

# Measure the content that has to stay in frame across the shot.
cmds.currentTime(24)
swatter_bb = world_bb(SWATTER)
spider_pts_top = []
for f in [24, 36, 48]:
    cmds.currentTime(f)
    spider_pts_top.append(world_bb(SPIDER_ROOT)[4])
bottom = min(swatter_bb[1], 40.0) - 10.0          # keep the swatter head in frame
top = max(spider_pts_top) + 12.0                   # keep the descending body in frame
height = top - bottom
centre_y = (top + bottom) / 2.0
subject_z = (world_bb(SPIDER_ROOT)[2] + world_bb(SPIDER_ROOT)[5]) / 2.0
dist = height / (2.0 * vap_half / focal)           # vertical visible height -> distance
cam_z = subject_z + dist
log("framing_solve", focal_mm=focal, bottom=round(bottom, 1), top=round(top, 1),
    centre_y=round(centre_y, 1), subject_z=round(subject_z, 1), distance=round(dist, 1),
    cam_z=round(cam_z, 1), keyed_curves=len(keyed))

if keyed:
    log("framing_skipped", reason="camera is keyed; retarget must be done in the keys", curves=keyed)
else:
    cmds.xform(CAM, ws=True, t=(0.0, centre_y, cam_z))
    cmds.xform(CAM, ws=True, ro=(-1.5911402711945815, 0.0, 0.0))
    log("framing_applied", translate=cmds.xform(CAM, q=True, ws=True, t=True))


def in_frame_fraction(node, frame):
    cmds.currentTime(frame)
    bb = world_bb(node)
    inv = om.MMatrix(cmds.xform(CAM, q=True, ws=True, m=True)).inverse()
    ins = 0
    for x in (bb[0], bb[3]):
        for y in (bb[1], bb[4]):
            for z in (bb[2], bb[5]):
                pc = om.MPoint(x, y, z) * inv
                if pc.z >= 0:
                    continue
                nx = (focal * pc.x / -pc.z) / hap_half
                ny = (focal * pc.y / -pc.z) / vap_half
                if abs(nx) <= 1 and abs(ny) <= 1:
                    ins += 1
    return ins


verify = {}
for f in FRAMES:
    verify[str(f)] = {"spider_corners_in": in_frame_fraction(SPIDER_ROOT, f),
                      "swatter_corners_in": in_frame_fraction(SWATTER, f)}
log("framing_verify", per_frame=verify)

# -------------------------------------------------------------- look -----------
def base_colour(material):
    for attr in ("color", "baseColor", "base_color"):
        if cmds.attributeQuery(attr, node=material, exists=True):
            conn = cmds.listConnections(material + "." + attr, source=True, destination=False)
            if conn:
                return None, conn[0]
            return tuple(cmds.getAttr(material + "." + attr)[0]), None
    return (0.6, 0.6, 0.6), None


def set_if(node, attr, value):
    if cmds.attributeQuery(attr, node=node, exists=True):
        try:
            cmds.setAttr(node + "." + attr, value)
            return True
        except Exception:
            return False
    return False


swapped = {}
backdrop_sg = None
shapes = cmds.ls(type="mesh", long=True, noIntermediate=True) or []

for shp in shapes:
    sgs = [s for s in (cmds.listConnections(shp, type="shadingEngine") or []) if s != "initialShadingGroup"]
    if not sgs:
        continue
    sg = sgs[0]
    if sg not in swapped:
        mats = cmds.listConnections(sg + ".surfaceShader", source=True, destination=False) or []
        mat = mats[0] if mats else sg
        colour, texture = base_colour(mat) if mats else ((0.6, 0.6, 0.6), None)
        is_backdrop = mat == BACKDROP_MAT
        base = sg.replace("SG", "").replace(":", "_").replace("|", "_") or "shader"
        toon = cmds.shadingNode("aiToon", asShader=True, name="AIT_" + base)
        if is_backdrop:
            colour, texture = WARM_BACKDROP, None
            backdrop_sg = sg
        if colour is not None:
            cmds.setAttr(toon + ".baseColor", *colour, type="double3")
        elif texture is not None:
            cmds.connectAttr(texture + ".outColor", toon + ".baseColor", force=True)
        # flat toon: no specular sheen, no rim on characters/props
        set_if(toon, "specular", 0.0)
        set_if(toon, "rimLight", 0.0)
        new_sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="AIT_" + base + "SG")
        cmds.connectAttr(toon + ".outColor", new_sg + ".surfaceShader", force=True)
        swapped[sg] = {"toon": toon, "sg": new_sg, "source_material": mat,
                       "colour": colour, "backdrop": is_backdrop}
    cmds.sets(shp, edit=True, forceElement=swapped[sg]["sg"])

log("look_applied", shapes_total=len(shapes), groups=len(swapped),
    backdrop_group=backdrop_sg, warm_backdrop=WARM_BACKDROP)
report["swapped"] = swapped

# ---------------------------------------------------------------- save ---------
cmds.file(rename=OUT)
cmds.file(save=True, type="mayaBinary", force=True)
log("saved_v11", path=OUT, exists=os.path.exists(OUT),
    size=os.path.getsize(OUT) if os.path.exists(OUT) else 0)

# --------------------------------------------------------------- render --------
cmds.setAttr("defaultRenderGlobals.currentRenderer", "arnold", type="string")
cmds.setAttr("defaultResolution.width", RES_W)
cmds.setAttr("defaultResolution.height", RES_H)
cmds.setAttr("defaultRenderGlobals.animation", 0)
cmds.setAttr("defaultRenderGlobals.imageFormat", 32)
for shp in cmds.listRelatives(CAM, shapes=True, type="camera") or []:
    cmds.setAttr(shp + ".renderable", 1)
os.makedirs(STILLS, exist_ok=True)
images_dir = os.path.join(cmds.workspace(q=True, rootDirectory=True), cmds.workspace(fileRuleEntry="images"))

for f in FRAMES:
    name = "v11_shot62_f%03d" % f
    cmds.currentTime(f)
    cmds.setAttr("defaultRenderGlobals.imageFilePrefix", name, type="string")
    err = None
    try:
        cmds.render(CAM, x=RES_W, y=RES_H)
    except Exception as e:  # noqa: BLE001
        err = str(e)
    found = sorted(glob.glob(os.path.join(images_dir, "**", name + "*.png"), recursive=True), key=os.path.getmtime)
    dest = os.path.join(STILLS, name + ".png")
    if found:
        shutil.copyfile(found[-1], dest)
    log("render", frame=f, ok=bool(found) and err is None, error=err, still=dest if found else None)

with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=2, default=str)
print("REPORT", REPORT)
maya.standalone.uninitialize()
