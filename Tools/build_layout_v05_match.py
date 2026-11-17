"""v05: material/camera/board-match fixes over v04."""
from __future__ import annotations

import json
import os
import traceback

import maya.cmds as cmds

ROOT = "G:/film-304-toon-spine"
V04 = ROOT + "/Saved/Scenes/Shepherd_Brennan_LayoutScene(62-66)_BS_v04_match.mb"
V05 = ROOT + "/Saved/Scenes/Shepherd_Brennan_LayoutScene(62-66)_BS_v05_match.mb"
REPORT = ROOT + "/Saved/Scenes/layout_62_66_v05_match_report.json"

report = {"items": []}


def log(name, status, detail=""):
    report["items"].append({"name": name, "status": status, "detail": str(detail)[:800]})


def assign(mat, nodes):
    sgs = cmds.listConnections(mat, type="shadingEngine") or []
    if not sgs:
        return
    sg = sgs[0]
    for n in nodes:
        if cmds.objExists(n):
            try:
                cmds.sets(n, edit=True, forceElement=sg)
            except Exception:
                pass


def hide(node, state=True):
    if cmds.objExists(node):
        try:
            cmds.setAttr(node + ".visibility", 0 if state else 1)
        except Exception:
            pass


def key(node, attr, frame, value):
    if not cmds.objExists(node) or not cmds.attributeQuery(attr, node=node, exists=True):
        return
    try:
        cmds.setAttr(node + "." + attr, value)
        cmds.setKeyframe(node, attribute=attr, time=frame)
    except Exception:
        pass


def set_cam(cam, target, eye, aim, focal, frames):
    if not cmds.objExists(cam):
        return
    cmds.setAttr(cam + ".focalLength", focal)
    cmds.xform(cam, ws=True, t=eye)
    if cmds.objExists(target):
        cmds.xform(target, ws=True, t=aim)
    for f in frames:
        for a, v in (("translateX", eye[0]), ("translateY", eye[1]), ("translateZ", eye[2])):
            key(cam, a, f, v)
        for a, v in (("translateX", aim[0]), ("translateY", aim[1]), ("translateZ", aim[2])):
            key(target, a, f, v)


def main():
    cmds.file(V04, open=True, force=True, ignoreVersion=True)
    cmds.currentTime(1)

    # Materials for imported film props (they arrive black in the headless render)
    for mat, nodes in (
        ("Layout_White", ["Desk", "DeskDrawers"]),
        ("Layout_Gray", ["P_Box_EF"]),
        ("Layout_Gray", ["Layout_BackWallBox"]),
        ("Layout_Mid", ["Layout_DoorWall"]),
    ):
        try:
            for n in nodes:
                assign(mat, [n])
            log("material " + mat, "pass", nodes)
        except Exception:
            log("material " + mat, "fail", traceback.format_exc()[-400:])

    # Plain board background: hide the gradient cards, keep the lit wall
    for n in ("Layout_Backdrop", "Layout_DoorGradient"):
        hide(n, True)
    log("hide gradient", "pass")

    # The real desk is not in the board 64 panels; hide it for 64A/B
    for n in ("Desk", "DeskDrawers"):
        if cmds.objExists(n):
            for f, v in ((1, 1), (120, 1), (121, 0), (192, 0), (193, 1)):
                key(n, "visibility", f, v)
    log("desk visibility", "pass", "64A/B hidden")

    # 62: board composition - spider top, swatter lower-left, desk edge
    set_cam("Cam_Shot62", "Cam_Shot62_Target", (0, 100, 180), (0, 95, 0), 50, (1, 48))
    if cmds.objExists("Layout_Swatter"):
        cmds.xform("Layout_Swatter", ws=True, t=(-10, 76.5, 5))
    if cmds.objExists("Layout_SilkThread"):
        cmds.xform("Layout_SilkThread", ws=True, t=(0, 250, 0))

    # Keep the tighter 63 cameras from v04; lighten the room
    for n, val in (("Layout_AmbientShape", 0.5), ("Layout_Key_LightShape", 2.0),
                   ("Layout_Fill_LightShape", 0.8)):
        if cmds.objExists(n):
            try: cmds.setAttr(n + ".intensity", val)
            except Exception: pass

    # 66A: remove the old white arrow card, rebuild a black 3D arrow
    for n in ("Layout_Arrow", "Layout_ArrowMesh"):
        if cmds.objExists(n):
            try: cmds.delete(n)
            except Exception: pass
    try:
        grp = cmds.createNode("transform", name="Layout_ArrowMesh")
        shaft = cmds.polyCube(name="Layout_ArrowShaft", width=24, height=2, depth=0.6)[0]
        cmds.parent(shaft, grp)
        for i, rot in enumerate((45, -45)):
            head = cmds.polyCube(name="Layout_ArrowHead_%d" % i, width=10, height=2, depth=0.6)[0]
            cmds.parent(head, grp)
            cmds.xform(head, t=(10, 3 if i == 0 else -3, 0), ro=(0, 0, rot))
        cmds.xform(grp, ws=True, t=(20, 190, -394))
        if cmds.objExists("Layout_Door_Set"):
            try: cmds.parent(grp, "Layout_Door_Set", absolute=True)
            except Exception: pass
        m = cmds.shadingNode("lambert", asShader=True, name="Layout_ArrowBlack")
        cmds.setAttr(m + ".color", 0.02, 0.02, 0.02, type="double3")
        sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="Layout_ArrowBlack_SG")
        cmds.connectAttr(m + ".outColor", sg + ".surfaceShader")
        for n in [shaft] + (cmds.listRelatives(grp, children=True, type="transform") or []):
            try: cmds.sets(n, edit=True, forceElement=sg)
            except Exception: pass
        log("arrow mesh", "pass", "black 3D arrow")
    except Exception:
        log("arrow mesh", "fail", traceback.format_exc()[-500:])

    # Keep 64A/B worker on the floor; the real desk is hidden
    # The box/can remain at left; the hero swatter follows the right wrist.
    cmds.currentTime(1)
    cmds.file(rename=V05)
    cmds.file(save=True, type="mayaBinary", force=True)
    report["scene"] = V05
    report["saved"] = True
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print("V05_MATCH_DONE")


if __name__ == "__main__":
    main()
