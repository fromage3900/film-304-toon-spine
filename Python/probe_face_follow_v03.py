"""Probe 3: does the FACE move when the pose moves the HEAD?

Hypothesis (from probe 2): Dana_CleanSkin_v08's face is a 316-bone subtree that
is a SIBLING of the body under the skeleton root `Group`, not a child of
`Head_M`. The rig's `FaceDeformationFollowHead` / `FaceMotionFollowHead` bones
are where Maya's head-follow CONSTRAINT lived; a constraint does not survive
into a UE skeleton. So the pose rotates the head while the face skin stays in
bind space, and the face skin slides across the skull.

Predicted, if the hypothesis is right:
    * Head_M / HeadEnd_M move by a visible amount (the head yields to the pose);
    * Eye_R, Eye_L, Jaw_M, FaceUpper_M, the lid and brow joints do NOT move
      (they are rigidly attached to the actor root, not to the head);
    * so the face ends up offset from the skull by exactly the head's motion.

Reads and drives the existing pose asset only: it applies
A_DanaFilm_Pose_IDLE_A, records, and clears the animation again. No render, no
asset save, no level save.

Writes Saved/Audit/UniversalFilm_20261016/face_follow_probe.json.
"""
import json
import math
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir())
AUDIT = ROOT / "Saved" / "Audit" / "UniversalFilm_20261016"
SPACE = unreal.RelativeTransformSpace.RTS_ACTOR
POSE = "/Game/Staging/DanaFilmRuntime_20261016/Poses/A_DanaFilm_Pose_IDLE_A"

WATCH = [
    # body reference
    "Chest_M", "Neck_M", "NeckPart1_M", "NeckPart2_M",
    # head
    "Head_M", "HeadEnd_M",
    # face -- every one of these should follow the head and (prediction) will not
    "FaceGroup", "FaceDeformationFollowHead", "FaceMotionFollowHead",
    "faceHeadJoint", "FaceUpper_M", "FaceLower_M",
    "Eye_R", "Eye_L", "Pupil_R", "Pupil_L", "Iris_R", "Iris_L",
    "Jaw_M", "Chin_M", "Lips_M", "TeethUpper_M", "TeethLower_M",
    "browInnerJoint_R", "browHalfJoint_R", "browOuterJoint_R",
    "upperLidMain0_R", "lowerLidMain0_R", "upperLidMain0_L",
]

doc = {"probe": "face_follow_v03", "space": "RTS_ACTOR",
       "pose": POSE, "mutates": "animation state of the subject only"}

subject = None
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl.startswith("Film_Subject_Dana"):
        subject = a
        break
    if subject is None and lbl.startswith("Film_Subject_"):
        subject = a
doc["subject"] = None if subject is None else subject.get_actor_label()
if subject is None:
    doc["error"] = "no Film_Subject actor in the open level"
    AUDIT.mkdir(parents=True, exist_ok=True)
    (AUDIT / "face_follow_probe.json").write_text(json.dumps(doc, indent=2),
                                                 encoding="utf-8")
    print("FACE_FOLLOW_NO_SUBJECT")
    raise SystemExit

comp = subject.get_component_by_class(unreal.SkeletalMeshComponent)


def snapshot():
    out = {}
    for name in WATCH:
        try:
            t = comp.get_bone_transform(name, SPACE).translation
            out[name] = (t.x, t.y, t.z)
        except Exception as exc:                                   # noqa: BLE001
            out[name] = "ERR: %s" % str(exc)[:60]
    return out


def clear_anim():
    """Try every route back to bind and report which one took."""
    steps = {}
    try:
        comp.set_animation_mode(unreal.AnimationMode.ANIMATION_NONE)
        steps["set_animation_mode"] = "ok"
    except Exception as exc:                                       # noqa: BLE001
        steps["set_animation_mode"] = "ERR: %s" % str(exc)[:60]
    for fn_name, arg in (("set_animation", None), ("override_animation_data", None)):
        try:
            fn = getattr(comp, fn_name, None)
            if fn is None:
                steps[fn_name] = "UNAVAILABLE"
                continue
            fn(arg) if fn_name == "set_animation" else fn(arg, True)
            steps[fn_name] = "ok"
        except Exception as exc:                                   # noqa: BLE001
            steps[fn_name] = "ERR: %s" % str(exc)[:60]
    return steps


doc["clear_steps"] = clear_anim()
bind = snapshot()
doc["bind"] = {k: ([round(c, 3) for c in v] if isinstance(v, tuple) else v)
               for k, v in bind.items()}

seq = unreal.EditorAssetLibrary.load_asset(POSE)
doc["sequence_loaded"] = seq.get_path_name() if seq else None
if seq is None:
    doc["error"] = "pose asset missing"
    AUDIT.mkdir(parents=True, exist_ok=True)
    (AUDIT / "face_follow_probe.json").write_text(json.dumps(doc, indent=2),
                                                 encoding="utf-8")
    print("FACE_FOLLOW_NO_SEQUENCE")
    raise SystemExit

comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
comp.set_animation(seq)
comp.play(True)
try:
    comp.set_play_rate(0.0)
    comp.set_position(0.0, False)
except Exception:                                                  # noqa: BLE001
    pass
comp.override_animation_data(seq, True)

posed = snapshot()
doc["posed"] = {k: ([round(c, 3) for c in v] if isinstance(v, tuple) else v)
                for k, v in posed.items()}

rows = []
for name in WATCH:
    b, p = bind.get(name), posed.get(name)
    if not isinstance(b, tuple) or not isinstance(p, tuple):
        rows.append({"bone": name, "error": str(b if not isinstance(b, tuple) else p)})
        continue
    d = math.sqrt(sum((p[i] - b[i]) ** 2 for i in range(3)))
    rows.append({"bone": name,
                 "bind": [round(c, 3) for c in b],
                 "posed": [round(c, 3) for c in p],
                 "moved_cm": round(d, 4)})
doc["movement"] = rows

by = {r["bone"]: r for r in rows if "moved_cm" in r}
head = by.get("Head_M", {}).get("moved_cm", 0.0)
head_end = by.get("HeadEnd_M", {}).get("moved_cm", 0.0)
face_probe = ["Eye_R", "Eye_L", "Jaw_M", "FaceUpper_M", "browInnerJoint_R",
              "upperLidMain0_R"]
face_moved = [by[n]["moved_cm"] for n in face_probe if n in by]
ratio = (max(face_moved) / head) if head > 1e-6 and face_moved else None
doc["verdict"] = {
    "head_moved_cm": head,
    "head_end_moved_cm": head_end,
    "max_face_moved_cm": max(face_moved) if face_moved else None,
    "face_to_head_ratio": (round(ratio, 4) if ratio is not None else None),
    "reading": ("face is RIGID to the actor root and does not follow the head -- "
                "confirmed" if (head > 0.2 and face_moved and max(face_moved) < 0.1 * head)
                else "inconclusive; read the per-bone rows"),
}

doc["clear_after"] = clear_anim()

AUDIT.mkdir(parents=True, exist_ok=True)
(AUDIT / "face_follow_probe.json").write_text(json.dumps(doc, indent=2),
                                             encoding="utf-8")
unreal.log("[FaceFollowProbe] " + json.dumps(doc["verdict"]))
print("FACE_FOLLOW_PROBE_OK")
