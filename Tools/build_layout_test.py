"""One-frame layout test: import David, scale to 180 cm, frame a close-up.

Run through dcc-mcp Maya headless. Saves _layout_test.mb and a report.
"""
from __future__ import annotations

import json
import traceback

import maya.cmds as cmds

SRC = "G:/film-304-toon-spine/Saved/OfflineIntake/Source/David_Rig_v1.51.mb"
OUT_SCENE = "G:/film-304-toon-spine/Saved/Scenes/_layout_test.mb"
OUT_JSON = "G:/film-304-toon-spine/Saved/Scenes/_layout_test.json"
TARGET_HEIGHT_CM = 180.0


def force_visible(node: str) -> None:
    if not cmds.objExists(node):
        return
    conns = cmds.listConnections(node + ".visibility", source=True, destination=False) or []
    for c in conns:
        for plug in ("outValue", "output", "visibility"):
            try:
                cmds.disconnectAttr(c + "." + plug, node + ".visibility")
                break
            except Exception:
                continue
    try:
        cmds.setAttr(node + ".visibility", lock=False)
    except Exception:
        pass
    try:
        cmds.setAttr(node + ".visibility", True)
    except Exception:
        pass


def force_visible_tree(node: str) -> None:
    """Show a node and every ancestor group."""
    if not cmds.objExists(node):
        return
    chain = [node]
    cur = node
    while True:
        parents = cmds.listRelatives(cur, parent=True, fullPath=False) or []
        if not parents:
            break
        cur = parents[0]
        chain.append(cur)
    for n in reversed(chain):
        force_visible(n)


def visible_bbox():
    ms = []
    for m in cmds.ls(type="mesh", long=True) or []:
        name = m.split("|")[-1]
        if "Orig" in name or "Base" in name:
            continue
        tr = (cmds.listRelatives(m, parent=True) or [m])[0]
        try:
            if cmds.getAttr(tr + ".visibility"):
                ms.append(m)
        except Exception:
            pass
    return [round(v, 2) for v in cmds.exactWorldBoundingBox(ms)] if ms else None


def main() -> None:
    out = {"steps": []}
    try:
        cmds.file(new=True, force=True)
        cmds.currentUnit(linear="centimeter")
        cmds.currentUnit(time="film")
        cmds.playbackOptions(minTime=1, maxTime=48, animationStartTime=1, animationEndTime=48)

        cmds.file(SRC, i=True, namespace="David", mergeNamespacesOnClash=False,
                  ignoreVersion=True, type="mayaBinary")
        root = (cmds.ls("*:Group", type="transform") or [None])[0]
        out["root"] = root
        if not root:
            raise RuntimeError("No imported root group")

        # Reset FK controls to default.
        for c in cmds.ls("*:FK*", type="transform") or []:
            for attr in ("translateX", "translateY", "translateZ",
                         "rotateX", "rotateY", "rotateZ"):
                if not cmds.attributeQuery(attr, node=c, exists=True):
                    continue
                try:
                    if not cmds.getAttr(c + "." + attr, lock=True):
                        cmds.setAttr(c + "." + attr, 0)
                except Exception:
                    pass

        # Show the real body and partial body; keep helper meshes hidden.
        for n in cmds.ls("*:David_Body_GEO", type="transform") or []:
            force_visible_tree(n)
        for n in cmds.ls("*:David_PartialBody_GEO", type="transform") or []:
            force_visible_tree(n)
        for n in cmds.ls("*:FaceGroup", type="transform") or []:
            force_visible_tree(n)
        for n in cmds.ls("*:FaceDeformationSystem", type="transform") or []:
            force_visible_tree(n)
        for n in cmds.ls("*:Geometry", type="transform") or []:
            force_visible_tree(n)
        # Show head/hair/face meshes and their ancestors.
        for m in cmds.ls(type="mesh", long=True) or []:
            name = m.split("|")[-1]
            if any(k in name for k in ("Hair_GEO", "Eyebrows", "Eye_", "Eyelash", "Teeth", "Tongue", "Cornea", "Chin")):
                tr = (cmds.listRelatives(m, parent=True) or [m])[0]
                force_visible_tree(tr)
        for n in cmds.ls("*:David_Body_breathe", type="transform") or []:
            try:
                cmds.setAttr(n + ".visibility", False)
            except Exception:
                pass
        for n in cmds.ls("*:David_Body_GEOBase*", type="transform") or []:
            try:
                cmds.setAttr(n + ".visibility", False)
            except Exception:
                pass

        # The imported root has locked scale/translate. Wrap it in a layout root.
        layout_root = cmds.createNode("transform", name="Layout_David_Root")
        cmds.parent(root, layout_root, absolute=True)
        out["layout_root"] = layout_root

        b0 = visible_bbox()
        out["bbox_before_scale"] = b0
        height = b0[4] - b0[1]
        scale = TARGET_HEIGHT_CM / height
        cmds.setAttr(layout_root + ".scale", scale, scale, scale)
        cmds.refresh(force=True)
        b1 = visible_bbox()
        out["bbox_scaled"] = b1
        out["scale"] = round(scale, 4)

        # Move feet to y=0, center x/z.
        cmds.setAttr(layout_root + ".translateY", -b1[1])
        cmds.setAttr(layout_root + ".translateX", -(b1[0] + b1[3]) / 2.0)
        cmds.setAttr(layout_root + ".translateZ", -(b1[2] + b1[5]) / 2.0)
        cmds.refresh(force=True)
        b2 = visible_bbox()
        out["bbox_positioned"] = b2

        # Simple set: floor + back wall.
        floor = cmds.polyPlane(name="Layout_Floor", width=800, height=800,
                               subdivisionsX=1, subdivisionsY=1)[0]
        cmds.xform(floor, ws=True, t=(0, 0, 0))
        wall = cmds.polyPlane(name="Layout_Wall", width=800, height=400,
                              subdivisionsX=1, subdivisionsY=1)[0]
        cmds.xform(wall, ws=True, t=(0, 200, -180), ro=(90, 0, 0))

        # Camera: 3/4 close-up at eye height.
        cam = cmds.camera(name="Cam_Test")[0]
        cmds.setAttr(cam + ".focalLength", 85)
        cmds.setAttr(cam + ".filmFit", 1)  # horizontal
        cmds.setAttr(cam + ".horizontalFilmAperture", 36)
        cmds.xform(cam, ws=True, t=(55, 168, 175))
        target = cmds.spaceLocator(name="Cam_Test_Target")[0]
        cmds.xform(target, ws=True, t=(0, 158, 0))
        cmds.aimConstraint(target, cam, aimVector=(0, 0, -1), upVector=(0, 1, 0),
                           worldUpType="vector", worldUpVector=(0, 1, 0))

        # Lights: key + fill.
        key_shape = cmds.directionalLight(name="Layout_Key_Light", intensity=2.2)[0]
        key_tr = cmds.listRelatives(key_shape, parent=True)[0]
        cmds.setAttr(key_tr + ".rotateX", -35)
        cmds.setAttr(key_tr + ".rotateY", -25)
        fill_shape = cmds.directionalLight(name="Layout_Fill_Light", intensity=0.6)[0]
        fill_tr = cmds.listRelatives(fill_shape, parent=True)[0]
        cmds.setAttr(fill_tr + ".rotateX", -20)
        cmds.setAttr(fill_tr + ".rotateY", 150)
        cmds.setAttr("defaultRenderGlobals.currentRenderer", "mayaSoftware", type="string")

        cmds.file(rename=OUT_SCENE)
        cmds.file(save=True, type="mayaBinary", force=True)
        out["scene"] = OUT_SCENE
        out["cam"] = cam
        out["ok"] = True
    except Exception:
        out["fatal"] = traceback.format_exc()
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print("LAYOUT_TEST_DONE", json.dumps({k: out.get(k) for k in
          ("ok", "scale", "bbox_scaled", "bbox_positioned", "fatal")}))


if __name__ == "__main__":
    main()
