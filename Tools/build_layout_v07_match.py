"""v07: final 64A/B board-match and hero-prop fixes."""
from __future__ import annotations

import json

import maya.cmds as cmds

ROOT = "G:/film-304-toon-spine"
V06 = ROOT + "/Saved/Scenes/Shepherd_Brennan_LayoutScene(62-66)_BS_v06_match.mb"
V07 = ROOT + "/Saved/Scenes/Shepherd_Brennan_LayoutScene(62-66)_BS_v07_match.mb"
REPORT = ROOT + "/Saved/Scenes/layout_62_66_v07_match_report.json"
report = {}


def key(node, attr, frame, value):
    if not cmds.objExists(node) or not cmds.attributeQuery(attr, node=node, exists=True):
        return
    try:
        cmds.setAttr(node + "." + attr, value)
        cmds.setKeyframe(node, attribute=attr, time=frame)
    except Exception:
        pass


def main():
    cmds.file(V06, open=True, force=True, ignoreVersion=True)
    cmds.currentTime(1)

    # 64A/B face the can (left)
    for f in (121, 144, 145, 192):
        key("Layout_David_Root", "rotateY", f, 90)

    # 64A crouch: lower the root, keep the feet near the floor, spread the stance
    for f in (121, 144):
        key("Layout_David_Root", "translateY", f, -15)
    for side, z in (("L", 15), ("R", -15)):
        node = "David:IKLegHandle_" + side
        for f in (121, 144):
            key(node, "translateZ", f, z)
            key(node, "translateY", f, 7)
    # 64B back to normal height for the run
    for f in (145, 192):
        key("Layout_David_Root", "translateY", f, 0)

    # larger spray can, like the board
    if cmds.objExists("Layout_SprayCan"):
        cmds.setAttr("Layout_SprayCan.scale", 1.5, 1.5, 1.5)
        cmds.xform("Layout_SprayCan", ws=True, t=(-110, 89.5, 15))

    # hero swatter to the camera-side (left) hand, readable scale
    if cmds.objExists("Layout_HeroSwatter") and cmds.objExists("David:Wrist_L"):
        cmds.currentTime(130)
        p = cmds.xform("David:Wrist_L", q=True, ws=True, t=True)
        cmds.xform("Layout_HeroSwatter", ws=True, t=p)
        try:
            cmds.parent("Layout_HeroSwatter", "David:Wrist_L", absolute=True)
        except Exception:
            pass
        cmds.xform("Layout_HeroSwatter", ws=True, ro=(0, 0, 20))
        cmds.setAttr("Layout_HeroSwatter.scale", 1.0, 1.0, 1.0)
        for f, v in ((1, 0), (121, 1), (192, 1), (193, 0)):
            key("Layout_HeroSwatter", "visibility", f, v)

    # 64A camera low enough to see the crouch
    if cmds.objExists("Cam_Shot64A1"):
        cmds.setAttr("Cam_Shot64A1.focalLength", 35)
        cmds.xform("Cam_Shot64A1", ws=True, t=(0, 90, 330))
        if cmds.objExists("Cam_Shot64A_Target"):
            cmds.xform("Cam_Shot64A_Target", ws=True, t=(0, 90, 0))
        for f in (121, 144):
            for a, v in (("translateX", 0), ("translateY", 90), ("translateZ", 330)):
                key("Cam_Shot64A1", a, f, v)
            for a, v in (("translateX", 0), ("translateY", 90), ("translateZ", 0)):
                key("Cam_Shot64A_Target", a, f, v)

    cmds.currentTime(1)
    cmds.file(rename=V07)
    cmds.file(save=True, type="mayaBinary", force=True)
    report["scene"] = V07
    report["saved"] = True
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print("V07_MATCH_DONE")


if __name__ == "__main__":
    main()
