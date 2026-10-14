"""Capture a clean, film-oriented Dana material prototype from Humber.

The character and its assigned material instances remain untouched. The
camera, backdrop, floor, and studio lights are temporary editor actors in the
loaded map; reload the map with discard after capture. The map and assets are
never saved by this script.

Run in the Humber editor with one argument:
    Python/stage_dana_lookdev.py full
    Python/stage_dana_lookdev.py detail
    Python/stage_dana_lookdev.py cleanup
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import unreal


REPO = Path(__file__).resolve().parents[1]
MAP_PATH = "/Game/Maps/L_Toon_Shot_Office"
DANA_MESH_PATH = "/Game/Meshes/Office/Props/C_DanaRenderTest_OSC"
ENVIRONMENT_MATERIAL = "/Game/Materials/Instances/MI_Toon_Environment"
OUT_DIR = REPO / "Saved" / "Renders" / "dana_lookdev"
PREFIX = "DANA_Lookdev_Transient_"
REPORT_DIR = REPO / "Saved" / "Audit"

SLOT_TO_INSTANCE = {
    "danahair_mat": "MI_Dana_Hair",
    "danairis_mat": "MI_Dana_Iris",
    "danaeye_mat": "MI_Dana_EyeWhite",
    "danacornea_mat": "MI_Dana_Cornea",
    "danaeyeint_mat": "MI_Dana_EyeInterior",
    "danashoes_mat": "MI_Dana_Shoes",
    "danapantsbutton_mat": "MI_Dana_Button",
    "danapants_mat": "MI_Dana_Skirt",
    "danashirt_mat": "MI_Dana_Shirt",
    "danaskin_mat": "MI_Dana_Skin",
    "openpbr_shader1": "MI_Dana_Skin",
}


def log(message: str) -> None:
    unreal.log("[DanaLookdev] " + str(message))


def editor_actors():
    return unreal.get_editor_subsystem(
        unreal.EditorActorSubsystem).get_all_level_actors()


def actor_label(actor) -> str:
    try:
        return actor.get_actor_label()
    except Exception:  # noqa: BLE001
        return ""


def clean_transients() -> list[str]:
    destroyed = []
    for actor in list(editor_actors()):
        label = actor_label(actor)
        if label.startswith(PREFIX):
            destroyed.append(label)
            actor.destroy_actor()
    return destroyed


def find_dana():
    matches = []
    for actor in editor_actors():
        for component in actor.get_components_by_class(
                unreal.SkeletalMeshComponent):
            mesh = component.get_editor_property("skeletal_mesh")
            if mesh and mesh.get_path_name().split(".")[0] == DANA_MESH_PATH:
                matches.append((actor, component, mesh))
    if len(matches) != 1:
        raise RuntimeError("expected exactly one Dana skeletal component in %s; found %d"
                           % (MAP_PATH, len(matches)))
    return matches[0]


def validate_materials(component, mesh) -> list[dict]:
    rows = []
    for index, slot in enumerate(mesh.materials):
        slot_name = str(slot.material_slot_name)
        target_name = SLOT_TO_INSTANCE.get(slot_name.lower())
        if not target_name:
            raise RuntimeError("unmapped Dana slot %d: %s" % (index, slot_name))
        material = component.get_material(index)
        expected = "/Game/Materials/Instances/%s.%s" % (
            target_name, target_name)
        actual = material.get_path_name() if material else None
        rows.append({"index": index, "slot": slot_name,
                     "expected": expected, "actual": actual,
                     "ok": actual == expected})
    if len(rows) != len(SLOT_TO_INSTANCE) or not all(row["ok"] for row in rows):
        raise RuntimeError("Dana material assignment readback failed: %s" % rows)
    return rows


def stage_asset_preview_materials() -> None:
    """Temporarily expose the staged MIs to Unreal's skeletal preview scene."""
    import builtins

    mesh = unreal.load_asset(DANA_MESH_PATH)
    if mesh is None:
        raise RuntimeError("Dana skeletal mesh could not be loaded")
    original = [item.copy() for item in mesh.get_editor_property("materials")]
    staged = []
    for item in original:
        slot = str(item.material_slot_name).lower()
        target_name = SLOT_TO_INSTANCE.get(slot)
        if not target_name:
            raise RuntimeError("unmapped Dana asset slot: %s" % slot)
        material = unreal.load_asset(
            "/Game/Materials/Instances/%s" % target_name)
        if material is None:
            raise RuntimeError("missing staged material instance: %s" % target_name)
        override = item.copy()
        override.set_editor_property("material_interface", material)
        staged.append(override)
    setattr(builtins, "_dana_preview_original_materials", original)
    mesh.set_editor_property("materials", staged)
    log(json.dumps({"event": "asset_preview_materials_staged",
                    "slots": len(staged), "asset_saved": False}))


def restore_asset_preview_materials() -> None:
    """Discard temporary mesh-asset overrides by reloading the clean package."""
    import builtins

    mesh = unreal.load_asset(DANA_MESH_PATH)
    original = getattr(builtins, "_dana_preview_original_materials", None)
    if mesh is None or original is None:
        raise RuntimeError("no saved Dana preview material state to restore")
    mesh.set_editor_property("materials", original)
    package = mesh.get_outermost()
    result = unreal.EditorLoadingAndSavingUtils.reload_packages(
        [package],
        interaction_mode=unreal.ReloadPackagesInteractionMode.ASSUME_POSITIVE)
    delattr(builtins, "_dana_preview_original_materials")
    log(json.dumps({"event": "asset_preview_materials_restored",
                    "reload_result": str(result), "asset_saved": False}))


def look_at_rotation(origin, target):
    dx = float(target.x - origin.x)
    dy = float(target.y - origin.y)
    dz = float(target.z - origin.z)
    yaw = math.degrees(math.atan2(dy, dx))
    pitch = math.degrees(math.atan2(dz, math.hypot(dx, dy)))
    # Unreal Python's Rotator constructor takes roll, pitch, yaw in that order.
    return unreal.Rotator(0.0, pitch, yaw)


def spawn_transient(actor_class, location, rotation, label):
    actor = unreal.get_editor_subsystem(
        unreal.EditorActorSubsystem).spawn_actor_from_class(
            actor_class, location, rotation, transient=False)
    if actor is None:
        raise RuntimeError("could not spawn transient %s" % label)
    actor.set_actor_label(PREFIX + label)
    return actor


def configure_camera(dana, shot: str):
    loc = dana.get_actor_location()
    front = dana.get_actor_forward_vector()
    right = dana.get_actor_right_vector()
    if shot == "full":
        distance, side, height, target_height, focal = 290.0, 58.0, 61.0, 40.0, 50.0
        stem = "DANA_FULLBODY_v01"
    elif shot == "detail":
        distance, side, height, target_height, focal = 178.0, 28.0, 66.0, 55.0, 70.0
        stem = "DANA_UPPER_MATERIAL_DETAIL_v01"
    else:
        raise RuntimeError("shot must be 'full', 'detail', or 'cleanup'")

    cam_location = unreal.Vector(
        loc.x + front.x * distance + right.x * side,
        loc.y + front.y * distance + right.y * side,
        loc.z + height)
    target = unreal.Vector(loc.x, loc.y, loc.z + target_height)
    rotation = look_at_rotation(cam_location, target)
    camera = spawn_transient(unreal.CineCameraActor, cam_location,
                             rotation, "Camera_" + shot)
    component = camera.get_cine_camera_component()
    component.set_editor_property("current_focal_length", focal)
    component.set_editor_property("current_aperture", 8.0)

    # High-res editor screenshots use the active level viewport. Set it from
    # the same camera so the capture does not fall back to the empty default.
    unreal.get_editor_subsystem(
        unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(
            cam_location, rotation)

    # The office shot camera already uses an exact 16:9 prototype filmback.
    source = next((a for a in editor_actors()
                  if actor_label(a) == "Cam_WS_SH030"), None)
    if source:
        filmback = source.get_cine_camera_component().get_editor_property("filmback")
        component.set_editor_property("filmback", filmback)
    return camera, stem, cam_location, target


def dynamic_stage_material(component, index: int, source, base, accent):
    mid = component.create_dynamic_material_instance(
        index, source, "DanaLookdevStageMID")
    if mid is None:
        raise RuntimeError("could not create transient stage material")
    mid.set_vector_parameter_value(
        "BaseTint", unreal.LinearColor(base[0], base[1], base[2], 1.0))
    mid.set_vector_parameter_value(
        "AccentTint", unreal.LinearColor(accent[0], accent[1], accent[2], 1.0))
    mid.set_scalar_parameter_value("InkIntensity", 0.0)
    mid.set_scalar_parameter_value("BandStrength", 0.0)
    return mid


def spawn_stage(dana):
    loc = dana.get_actor_location()
    front = dana.get_actor_forward_vector()
    rotation = dana.get_actor_rotation()
    env = unreal.load_asset(ENVIRONMENT_MATERIAL)
    if env is None:
        raise RuntimeError("missing neutral Humber environment instance")

    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    plane = unreal.load_asset("/Engine/BasicShapes/Plane")
    if cube is None or plane is None:
        raise RuntimeError("engine cube or plane mesh missing")

    # Muted, unpatterned slate card behind Dana and a quiet neutral floor.
    wall_center = unreal.Vector(loc.x - front.x * 165.0,
                                loc.y - front.y * 165.0,
                                loc.z + 108.0)
    wall_rotation = unreal.Rotator(0.0, 0.0, rotation.yaw)
    wall = spawn_transient(unreal.StaticMeshActor, wall_center,
                           wall_rotation, "Backdrop")
    wall_comp = wall.get_component_by_class(unreal.StaticMeshComponent)
    wall_comp.set_static_mesh(cube)
    wall_comp.set_world_scale3d(unreal.Vector(0.08, 4.8, 2.6))
    dynamic_stage_material(wall_comp, 0, env,
                           (0.10, 0.14, 0.18), (0.16, 0.21, 0.25))

    floor = spawn_transient(unreal.StaticMeshActor,
                            unreal.Vector(loc.x, loc.y, loc.z - 1.0),
                            unreal.Rotator(0.0, 0.0, 0.0), "Floor")
    floor_comp = floor.get_component_by_class(unreal.StaticMeshComponent)
    floor_comp.set_static_mesh(plane)
    floor_comp.set_world_scale3d(unreal.Vector(7.0, 7.0, 1.0))
    dynamic_stage_material(floor_comp, 0, env,
                           (0.28, 0.29, 0.28), (0.36, 0.37, 0.36))

    target = unreal.Vector(loc.x, loc.y, loc.z + 48.0)
    key_location = unreal.Vector(loc.x + front.x * 185.0,
                                 loc.y + front.y * 185.0,
                                 loc.z + 166.0)
    fill_location = unreal.Vector(loc.x + front.x * 150.0 - front.y * 82.0,
                                 loc.y + front.y * 150.0 + front.x * 82.0,
                                 loc.z + 92.0)
    rim_location = unreal.Vector(loc.x - front.x * 150.0,
                                 loc.y - front.y * 150.0,
                                 loc.z + 150.0)

    light_specs = (
        ("Key", key_location, 3600.0, (255, 246, 233, 255), 170.0, 220.0),
        ("Fill", fill_location, 1300.0, (234, 242, 255, 255), 180.0, 220.0),
        ("Rim", rim_location, 1800.0, (255, 250, 242, 255), 150.0, 210.0),
    )
    for label, light_location, intensity, rgb, width, height in light_specs:
        light = spawn_transient(unreal.RectLight, light_location,
                                look_at_rotation(light_location, target),
                                "Light_" + label)
        component = light.get_component_by_class(unreal.RectLightComponent)
        component.set_editor_property("intensity", intensity)
        component.set_editor_property("light_color", unreal.Color(*rgb))
        component.set_editor_property("source_width", width)
        component.set_editor_property("source_height", height)
        component.set_editor_property("cast_shadows", label != "Fill")


def run(shot: str) -> None:
    world = unreal.get_editor_subsystem(
        unreal.UnrealEditorSubsystem).get_editor_world()
    current = world.get_path_name() if world else ""
    if shot == "preview_stage":
        stage_asset_preview_materials()
        return
    if shot == "preview_restore":
        restore_asset_preview_materials()
        return
    if not current.startswith(MAP_PATH + "."):
        raise RuntimeError("open %s first (current=%s)" % (MAP_PATH, current))

    removed = clean_transients()
    if shot == "cleanup":
        log(json.dumps({"cleaned": removed, "map_saved": False}))
        return

    dirty = [p.get_name() for p in
             unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
    if dirty:
        raise RuntimeError("refusing to stage over dirty map packages: %s" % dirty)

    actor, component, mesh = find_dana()
    material_rows = validate_materials(component, mesh)
    spawn_stage(actor)
    camera, stem, cam_location, target = configure_camera(actor, shot)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    task = unreal.AutomationLibrary.take_high_res_screenshot(
        res_x=1280, res_y=720, filename=str(OUT_DIR / stem), camera=camera,
        mask_enabled=False, capture_hdr=False, force_game_view=True)
    record = {
        "shot": shot,
        "stem": stem,
        "expected_png": str(OUT_DIR / (stem + ".png")),
        "resolution": [1280, 720],
        "camera_label": actor_label(camera),
        "camera_location": [round(cam_location.x, 3), round(cam_location.y, 3),
                            round(cam_location.z, 3)],
        "target": [round(target.x, 3), round(target.y, 3), round(target.z, 3)],
        "focal_length_mm": camera.get_cine_camera_component().get_editor_property(
            "current_focal_length"),
        "aperture": camera.get_cine_camera_component().get_editor_property(
            "current_aperture"),
        "dana_actor": actor_label(actor),
        "dana_mesh": mesh.get_path_name(),
        "dana_actor_count": 1,
        "material_slots": material_rows,
        "temporary_editor_stage": True,
        "map_saved": False,
        "map_requires_discard": True,
        "call_blocked_seconds": round(time.time() - t0, 2),
        "task_type": type(task).__name__ if task is not None else None,
        "note": "early rig/material prototype; source-rest geometry remains unchanged",
    }
    (OUT_DIR / ("_pending_" + stem + ".json")).write_text(
        json.dumps(record, indent=2), encoding="utf-8")
    transient_count = sum(1 for a in editor_actors()
                          if actor_label(a).startswith(PREFIX))
    log(json.dumps({"event": "capture_fired", "shot": shot,
                    "png": record["expected_png"],
                    "slots": len(material_rows),
                    "transient_actors": transient_count}))


def main() -> None:
    args = sys.argv[1:]
    run(args[0].lower() if args else "full")


main()
