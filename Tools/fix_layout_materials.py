"""Fix layout readability: assign flat materials, hide stray spider mesh,
replace the back-wall plane with a lit box, add ambient/background.
"""
from __future__ import annotations

import json
import traceback

import maya.cmds as cmds

OUT = "G:/film-304-toon-spine/Saved/Scenes/layout_material_pass.json"


def mat(name, rgb):
    if cmds.objExists(name):
        return name
    m = cmds.shadingNode("lambert", asShader=True, name=name)
    cmds.setAttr(m + ".color", rgb[0], rgb[1], rgb[2], type="double3")
    sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=name + "_SG")
    cmds.connectAttr(m + ".outColor", sg + ".surfaceShader")
    return m


def assign(m, nodes):
    sgs = cmds.listConnections(m, type="shadingEngine") or []
    if not sgs:
        return
    sg = sgs[0]
    for n in nodes:
        if not n or not cmds.objExists(n):
            continue
        try:
            cmds.sets(n, edit=True, forceElement=sg)
        except Exception:
            pass


def main() -> None:
    out = {"assigned": {}, "errors": []}
    try:
        skin = mat("Layout_Skin", (0.70, 0.52, 0.40))
        shirt = mat("Layout_Shirt", (0.20, 0.28, 0.42))
        pants = mat("Layout_Pants", (0.10, 0.10, 0.13))
        hair = mat("Layout_Hair", (0.07, 0.045, 0.03))
        shoe = mat("Layout_Shoe", (0.03, 0.03, 0.035))
        teeth = mat("Layout_Teeth", (0.90, 0.88, 0.82))
        eye = mat("Layout_Eye", (0.85, 0.85, 0.82))
        eye_dark = mat("Layout_EyeDark", (0.035, 0.025, 0.02))
        cornea = mat("Layout_Cornea", (0.90, 0.90, 0.88))
        spid = mat("Layout_SpiderMat", (0.13, 0.07, 0.035))
        setmat = mat("Layout_SetMat", (0.62, 0.62, 0.62))
        midmat = mat("Layout_Mid", (0.34, 0.34, 0.36))

        # David meshes by role.
        groups = {"skin": [], "shirt": [], "pants": [], "hair": [], "shoe": [],
                  "teeth": [], "eye": [], "eye_dark": [], "cornea": []}
        for m in cmds.ls(type="mesh", long=True) or []:
            name = m.split("|")[-1]
            if "Orig" in name or "Base" in name:
                continue
            tr = (cmds.listRelatives(m, parent=True) or [m])[0]
            low = name.lower()
            if "shirt" in low:
                groups["shirt"].append(tr)
            elif "pants" in low:
                groups["pants"].append(tr)
            elif "hair" in low or "brow" in low or "lash" in low:
                groups["hair"].append(tr)
            elif "shoe" in low or "boot" in low:
                groups["shoe"].append(tr)
            elif "teeth" in low or "tongue" in low:
                groups["teeth"].append(tr)
            elif "cornea" in low:
                groups["cornea"].append(tr)
            elif "eyelid" in low or "lidregion" in low:
                groups["skin"].append(tr)
            elif "eye" in low:
                groups["eye_dark"].append(tr)
            elif tr.startswith("David") or "David:" in tr or "body" in low or "head" in low or "chin" in low:
                groups["skin"].append(tr)
        assign(skin, groups["skin"])
        assign(shirt, groups["shirt"])
        assign(pants, groups["pants"])
        assign(hair, groups["hair"])
        assign(shoe, groups["shoe"])
        assign(teeth, groups["teeth"])
        assign(eye, groups["eye"])
        assign(eye_dark, groups["eye_dark"])
        assign(cornea, groups["cornea"])
        out["assigned"] = {k: len(v) for k, v in groups.items()}

        # Spider: all referenced meshes.
        spider_meshes = []
        for m in cmds.ls(type="mesh", long=True) or []:
            name = m.split("|")[-1]
            if "Orig" in name or "Base" in name:
                continue
            tr = (cmds.listRelatives(m, parent=True) or [m])[0]
            if tr.startswith("Spider:") or "Spider:" in tr:
                spider_meshes.append(tr)
        assign(spid, spider_meshes)
        out["spider_assigned"] = len(spider_meshes)

        # Hide the stray stretched torso mesh (the real body/legs remain).
        for n in ("Spider:wolfSpider_Body_Torso_LOWRES_geo",
                  "Spider:wolfSpider_Body_Thorax_LOWRES_geo"):
            if cmds.objExists(n):
                try:
                    cmds.setAttr(n + ".visibility", False)
                    out.setdefault("hidden", []).append(n)
                except Exception:
                    out["errors"].append("hide " + n)

        # Replace the back-wall plane with a box (front normal +Z).
        if cmds.objExists("Layout_BackWall"):
            try:
                cmds.setAttr("Layout_BackWall.visibility", False)
            except Exception:
                pass
        if not cmds.objExists("Layout_BackWallBox"):
            wall = cmds.polyCube(name="Layout_BackWallBox", width=900, height=420, depth=4)[0]
            cmds.xform(wall, ws=True, t=(0, 210, -192))
            assign(midmat, [wall])
            if cmds.objExists("Layout_Office_Set"):
                cmds.parent(wall, "Layout_Office_Set", absolute=True)
            out["back_wall_box"] = wall

        # Background + ambient.
        try:
            cmds.setAttr("defaultRenderGlobals.imageBackground", 0.82, 0.82, 0.82, type="double3")
        except Exception:
            pass
        if not cmds.objExists("Layout_Ambient"):
            cmds.ambientLight(name="Layout_Ambient", intensity=0.65)
        out["ok"] = True
    except Exception:
        out["fatal"] = traceback.format_exc()
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print("MATERIAL_PASS_DONE", json.dumps({k: out.get(k) for k in ("ok", "assigned", "spider_assigned", "fatal")}))


if __name__ == "__main__":
    main()
