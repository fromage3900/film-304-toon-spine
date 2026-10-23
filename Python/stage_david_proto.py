"""Stage David for ONE prototype still in the live editor (no saves).

WHY this file: the David FBX (Downloads/C_DavidRenderTest_OSC.fbx, headless
import 2026-10-11) landed as C_DavidRenderTest_OSC + 9 david*_mat beside the
Dana set. Its 9 imported materials are raw openPBR-style surfaces, not the
film toon spine. This script spawns David in the ALREADY-OPEN office stage,
overrides the spawned component's materials with the existing toon MIs
(asset untouched), and fires one 1280x720 still from Cam_WS_SH020.

Run (film editor open on L_Toon_Shot_Office, via Monolith):
    editor_query run_python {command: "Python/stage_david_proto.py",
                             mode: execute_file}
Then poll Saved/Renders/office_stage/DAVID_SH020_proto_v01.png.

Writes nothing to the project: no level save, no asset mutation. The pending
record beside the PNG is the only disk write (gitignored Saved/).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import unreal  # noqa: E402

try:
    REPO = Path(__file__).resolve().parents[1]
except NameError:  # exec() in the in-editor Python console: no __file__
    REPO = Path("G:/film-304-toon-spine")
OUT_DIR = REPO / "Saved" / "Renders" / "office_stage"
STEM = "DAVID_SH030_proto_v01"
CAMERA_LABEL = "Cam_WS_SH030"
# Desk-side mark beside the staged Dana actor (-50,-930,30): clear of the
# BackWall (y=-1550) with a clean SH030 sightline. Faces -Y (the camera).
SPOT = (30.0, -930.0, 30.0)
FACE_YAW = -90.0

SK_PATH = "/Game/Meshes/Office/Props/C_DavidRenderTest_OSC"

# Existing film toon instances (built by Python/build_instances.py et al).
MI = {
    "skin": "/Game/Materials/Instances/MI_Toon_Character",
    "face": "/Game/Materials/Instances/MI_Toon_Face",
    "glass": "/Game/Materials/Instances/MI_Toon_Glass",
    "hair": "/Game/Materials/Instances/MI_Toon_Hair",
    "shirt": "/Game/Materials/Instances/MI_OfficeSpider_WorkerShirt",
    "shoes": "/Game/Materials/Instances/MI_OfficeSpider_Shoes",
    # No worker-pants row exists yet: pants ride the neutral character MI.
    "pants": "/Game/Materials/Instances/MI_Toon_Character",
}


def slot_target(slot_name):
    s = slot_name.lower()
    if "pants" in s:
        return MI["pants"]
    if "shirt" in s:
        return MI["shirt"]
    if "shoe" in s:
        return MI["shoes"]
    if "hair" in s:
        return MI["hair"]
    if "cornea" in s or "eyeint" in s or "glass" in s:
        return MI["glass"]
    if "eye" in s or "iris" in s or "face" in s:
        return MI["face"]
    return MI["skin"]


def main():
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = ues.get_editor_world()
    current = world.get_path_name() if world else ""
    if "L_Toon_Shot_Office" not in current:
        raise RuntimeError(
            "open L_Toon_Shot_Office first (current=%s); "
            "this script never switches levels" % current)

    cam = None
    actors = unreal.get_editor_subsystem(
        unreal.EditorActorSubsystem).get_all_level_actors()
    cam = None
    for a in actors:
        try:
            if a.get_actor_label() == CAMERA_LABEL:
                cam = a
            elif a.get_actor_label() == "David_Proto_Staging":
                a.destroy_actor()
        except Exception:  # noqa: BLE001
            continue
    if cam is None:
        raise RuntimeError("camera %s not in level" % CAMERA_LABEL)

    sk = unreal.EditorAssetLibrary.load_asset(SK_PATH)
    if sk is None:
        raise RuntimeError("skeletal mesh missing: %s" % SK_PATH)

    loc = cam.get_actor_location()
    spot = unreal.Vector(SPOT[0], SPOT[1], SPOT[2])
    face = unreal.Rotator(0.0, FACE_YAW, 0.0)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SkeletalMeshActor, spot, face)
    actor.set_actor_label("David_Proto_Staging")
    comp = actor.skeletal_mesh_component
    comp.set_skeletal_mesh_asset(sk)

    applied = []
    for i, skel_mat in enumerate(sk.materials):
        slot = skel_mat.material_slot_name
        try:
            name = str(slot)
        except Exception:  # noqa: BLE001
            name = "slot_%d" % i
        mi = unreal.EditorAssetLibrary.load_asset(slot_target(name))
        if mi is None:
            raise RuntimeError("toon MI missing for slot %s" % name)
        comp.set_material(i, mi)
        applied.append({"slot": i, "from": name,
                        "to": mi.get_path_name()})

    t0 = time.time()
    task = unreal.AutomationLibrary.take_high_res_screenshot(
        res_x=1280, res_y=720, filename=str(OUT_DIR / STEM),
        camera=cam, mask_enabled=False, capture_hdr=False,
        force_game_view=True)
    rec = {
        "shot_id": "DAVID_SH020", "stem": STEM,
        "expected_png": str(OUT_DIR / (STEM + ".png")),
        "requested_resolution": [1280, 720],
        "camera_label": CAMERA_LABEL,
        "actor": actor.get_actor_label(),
        "actor_location": [spot.x, spot.y, spot.z],
        "material_overrides": applied,
        "call_blocked_seconds": round(time.time() - t0, 2),
        "task_type": type(task).__name__ if task is not None else None,
        "note": "spawn + component overrides only; level/assets unsaved",
    }
    (OUT_DIR / ("_pending_" + STEM + ".json")).write_text(
        json.dumps(rec, indent=2), encoding="utf-8")
    print("DAVID_PROTO_FIRED " + json.dumps({
        "overrides": len(applied), "png": rec["expected_png"]}))


main()
