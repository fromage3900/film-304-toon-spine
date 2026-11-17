"""Office Spider layout - Arnold toon (aiToon) TEST pass.

Opens the v09 handoff scene READ-ONLY, saves a NEW versioned copy, swaps each
renderable mesh's shading group to an aiToon shader that keeps the original
base colour, then renders one still per requested camera with Arnold.

Never overwrites L_Scene62-66_BS.mb or any v0x scene.

Run:
  "C:\\Program Files\\Autodesk\\Maya2027\\bin\\mayapy.exe" Tools\\apply_aitoon_test.py
"""
import os
import json
import glob
import shutil

os.environ.setdefault("MAYA_MODULE_PATH", r"C:\Program Files\Autodesk\Arnold\Maya2027")

import maya.standalone
maya.standalone.initialize(name="python")
import maya.cmds as cmds

ROOT = r"G:\film-304-toon-spine"
SRC = os.path.join(ROOT, "Saved", "Scenes", "L_Scene62-66_BS.mb")
OUT = os.path.join(ROOT, "Saved", "Scenes", "L_Scene62-66_BS_v10_aitoon_test.mb")
STILLS = os.path.join(ROOT, "Saved", "Playblasts", "Layout_62-66", "stills")
REPORT = os.path.join(ROOT, "Saved", "Scenes", "layout_62_66_v10_aitoon_test_report.json")
SHOTS = [("Cam_Shot62", 24, "v10_aitoon_shot62")]
RES_W, RES_H = 960, 540

assert os.path.abspath(OUT) != os.path.abspath(SRC), "refusing to overwrite source scene"

report = {"source": SRC, "output": OUT, "steps": [], "renders": []}


def log(step, **kw):
    kw["step"] = step
    report["steps"].append(kw)
    print("STEP", json.dumps(kw, default=str))


cmds.file(SRC, open=True, force=True, ignoreVersion=True)
log("opened_source", ok=True)

cmds.loadPlugin("mtoa", quiet=True)
log("mtoa", loaded=cmds.pluginInfo("mtoa", q=True, loaded=True))

# --- probe aiToon attributes so we only set what exists -----------------------
probe = cmds.shadingNode("aiToon", asShader=True, name="__aiToon_probe__")
attrs = cmds.listAttr(probe, keyable=True) or []
report["aiToon_attrs"] = attrs
cmds.delete(probe)
log("aiToon_probe", attr_count=len(attrs), attrs=attrs[:40])


def base_colour(material):
    """Best-effort base colour of a material (Lambert / standardSurface / openPBR)."""
    for attr in ("color", "base_color", "baseColor"):
        if cmds.attributeQuery(attr, node=material, exists=True):
            conn = cmds.listConnections(material + "." + attr, source=True, destination=False)
            if conn:
                return None, conn[0]  # textured: leave the colour to the connection
            return cmds.getAttr(material + "." + attr)[0], None
    return (0.6, 0.6, 0.6), None


# --- assign aiToon per shading group -----------------------------------------
swapped = {}
skipped = []
shapes = cmds.ls(type="mesh", long=True, noIntermediate=True) or []

for shape in shapes:
    sgs = [s for s in (cmds.listConnections(shape, type="shadingEngine") or []) if s != "initialShadingGroup"]
    if not sgs:
        skipped.append(shape)
        continue
    sg = sgs[0]
    if sg not in swapped:
        mats = cmds.listConnections(sg + ".surfaceShader", source=True, destination=False) or []
        mat = mats[0] if mats else sg
        colour, texture = base_colour(mat) if mats else ((0.6, 0.6, 0.6), None)
        base = sg.replace("SG", "").replace(":", "_").replace("|", "_") or "shader"
        toon = cmds.shadingNode("aiToon", asShader=True, name="AIT_" + base)
        # aiToon (mtoa 5.6.2) exposes the base colour as `baseColor`, not `color`.
        if colour is not None and cmds.attributeQuery("baseColor", node=toon, exists=True):
            cmds.setAttr(toon + ".baseColor", *colour, type="double3")
        elif texture is not None and cmds.attributeQuery("baseColor", node=toon, exists=True):
            cmds.connectAttr(texture + ".outColor", toon + ".baseColor", force=True)
        new_sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="AIT_" + base + "SG")
        cmds.connectAttr(toon + ".outColor", new_sg + ".surfaceShader", force=True)
        swapped[sg] = {"toon": toon, "sg": new_sg, "source_material": mat, "colour": colour}
    cmds.sets(shape, edit=True, forceElement=swapped[sg]["sg"])

log("assign", shapes_total=len(shapes), skipped=len(skipped), groups_swapped=len(swapped))
report["swapped"] = {k: {kk: vv for kk, vv in v.items()} for k, v in swapped.items()}

# --- make the shot cameras renderable (flag was off in the v09 handoff) ------
for cam, _frame, _name in SHOTS:
    for shape in cmds.listRelatives(cam, shapes=True, type="camera") or []:
        cmds.setAttr(shape + ".renderable", 1)
log("renderable", cameras=[c for c, _f, _n in SHOTS])

# --- save the NEW version (never the source) ---------------------------------
cmds.file(rename=OUT)
cmds.file(save=True, type="mayaBinary", force=True)
log("saved_v10", path=OUT, exists=os.path.exists(OUT), size=os.path.getsize(OUT) if os.path.exists(OUT) else 0)

# --- Arnold render, one still per shot ---------------------------------------
cmds.setAttr("defaultRenderGlobals.currentRenderer", "arnold", type="string")
cmds.setAttr("defaultResolution.width", RES_W)
cmds.setAttr("defaultResolution.height", RES_H)
cmds.setAttr("defaultRenderGlobals.animation", 0)
cmds.setAttr("defaultRenderGlobals.imageFormat", 32)  # PNG
os.makedirs(STILLS, exist_ok=True)

for cam, frame, name in SHOTS:
    cmds.currentTime(frame)
    cmds.setAttr("defaultRenderGlobals.imageFilePrefix", name, type="string")
    try:
        cmds.render(cam, x=RES_W, y=RES_H)
        ok = True
        err = None
    except Exception as e:  # noqa: BLE001
        ok, err = False, str(e)
    images_dir = os.path.join(cmds.workspace(q=True, rootDirectory=True), cmds.workspace(fileRuleEntry="images"))
    # Maya writes per-camera subfolders (images\<CamShape>\<name>.png); search recursively.
    found = sorted(glob.glob(os.path.join(images_dir, "**", name + "*.png"), recursive=True), key=os.path.getmtime)
    dest = os.path.join(STILLS, name + ".png")
    if found:
        shutil.copyfile(found[-1], dest)
    report["renders"].append({"camera": cam, "frame": frame, "ok": ok, "error": err,
                              "rendered_from": found[-1] if found else None, "still": dest if found else None})
    log("render", camera=cam, frame=frame, ok=ok, error=err, still=dest if found else None)

with open(REPORT, "w") as f:
    json.dump(report, f, indent=2, default=str)
print("REPORT", REPORT)
maya.standalone.uninitialize()
