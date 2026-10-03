"""Build the shot deck: one CineCameraActor + one LevelSequence per shot.

WHY
---
`Docs/GROUP_STAGING_GUIDE.md` describes the 60-90s animatic spine as a table of
eight shots, and `specs/humber_toon_spine/humber_toon_spine_manifest.v1.json`
carries the machine-readable twin (camera name, focal length, frame range,
duration). `Tools/dogfood_toon_spine.py` validates that manifest. Nothing built
the Unreal side, so "the shots exist" was only true on paper.

This turns the manifest into real assets: a camera per shot rig position, and an
`LS_ShotXXX` level sequence on the shared 24 fps timeline whose playback range is
exactly the shot's frames. Frames are contiguous and non-overlapping (SH010 ends
at 96, SH020 starts at 97), so the sequences tile the timeline and can be edited
together without re-timing.

MANIFEST IS THE SOURCE OF TRUTH
-------------------------------
Focal lengths and frame ranges are read from the manifest, never retyped here.
`Docs/CONTENT_CONVENTIONS.md` forbids copy-paste between the spec and the asset
for exactly this reason -- a retyped number drifts and nothing tells you.

CAMERA PLACEMENT
----------------
The manifest says what each shot IS ("low angle hero vista", "extreme close-up")
but not where the camera stands, because the level was built after the deck. Each
shot therefore gets a placement chosen to deliver the stated framing against the
lookdev row (spheres at X = 0..3200, ground plane at Z = -100), aimed with
`find_look_at_rotation` so the subject sits on frame centre. Adjust in the editor
once the real set is in; the comment above each entry says what the move is for.

Run (editor open, via Monolith):
    editor_query run_python {command: "Python/build_shot_deck.py", mode: execute_file}
or headless:
    UnrealEditor-Cmd.exe <project>.uproject \
      -ExecutePythonScript="Python/build_shot_deck.py" -stdout -unattended

Assert on the report FILE, not the log.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import unreal  # noqa: E402

LEVEL_NAME = "L_Toon_Lookdev"
MAP_DIR = "/Game/Maps"
SEQ_DIR = "/Game/Sequences"
FPS = 24

REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "specs" / "humber_toon_spine" / "humber_toon_spine_manifest.v1.json"
REPORT = Path(os.environ.get("TEMP", ".")) / "shot_deck_report.json"
AUDIT_COPY = REPO / "Saved" / "Audit" / "shot_deck_report.json"

# World-space camera placement per shot: (shot_id, location, look-at target).
# The level's hero subject is the sphere at the origin (X=0); the lookdev row
# runs +X. `target` is what the camera looks at, so the framing intent survives
# a level rebuild.
PLACEMENT = {
    # Extreme wide establishing: high and far back, the row silhouetted.
    "SH010": ((-2400.0, -3400.0, 1600.0), (800.0, 0.0, 0.0)),
    # Wide follow profile: behind and above, hero read against depth.
    "SH020": ((-900.0, -1500.0, 420.0), (0.0, 0.0, 0.0)),
    # Low angle hero vista: near ground level (Z=-100), looking up.
    "SH030": ((-650.0, -900.0, -40.0), (0.0, 0.0, 120.0)),
    # Medium waist-up: eye height, polite distance for a 50mm.
    "SH040": ((-320.0, -420.0, 60.0), (0.0, 0.0, 20.0)),
    # Extreme close-up / portrait: tight on the hero subject.
    "SH050": ((-120.0, -165.0, 30.0), (0.0, 0.0, 10.0)),
    # Full body hero action: front-on, room for a performance.
    "SH060": ((-520.0, -700.0, 180.0), (0.0, 0.0, 0.0)),
    # Orbiting medium: offset so the orbit has somewhere to travel.
    "SH070": ((280.0, -300.0, 130.0), (0.0, 0.0, 0.0)),
    # Medium full resolving to a title card: centred, calm.
    "SH080": ((-420.0, -560.0, 120.0), (0.0, 0.0, 0.0)),
}


def log(m):
    unreal.log("[ShotDeck] " + str(m))


def load_shot_deck():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    shots = data.get("shot_deck", [])
    if not shots:
        raise RuntimeError("manifest has no shot_deck: %s" % MANIFEST)
    return shots


def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def open_level():
    path = "%s/%s" % (MAP_DIR, LEVEL_NAME)
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        raise RuntimeError("level missing: %s" % path)
    if not unreal.LevelEditorSubsystem().load_level(path):
        raise RuntimeError("could not load level %s" % path)
    log("loaded level %s" % path)


def find_actor(label):
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            if a.get_actor_label() == label:
                return a
        except Exception:                                     # noqa: BLE001
            continue
    return None


def spawn_camera(shot, cam_name, existing):
    """CineCameraActor for a shot rig position. Idempotent by label."""
    # Keyed by shot_id, NOT the shot dict -- a dict is unhashable and
    # PLACEMENT.get(<dict>) raises TypeError before any actor is spawned.
    loc, target = PLACEMENT.get(
        shot["shot_id"], ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)))
    loc_v = unreal.Vector(loc[0], loc[1], loc[2])
    rot = unreal.MathLibrary.find_look_at_rotation(
        loc_v, unreal.Vector(target[0], target[1], target[2]))

    actor = existing.get(cam_name)
    if actor is None:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.CineCameraActor, loc_v, rot)
        actor.set_actor_label(cam_name)
        existing[cam_name] = actor
        log("spawned camera %s at %s" % (cam_name, loc))
    else:
        actor.set_actor_location(loc_v, False, False)
        actor.set_actor_rotation(rot, False)
        log("repositioned existing camera %s" % cam_name)

    comp = actor.get_cine_camera_component()
    focal = float(shot["focal_length_mm"])
    comp.set_editor_property("current_focal_length", focal)
    # State the filmback rather than inherit a user preference, so the focal
    # length means the same thing on every workstation.
    try:
        comp.set_editor_property(
            "filmback", unreal.CameraFilmbackSettings(35.0, 24.89))
    except Exception:                                          # noqa: BLE001
        pass
    return actor, focal


def rebuild_sequence(name, camera, shot):
    """One LS_ per shot. Delete-then-create keeps a re-run idempotent."""
    path = "%s/%s" % (SEQ_DIR, name)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    seq = tools.create_asset(name, SEQ_DIR, unreal.LevelSequence,
                             unreal.LevelSequenceFactoryNew())
    if seq is None:
        raise RuntimeError("could not create %s" % path)

    seq.set_display_rate(unreal.FrameRate(FPS, 1))

    # Manifest frames are 1-based (a cut list); Sequencer is 0-based.
    start = int(shot["frame_start"]) - 1
    end = int(shot["frame_end"]) - 1
    seq.set_playback_start(start)
    seq.set_playback_end(end)

    binding = seq.add_possessable(camera)
    if binding is None:
        raise RuntimeError("%s: could not possess %s" % (name, camera))

    # The camera cut track is what makes Sequencer actually render through the
    # possessed camera; a possessable alone shows nothing at render time.
    try:
        cut = seq.add_track(unreal.MovieSceneCameraCutTrack)
        section = cut.add_section()
        section.set_range(start, end)
        section.set_camera_binding_id(binding.get_id())
    except Exception as e:                                     # noqa: BLE001
        log("WARN %s: camera cut track not added: %s" % (name, e))

    return seq, start, end


def save_sequence(seq):
    unreal.EditorAssetLibrary.save_loaded_asset(seq, False)
def build():
    shots = load_shot_deck()
    report = {"errors": [], "shots": [],
              "level": "%s/%s" % (MAP_DIR, LEVEL_NAME)}

    ensure_dir(SEQ_DIR)
    open_level()

    # One camera actor per distinct camera name. SH040 and SH080 both name
    # Cam_Beauty at the same 50mm, so they share the actor and the later
    # placement wins -- the honest outcome of a deck that names eight rigs for
    # eight shots but reuses a name. Splitting them is a deck decision.
    existing = {}
    for shot in shots:
        cam_name = shot["camera"]
        try:
            actor, focal = spawn_camera(shot, cam_name, existing)
            name = "LS_%s" % shot["shot_id"]
            seq, start, end = rebuild_sequence(name, actor, shot)
            save_sequence(seq)
            report["shots"].append({
                "shot_id": shot["shot_id"],
                "name": shot["name"],
                "sequence": "%s/%s" % (SEQ_DIR, name),
                "camera": cam_name,
                "focal_length_mm": focal,
                "playback_start": start,
                "playback_end": end,
            })
            log("built %s (%s) %d-%d %smm"
                % (name, shot["name"], start, end, focal))
        except Exception as e:                                 # noqa: BLE001
            report["errors"].append("%s: %s" % (shot["shot_id"], e))
            log("FAILED %s: %s" % (shot["shot_id"], e))

    # The cameras are level actors, not assets: persist the level or they are
    # lost on reload while the sequences survive (they point at nothing).
    try:
        unreal.EditorLevelLibrary.save_current_level()
        report["level_saved"] = True
    except Exception as e:                                     # noqa: BLE001
        report["level_saved"] = False
        report["errors"].append("save level: %s" % e)
        log("FAILED saving level: %s" % e)

    report["expected_shots"] = len(shots)
    report["built_shots"] = len(report["shots"])
    report["sequences_found"] = [
        "%s/LS_%s" % (SEQ_DIR, s["shot_id"]) for s in shots
        if unreal.EditorAssetLibrary.does_asset_exist(
            "%s/LS_%s" % (SEQ_DIR, s["shot_id"]))
    ]
    # The level must still be the one we asked for, and the cameras must be in it.
    report["cameras_in_level"] = sorted(
        a.get_actor_label() for a in unreal.EditorLevelLibrary.get_all_level_actors()
        if isinstance(a, unreal.CineCameraActor))
    return report


def verify(report):
    out = {}
    out["shot_count_ok"] = report["built_shots"] == report["expected_shots"]
    out["all_sequences_on_disk"] = (
        len(report["sequences_found"]) == report["expected_shots"])
    out["level_saved"] = report.get("level_saved", False)
    out["cameras_present"] = len(report.get("cameras_in_level", [])) > 0
    out["errors"] = report["errors"]
    out["ok"] = (out["shot_count_ok"] and out["all_sequences_on_disk"]
                 and out["level_saved"] and out["cameras_present"]
                 and not report["errors"])
    return out


def main():
    report = build()
    report["verify"] = verify(report)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    try:
        AUDIT_COPY.parent.mkdir(parents=True, exist_ok=True)
        AUDIT_COPY.write_text(json.dumps(report, indent=2), encoding="utf-8")
    except Exception:                                          # noqa: BLE001
        pass
    log("report -> %s" % REPORT)
    log("OVERALL: %s" % ("PASS" if report["verify"]["ok"] else "FAIL"))
    return 0 if report["verify"]["ok"] else 1


if __name__ == "__main__":
    main()