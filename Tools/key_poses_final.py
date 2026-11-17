"""Key the per-shot David poses on the opened (non-namespaced) rig."""
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


def base_pose():
    set_rot("FKSpine1_M", 0, 0, 0)
    set_rot("FKSpine2_M", 0, 0, 0)
    set_rot("FKChest_M", 0, 0, 0)
    set_rot("FKNeck_M", 0, 0, 0)
    set_rot("FKHead_M", 0, 0, 0)
    set_rot("FKShoulder_L", 0, 70, 8)
    set_rot("FKShoulder_R", 0, 70, -8)
    set_rot("FKElbow_L", 0, 25, 0)
    set_rot("FKElbow_R", 0, 25, 0)
    set_rot("FKWrist_L", 0, 0, 0)
    set_rot("FKWrist_R", 0, 0, 0)
    set_rot("FKJaw_M", 0, 0, 0)


def pose_angry():
    base_pose()
    set_rot("FKSpine1_M", 4, 0, 0)
    set_rot("FKChest_M", 3, 0, 0)
    set_rot("FKNeck_M", 4, 0, 0)
    set_rot("FKHead_M", 6, -8, 0)
    set_rot("FKShoulder_L", 0, 55, 12)
    set_rot("FKShoulder_R", 0, 55, -12)
    set_rot("FKElbow_L", 0, 40, 0)
    set_rot("FKElbow_R", 0, 40, 0)


def pose_rage():
    base_pose()
    set_rot("FKSpine1_M", 2, 0, 0)
    set_rot("FKChest_M", -4, 0, 0)
    set_rot("FKNeck_M", -2, 0, 0)
    set_rot("FKHead_M", -4, -6, 0)
    set_rot("FKShoulder_L", 0, 45, 18)
    set_rot("FKShoulder_R", 0, 45, -18)
    set_rot("FKElbow_L", 0, 55, 0)
    set_rot("FKElbow_R", 0, 55, 0)
    set_rot("FKJaw_M", 22, 0, 0)


def pose_ready():
    base_pose()
    set_rot("FKSpine1_M", 12, 0, 0)
    set_rot("FKChest_M", 6, 0, 0)
    set_rot("FKNeck_M", -6, 0, 0)
    set_rot("FKHead_M", -8, 0, 0)
    set_rot("FKShoulder_L", 0, 35, 30)
    set_rot("FKShoulder_R", 0, 35, -30)
    set_rot("FKElbow_L", 0, 45, 0)
    set_rot("FKElbow_R", 0, 45, 0)


def pose_run():
    base_pose()
    set_rot("FKSpine1_M", 18, 0, 0)
    set_rot("FKChest_M", 8, 0, 0)
    set_rot("FKNeck_M", -10, 0, 0)
    set_rot("FKHead_M", -10, 0, 0)
    set_rot("FKShoulder_L", 0, 55, 35)
    set_rot("FKShoulder_R", 0, 55, -35)
    set_rot("FKElbow_L", 0, 75, 0)
    set_rot("FKElbow_R", 0, 75, 0)


def pose_startled():
    base_pose()
    set_rot("FKSpine1_M", -10, 0, 0)
    set_rot("FKChest_M", -8, 0, 0)
    set_rot("FKNeck_M", 8, 0, 0)
    set_rot("FKHead_M", 12, 0, 0)
    set_rot("FKShoulder_L", 0, 40, 30)
    set_rot("FKShoulder_R", 0, 40, -30)
    set_rot("FKElbow_L", 0, 60, 0)
    set_rot("FKElbow_R", 0, 60, 0)


def key_all(frame):
    for c in cmds.ls("FK*", type="transform") or []:
        for attr in ("rotateX", "rotateY", "rotateZ"):
            if cmds.attributeQuery(attr, node=c, exists=True):
                try:
                    cmds.setKeyframe(c, attribute=attr, time=frame)
                except Exception:
                    pass


def main() -> None:
    shots = ((49, 72, pose_angry), (73, 120, pose_rage),
             (121, 144, pose_ready), (145, 192, pose_run),
             (241, 288, pose_startled))
    for f0, f1, fn in shots:
        fn()
        key_all(f0)
        key_all(f1)
    # Rage jaw beat after the generic pose keys.
    if cmds.objExists("FKJaw_M"):
        for f, v in ((73, 0), (84, 22), (112, 22), (120, 0)):
            cmds.setAttr("FKJaw_M.rotateX", v)
            cmds.setKeyframe("FKJaw_M", attribute="rotateX", time=f)
    cmds.file(save=True, type="mayaBinary", force=True)
    print("POSE_KEYS_SAVED")


if __name__ == "__main__":
    main()
