"""Compose the break-room set from the staged 2026-10-16 meshes.

The break room is plan gap 7.12 in Docs/OFFICE_SPIDER_SHOT_PLAN.md: SH090
(Break Room) and SH100 (Coffee Machine) have no set at all, and the SH110 money
shot is staged against it.

Reads specs/office_spider/breakroom_stage.v1.json. Every placement, scale and
camera in that file is an explicit art-direction decision - this script does not
derive layout, it applies and then verifies what the spec declares. That split
matters because the staged meshes come from four different source kits at four
different scales; a builder that guessed positions would silently produce a room
nobody art-directed.

It owns the level end to end and is safe to re-run: only actors this script
labels are removed first, so a re-run never stacks a second set.

Run inside the editor:

    UnrealEditor-Cmd.exe HumberToonShader.uproject \
      -ExecutePythonScript="Python/build_breakroom_scene.py" -stdout -unattended
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

SPEC_PATH = ROOT / "specs/office_spider/breakroom_stage.v1.json"
REPORT_PATH = ROOT / "Saved/Audit/BreakRoom_20261016/breakroom_stage.json"


def spawn(spec: dict) -> dict:
    pkg = spec["level"]
    placements = spec["placements"]

    # Every actor this script owns is labelled BR_*, Cam_BR_* or LGT_*. Destroy
    # them BY PREFIX, not by exact label.
    #
    # Exact-label cleanup is not enough here: Unreal suffixes a duplicate label
    # (BR_Light_Counter_1, _2, ...), so after three rebuilds the level held
    # SIXTY copies' worth of practicals - sixteen point lights in a 111 x 55 room.
    # The verifier did not catch it because it only asked whether the label
    # existed, and "BR_Light_Counter" always existed.
    owned_prefixes = tuple(spec.get("owned_prefixes", ["BR_", "Cam_BR_", "LGT_", "Sky"]))

    action = level_lib.open_or_create_level(pkg, clean_labels=None)
    print("[breakroom] level %s" % action, flush=True)

    stale = []
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            label = a.get_actor_label()
        except Exception:                                          # noqa: BLE001
            continue
        if label.startswith(owned_prefixes):
            stale.append(label)
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            if a.get_actor_label().startswith(owned_prefixes):
                unreal.EditorLevelLibrary.destroy_actor(a)
        except Exception:                                          # noqa: BLE001
            continue
    print("[breakroom] removed %d stale owned actor(s): %s"
          % (len(stale), sorted(stale)), flush=True)

    spawned, skipped, failures = [], [], []
    for item in placements:
        asset_path = item["mesh"]
        mesh = unreal.load_asset(asset_path)
        if mesh is None:
            skipped.append({"label": item["label"], "reason": "mesh not found",
                            "mesh": asset_path})
            continue

        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.StaticMeshActor,
            unreal.Vector(*item["location"]),
            unreal.Rotator(roll=float(item.get("rotation", [0, 0, 0])[2]),
                           pitch=float(item.get("rotation", [0, 0, 0])[1]),
                           yaw=float(item.get("rotation", [0, 0, 0])[0])))
        actor.set_actor_label(item["label"])
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        if comp is None:
            unreal.EditorLevelLibrary.destroy_actor(actor)
            failures.append({"label": item["label"], "reason": "no StaticMeshComponent"})
            continue

        scale = item.get("scale", [1.0, 1.0, 1.0])
        comp.set_mobility(unreal.ComponentMobility.MOVABLE)
        comp.set_static_mesh(mesh)
        # Actor-level scale: SceneComponent exposes set_relative_scale3d, not
        # set_actor_relative_scale3d, and the actor call is what a static mesh
        # actor's editor UI drives anyway.
        actor.set_actor_scale3d(unreal.Vector(*scale))

        spawned.append({
            "label": item["label"],
            "mesh": asset_path,
            "zone": item.get("zone"),
            "location": item["location"],
            "scale": scale,
        })

    cameras = []
    for cam in spec["cameras"]:
        rot = cam.get("rotation", [0, 0, 0])
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.CineCameraActor,
            unreal.Vector(*cam["location"]),
            # Spec rotations are (yaw, pitch, roll) - the same convention as
            # every placement in this file. sun_rotator() takes
            # (pitch, yaw, roll), so passing the array positionally transposed
            # Y and Z and aimed every camera at the floor: SH100's forward
            # vector came out (0.50, -0.07, -0.87) instead of (0.50, -0.86,
            # -0.14). Build the rotator explicitly, as the placements do.
            unreal.Rotator(roll=float(rot[2]), pitch=float(rot[1]),
                           yaw=float(rot[0])))
        actor.set_actor_label(cam["label"])
        comp = actor.get_component_by_class(unreal.CineCameraComponent)
        if comp is not None:
            comp.set_field_of_view(float(cam.get("fov", 40.0)))
            # 16:9 filmback. take_high_res_screenshot constrains the capture to
            # the CAMERA's filmback aspect, so an inherited 35 x 24.89 Academy
            # back (1.406:1) returns 1012 x 720 for a 1280 x 720 request -
            # measured 2026-10-01 and recorded in the prototype render spec.
            fb = cam.get("filmback")
            if fb:
                # UE 5.8 exposes CineCameraComponent.filmback as a STRUCT
                # property; there is no filmback_width on the component. The
                # supported way to hit a target aspect is to constrain it.
                ratio = float(fb["width"]) / float(fb["height"])
                comp.set_editor_property("constrain_aspect_ratio", True)
                comp.set_aspect_ratio(ratio)
        cameras.append({"label": cam["label"], "shot": cam.get("shot"),
                        "location": cam["location"],
                        "aspect_ratio": (float(cam["filmback"]["width"])
                                         / float(cam["filmback"]["height"]))
                        if cam.get("filmback") else None,
                        "fov": float(cam.get("fov", 40.0)) if comp is not None else None})

    level_lib.spawn_lights(
        sun_rotation=tuple(spec["lighting"]["sun_rotation"]),
        sun_intensity=float(spec["lighting"]["sun_intensity"]),
        sun_height=float(spec["lighting"].get("sun_height", 4000.0)),
        light_mobility="movable")

    # Interior practicals. An interior lit by a sun alone reads flat and, under
    # the headless -game path, risks the black-render class; the practicals are
    # what actually separate the counter band from the shelf wall.
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
            # Movable, for the same reason the sun is: a stationary practical
            # leans on built-shadow data that an unbaked level does not have.
            comp.set_mobility(unreal.ComponentMobility.MOVABLE)
        practicals.append({"label": item["label"], "intensity": item["intensity"]})

    unreal.EditorLevelLibrary.save_current_level()
    return {"level": pkg, "level_action": action, "spawned": spawned,
            "cameras": cameras, "practicals": practicals,
            "skipped": skipped, "failures": failures}


def verify(spec: dict, result: dict) -> dict:
    """Read every placed actor back and measure it against the room."""
    actors = {a.get_actor_label(): a
              for a in unreal.EditorLevelLibrary.get_all_level_actors()}
    room = spec["room_bounds"]

    problems = []
    measured = []
    for item in spec["placements"]:
        actor = actors.get(item["label"])
        if actor is None:
            problems.append("%s: actor missing after save" % item["label"])
            continue
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        if comp is None:
            problems.append("%s: no StaticMeshComponent" % item["label"])
            continue
        mesh = comp.get_editor_property("static_mesh")
        if mesh is None:
            problems.append("%s: no mesh assigned" % item["label"])
            continue
        if mesh.get_path_name().split(".")[0] != item["mesh"]:
            problems.append("%s: mesh mismatch" % item["label"])
            continue

        loc = actor.get_actor_location()
        bounds = mesh.get_bounds()
        origin, extent = bounds.origin, bounds.box_extent
        scale = actor.get_actor_scale3d()
        # World AABB of the placed mesh, so a prop poking through a wall is
        # caught rather than only its actor origin being inside the room.
        # The asset's OWN bounds origin has to be added: these meshes are
        # authored off-centre (BR_Shell's local origin is (-64.3, -46.3, 21.8)),
        # so treating local space as centred on the actor origin reports every
        # placement as 64 units out.
        half = unreal.Vector(extent.x * abs(scale.x), extent.y * abs(scale.y),
                             extent.z * abs(scale.z))
        minx, maxx = loc.x + origin.x - half.x, loc.x + origin.x + half.x
        miny, maxy = loc.y + origin.y - half.y, loc.y + origin.y + half.y
        minz, maxz = loc.z + origin.z - half.z, loc.z + origin.z + half.z

        fits = (minx >= room["x"][0] - 1.0 and maxx <= room["x"][1] + 1.0 and
                miny >= room["y"][0] - 1.0 and maxy <= room["y"][1] + 1.0 and
                minz >= room["z"][0] - 1.0)
        if not fits:
            problems.append(
                "%s: world bounds (%.1f,%.1f,%.1f)-(%.1f,%.1f,%.1f) do not fit the room"
                % (item["label"], minx, miny, minz, maxx, maxy, maxz))
        measured.append({"label": item["label"],
                         "origin": [round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)],
                         "world_min": [round(minx, 1), round(miny, 1), round(minz, 1)],
                         "world_max": [round(maxx, 1), round(maxy, 1), round(maxz, 1)],
                         "fits_room": bool(fits)})

    for cam in spec["cameras"]:
        if cam["label"] not in actors:
            problems.append("%s: camera missing after save" % cam["label"])

    for light in spec.get("practicals", []):
        if light["label"] not in actors:
            problems.append("%s: practical missing after save" % light["label"])

    # A camera can sit inside the room, pass every position and bounds check, and
    # still be aimed at the floor or the side wall - which is exactly what a
    # transposed pitch/yaw looks like, and exactly what SH090 and SH100 did
    # before this check existed. Each camera declares the world point it frames
    # (aim_at), so "is this shot pointed at its subject" is assertable rather
    # than a matter of taste. Pointing at the room centre is not good enough:
    # SH100 frames a prop on the counter, not the room.
    for cam in spec["cameras"]:
        actor = actors.get(cam["label"])
        aim = cam.get("aim_at")
        if actor is None or not aim:
            continue
        fwd = actor.get_actor_forward_vector()
        loc = actor.get_actor_location()
        delta = unreal.Vector(aim[0] - loc.x, aim[1] - loc.y, aim[2] - loc.z)
        length = delta.length()
        if length <= 1e-6:
            problems.append("%s: aim_at is the camera's own position" % cam["label"])
            continue
        dot = (fwd.x * delta.x + fwd.y * delta.y + fwd.z * delta.z) / length
        if dot < 0.9:
            problems.append(
                "%s: forward (%.2f, %.2f, %.2f) misses its aim_at %s "
                "(dot=%.2f, need >= 0.90). In UE yaw 180 faces -X, not -Y, "
                "and the rotator is (roll, pitch, yaw) positionally."
                % (cam["label"], fwd.x, fwd.y, fwd.z, list(aim), dot))

    # Duplicate-label check. Unreal suffixes a repeated label instead of
    # refusing it, so a re-run that does not clean up leaves BR_Light_Counter,
    # BR_Light_Counter_1, _2, ... in the level. Every one of those lights is
    # real and contributes to the render; asking only "does the label exist"
    # passes while the room silently gains sixteen point lights.
    counts = {}
    for label in actors:
        counts[label] = counts.get(label, 0) + 1
    duplicates = {k: v for k, v in counts.items() if v > 1}
    if duplicates:
        problems.append("duplicate actor labels (rebuild did not clean up): %s"
                        % dict(sorted(duplicates.items())))

    return {"measured": measured, "problems": problems,
            "problem_count": len(problems),
            "verdict": "verified" if not problems else "problems_found"}


def main() -> None:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    report = {"schema": "humber-breakroom-stage.v1", "spec": str(SPEC_PATH)}
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
    print("BREAKROOM_JSON " + json.dumps({
        "result": report["result"],
        "counts": report["counts"],
        "verify": report["verify"]["verdict"],
        "problems": report["verify"]["problems"][:12],
    }))
    unreal.log("break room staged: %s -> %s" % (report["result"], REPORT_PATH))


if __name__ == "__main__":
    main()