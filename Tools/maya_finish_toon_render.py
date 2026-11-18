"""Finish the converge: lights + ramp->baseTonemap + render proof.

Their set has ZERO lights (that is why the first render was empty), and the
documented ramp belongs on aiToon.baseTonemap (not "tonemap").
"""
import os, json, glob, shutil
os.environ.setdefault("MAYA_MODULE_PATH", r"C:\Program Files\Autodesk\Arnold\Maya2027")
import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds

ROOT = r"G:\film-304-toon-spine"
SCENE = os.path.join(ROOT, "Saved", "Scenes", "S_OfficeScene01_BS_Toon_v01.mb")
OUT = os.path.join(ROOT, "Saved", "Scenes", "S_OfficeScene01_BS_Toon_v02.mb")
STILLS = os.path.join(ROOT, "Saved", "Audit", "OfficeToon_2026-11-18")
REPORT = os.path.join(ROOT, "Film304_Packages", "Office_CAD_Pass_2026-11-17", "render_report.json")
os.makedirs(STILLS, exist_ok=True)

report = {"scene": SCENE, "steps": []}
def log(step, **kw):
    kw["step"] = step; report["steps"].append(kw)
    print("STEP", json.dumps(kw, default=str), flush=True)

cmds.file(SCENE, open=True, force=True, ignoreVersion=True)
cmds.loadPlugin("mtoa", quiet=True)

log("inventory", lights=len(cmds.ls(lights=True, long=True) or []),
    toon_nodes=len(cmds.ls("AIT_BS_*") or []),
    ramp_nodes=len(cmds.ls("RAMP_BS_*") or []))

# ---- lights (documented: no skydome, use directional/other) --------------
made = []
for name, ltype, pos, rot, inten in (
        ("BS_KeyDir", "directionalLight", (1800, 2600, 1400), (-38, 35, 0), 3.0),
        ("BS_FillDir", "directionalLight", (-1600, 1800, 900), (-30, -50, 0), 1.2)):
    try:
        n = cmds.shadingNode(ltype, asLight=True, name=name)
        cmds.xform(n, ws=True, t=pos)
        cmds.xform(n, ws=True, ro=rot)
        shp = cmds.listRelatives(n, shapes=True, fullPath=True)[0]
        cmds.setAttr(shp + ".intensity", inten)
        made.append(n)
    except Exception as e:
        log("light_failed", name=name, error=str(e)[:160])
log("lights_added", made=made)

# ---- ramp -> baseTonemap, grayscale base ---------------------------------
linked, failed = [], []
for toon in (cmds.ls("AIT_BS_*") or []):
    ramp = toon.replace("AIT_BS_", "RAMP_BS_")
    if not cmds.objExists(ramp):
        failed.append({"toon": toon, "reason": "no ramp"}); continue
    try:
        cmds.connectAttr(ramp + ".outColor", toon + ".baseTonemap", force=True)
        linked.append(toon)
    except Exception as e:
        failed.append({"toon": toon, "reason": str(e)[:160]})
    # grayscale base per the doc (non-skin assets)
    for attr, val, typ in (("baseColor", (0.82, 0.82, 0.82), "double3"),
                           ("specular", 0.0, None),
                           ("rimLight", 0.0, None),
                           ("rim", 0.0, None)):
        try:
            if not cmds.attributeQuery(attr, node=toon, exists=True):
                continue
            if typ:
                cmds.setAttr(toon + "." + attr, *val, type=typ)
            else:
                cur = cmds.getAttr(toon + "." + attr)
                if isinstance(cur, (int, float)):
                    cmds.setAttr(toon + "." + attr, val)
        except Exception:
            pass
    try:
        cmds.setAttr(ramp + ".interpolation", 0)
    except Exception:
        pass
log("ramp_linked", count=len(linked), failed=failed[:4],
    sample=linked[:3])

# ---- save v02 ------------------------------------------------------------
cmds.file(rename=OUT)
cmds.file(save=True, type="mayaBinary", force=True)
log("saved", path=OUT, exists=os.path.exists(OUT),
    size=os.path.getsize(OUT) if os.path.exists(OUT) else 0)

# ---- render --------------------------------------------------------------
renders = []
try:
    cmds.setAttr("defaultRenderGlobals.currentRenderer", "arnold", type="string")
    cmds.setAttr("defaultResolution.width", 960)
    cmds.setAttr("defaultResolution.height", 540)
    cmds.setAttr("defaultRenderGlobals.animation", 0)
    cmds.setAttr("defaultRenderGlobals.imageFormat", 32)
    cams = []
    for shape in (cmds.ls(type="camera", long=True) or []):
        if any(k in shape for k in ("perspShape", "topShape", "frontShape", "sideShape")):
            continue
        parents = cmds.listRelatives(shape, parent=True, fullPath=True) or []
        if parents:
            cams.append(parents[0])
    cams = cams[:3]
    log("render_cameras", cameras=cams)
    for i, cam in enumerate(cams):
        for s in (cmds.listRelatives(cam, shapes=True, type="camera") or []):
            cmds.setAttr(s + ".renderable", 1)
        prefix = "BS_Toon_v02_cam%d" % i
        cmds.setAttr("defaultRenderGlobals.imageFilePrefix", prefix, type="string")
        err = None
        try:
            cmds.render(cam, x=960, y=540)
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
        renders.append({"camera": cam.split(":")[-1], "ok": bool(dest), "error": err,
                        "still": dest, "image_dir": imgdir, "found": len(found)})
        log("render", camera=cam.split(":")[-1], ok=bool(dest), error=err, still=dest)
except Exception as e:
    log("render_failed", error=repr(e)[:300])

report["renders"] = renders
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=2, default=str)
print("REPORT", REPORT, flush=True)
try:
    maya.standalone.uninitialize()
except Exception:
    pass
