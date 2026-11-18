"""Compose the CAD pass into an existing layout and apply the documented toon look.

Documented look (Tools/apply_aitoon_look.py):
    Arnold aiToon, base colour kept (or the warm backdrop cream), specular 0,
    rimLight 0.

Opens L_Scene62-66_BS_v27_eyefix.mb READ-ONLY, imports the CAD modules, applies
the look to them, saves a NEW scene (v28) and writes a JSON report. The source
scene is never overwritten.

Run:
    "C:\\Program Files\\Autodesk\\Maya2027\\bin\\mayapy.exe" Tools\\maya_compose_cad.py
"""
import os, json, glob

os.environ.setdefault("MAYA_MODULE_PATH", r"C:\Program Files\Autodesk\Arnold\Maya2027")

import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds

ROOT = r"G:\film-304-toon-spine"
SRC = os.path.join(ROOT, "Saved", "Scenes", "L_Scene62-66_BS_v27_eyefix.mb")
OUT = os.path.join(ROOT, "Saved", "Scenes", "L_Scene62-66_BS_v28_cad_pass.mb")
CAD = os.path.join(ROOT, "Film304_Packages", "Office_CAD_Pass_2026-11-17", "01_Modules")
REPORT = os.path.join(ROOT, "Film304_Packages", "Office_CAD_Pass_2026-11-17", "maya_report.json")
WARM = (1.0, 0.957, 0.882)

assert os.path.abspath(OUT) != os.path.abspath(SRC)
report = {"source": SRC, "output": OUT, "steps": []}
def log(step, **kw):
    kw["step"] = step
    report["steps"].append(kw)
    print("STEP", json.dumps(kw, default=str), flush=True)

cmds.file(SRC, open=True, force=True, ignoreVersion=True)
cmds.loadPlugin("mtoa", quiet=True)
cmds.loadPlugin("fbxmaya", quiet=True)
log("opened_source", ok=True)

before = set(cmds.ls(type="mesh", long=True, noIntermediate=True) or [])

# ---------------------------------------------------------------- import CAD
imported = []
for fbx in sorted(glob.glob(os.path.join(CAD, "CAD_*.fbx"))):
    try:
        cmds.file(fbx, i=True, type="FBX", ignoreVersion=True, force=True,
                  importTimeRange="combine")
        imported.append(os.path.basename(fbx))
    except Exception as e:
        log("import_failed", file=os.path.basename(fbx), error=str(e)[:200])

after = set(cmds.ls(type="mesh", long=True, noIntermediate=True) or [])
new_shapes = sorted(after - before)
log("imported", files=imported, new_shapes=len(new_shapes))

# scale/orient diagnostic on the imported set
diag = {}
for shp in new_shapes[:3]:
    bb = cmds.exactWorldBoundingBox(shp)
    diag[shp.split("|")[-1]] = [round(v, 1) for v in bb]
log("imported_bounds_sample", diag=diag)

# ------------------------------------------------------------- toon look
def set_if(node, attr, value):
    if cmds.attributeQuery(attr, node=node, exists=True):
        try:
            cmds.setAttr(node + "." + attr, value)
            return True
        except Exception:
            return False
    return False

swapped = {}
for shp in new_shapes:
    sgs = [s for s in (cmds.listConnections(shp, type="shadingEngine") or []) if s != "initialShadingGroup"]
    if sgs:
        sg = sgs[0]
        if sg in swapped:
            cmds.sets(shp, edit=True, forceElement=swapped[sg]["sg"])
            continue
        mats = cmds.listConnections(sg + ".surfaceShader", source=True, destination=False) or []
        mat = mats[0] if mats else sg
        colour = None
        for attr in ("color", "baseColor"):
            if cmds.attributeQuery(attr, node=mat, exists=True):
                conn = cmds.listConnections(mat + "." + attr, source=True, destination=False)
                if not conn:
                    colour = tuple(cmds.getAttr(mat + "." + attr)[0])
                break
        base = sg.replace("SG", "").replace(":", "_").replace("|", "_") or "cad"
    else:
        # fresh FBX import: nothing but initialShadingGroup -- name from the mesh
        base = shp.split("|")[-1].split(":")[-1].replace("Shape", "").replace("curv", "") or "cad"
        mat, colour = None, None
    key = "AIT_CAD_" + base
    if key not in swapped:
        toon = cmds.shadingNode("aiToon", asShader=True, name=key)
        if colour is not None:
            cmds.setAttr(toon + ".baseColor", *colour, type="double3")
        set_if(toon, "specular", 0.0)
        set_if(toon, "rimLight", 0.0)
        new_sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=key + "SG")
        cmds.connectAttr(toon + ".outColor", new_sg + ".surfaceShader", force=True)
        swapped[key] = {"toon": toon, "sg": new_sg, "source_material": mat, "colour": colour}
    cmds.sets(shp, edit=True, forceElement=swapped[key]["sg"])

log("look_applied", new_shapes=len(new_shapes), shading_groups=len(swapped),
    groups=sorted(swapped.keys()))

# ---------------------------------------------------------------- save
cmds.file(rename=OUT)
cmds.file(save=True, type="mayaBinary", force=True)
log("saved", path=OUT, exists=os.path.exists(OUT),
    size=os.path.getsize(OUT) if os.path.exists(OUT) else 0)

with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=2, default=str)
print("REPORT", REPORT, flush=True)
maya.standalone.uninitialize()
