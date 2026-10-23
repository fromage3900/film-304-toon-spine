"""Verify every pose in specs/cast/pose_library.v1.json. Read-only.

A fixed pose is two identical keys. This checks that, plus grounding. Contact
targets that need the level (a desk edge) are reported as not_checked rather
than guessed.

Run in the editor: python Tools/houdini/run_ue_script.py Python/verify_pose_library.py
"""
import json
import math
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
SPEC = json.loads((ROOT / "specs/cast/pose_library.v1.json").read_text(encoding="utf-8"))
OUT = ROOT / "Saved/Audit/Poses"
OUT.mkdir(parents=True, exist_ok=True)
AP = unreal.AnimPoseExtensions
TOL = SPEC["tolerances"]


def safe(fn, default=None):
    try:
        return fn()
    except Exception as exc:
        report["errors"].append(str(exc)[:160])
        return default


def xyz(v):
    return [v.x, v.y, v.z]


def quat_dist(a, b):
    d = abs(sum(x * y for x, y in zip(a, b)))
    return 2.0 * math.acos(min(1.0, d))


def bone_local(pose, name):
    t = AP.get_bone_pose(pose, name, unreal.AnimPoseSpaces.LOCAL)
    q = t.rotation
    return [t.translation.x, t.translation.y, t.translation.z,
            q.x, q.y, q.z, q.w,
            t.scale3d.x, t.scale3d.y, t.scale3d.z]


def bone_world(pose, name):
    return AP.get_bone_pose(pose, name, unreal.AnimPoseSpaces.WORLD)


report = {"spec": str(ROOT / "specs/cast/pose_library.v1.json"), "poses": [],
          "errors": []}

for entry in SPEC["poses"]:
    row = {"id": entry["id"], "animation": entry["animation"], "checks": {},
           "values": {}, "not_checked": [], "ok": False}
    anim = safe(lambda: unreal.load_asset(entry["animation"]), None)
    if anim is None:
        row["error"] = "animation did not load"
        report["poses"].append(row)
        continue

    mesh = safe(lambda: unreal.load_asset(entry["skeletal_mesh"]), None)
    opts = unreal.AnimPoseEvaluationOptions()
    opts.set_editor_properties({"should_retarget": False,
                                "extract_root_motion": False,
                                "optional_skeletal_mesh": mesh})
    start = safe(lambda: AP.get_anim_pose_at_time(anim, 0.0, opts), None)
    end = safe(lambda: AP.get_anim_pose_at_time(anim, anim.get_play_length(), opts), None)
    if start is None or end is None:
        row["error"] = "pose evaluation failed"
        report["poses"].append(row)
        continue

    names = [str(n) for n in AP.get_bone_names(start)]
    keys = int(unreal.AnimationLibrary.get_num_keys(anim))
    row["values"]["num_keys"] = keys
    row["values"]["length_s"] = round(float(anim.get_play_length()), 6)
    row["values"]["bones"] = len(names)
    row["checks"]["two_keys"] = keys == TOL["keys_expected"]

    endpoint = 0.0
    for name in names:
        a = bone_local(start, name)
        b = bone_local(end, name)
        lin = max(abs(x - y) for x, y in zip(a[:3] + a[7:], b[:3] + b[7:]))
        rot = quat_dist(a[3:7], b[3:7])
        endpoint = max(endpoint, lin, rot)
    row["values"]["endpoint_max"] = round(endpoint, 6)
    row["checks"]["endpoint"] = endpoint < TOL["endpoint_local_max"]

    foot_rule = next((c for c in entry.get("contacts", [])
                      if c["type"] == "feet_on_floor"), None)
    if foot_rule:
        present = [b for b in foot_rule["bones"] if b in names]
        if present:
            zs = {b: round(bone_world(start, b).translation.z, 3) for b in present}
            lowest = min(zs.values())
            row["values"]["foot_z_cm"] = zs
            row["checks"]["feet_on_floor"] = (
                TOL["feet_floor_min_cm"] <= lowest <= TOL["feet_floor_max_cm"])
        else:
            row["checks"]["feet_on_floor"] = False
            row["not_checked"].append("no ankle/toe bone found")

    pelvis = next((b for b in ("Hip_L", "Pelvis", "Root_M") if b in names), None)
    if pelvis:
        row["values"]["pelvis_z_cm"] = round(bone_world(start, pelvis).translation.z, 3)

    for contact in entry.get("contacts", []):
        if contact["type"] == "hand_to_surface":
            row["not_checked"].append(
                "hand_to_surface vs %s needs the level; measure in the shot camera"
                % contact.get("target"))
        if contact["type"] == "pelvis_record_only":
            row["not_checked"].append(
                "pelvis vs seat needs the chair's world bounds in-level (pose space is not level cm)")
        if contact["type"] == "pelvis_above_seat":
            z = row["values"].get("pelvis_z_cm")
            if z is not None:
                above = z - contact["seat_top_cm"]
                row["values"]["pelvis_above_seat_cm"] = round(above, 2)
                row["checks"]["pelvis_above_seat"] = (
                    abs(above - contact["expected_cm"]) <= contact["tol_cm"])
        if contact["type"] == "wrist_beyond_opposite_elbow":
            w, e = contact["wrist"], contact["elbow"]
            if w in names and e in names:
                dy = bone_world(start, w).translation.y - bone_world(start, e).translation.y
                row["values"]["wrist_vs_opposite_elbow_cm"] = round(dy, 2)
                row["checks"]["wrist_beyond_elbow"] = abs(dy) >= contact["min_cm"]

    row["ok"] = all(row["checks"].values())
    report["poses"].append(row)

report["ok"] = all(p.get("ok") for p in report["poses"])
(OUT / "pose_library.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("pose library ok=" + str(report["ok"]))
for p in report["poses"]:
    print(" ", p["id"], "ok=", p.get("ok"), p.get("checks"),
          "not_checked=", p.get("not_checked"))
for e in report["errors"]:
    print("  ERROR", e)
