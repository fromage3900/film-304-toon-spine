"""Final layout polish: ready-stance arms and spider screen-left."""
from __future__ import annotations

import maya.cmds as cmds


def set_rot(ctrl, rx=0.0, ry=0.0, rz=0.0):
    if not cmds.objExists(ctrl):
        return
    for attr, val in (("rotateX", rx), ("rotateY", ry), ("rotateZ", rz)):
        if cmds.attributeQuery(attr, node=ctrl, exists=True):
            try:
                if not cmds.getAttr(ctrl + "." + attr, lock=True):
                    cmds.setAttr(ctrl + "." + attr, val)
            except Exception:
                pass


def key_all(frame):
    for c in cmds.ls("FK*", type="transform") or []:
        for attr in ("rotateX", "rotateY", "rotateZ"):
            if cmds.attributeQuery(attr, node=c, exists=True):
                try:
                    cmds.setKeyframe(c, attribute=attr, time=frame)
                except Exception:
                    pass


def main() -> None:
    # 64A ready stance: arms out and slightly forward.
    set_rot("FKSpine1_M", 12, 0, 0)
    set_rot("FKChest_M", 6, 0, 0)
    set_rot("FKNeck_M", -6, 0, 0)
    set_rot("FKHead_M", -8, 0, 0)
    set_rot("FKShoulder_L", 0, 10, 25)
    set_rot("FKShoulder_R", 0, 10, -25)
    set_rot("FKElbow_L", 0, 15, 0)
    set_rot("FKElbow_R", 0, 15, 0)
    set_rot("FKJaw_M", 0, 0, 0)
    key_all(121)
    key_all(144)

    # Spider at screen-left, still descending to the swatter.
    if cmds.objExists("Layout_Spider_Root"):
        cmds.setAttr("Layout_Spider_Root.translateX", -25)
        cmds.setKeyframe("Layout_Spider_Root", attribute="translateX", time=48)
    if cmds.objExists("Layout_SilkThread"):
        cmds.setAttr("Layout_SilkThread.translateX", -25)

    cmds.file(save=True, type="mayaBinary", force=True)
    print("FINAL_POLISH_SAVED")


if __name__ == "__main__":
    main()
