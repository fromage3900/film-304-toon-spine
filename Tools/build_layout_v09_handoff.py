"""v09: 64A hero-swatter + 66A arrow polish on the handoff scene."""
from __future__ import annotations

import json

import maya.cmds as cmds

ROOT = "G:/film-304-toon-spine"
SCENE = ROOT + "/Saved/Scenes/L_Scene62-66_BS.mb"
REPORT = ROOT + "/Saved/Scenes/layout_62_66_v09_handoff_report.json"
report = {}


def main():
    cmds.file(SCENE, open=True, force=True, ignoreVersion=True)
    cmds.currentTime(1)

    # 64A: bring the hero swatter into the hand and scale it like the board
    hero = "Layout_HeroSwatter"
    if cmds.objExists(hero):
        cmds.setAttr(hero + ".scale", 0.75, 0.75, 0.75)
        cmds.xform(hero, ws=True, ro=(0, 0, -90))
    # can slightly larger like the storyboard
    if cmds.objExists("Layout_SprayCan"):
        cmds.setAttr("Layout_SprayCan.scale", 1.8, 1.8, 1.8)
        cmds.xform("Layout_SprayCan", ws=True, t=(-110, 89.5, 15))

    # 66A: move the arrow to the board's upper-right and kill its shadow
    arrow = "Layout_ArrowMesh"
    if cmds.objExists(arrow):
        cmds.setAttr(arrow + ".scale", 0.45, 0.45, 0.45)
        cmds.xform(arrow, ws=True, t=(40, 170, -394))
        for sh in cmds.listRelatives(arrow, allDescendents=True, type="mesh") or []:
            try:
                cmds.setAttr(sh + ".castsShadows", False)
            except Exception:
                pass
    cmds.currentTime(1)
    cmds.file(save=True, type="mayaBinary", force=True)
    report["scene"] = SCENE
    report["saved"] = True
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print("V09_HANDOFF_DONE")


if __name__ == "__main__":
    main()
