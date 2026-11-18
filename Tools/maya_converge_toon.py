"""Converge Brennan's CAD office modules into the group's TEXTURED office set,
apply the group's documented toon shader, render proof.

Documented shader (VFX & Postproduction/toonshader/ToonShader_Setup.pdf):
    AIToon node + a Ramp node with interpolation "none";
    textures -> Base/Specular colour; ramp -> Tonemap;
    no Skydome (directional/other lights only);
    skin ramps grayish-purple, everything else grayscale.

Source scene is opened READ-ONLY; a NEW scene is saved.

Run:
    mayapy Tools/maya_converge_toon.py
"""
import os, json, glob, traceback

os.environ.setdefault("MAYA_MODULE_PATH", r"C:\Program Files\Autodesk\Arnold\Maya2027")
import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds

ROOT = r"G:\film-304-toon-spine"
SRC = r"G:\film-304-canon-onedrive\Set_Environments\Textured\S_OfficeScene01\scenes\S_OfficeScene01_ENR (1).0008.mb"
if not os.path.exists(SRC):
    SRC = r"G:\film-304-canon-onedrive\Set_Environments\S_OfficeScene01_ENR.mb"
CAD = os.path.join(ROOT, "Film304_Packages", "Office_CAD_Pass_2026-11-17", "01_Modules")
UV = os.path.join(ROOT, "Film304_Packages", "Office_UV_Unwrapped_2026-11-17", "01_FBX")
OUTSCENE = os.path.join(ROOT, "Saved", "Scenes", "S_OfficeScene01_BS_Toon_v01.mb")
STILLS = os.path.join(ROOT, "Saved", "Audit", "OfficeToon_2026-11-18")
REPORT = os.path.join(ROOT, "Film304_Packages", "Office_CAD_Pass_2026-11-17", "converge_report.json")
os.makedirs(os.path.dirname(OUTSCENE), exist_ok=True)
os.makedirs(STILLS, exist_ok=True)

report = {"source_scene": SRC, "output_scene": OUTSCENE, "steps": []}
def log(step, **kw):
    kw["step"] = step
    report["steps"].append(kw)
    print("STEP", json.dumps(kw, default=str), flush=True)

assert os.path.exists(SRC), SRC
cmds.file(SRC, open=True, force=True, ignoreVersion=True)
cmds.loadPlugin("mtoa", quiet=True)
cmds.loadPlugin("fbxmaya", quiet=True)

# ---------------------------------------------------------------- inventory
meshes = cmds.ls(type="mesh", long=True, noIntermediate=True) or []
lights = cmds.ls(type=("directionalLight", "pointLight", "spotLight", "areaLight", "aiAreaLight"), long=True) or []
cams = cmds.ls(type="camera", long=True) or []
anim = cmds.ls(type="animCurve", long=True) or []
skydome = [n for n in cmds.ls(lights=True, long=True) if "sky" in n.lower() or "dome" in n.lower()]
all_lights = cmds.ls(lights=True, long=True) or []
bb = cmds.exactWorldBoundingBox(cmds.ls(geometry=True, long=True) or ["persp"])
log("inventory", meshes=len(meshes), lights=len(all_lights), cameras=len(cams),
    anim_curves=len(anim), skydome_candidates=skydome[:6],
    scene_min=[round(v, 1) for v in bb[:3]], scene_max=[round(v, 1) for v in bb[3:]])

# ---------------------------------------------------------------- skydome off
disabled = []
for n in all_lights:
    if "sky" in n.lower() or "dome" in n.lower():
        try:
            shp = cmds.listRelatives(n, shapes=True, fullPath=True) or []
            for s in shp:
                if cmds.attributeQuery("enable", node=s, exists=True):
                    cmds.setAttr(s + ".enable", 0); disabled.append(s)
        except Exception:
            pass
log("skydome_disabled", disabled=disabled)

# ---------------------------------------------------------------- import CAD
before = set(cmds.ls(type="mesh", long=True, noIntermediate=True) or [])
imported = []
for fbx in sorted(glob.glob(os.path.join(CAD, "CAD_*.fbx"))):
    try:
        cmds.file(fbx, i=True, type="FBX", ignoreVersion=True, force=True)
        imported.append(os.path.basename(fbx))
    except Exception as e:
        log("import_failed", file=os.path.basename(fbx), error=str(e)[:200])
new = sorted(set(cmds.ls(type="mesh", long=True, noIntermediate=True) or []) - before)
log("imported_cad", files=imported, new_meshes=len(new))

# ---------------------------------------------------------------- place
# room authority: floor 2200 x 2200 cm, ceiling underside z=340, yaw -25 deg
# Maya is Y-up, so the authored Z becomes world Y.
scene_floor_y = bb[1]
placed = []
for m in new:
    short = m.split("|")[-1]
    try:
        b = cmds.exactWorldBoundingBox(m)
        h = max(1.0, b[4] - b[1])
        w = max(1.0, b[3] - b[0])
        d = max(1.0, b[5] - b[2])
        # sit the module's base on the set's floor plane, centred on the set
        dx = (bb[0] + bb[3]) / 2.0 - (b[0] + b[3]) / 2.0
        dy = scene_floor_y - b[1]
        dz = (bb[2] + bb[5]) / 2.0 - (b[2] + b[5]) / 2.0
        cmds.xform(m, ws=True, t=(dx, dy, dz))
        placed.append({"mesh": short, "size_cm": [round(w, 1), round(h, 1), round(d, 1)],
                       "shift": [round(dx, 1), round(dy, 1), round(dz, 1)]})
    except Exception as e:
        placed.append({"mesh": short, "error": str(e)[:160]})
log("placed", count=len(placed), detail=placed)

# ------------------------------------------------------- documented toon look
def set_if(node, attr, value):
    if cmds.attributeQuery(attr, node=node, exists=True):
        try:
            cmds.setAttr(node + "." + attr, value)
            return True
        except Exception:
            return False
    return False

# discover the real aiToon attribute names once
probe = cmds.shadingNode("aiToon", asShader=True, name="AIT_probe")
attrs = [a for a in cmds.listAttr(probe) if any(k in a.lower() for k in ("tone", "ramp", "base", "spec", "rim", "color"))]
cmds.delete(probe)
log("aiToon_attrs", attrs=attrs[:25])

look = {}
for m in new:
    short = m.split("|")[-1]
    toon = cmds.shadingNode("aiToon", asShader=True, name="AIT_BS_" + short[:28])
    ramp = cmds.shadingNode("ramp", asTexture=True, name="RAMP_BS_" + short[:28])
    set_if(ramp, "interpolation", "None")
    set_if(ramp, "interpolation", "none")
    set_if(ramp, "interpolation", 0)
    set_if(toon, "specular", 0.0)
    set_if(toon, "rimLight", 0.0)
    set_if(toon, "rim", 0.0)
    connected = []
    for attr in ("tonemap", "toneMap", "tone_map", "ramp", "colorRamp"):
        if cmds.attributeQuery(attr, node=toon, exists=True):
            try:
                cmds.connectAttr(ramp + ".outColor", toon + "." + attr, force=True)
                connected.append(attr); break
            except Exception:
                pass
    sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="AIT_BS_" + short[:28] + "SG")
    cmds.connectAttr(toon + ".outColor", sg + ".surfaceShader", force=True)
    try:
        cmds.sets(m, edit=True, forceElement=sg)
    except Exception as e:
        log("assign_failed", mesh=short, error=str(e)[:160])
    look[short] = {"toon": toon, "ramp": ramp, "tonemap_input": connected,
                   "ramp_interpolation": cmds.getAttr(ramp + ".interpolation") if cmds.attributeQuery("interpolation", node=ramp, exists=True) else "n/a"}
log("toon_applied", groups=len(look), detail=look)

# ---------------------------------------------------------------- save
cmds.file(rename=OUTSCENE)
cmds.file(save=True, type="mayaBinary", force=True)
log("saved", path=OUTSCENE, exists=os.path.exists(OUTSCENE),
    size=os.path.getsize(OUTSCENE) if os.path.exists(OUTSCENE) else 0)

# ---------------------------------------------------------------- render
renders = []
try:
    cmds.setAttr("defaultRenderGlobals.currentRenderer", "arnold", type="string")
    cmds.setAttr("defaultResolution.width", 960)
    cmds.setAttr("defaultResolution.height", 540)
    cmds.setAttr("defaultRenderGlobals.animation", 0)
    cmds.setAttr("defaultRenderGlobals.imageFormat", 32)
    cams = [c for c in (cmds.ls(type="camera", long=True) or []) if "persp" not in c and "top" not in c and "front" not in c and "side" not in c] or (cmds.ls(type="camera", long=True) or [])
    for i, cam in enumerate(cams[:3]):
        for s in (cmds.listRelatives(cam, shapes=True, type="camera") or []):
            cmds.setAttr(s + ".renderable", 1)
        prefix = "BS_Toon_v01_cam%d" % i
        cmds.setAttr("defaultRenderGlobals.imageFilePrefix", prefix, type="string")
        err = None
        try:
            cmds.render(cam, x=960, y=540)
        except Exception as e:
            err = str(e)[:200]
        imgdir = os.path.join(cmds.workspace(q=True, rootDirectory=True),
                              cmds.workspace(fileRuleEntry="images"))
        found = sorted(glob.glob(os.path.join(imgdir, "**", prefix + "*.png"), recursive=True), key=os.path.getmtime)
        dest = None
        if found:
            import shutil
            dest = os.path.join(STILLS, prefix + ".png")
            shutil.copyfile(found[-1], dest)
        renders.append({"camera": cam, "ok": bool(dest), "error": err, "still": dest})
        log("render", camera=cam, ok=bool(dest), error=err, still=dest)
except Exception as e:
    log("render_setup_failed", error=repr(e)[:300])

with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=2, default=str)
print("REPORT", REPORT, flush=True)
maya.standalone.uninitialize()
