"""Office Spider layout - Shot 62 framing fix (camera keys), lambert materials kept.

Opens the v09 handoff READ-ONLY, edits the Cam_Shot62 translateY/translateZ KEY
values (the camera is keyed on frames 1 and 48) so the spider descent and the
hero swatter stay in frame, then saves a NEW file and renders four frames with
the original lambert materials so the framing can be judged on readable colours.

Never overwrites L_Scene62-66_BS.mb or any earlier v0x scene.

Run:
  "C:\\Program Files\\Autodesk\\Maya2027\\bin\\mayapy.exe" Tools\\apply_shot62_framing.py
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
OUT = os.path.join(ROOT, "Saved", "Scenes", "L_Scene62-66_BS_v11_framing.mb")
STILLS = os.path.join(ROOT, "Saved", "Playblasts", "Layout_62-66", "stills")
REPORT = os.path.join(ROOT, "Saved", "Scenes", "layout_62_66_v11_framing_report.json")
CAM = "Cam_Shot62"
SWATTER = "Layout_HeroSwatter"
SPIDER_ROOT = "Layout_Spider_Root"
CHECK_FRAMES = list(range(12, 49, 6))
RENDER_FRAMES = [12, 24, 36, 48]
RES_W, RES_H = 960, 540

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


# Solve the framing from the measured content (frames 24-48 body top, swatter head).
cmds.currentTime(24)
swatter_bb = world_bb(SWATTER)
tops = []
for f in [24, 36, 48]:
    cmds.currentTime(f)
    tops.append(world_bb(SPIDER_ROOT)[4])
bottom = min(swatter_bb[1], 40.0) - 10.0
top = max(tops) + 12.0
centre_y = (top + bottom) / 2.0
sb = world_bb(SPIDER_ROOT)
subject_z = (sb[2] + sb[5]) / 2.0
dist = (top - bottom) / (2.0 * vap_half / focal)
cam_z = subject_z + dist
log("framing_solve", bottom=round(bottom, 1), top=round(top, 1), centre_y=round(centre_y, 1),
    subject_z=round(subject_z, 1), distance=round(dist, 1), cam_z=round(cam_z, 1))

# Edit the existing keys (translateY, translateZ) so the shot still animates from its keys.
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


verify = {}
for f in CHECK_FRAMES:
    verify[str(f)] = {"spider_bbox_corners_in": in_frame(SPIDER_ROOT, f),
                      "swatter_bbox_corners_in": in_frame(SWATTER, f)}
log("framing_verify", per_frame=verify)

cmds.file(rename=OUT)
cmds.file(save=True, type="mayaBinary", force=True)
log("saved_framing", path=OUT, exists=os.path.exists(OUT))

# Render with the original (lambert) materials so the framing is readable.
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
    name = "v11framing_shot62_f%03d" % f
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
