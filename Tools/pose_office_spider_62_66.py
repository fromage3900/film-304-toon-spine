"""Pose setup for Office Spider shots 62-66."""
try:
    import maya.standalone
    maya.standalone.initialize(name="python")
    STANDALONE = True
except RuntimeError:
    STANDALONE = False

import maya.cmds as cmds

if STANDALONE:
    SCENE = "G:/film-304-toon-spine/Saved/Scenes/OfficeSpider_Layout_62_66.mb"
    cmds.file(SCENE, open=True, force=True, ignoreVersion=True)
    print("Opened scene:", SCENE)


def set_attr(ctrl, attr, value):
    full = ctrl + "." + attr
    if not cmds.objExists(ctrl):
        return
    if not cmds.attributeQuery(attr, node=ctrl, exists=True):
        return
    try:
        if cmds.getAttr(full, lock=True):
            return
        cmds.setAttr(full, value)
    except Exception:
        pass


def set_rot(ctrl, rx=0, ry=0, rz=0):
    set_attr(ctrl, "rotateX", rx)
    set_attr(ctrl, "rotateY", ry)
    set_attr(ctrl, "rotateZ", rz)


def set_pos(ctrl, tx=0, ty=0, tz=0):
    set_attr(ctrl, "translateX", tx)
    set_attr(ctrl, "translateY", ty)
    set_attr(ctrl, "translateZ", tz)


def pose_neutral():
    print("Pose: Neutral (Shot 62 - typing at desk)")
    set_rot("David:FKRoot_M", 0, 0, 0)
    set_rot("David:FKSpine1_M", 0, 0, 0)
    set_rot("David:FKSpine2_M", 0, 0, 0)
    set_rot("David:FKChest_M", 0, 0, 0)
    set_rot("David:FKHead_M", 0, 0, 0)
    set_rot("David:FKNeck_M", 0, 0, 0)
    for side in ("L", "R"):
        set_rot("David:FKShoulder_" + side, 0, 0, 0)
        set_rot("David:FKElbow_" + side, 0, 0, 0)
        set_rot("David:FKWrist_" + side, 0, 0, 0)
        set_rot("David:FKHip_" + side, 0, 0, 0)
        set_rot("David:FKKnee_" + side, 0, 0, 0)
        set_rot("David:FKAnkle_" + side, 0, 0, 0)
    set_attr("David:ctrlBrow_L", "translateY", 0)
    set_attr("David:ctrlBrow_R", "translateY", 0)
    set_attr("David:ctrlMouth_M", "translateY", 0)
    set_attr("David:ctrlMouthCorner_L", "translateY", 0)
    set_attr("David:ctrlMouthCorner_R", "translateY", 0)


def pose_angry():
    print("Pose: Angry/Scowling (Shot 63)")
    set_attr("David:ctrlBrow_L", "translateY", -0.5)
    set_attr("David:ctrlBrow_R", "translateY", -0.5)
    set_attr("David:browInner_L", "translateY", -0.3)
    set_attr("David:browInner_R", "translateY", -0.3)
    set_attr("David:browOuter_L", "translateY", -0.2)
    set_attr("David:browOuter_R", "translateY", -0.2)
    set_attr("David:ctrlMouth_M", "translateY", -0.3)
    set_attr("David:ctrlMouthCorner_L", "translateY", -0.2)
    set_attr("David:ctrlMouthCorner_R", "translateY", -0.2)
    set_rot("David:FKHead_M", -5, 0, 0)
    set_rot("David:FKNeck_M", -3, 0, 0)
    set_rot("David:FKChest_M", -3, 0, 0)
    set_rot("David:FKShoulder_L", -20, 0, 10)
    set_rot("David:FKShoulder_R", -20, 0, -10)
    set_rot("David:FKElbow_L", 30, 0, 0)
    set_rot("David:FKElbow_R", 30, 0, 0)


def pose_ready_swing():
    print("Pose: Ready Stance + Swing (Shot 64)")
    set_pos("David:FKRoot_M", 0, -5, 0)
    set_rot("David:FKSpine1_M", 5, 0, 0)
    set_rot("David:FKSpine2_M", 3, 0, 0)
    set_rot("David:FKChest_M", 2, 0, 0)
    set_rot("David:FKHead_M", 15, 0, 0)
    set_rot("David:FKNeck_M", 10, 0, 0)
    set_rot("David:FKShoulder_R", -60, 0, -20)
    set_rot("David:FKElbow_R", 45, 0, 0)
    set_rot("David:FKWrist_R", 0, 0, -30)
    set_rot("David:FKShoulder_L", -30, 0, 30)
    set_rot("David:FKElbow_L", 20, 0, 0)
    set_rot("David:FKHip_L", 0, 0, -10)
    set_rot("David:FKHip_R", 0, 0, 10)
    set_rot("David:FKKnee_L", 15, 0, 0)
    set_rot("David:FKKnee_R", 15, 0, 0)
    set_attr("David:ctrlBrow_L", "translateY", -0.4)
    set_attr("David:ctrlBrow_R", "translateY", -0.4)
    set_attr("David:ctrlMouth_M", "translateY", -0.2)


def pose_frustrated():
    print("Pose: Frustrated/Defeated (Shot 66)")
    set_rot("David:FKSpine1_M", -5, 0, 0)
    set_rot("David:FKSpine2_M", -3, 0, 0)
    set_rot("David:FKChest_M", -5, 0, 0)
    set_rot("David:FKHead_M", 10, 0, 0)
    set_rot("David:FKNeck_M", 5, 0, 0)
    set_rot("David:FKShoulder_L", 10, 0, 5)
    set_rot("David:FKShoulder_R", 10, 0, -5)
    set_rot("David:FKElbow_L", 20, 0, 0)
    set_rot("David:FKElbow_R", 20, 0, 0)
    set_rot("David:FKWrist_R", 0, 0, 0)
    set_rot("David:FKHip_L", 0, 0, 0)
    set_rot("David:FKHip_R", 0, 0, 0)
    set_rot("David:FKKnee_L", 0, 0, 0)
    set_rot("David:FKKnee_R", 0, 0, 0)
    set_attr("David:ctrlBrow_L", "translateY", -0.3)
    set_attr("David:ctrlBrow_R", "translateY", -0.3)
    set_attr("David:ctrlMouth_M", "translateY", -0.5)
    set_attr("David:ctrlMouthCorner_L", "translateY", -0.3)
    set_attr("David:ctrlMouthCorner_R", "translateY", -0.3)
    set_attr("David:upperLid1_L", "translateY", -0.2)
    set_attr("David:upperLid1_R", "translateY", -0.2)


def pose_spider_descend():
    print("Pose: Spider descending on silk thread (Shot 62)")
    root = "Spider:wolfSpider_Root"
    if cmds.objExists(root):
        set_pos(root, 30, 130, 0)
    thorax = "Spider:wolfSpider_Thorax_ctl"
    if cmds.objExists(thorax):
        set_rot(thorax, 0, 0, 0)


def set_camera(shot_name):
    cam_map = {
        "62": "Cam_Shot62",
        "63": "Cam_Shot63",
        "64": "Cam_Shot64",
        "66a": "Cam_Shot66a",
        "66b": "Cam_Shot66b",
    }
    if shot_name in cam_map and not STANDALONE:
        cam = cam_map[shot_name]
        try:
            cmds.lookThru(cam)
            print("Viewport set to:", cam)
        except Exception:
            print("Camera:", cam, "(set manually in viewport)")


if __name__ == "__main__":
    print("=" * 60)
    print("Office Spider - Pose Setup (Shots 62-66)")
    print("=" * 60)

    pose_neutral()
    pose_spider_descend()
    set_camera("62")

    pose_angry()
    set_camera("63")

    pose_ready_swing()
    set_camera("64")

    pose_frustrated()
    set_camera("66b")

    if STANDALONE:
        out = "G:/film-304-toon-spine/Saved/Scenes/OfficeSpider_Layout_62_66_Posed.mb"
        cmds.file(rename=out)
        cmds.file(save=True, type="mayaBinary", force=True)
        print("Saved posed scene:", out)

    print("=" * 60)
    print("Poses applied. Adjust manually in Maya as needed.")
    print("Cameras: Cam_Shot62, Cam_Shot63, Cam_Shot64, Cam_Shot66a, Cam_Shot66b")
    print("=" * 60)

    if STANDALONE:
        import maya.standalone
        maya.standalone.uninitialize()
