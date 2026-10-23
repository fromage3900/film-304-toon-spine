"""Probe 2: the FACE SUBTREE's parent chain, in component space.

Hypothesis under test (owner note 2026-10-17: "eyes and afcial features didnt
follow pose"):

    Dana_CleanSkin_v08 carries a 345-bone deform-side FACE rig (Eye_R/L,
    Pupil_*, Iris_*, Jaw_M, lips, lids, brows, teeth, tongue) that this lane's
    pose table never keys -- and the rig also carries FaceMotionSystem /
    FaceMotionFollowHead / FaceDeformationFollowHead / FaceGroup, which in Maya
    followed the head through a CONSTRAINT. A constraint does not survive FBX
    into a UE skeleton: UE only evaluates the skeletal hierarchy. So if that
    face subtree is not parented under Head_M, the whole face stays in bind
    space while the head rotates, and the eyes hang off the skull.

    That is a hierarchy question, and it is answerable without rendering.

Reads only; writes Saved/Audit/UniversalFilm_20261016/face_hierarchy_probe.json.
"""
import json
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir())
AUDIT = ROOT / "Saved" / "Audit" / "UniversalFilm_20261016"
SPACE = unreal.RelativeTransformSpace.RTS_COMPONENT

INTEREST = [
    "Head_M", "Neck_M", "NeckPart1_M", "NeckPart2_M", "Chest_M", "Spine2_M",
    "Spine1_M", "HeadEnd_M",
    "FaceGroup", "FaceMotionSystem", "FaceMotionFollowHead",
    "FaceDeformationSystem", "FaceDeformationFollowHead", "faceHeadJoint",
    "faceLid", "FaceUpper_M", "FaceLower_M", "FaceUpperReverseOffset_M",
    "FaceUpperRegion_M", "FaceLowerRegion_M",
    "EyeRegion_R", "EyeRegion_L", "Eye_R", "EyeEnd_R", "Eye_L", "EyeEnd_L",
    "Pupil_R", "Pupil_L", "Iris_R", "Iris_L",
    "Jaw_M", "Chin_M", "Lips_M", "TeethUpper_M", "TeethLower_M",
    "Tongue0_M", "Tongue4_M",
    "upperLidMain0_R", "upperLidMain0Aim_R", "lowerLidMain0_R",
    "browInnerJoint_R", "browHalfJoint_R", "browOuterJoint_R",
    "LidSetup", "LidJoints", "LidSetup_R", "LidSetup_L",
    "LipSetup", "LipJoints_M", "LipsRotateJoints_M", "LipsScaleJoints_M",
]

doc = {"probe": "face_hierarchy_v02", "mutates": False}

# what space enums exist at all, so the next probe does not guess
doc["bone_spaces"] = [n for n in dir(unreal.RelativeTransformSpace)
                      if not n.startswith("_")]

subject = None
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl.startswith("Film_Subject_Dana") or (subject is None and lbl.startswith("Film_Subject_")):
        subject = a
        if lbl.startswith("Film_Subject_Dana"):
            break
if subject is None:
    doc["error"] = "no Film_Subject actor"
    (AUDIT / "face_hierarchy_probe.json").write_text(
        json.dumps(doc, indent=2), encoding="utf-8")
    print("FACE_HIER_PROBE_NO_SUBJECT")
    raise SystemExit

comp = subject.get_component_by_class(unreal.SkeletalMeshComponent)
doc["subject"] = subject.get_actor_label()
doc["num_bones"] = comp.get_num_bones()

index = {}
for i in range(comp.get_num_bones()):
    index[str(comp.get_bone_name(i))] = i


def chain_of(name, limit=12):
    """Names from `name` up to the root, via get_parent_bone(name)."""
    out, cur = [], name
    for _ in range(limit):
        try:
            parent = comp.get_parent_bone(cur)
        except Exception as exc:                                   # noqa: BLE001
            out.append({"at": cur, "parent": "ERR: %s" % exc})
            break
        pname = str(parent) if parent else None
        out.append({"at": cur, "parent": pname})
        if not pname or pname == "None":
            break
        cur = pname
    return out


rows = []
for name in INTEREST:
    row = {"bone": name, "index": index.get(name, -1)}
    if row["index"] < 0:
        row["note"] = "NOT ON SKELETON"
        rows.append(row)
        continue
    try:
        xf = comp.get_bone_transform(name, SPACE)
        row["component_translation"] = [round(v, 2) for v in
                                        (xf.translation.x, xf.translation.y,
                                         xf.translation.z)]
    except Exception as exc:                                       # noqa: BLE001
        row["component_translation"] = "ERR: %s" % exc
    row["chain"] = chain_of(name)
    # walk to the root: is Head_M an ancestor?
    ancestors = [c.get("parent") for c in row["chain"]]
    row["under_head_M"] = "Head_M" in ancestors
    row["depth"] = len(row["chain"])
    rows.append(row)
doc["bones"] = rows

# how many bones in total descend from Head_M vs from FaceGroup
heads = 0
facegrp = 0
for i in range(comp.get_num_bones()):
    nm = str(comp.get_bone_name(i))
    anc = [c.get("parent") for c in chain_of(nm, limit=16)]
    if "Head_M" in anc:
        heads += 1
    if "FaceGroup" in anc:
        facegrp += 1
doc["descendants_of_Head_M"] = heads
doc["descendants_of_FaceGroup"] = facegrp
doc["total_bones"] = comp.get_num_bones()

# root chain, for orientation
doc["root_chain"] = chain_of(str(comp.get_bone_name(0)), limit=8)
doc["bone0"] = str(comp.get_bone_name(0))

AUDIT.mkdir(parents=True, exist_ok=True)
(AUDIT / "face_hierarchy_probe.json").write_text(json.dumps(doc, indent=2),
                                                encoding="utf-8")
unreal.log("[FaceHierProbe] wrote face_hierarchy_probe.json")
print("FACE_HIER_PROBE_OK")
