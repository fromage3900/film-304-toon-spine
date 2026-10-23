"""David prototype still v2: dedicated camera past the BackWall.

v1 proved the spawn/material path but fired through SH020/SH030, whose views
are mostly wall/void from behind BackWall (y=-1550). This pass duplicates
Cam_WS_SH030 (inheriting its proven lens/filmback), parks the duplicate at
(30,-1400,150) looking +Y at David beside the desk (30,-930,30), and fires
DAVID_CAM_proto_v01 at 1280x720. No level/asset saves.
"""

from __future__ import annotations

import json
import math as pymath
import time
from pathlib import Path

import unreal  # noqa: E402

try:
    REPO = Path(__file__).resolve().parents[1]
except NameError:  # exec() in the in-editor Python console: no __file__
    REPO = Path("G:/film-304-toon-spine")

OUT_DIR = REPO / "Saved" / "Renders" / "office_stage"
STEM = "DAVID_CAM_proto_v01"
SRC_CAM_LABEL = "Cam_WS_SH030"
CAM_LABEL = "David_Cam"
SK_PATH = "/Game/Meshes/Office/Props/C_DavidRenderTest_OSC"
SPOT = (30.0, -930.0, 30.0)
CAM_SPOT = (30.0, -1400.0, 150.0)
RIM_SPOT = (30.0, -300.0, 220.0)
# argv: [stem] [key_intensity] [rim_intensity 0=skip]
#   e.g. execute_file "G:/film-304-toon-spine/Python/stage_david_cam.py
#                     DAVID_CAM_proto_v02 7.0 0.0"

MI = {
    "skin": "/Game/Materials/Instances/MI_Toon_Character",
    "face": "/Game/Materials/Instances/MI_Toon_Face",
    "glass": "/Game/Materials/Instances/MI_Toon_Glass",
    "hair": "/Game/Materials/Instances/MI_Toon_Hair",
    "shirt": "/Game/Materials/Instances/MI_OfficeSpider_WorkerShirt",
    "shoes": "/Game/Materials/Instances/MI_OfficeSpider_Shoes",
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


def aim(actor, eye, target):
    """Face actor at target. Rotator arg order is self-corrected in place."""
    dx, dy, dz = target[0] - eye[0], target[1] - eye[1], target[2] - eye[2]
    yaw = pymath.degrees(pymath.atan2(dy, dx))
    pitch = pymath.degrees(pymath.atan2(dz, pymath.hypot(dx, dy)))
    want = (dx, dy, dz)
    wl = pymath.sqrt(dx * dx + dy * dy + dz * dz)
    best = None
    for cand in (unreal.Rotator(0.0, pitch, yaw),
                 unreal.Rotator(yaw, pitch, 0.0)):
        actor.set_actor_rotation(cand, False)
        f = actor.get_actor_forward_vector()
        dot = (f.x * dx + f.y * dy + f.z * dz) / wl
        if best is None or dot > best[0]:
            best = (dot, cand)
        if dot > 0.99:
            break
    print("AIM|dot=%.3f" % best[0])
    return best[0]


def main():
    import sys
    argv = sys.argv[1:] if len(sys.argv) > 1 else []
    stem = argv[0] if len(argv) > 0 else STEM
    key_i = float(argv[1]) if len(argv) > 1 else 5.0
    rim_i = float(argv[2]) if len(argv) > 2 else 0.0
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = ues.get_editor_world()
    current = world.get_path_name() if world else ""
    if "L_Toon_Shot_Office" not in current:
        raise RuntimeError("open L_Toon_Shot_Office first (current=%s)" % current)

    actors = unreal.get_editor_subsystem(
        unreal.EditorActorSubsystem).get_all_level_actors()
    src = None
    for a in list(actors):
        try:
            lbl = a.get_actor_label()
        except Exception:  # noqa: BLE001
            continue
        if lbl == SRC_CAM_LABEL:
            src = a
        elif lbl in ("David_Proto_Staging", CAM_LABEL, "David_Rim_Proto"):
            a.destroy_actor()
    if src is None:
        raise RuntimeError("source camera %s not in level" % SRC_CAM_LABEL)

    ella = unreal.EditorLevelLibrary
    key = None
    for a in list(actors):
        try:
            if a.get_actor_label() == "LGT_Fill":
                key = a
                break
        except Exception:  # noqa: BLE001
            continue
    if key is None:
        raise RuntimeError("LGT_Fill not in level")
    key.get_component_by_class(
        unreal.DirectionalLightComponent).set_editor_property(
            "intensity", key_i)
    kloc = key.get_actor_location()
    aim(key, (kloc.x, kloc.y, kloc.z),
        (kloc.x, kloc.y + 1000.0, kloc.z - 400.0))
    cam = ella.spawn_actor_from_class(
        unreal.CineCameraActor, unreal.Vector(*CAM_SPOT),
        unreal.Rotator(0.0, 0.0, 0.0))
    cam.set_actor_label(CAM_LABEL)
    aim(cam, CAM_SPOT, (SPOT[0], SPOT[1], 120.0))
    fwd = cam.get_actor_forward_vector()
    print("CAMFWD|%s" % ([round(fwd.x, 3), round(fwd.y, 3),
                          round(fwd.z, 3)],))
    sc = src.get_cine_camera_component()
    nc = cam.get_cine_camera_component()
    nc.set_editor_property(
        "current_focal_length",
        sc.get_editor_property("current_focal_length"))
    nc.set_editor_property(
        "filmback", sc.get_editor_property("filmback"))

    sk = unreal.EditorAssetLibrary.load_asset(SK_PATH)
    if sk is None:
        raise RuntimeError("skeletal mesh missing: %s" % SK_PATH)
    actor = ella.spawn_actor_from_class(
        unreal.SkeletalMeshActor, unreal.Vector(*SPOT),
        unreal.Rotator(0.0, 0.0, 0.0))
    actor.set_actor_label("David_Proto_Staging")
    aim(actor, SPOT, CAM_SPOT)
    comp = actor.skeletal_mesh_component
    comp.set_skeletal_mesh_asset(sk)

    applied = []
    for i, skel_mat in enumerate(sk.materials):
        try:
            name = str(skel_mat.material_slot_name)
        except Exception:  # noqa: BLE001
            name = "slot_%d" % i
        mi = unreal.EditorAssetLibrary.load_asset(slot_target(name))
        if mi is None:
            raise RuntimeError("toon MI missing for slot %s" % name)
        comp.set_material(i, mi)
        applied.append({"slot": i, "from": name,
                        "to": mi.get_path_name()})

    rim_desc = None
    if rim_i > 0.0:
        rim = ella.spawn_actor_from_class(
            unreal.DirectionalLight, unreal.Vector(*RIM_SPOT),
            unreal.Rotator(0.0, 0.0, 0.0))
        rim.set_actor_label("David_Rim_Proto")
        rim.get_component_by_class(
            unreal.DirectionalLightComponent).set_editor_property(
                "intensity", rim_i)
        aim(rim, RIM_SPOT, (SPOT[0], SPOT[1], 120.0))
        rim_desc = {"location": list(RIM_SPOT), "intensity": rim_i}

    t0 = time.time()
    task = unreal.AutomationLibrary.take_high_res_screenshot(
        res_x=1280, res_y=720, filename=str(OUT_DIR / stem),
        camera=cam, mask_enabled=False, capture_hdr=False,
        force_game_view=True)
    rec = {
        "shot_id": "DAVID_CAM", "stem": stem,
        "expected_png": str(OUT_DIR / (stem + ".png")),
        "requested_resolution": [1280, 720],
        "camera_label": CAM_LABEL,
        "camera_location": list(CAM_SPOT),
        "actor_location": list(SPOT),
        "key_intensity": key_i,
        "rim": rim_desc,
        "material_overrides": applied,
        "call_blocked_seconds": round(time.time() - t0, 2),
        "task_type": type(task).__name__ if task is not None else None,
        "note": "spawn + staging lights only; level/assets unsaved",
    }
    (OUT_DIR / ("_pending_" + stem + ".json")).write_text(
        json.dumps(rec, indent=2), encoding="utf-8")
    print("DAVID_CAM_FIRED " + json.dumps({
        "overrides": len(applied), "png": rec["expected_png"]}))


main()
