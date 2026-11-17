"""Office Spider layout - Shot 62 flat look (aiStandardSurface) + larger spider framing (v12).

Opens the v09 handoff READ-ONLY and saves a NEW versioned copy (v12):
  * framing: Cam_Shot62 translateY/translateZ KEY values are re-solved so the
    spider descent is larger in frame (vertical range trimmed to the swatter
    head up to the spider's descent top; lens unchanged, 50 mm);
  * look: every shape that has a real material is swapped to an aiStandardSurface
    with the original base colour, specular weight 0 (flat, no highlight).
    Shapes on initialShadingGroup (the warm backdrop) and unassigned shapes are
    left exactly as in v09 so the warm backdrop is preserved;
  * renders Cam_Shot62 at frames 12, 24, 36, 48 with Arnold (960x540).

Never overwrites L_Scene62-66_BS.mb or any earlier v0x scene.

Run:
  "C:\\Program Files\\Autodesk\\Maya2027\\bin\\mayapy.exe" Tools\\apply_shot62_standard_flat.py
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
# LOOK_MODE=standard (default) swaps materials; LOOK_MODE=none keeps every v09 material
# (control render that isolates the look swap from the framing change).
# LOOK_MODE=chars  swaps only character/prop materials (bisect);
# LOOK_MODE=sets   swaps only set-dressing materials (bisect).
LOOK_MODE = os.environ.get("LOOK_MODE", "standard")
RENDER_FRAMES = [int(x) for x in os.environ.get("RENDER_FRAMES", "12,24,36,48").split(",")]
TAGS = {"standard": "v12b_standard_flat_tight", "none": "v12b_control_nolook_tight",
        "chars": "v12b_bisect_chars_tight", "sets": "v12b_bisect_sets_tight",
        "setsA": "v12b_bisect_setsA_tight", "setsB": "v12b_bisect_setsB_tight"}
SET_A_MATS = {"Layout_White", "Layout_SilkMat", "Layout_MugMat", "Layout_Screen"}
TAG = TAGS[LOOK_MODE]
CHAR_MATS = {"Layout_Skin", "Layout_Shirt", "Layout_Pants", "Layout_Shoe", "Layout_Hair", "Layout_Teeth",
             "Layout_Eye", "Layout_EyeDark", "Layout_Cornea", "Layout_SpiderMat", "Material1",
             "MaterialFBXASC032FBXASC03556", "MaterialFBXASC032FBXASC03540"}


def want_material(mat):
    if LOOK_MODE == "standard":
        return True
    if LOOK_MODE == "none":
        return False
    is_char = mat.startswith(("David:", "Spider:")) or mat in CHAR_MATS
    if LOOK_MODE == "chars":
        return is_char
    if LOOK_MODE == "sets":
        return not is_char
    if LOOK_MODE == "setsA":
        return mat in SET_A_MATS
    if LOOK_MODE == "setsB":
        return (not is_char) and mat not in SET_A_MATS
    return False
OUT = os.path.join(ROOT, "Saved", "Scenes", "L_Scene62-66_BS_%s.mb" % TAG)
STILLS = os.path.join(ROOT, "Saved", "Playblasts", "Layout_62-66", "stills")
REPORT = os.path.join(ROOT, "Saved", "Scenes", "layout_62_66_%s_report.json" % TAG)
SPIDER_TOP_CAP = 165.0    # cm: tighter top -> larger spider; it enters from the top edge ~frame 28
CAM = "Cam_Shot62"
SWATTER = "Layout_HeroSwatter"
SPIDER_ROOT = "Layout_Spider_Root"
RENDER_FRAMES = [12, 24, 36, 48]
RES_W, RES_H = 960, 540
DESK_CLEARANCE = 8.0      # cm below the swatter's lowest point
SPIDER_TOP_PAD = 10.0     # cm above the spider's highest body point in frames 24-48

assert os.path.abspath(OUT) != os.path.abspath(SRC), "refusing to overwrite source scene"
report = {"source": SRC, "output": OUT, "steps": []}


def log(step, **kw):
    kw["step"] = step
    report["steps"].append(kw)
    print("STEP", json.dumps(kw, default=str))


cmds.file(SRC, open=True, force=True, ignoreVersion=True)
cmds.loadPlugin("mtoa", quiet=True)
log("opened_source", ok=True)

shape = cmds.listRelatives(CAM, shapes=True, type="camera")[0]
focal = cmds.getAttr(shape + ".focalLength")
vap_half = cmds.getAttr(shape + ".verticalFilmAperture") * 25.4 / 2.0
hap_half = cmds.getAttr(shape + ".horizontalFilmAperture") * 25.4 / 2.0


def world_bb(node):
    return cmds.exactWorldBoundingBox(node)


# ----------------------------------------------------------- framing solve ----
cmds.currentTime(24)
swatter_bb = world_bb(SWATTER)
tops = []
for f in [24, 36, 48]:
    cmds.currentTime(f)
    tops.append(world_bb(SPIDER_ROOT)[4])
bottom = swatter_bb[1] - DESK_CLEARANCE
top = min(max(tops) + SPIDER_TOP_PAD, SPIDER_TOP_CAP)
centre_y = (top + bottom) / 2.0
sb = world_bb(SPIDER_ROOT)
subject_z = (sb[2] + sb[5]) / 2.0
dist = (top - bottom) / (2.0 * vap_half / focal)
cam_z = subject_z + dist
log("framing_solve", swatter_ymin=round(swatter_bb[1], 1), bottom=round(bottom, 1), top=round(top, 1),
    centre_y=round(centre_y, 1), subject_z=round(subject_z, 1), distance=round(dist, 1), cam_z=round(cam_z, 1))

edited = {}
for attr, value in (("translateY", centre_y), ("translateZ", cam_z)):
    plug = CAM + "." + attr
    keys = cmds.keyframe(plug, q=True, indexValue=True) or []
    for i in keys:
        cmds.keyframe(plug, index=(i, i), edit=True, valueChange=value)
    edited[attr] = {"keys": len(keys), "value": round(value, 2)}
log("keys_edited", **edited)


def in_frame(node, frame):
    cmds.currentTime(frame)
    bb = world_bb(node)
    inv = om.MMatrix(cmds.xform(CAM, q=True, ws=True, m=True)).inverse()
    ins = total = 0
    for x in (bb[0], bb[3]):
        for y in (bb[1], bb[4]):
            for z in (bb[2], bb[5]):
                pc = om.MPoint(x, y, z) * inv
                total += 1
                if pc.z >= 0:
                    continue
                nx = (focal * pc.x / -pc.z) / hap_half
                ny = (focal * pc.y / -pc.z) / vap_half
                if abs(nx) <= 1 and abs(ny) <= 1:
                    ins += 1
    return "%d/%d" % (ins, total)


log("framing_verify", swatter={str(f): in_frame(SWATTER, f) for f in [12, 24, 36, 48]},
    spider_bbox={str(f): in_frame(SPIDER_ROOT, f) for f in [12, 24, 36, 48]})


# -------------------------------------------------------------- look ----------
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
kept = []
skipped_sgs = set()
shapes = cmds.ls(type="mesh", long=True, noIntermediate=True) or []
for shp in shapes:
    sgs = [s for s in (cmds.listConnections(shp, type="shadingEngine") or []) if s != "initialShadingGroup"]
    if not sgs:
        kept.append(shp)
        continue
    sg = sgs[0]
    if sg in skipped_sgs:
        kept.append(shp)
        continue
    if sg not in swapped:
        mats = cmds.listConnections(sg + ".surfaceShader", source=True, destination=False) or []
        mat = mats[0] if mats else sg
        if not want_material(mat):
            skipped_sgs.add(sg)
            kept.append(shp)
            continue
        colour, texture = base_colour(mat) if mats else ((0.6, 0.6, 0.6), None)
        base = sg.replace("SG", "").replace(":", "_").replace("|", "_") or "shader"
        std = cmds.shadingNode("aiStandardSurface", asShader=True, name="FLAT_" + base)
        if colour is not None:
            cmds.setAttr(std + ".baseColor", *colour, type="double3")
        elif texture is not None:
            cmds.connectAttr(texture + ".outColor", std + ".baseColor", force=True)
        set_if(std, "specular", 0.0)   # flat: no specular highlight
        new_sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="FLAT_" + base + "SG")
        cmds.connectAttr(std + ".outColor", new_sg + ".surfaceShader", force=True)
        swapped[sg] = {"shader": std, "sg": new_sg, "source_material": mat, "colour": colour}
    cmds.sets(shp, edit=True, forceElement=swapped[sg]["sg"])

log("look_applied", shapes_total=len(shapes), groups=len(swapped), kept_untouched=len(kept))
report["swapped"] = swapped
report["kept_untouched"] = kept

# -------------------------------------------------------------- save ----------
cmds.file(rename=OUT)
cmds.file(save=True, type="mayaBinary", force=True)
log("saved_v12", path=OUT, exists=os.path.exists(OUT), size=os.path.getsize(OUT) if os.path.exists(OUT) else 0)

# ------------------------------------------------------------- render ---------
cmds.setAttr("defaultRenderGlobals.currentRenderer", "arnold", type="string")
cmds.setAttr("defaultResolution.width", RES_W)
cmds.setAttr("defaultResolution.height", RES_H)
cmds.setAttr("defaultRenderGlobals.animation", 0)
cmds.setAttr("defaultRenderGlobals.imageFormat", 32)
for s in cmds.listRelatives(CAM, shapes=True, type="camera") or []:
    cmds.setAttr(s + ".renderable", 1)
os.makedirs(STILLS, exist_ok=True)
images_dir = os.path.join(cmds.workspace(q=True, rootDirectory=True), cmds.workspace(fileRuleEntry="images"))
for f in RENDER_FRAMES:
    name = "%s_shot62_f%03d" % (TAG, f)
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
