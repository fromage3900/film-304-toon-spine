"""Re-render the converge stills at native 1920x1080."""
import os, json, glob, shutil
os.environ.setdefault("MAYA_MODULE_PATH", r"C:\Program Files\Autodesk\Arnold\Maya2027")
import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds

ROOT = r"G:\film-304-toon-spine"
SCENE = os.path.join(ROOT, "Saved", "Scenes", "S_OfficeScene01_BS_Toon_v02.mb")
STILLS = os.path.join(ROOT, "Saved", "Audit", "OfficeToon_2026-11-18")
REPORT = os.path.join(ROOT, "Saved", "Audit", "OfficeToon_2026-11-18", "hd_render_report.json")
rep = {"steps": []}
def log(s, **kw):
    kw["step"] = s; rep["steps"].append(kw); print("STEP", json.dumps(kw, default=str), flush=True)

cmds.file(SCENE, open=True, force=True, ignoreVersion=True)
cmds.loadPlugin("mtoa", quiet=True)
cmds.setAttr("defaultRenderGlobals.currentRenderer", "arnold", type="string")
cmds.setAttr("defaultResolution.width", 1920)
cmds.setAttr("defaultResolution.height", 1080)
cmds.setAttr("defaultRenderGlobals.animation", 0)
cmds.setAttr("defaultRenderGlobals.imageFormat", 32)

cams = []
for shape in (cmds.ls(type="camera", long=True) or []):
    if any(k in shape for k in ("perspShape", "topShape", "frontShape", "sideShape")):
        continue
    par = cmds.listRelatives(shape, parent=True, fullPath=True) or []
    if par:
        cams.append(par[0])
log("cameras", cams=cams[:3])

renders = []
for i, cam in enumerate(cams[:2]):
    for s in (cmds.listRelatives(cam, shapes=True, type="camera") or []):
        cmds.setAttr(s + ".renderable", 1)
    prefix = "BS_Toon_v02_HD_cam%d" % i
    cmds.setAttr("defaultRenderGlobals.imageFilePrefix", prefix, type="string")
    err = None
    try:
        cmds.render(cam, x=1920, y=1080)
    except Exception as e:
        err = str(e)[:200]
    imgdir = os.path.join(cmds.workspace(q=True, rootDirectory=True),
                          cmds.workspace(fileRuleEntry="images"))
    found = sorted(glob.glob(os.path.join(imgdir, "**", prefix + "*.*"), recursive=True),
                   key=os.path.getmtime)
    dest = None
    if found:
        dest = os.path.join(STILLS, prefix + os.path.splitext(found[-1])[1])
        shutil.copyfile(found[-1], dest)
    renders.append({"camera": cam.split(":")[-1], "ok": bool(dest), "error": err, "still": dest})
    log("render", camera=cam.split(":")[-1], ok=bool(dest), error=err, still=dest)

rep["renders"] = renders
json.dump(rep, open(REPORT, "w"), indent=2, default=str)
print("REPORT", REPORT, flush=True)
try:
    maya.standalone.uninitialize()
except Exception:
    pass
