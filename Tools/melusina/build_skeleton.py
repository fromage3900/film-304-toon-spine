# Tools/melusina/build_skeleton.py
# Build a clean 66-joint HumanIK deform skeleton fitted to Melusina's ARP proportions.
import sys, os, json, datetime
sys.path.insert(0, r"G:\film-304-toon-spine\Tools\melusina")
import maya.standalone
maya.standalone.initialize(name="python")
from maya import cmds
from melusina_common import (decode_name, write_json, read_json, vec_sub, vec_add,
                             vec_scale, vec_norm, vec_cross, vec_dot, vec_len)

SCRATCH = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\scratch\arp_import.ma"
SUMMARY = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\report\arp_inventory_summary.json"
TARGETS = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\report\skeleton_targets.json"
OUT_MA = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\scratch\skeleton_test.ma"
OUT_JSON = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\report\skeleton_report.json"

HIK_MAP = {
    "Hips": "pelvis",
    "Spine": "spine_01",
    "Spine1": "spine_02",
    "Spine2": "spine_03",
    "Neck": "neck_02",
    "Head": "head",
    "LeftShoulder": "clavicle_l",
    "LeftArm": "upperarm_l",
    "LeftForeArm": "lowerarm_l",
    "LeftHand": "hand_l",
    "RightShoulder": "clavicle_r",
    "RightArm": "upperarm_r",
    "RightForeArm": "lowerarm_r",
    "RightHand": "hand_r",
    "LeftUpLeg": "thigh_l",
    "LeftLeg": "calf_l",
    "LeftFoot": "foot_l",
    "LeftToeBase": "ball_l",
    "RightUpLeg": "thigh_r",
    "RightLeg": "calf_r",
    "RightFoot": "foot_r",
    "RightToeBase": "ball_r",
}
FINGER_MAP = {"Thumb": "thumb", "Index": "index", "Middle": "middle", "Ring": "ring", "Pinky": "pinky"}

def cleanup_scene(real_names):
    for sc in cmds.ls(type="skinCluster") or []:
        cmds.delete(sc)
    joints = cmds.ls(type="joint") or []
    if joints:
        cmds.delete(joints)
    # Delete intermediate/original shapes
    for m in cmds.ls(type="mesh") or []:
        try:
            if cmds.getAttr(m + ".intermediateObject"):
                cmds.delete(m)
        except Exception:
            pass
    # Delete transforms that are not real character meshes
    for m in cmds.ls(type="mesh") or []:
        transforms = cmds.listRelatives(m, parent=True, fullPath=True)
        if not transforms:
            continue
        t = transforms[0]
        short = t.split("|")[-1]
        if short not in real_names:
            cmds.delete(t)
    # Flatten remaining mesh transforms to world
    for m in cmds.ls(type="mesh") or []:
        transforms = cmds.listRelatives(m, parent=True, fullPath=True)
        if not transforms:
            continue
        t = transforms[0]
        if cmds.listRelatives(t, parent=True):
            try:
                cmds.parent(t, world=True)
            except Exception:
                pass
    # Delete empty groups
    for grp in cmds.ls(type="transform") or []:
        if grp in real_names:
            continue
        children = cmds.listRelatives(grp, children=True)
        if not children:
            cmds.delete(grp)

def build_skeleton(targets):
    cmds.select(clear=True)
    ref = cmds.joint(name="Reference", position=(0.0, 0.0, 0.0))
    hips = cmds.joint(name="Hips", position=targets["pelvis"])
    cmds.parent(hips, ref)
    spine_keys = ["spine_01", "spine_02", "spine_03"]
    spine_names = ["Spine", "Spine1", "Spine2"]
    parent = hips
    spine_joints = []
    for name, key in zip(spine_names, spine_keys):
        j = cmds.joint(name=name, position=targets[key])
        cmds.parent(j, parent)
        spine_joints.append(j)
        parent = j
    neck = cmds.joint(name="Neck", position=targets["neck_02"])
    cmds.parent(neck, spine_joints[-1])
    head = cmds.joint(name="Head", position=targets["head"])
    cmds.parent(head, neck)
    head_pos = targets["head"]
    neck_pos = targets["neck_02"]
    head_dir = vec_norm(vec_sub(head_pos, neck_pos))
    head_end = cmds.joint(name="HeadEnd", position=vec_add(head_pos, vec_scale(head_dir, 15.0)))
    cmds.parent(head_end, head)
    return ref, hips, spine_joints

def build_arms_and_fingers(targets, spine_joints):
    for side, prefix in (("Left", "l"), ("Right", "r")):
        shoulder = cmds.joint(name="%sShoulder" % side, position=targets["clavicle_%s" % prefix])
        cmds.parent(shoulder, spine_joints[-1])
        arm = cmds.joint(name="%sArm" % side, position=targets["upperarm_%s" % prefix])
        cmds.parent(arm, shoulder)
        forearm = cmds.joint(name="%sForeArm" % side, position=targets["lowerarm_%s" % prefix])
        cmds.parent(forearm, arm)
        hand = cmds.joint(name="%sHand" % side, position=targets["hand_%s" % prefix])
        cmds.parent(hand, forearm)
        for hik_finger, arp_finger in FINGER_MAP.items():
            parent_f = hand
            seg_positions = [targets["%s_%s_%s" % (arp_finger, seg, prefix)] for seg in ("01", "02", "03")]
            for idx, pos in enumerate(seg_positions, start=1):
                j = cmds.joint(name="%sHand%s%d" % (side, hik_finger, idx), position=pos)
                cmds.parent(j, parent_f)
                parent_f = j
            tip_dir = vec_norm(vec_sub(seg_positions[-1], seg_positions[-2]))
            tip = cmds.joint(name="%sHand%s4" % (side, hik_finger),
                             position=vec_add(seg_positions[-1], vec_scale(tip_dir, 3.0)))
            cmds.parent(tip, parent_f)

def build_legs(targets, hips):
    for side, prefix in (("Left", "l"), ("Right", "r")):
        upleg = cmds.joint(name="%sUpLeg" % side, position=targets["thigh_%s" % prefix])
        cmds.parent(upleg, hips)
        leg = cmds.joint(name="%sLeg" % side, position=targets["calf_%s" % prefix])
        cmds.parent(leg, upleg)
        foot = cmds.joint(name="%sFoot" % side, position=targets["foot_%s" % prefix])
        cmds.parent(foot, leg)
        toe = cmds.joint(name="%sToeBase" % side, position=targets["ball_%s" % prefix])
        cmds.parent(toe, foot)
        foot_pos = targets["foot_%s" % prefix]
        toe_pos = targets["ball_%s" % prefix]
        toe_dir = vec_norm(vec_sub(toe_pos, foot_pos))
        toe_end = cmds.joint(name="%sToe_End" % side, position=vec_add(toe_pos, vec_scale(toe_dir, 10.0)))
        cmds.parent(toe_end, toe)

def orient_all_joints():
    joints = cmds.ls(type="joint") or []
    ordered = []
    def walk(j):
        ordered.append(j)
        for c in cmds.listRelatives(j, children=True, type="joint") or []:
            walk(c)
    roots = [j for j in joints if not cmds.listRelatives(j, parent=True, type="joint")]
    for r in roots:
        walk(r)
    for j in ordered:
        children = cmds.listRelatives(j, children=True, type="joint") or []
        if not children:
            continue
        cmds.select(j)
        cmds.joint(e=True, orientJoint="xyz", secondaryAxisOrient="yup", children=False, zeroScaleOrient=True)
    cmds.select(clear=True)

def verify_orientation():
    rows = []
    for j in cmds.ls(type="joint") or []:
        children = cmds.listRelatives(j, children=True, type="joint") or []
        if not children:
            continue
        child = children[0]
        pj = cmds.xform(j, q=True, ws=True, rp=True)
        pc = cmds.xform(child, q=True, ws=True, rp=True)
        direction = vec_norm(vec_sub(pc, pj))
        x_axis = cmds.xform(j, q=True, ws=True, matrix=True)[0:3]
        x_axis = vec_norm(x_axis)
        dot = vec_dot(x_axis, direction)
        rows.append({"joint": j, "child": child, "x_dot_direction": dot})
    return rows

def main():
    summary = read_json(SUMMARY)
    targets = read_json(TARGETS)["targets"]
    real_names = {m["encoded"] for m in summary["real_meshes"]}

    cmds.file(SCRATCH, open=True, force=True)
    cmds.currentUnit(linear="cm", time="film", angle="deg")
    cleanup_scene(real_names)
    ref, hips, spine_joints = build_skeleton(targets)
    build_arms_and_fingers(targets, spine_joints)
    build_legs(targets, hips)
    orient_all_joints()
    orientation_rows = verify_orientation()

    cmds.file(rename=OUT_MA)
    cmds.file(save=True, type="mayaAscii")

    joints = cmds.ls(type="joint") or []
    meshes = cmds.ls(type="mesh") or []
    report = {
        "tool": "build_skeleton",
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "joint_count": len(joints),
        "joint_names": joints,
        "mesh_count": len(meshes),
        "orientation_rows": orientation_rows,
        "min_x_dot": min(r["x_dot_direction"] for r in orientation_rows) if orientation_rows else None,
        "saved_ma": OUT_MA,
    }
    write_json(OUT_JSON, report)

main()
