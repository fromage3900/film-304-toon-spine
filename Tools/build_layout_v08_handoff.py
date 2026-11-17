"""v08: final 62/64/66 fixes and the L_Scene62-66_BS handoff scene."""
from __future__ import annotations

import json

import maya.cmds as cmds

ROOT = "G:/film-304-toon-spine"
V07 = ROOT + "/Saved/Scenes/Shepherd_Brennan_LayoutScene(62-66)_BS_v07_match.mb"
OUT = ROOT + "/Saved/Scenes/L_Scene62-66_BS.mb"
REPORT = ROOT + "/Saved/Scenes/layout_62_66_v08_handoff_report.json"
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
    cmds.file(V07, open=True, force=True, ignoreVersion=True)
    cmds.currentTime(1)

    # 62: swatter closer to lower-centre
    if cmds.objExists("Layout_Swatter"):
        cmds.xform("Layout_Swatter", ws=True, t=(-20, 76.5, 5))

    # 66A: shrink the wall arrow to the board scale
    if cmds.objExists("Layout_ArrowMesh"):
        cmds.setAttr("Layout_ArrowMesh.scale", 0.55, 0.55, 0.55)
        cmds.xform("Layout_ArrowMesh", ws=True, t=(25, 195, -394))

    # 66B: subtle handheld jolt on the slam
    cam = "Cam_Shot66B1"
    if cmds.objExists(cam):
        for f, x, y in ((241, 0, 30), (252, 3, 32), (254, -2, 28), (258, 0, 30), (288, 0, 30)):
            key(cam, "translateX", f, x)
            key(cam, "translateY", f, y)

    # 64A/B: make the hero swatter read in the ready pose
    hero = "Layout_HeroSwatter"
    if cmds.objExists(hero):
        cmds.setAttr(hero + ".scale", 1.2, 1.2, 1.2)
        cmds.xform(hero, ws=True, ro=(0, 0, 20))
        for f, v in ((1, 0), (121, 1), (192, 1), (193, 0)):
            key(hero, "visibility", f, v)

    # Shorten to the scene range and save under the group filename
    cmds.playbackOptions(minTime=1, maxTime=288, animationStartTime=1, animationEndTime=288)
    cmds.currentTime(1)
    cmds.file(rename=OUT)
    cmds.file(save=True, type="mayaBinary", force=True)
    report["scene"] = OUT
    report["saved"] = True
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print("V08_HANDOFF_DONE")


if __name__ == "__main__":
    main()
