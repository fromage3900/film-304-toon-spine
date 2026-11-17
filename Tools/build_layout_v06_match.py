"""v06: final board-match fixes for 62, 63, and 64."""
from __future__ import annotations

import json
import traceback

import maya.cmds as cmds

ROOT = "G:/film-304-toon-spine"
V05 = ROOT + "/Saved/Scenes/Shepherd_Brennan_LayoutScene(62-66)_BS_v05_match.mb"
V06 = ROOT + "/Saved/Scenes/Shepherd_Brennan_LayoutScene(62-66)_BS_v06_match.mb"
REPORT = ROOT + "/Saved/Scenes/layout_62_66_v06_match_report.json"
report = {"items": []}


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
    cmds.file(V05, open=True, force=True, ignoreVersion=True)
    cmds.currentTime(1)

    # 62: centre the swatter like the panel
    if cmds.objExists("Layout_Swatter"):
        cmds.xform("Layout_Swatter", ws=True, t=(-25, 76.5, 5))

    # 63: back off slightly so shoulders/collar are included
    set_cam("Cam_Shot63A1", "Cam_Shot63A_Target", (50, 168, 170), (0, 160, 0), 75, (49, 72))
    set_cam("Cam_Shot63B1", "Cam_Shot63B_Target", (55, 165, 180), (0, 158, 0), 70, (73, 120))

    # 64A: arms out (true ready stance), feet spread, desk swatter hidden
    for f in (121, 144):
        for c in ("David:FKShoulder_L", "David:FKShoulder_R"):
            for a, v in (("rotateX", 0), ("rotateY", 0), ("rotateZ", 0)):
                key(c, a, f, v)
        key("David:FKElbow_L", "rotateY", f, 20)
        key("David:FKElbow_R", "rotateY", f, 20)
        key("David:FKSpine1_M", "rotateX", f, 10)
        key("David:FKChest_M", "rotateX", f, 5)
        key("David:FKHead_M", "rotateX", f, -8)
    for side, z in (("L", 15), ("R", -15)):
        node = "David:IKLegHandle_" + side
        for f in (121, 144):
            key(node, "translateZ", f, z)
            key(node, "translateY", f, 0)
    # hide the desk swatter while the hero swatter is in hand
    if cmds.objExists("Layout_Swatter"):
        for f, v in ((1, 1), (120, 1), (121, 0), (192, 0), (193, 1)):
            key("Layout_Swatter", "visibility", f, v)

    # 64B: stronger arm swing
    for f in (145, 192):
        key("David:FKShoulder_L", "rotateY", f, 55)
        key("David:FKShoulder_R", "rotateY", f, 55)
        key("David:FKShoulder_L", "rotateZ", f, 50)
        key("David:FKShoulder_R", "rotateZ", f, -50)
        key("David:FKElbow_L", "rotateY", f, 75)
        key("David:FKElbow_R", "rotateY", f, 75)

    cmds.currentTime(1)
    cmds.file(rename=V06)
    cmds.file(save=True, type="mayaBinary", force=True)
    report["scene"] = V06
    report["saved"] = True
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print("V06_MATCH_DONE")


if __name__ == "__main__":
    main()
