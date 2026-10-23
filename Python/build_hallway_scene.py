"""Compose the hallway connector set from specs/office_spider/hallway_stage.v1.json.

Plan gap 7.12 in Docs/OFFICE_SPIDER_SHOT_PLAN.md: shots 5-6, 14, 18, 41, 46, 47
need a corridor between the cubicle bay and the break room, and until this existed
those cameras had nothing to see.

Reads the spec; applies placements, cameras, lights and then verifies what it
declared. Safe to re-run: only actors this script owns (HL_*, Cam_HW_*, LGT_*)
are removed first.

Run inside the editor:

    UnrealEditor-Cmd.exe HumberToonShader.uproject \\
      -ExecutePythonScript="Python/build_hallway_scene.py" -stdout -unattended
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Python"))
import level_lib  # noqa: E402

SPEC_PATH = ROOT / "specs/office_spider/hallway_stage.v1.json"
REPORT_PATH = ROOT / "Saved/Audit/Hallway_20261017/hallway_stage.json"


def _pos(item):
    if "position_uu" in item:
        return item["position_uu"]
    return item["location"]


def _scale(item):
    if "scale_uu" in item:
        return item["scale_uu"]
    return item.get("scale", [1.0, 1.0, 1.0])


def _rot_z(item):
    return float(item.get("rotation_z_deg", item.get("rotation", [0, 0, 0])[2] if isinstance(item.get("rotation"), list) else 0.0))


def spawn(spec):
    pkg = spec["level"]
    owned_prefixes = tuple(spec.get("owned_prefixes", ["HL_", "Cam_HW_", "LGT_", "Sky"]))

    action = level_lib.open_or_create_level(pkg, clean_labels=None)
    print("[hallway] level %s" % action, flush=True)

    stale = []
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            if a.get_actor_label().startswith(owned_prefixes):
                stale.append(a.get_actor_label())
        except Exception:
            continue
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            if a.get_actor_label().startswith(owned_prefixes):
                unreal.EditorLevelLibrary.destroy_actor(a)
        except Exception:
            continue
    print("[hallway] removed %d stale owned actor(s)" % len(stale), flush=True)

    spawned, skipped, failures = [], [], []
    for item in spec["placements"]:
        asset_path = item["asset"]
        mesh = unreal.load_asset(asset_path)
        if mesh is None:
            skipped.append({"label": item["object"], "reason": "mesh not found", "mesh": asset_path})
            continue

        loc = _pos(item)
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.StaticMeshActor,
            unreal.Vector(*loc),
            unreal.Rotator(roll=0.0, pitch=0.0, yaw=_rot_z(item)))
        actor.set_actor_label("HL_" + item["object"])
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        if comp is None:
            unreal.EditorLevelLibrary.destroy_actor(actor)
            failures.append({"label": item["object"], "reason": "no StaticMeshComponent"})
            continue

        scale = _scale(item)
        comp.set_mobility(unreal.ComponentMobility.MOVABLE)
        comp.set_static_mesh(mesh)
        actor.set_actor_scale3d(unreal.Vector(*scale))

        mat_path = item.get("material")
        if mat_path:
            mat = unreal.load_asset(mat_path)
            if mat is not None and comp.get_num_materials() >= 1:
                comp.set_material(0, mat)

        spawned.append({"label": "HL_" + item["object"], "mesh": asset_path,
                        "location": loc, "scale": scale, "material": mat_path})

    cameras = []
    for cam in spec["shots"]:
        rot = cam.get("rotation", None)
        if rot is None:
            # derive yaw from location->target so the camera faces its subject
            loc = cam["location_uu"]
            tgt = cam["target_uu"]
            import math
            dx, dy, dz = tgt[0] - loc[0], tgt[1] - loc[1], tgt[2] - loc[2]
            yaw = math.degrees(math.atan2(dy, dx))
            pitch = math.degrees(math.atan2(dz, (dx * dx + dy * dy) ** 0.5))
            rot = [yaw, pitch, 0.0]
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.CineCameraActor,
            unreal.Vector(*cam["location_uu"]),
            unreal.Rotator(roll=float(rot[2]), pitch=float(rot[1]), yaw=float(rot[0])))
        actor.set_actor_label(cam["camera_label"])
        comp = actor.get_component_by_class(unreal.CineCameraComponent)
        if comp is not None:
            fl = float(cam.get("focal_length_mm", 50.0))
            comp.set_editor_property("current_focal_length", fl)
            fb = cam.get("filmback", {"width": 35.0, "height": 19.6875})
            ratio = float(fb["width"]) / float(fb["height"])
            comp.set_editor_property("constrain_aspect_ratio", True)
            comp.set_aspect_ratio(ratio)
        cameras.append({"label": cam["camera_label"], "shot": cam["shot_id"],
                        "location": cam["location_uu"], "target": cam["target_uu"],
                        "focal_length_mm": cam.get("focal_length_mm")})

    level_lib.spawn_lights(
        sun_rotation=tuple(spec["lighting"]["sun_rotation"]),
        sun_intensity=float(spec["lighting"]["sun_intensity"]),
        sun_height=float(spec["lighting"].get("sun_height", 3000.0)),
        light_mobility="movable")

    practicals = []
    for item in spec.get("practicals", []):
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.PointLight, unreal.Vector(*item["location"]),
            unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
        actor.set_actor_label(item["label"])
        comp = actor.get_component_by_class(unreal.PointLightComponent)
        if comp is not None:
            comp.set_intensity(float(item["intensity"]))
            comp.set_light_color(unreal.LinearColor(*item.get("colour", [1.0, 1.0, 1.0])))
            comp.set_mobility(unreal.ComponentMobility.MOVABLE)
        practicals.append({"label": item["label"], "intensity": item["intensity"]})

    unreal.EditorLevelLibrary.save_current_level()
    return {"level": pkg, "level_action": action, "spawned": spawned,
            "cameras": cameras, "practicals": practicals,
            "skipped": skipped, "failures": failures}


def verify(spec, result):
    actors = {a.get_actor_label(): a for a in unreal.EditorLevelLibrary.get_all_level_actors()}
    room = spec["room_bounds"]
    problems = []
    measured = []
    for item in spec["placements"]:
        label = "HL_" + item["object"]
        actor = actors.get(label)
        if actor is None:
            problems.append("%s: actor missing after save" % label)
            continue
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        if comp is None:
            problems.append("%s: no StaticMeshComponent" % label)
            continue
        mesh = comp.get_editor_property("static_mesh")
        if mesh is None:
            problems.append("%s: no mesh assigned" % label)
            continue
        loc = actor.get_actor_location()
        bounds = mesh.get_bounds()
        origin, extent = bounds.origin, bounds.box_extent
        scale = actor.get_actor_scale3d()
        half = unreal.Vector(extent.x * abs(scale.x), extent.y * abs(scale.y),
                             extent.z * abs(scale.z))
        minx, maxx = loc.x + origin.x - half.x, loc.x + origin.x + half.x
        miny, maxy = loc.y + origin.y - half.y, loc.y + origin.y + half.y
        minz, maxz = loc.z + origin.z - half.z, loc.z + origin.z + half.z
        fits = (minx >= room["x"][0] - 1.0 and maxx <= room["x"][1] + 1.0 and
                miny >= room["y"][0] - 1.0 and maxy <= room["y"][1] + 1.0 and
                minz >= room["z"][0] - 1.0)
        if not fits:
            problems.append("%s: world bounds do not fit the room" % label)
        measured.append({"label": label, "origin": [round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)],
                        "fits_room": bool(fits)})

    for cam in spec["shots"]:
        if cam["camera_label"] not in actors:
            problems.append("%s: camera missing after save" % cam["camera_label"])
        else:
            actor = actors[cam["camera_label"]]
            aim = cam["target_uu"]
            fwd = actor.get_actor_forward_vector()
            loc = actor.get_actor_location()
            delta = unreal.Vector(aim[0] - loc.x, aim[1] - loc.y, aim[2] - loc.z)
            length = delta.length()
            if length > 1e-6:
                dot = (fwd.x * delta.x + fwd.y * delta.y + fwd.z * delta.z) / length
                if dot < 0.85:
                    problems.append("%s: forward misses aim_at (dot=%.2f)" % (cam["camera_label"], dot))

    for light in spec.get("practicals", []):
        if light["label"] not in actors:
            problems.append("%s: practical missing after save" % light["label"])

    counts = {}
    for label in actors:
        counts[label] = counts.get(label, 0) + 1
    duplicates = {k: v for k, v in counts.items() if v > 1}
    if duplicates:
        problems.append("duplicate actor labels: %s" % dict(sorted(duplicates.items())))

    return {"measured": measured, "problems": problems,
            "problem_count": len(problems),
            "verdict": "verified" if not problems else "problems_found"}


def main():
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    report = {"schema": "humber-hallway-stage.v1", "spec": str(SPEC_PATH)}
    try:
        result = spawn(spec)
        report.update(result)
        report["verify"] = verify(spec, result)
        report["counts"] = {
            "placements_declared": len(spec["placements"]),
            "spawned": len(result["spawned"]),
            "skipped": len(result["skipped"]),
            "failures": len(result["failures"]),
            "cameras": len(result["cameras"]),
        }
        report["result"] = ("staged_and_verified"
                            if report["verify"]["problem_count"] == 0
                            and not result["failures"] else "staged_with_problems")
    except Exception as exc:
        report["result"] = "failed"
        report["error"] = str(exc)
        report["traceback"] = traceback.format_exc()
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
        raise

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("HALLWAY_JSON " + json.dumps({
        "result": report["result"],
        "counts": report["counts"],
        "verify": report["verify"]["verdict"],
        "problems": report["verify"]["problems"][:12],
    }))


if __name__ == "__main__":
    main()