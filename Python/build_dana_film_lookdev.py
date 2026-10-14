"""Build and capture Humber's reusable Dana film lookdev stage.

Run in the Humber editor while /Game/Maps/Lookdev/L_Dana_Film_Lookdev is open:
    Python/build_dana_film_lookdev.py build
    Python/build_dana_film_lookdev.py full
    Python/build_dana_film_lookdev.py detail

The build creates one Dana actor, a quiet studio floor/backdrop, fixed studio
lights, and two 16:9 CineCameras. It assigns only Humber film material
instances. Capture outputs are still prototypes; the source rig pose and mesh
are not altered.
"""
from __future__ import annotations

import json
import math
import sys
import time
import builtins
from pathlib import Path

import unreal


REPO = Path(__file__).resolve().parents[1]
MAP_PATH = "/Game/Maps/Lookdev/L_Dana_Film_Lookdev"
DANA_MESH_PATH = "/Game/Meshes/Office/Props/C_DanaRenderTest_OSC"
ENVIRONMENT_MATERIAL = "/Game/Materials/Instances/MI_Toon_Environment"
OUT_DIR = REPO / "Saved" / "Renders" / "dana_lookdev"
PREFIX = "DANA_FILM_"

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
    unreal.log("[DanaFilmLookdev] " + str(message))


def actors():
    return unreal.get_editor_subsystem(
        unreal.EditorActorSubsystem).get_all_level_actors()


def label(actor) -> str:
    try:
        return actor.get_actor_label()
    except Exception:  # noqa: BLE001
        return ""


def spawn(actor_class, location, rotation, name):
    actor = unreal.get_editor_subsystem(
        unreal.EditorActorSubsystem).spawn_actor_from_class(
            actor_class, location, rotation, transient=False)
    if actor is None:
        raise RuntimeError("failed to spawn %s" % name)
    actor.set_actor_label(PREFIX + name)
    return actor


def look_at_rotation(origin, target):
    dx = float(target.x - origin.x)
    dy = float(target.y - origin.y)
    dz = float(target.z - origin.z)
    yaw = math.degrees(math.atan2(dy, dx))
    pitch = math.degrees(math.atan2(dz, math.hypot(dx, dy)))
    # Unreal Python's Rotator constructor order is roll, pitch, yaw.
    return unreal.Rotator(0.0, pitch, yaw)


def set_environment_tint(component, index, base, accent):
    source = unreal.load_asset(ENVIRONMENT_MATERIAL)
    if source is None:
        raise RuntimeError("missing Humber environment material instance")
    mid = component.create_dynamic_material_instance(index, source)
    if mid is None:
        raise RuntimeError("could not create stage environment material")
    mid.set_vector_parameter_value(
        "BaseTint", unreal.LinearColor(base[0], base[1], base[2], 1.0))
    mid.set_vector_parameter_value(
        "AccentTint", unreal.LinearColor(accent[0], accent[1], accent[2], 1.0))
    for parameter in ("InkIntensity", "BandStrength"):
        try:
            mid.set_scalar_parameter_value(parameter, 0.0)
        except Exception:  # noqa: BLE001
            pass


def find_dana():
    matches = []
    for actor in actors():
        if label(actor) != PREFIX + "Dana":
            continue
        for component in actor.get_components_by_class(
                unreal.SkeletalMeshComponent):
            mesh = component.get_skeletal_mesh_asset()
            if mesh and mesh.get_path_name().split(".")[0] == DANA_MESH_PATH:
                matches.append((actor, component, mesh))
    if len(matches) != 1:
        raise RuntimeError("lookdev map requires exactly one staged Dana; found %d"
                           % len(matches))
    return matches[0]


def validate_materials(component, mesh):
    rows = []
    for index, slot in enumerate(mesh.materials):
        slot_name = str(slot.material_slot_name)
        instance_name = SLOT_TO_INSTANCE.get(slot_name.lower())
        if not instance_name:
            raise RuntimeError("unmapped Dana slot %d: %s" % (index, slot_name))
        expected = "/Game/Materials/Instances/%s.%s" % (
            instance_name, instance_name)
        material = component.get_material(index)
        actual = material.get_path_name() if material else None
        rows.append({"index": index, "slot": slot_name,
                     "expected": expected, "actual": actual,
                     "ok": actual == expected})
    if len(rows) != len(SLOT_TO_INSTANCE) or not all(r["ok"] for r in rows):
        raise RuntimeError("staged Dana material readback failed: %s" % rows)
    return rows


def make_camera(name, location, target, focal):
    camera = spawn(unreal.CineCameraActor, location,
                   look_at_rotation(location, target), name)
    component = camera.get_cine_camera_component()
    component.set_editor_property("filmback", unreal.CameraFilmbackSettings(
        sensor_width=35.0, sensor_height=19.6875))
    component.set_editor_property("current_focal_length", focal)
    component.set_editor_property("current_aperture", 8.0)

    pp = unreal.PostProcessSettings()
    pp.set_editor_property("override_auto_exposure_method", True)
    pp.set_editor_property("auto_exposure_method",
                           unreal.AutoExposureMethod.AEM_MANUAL)
    pp.set_editor_property("override_auto_exposure_min_brightness", True)
    pp.set_editor_property("auto_exposure_min_brightness", 1.0)
    pp.set_editor_property("override_auto_exposure_max_brightness", True)
    pp.set_editor_property("auto_exposure_max_brightness", 1.0)
    component.set_editor_property("post_process_settings", pp)
    component.set_editor_property("post_process_blend_weight", 1.0)
    return camera


def make_light(name, location, target, lumens, rgb, width, height):
    light = spawn(unreal.RectLight, location,
                  look_at_rotation(location, target), "Light_" + name)
    component = light.get_component_by_class(unreal.RectLightComponent)
    component.set_intensity_units(unreal.LightUnits.LUMENS)
    component.set_editor_property("intensity", lumens)
    component.set_editor_property("light_color", unreal.Color(
        int(rgb[0]), int(rgb[1]), int(rgb[2]), 255))
    component.set_editor_property("source_width", width)
    component.set_editor_property("source_height", height)
    component.set_editor_property("cast_shadows", name != "Fill")
    component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    return light


def build():
    world = unreal.get_editor_subsystem(
        unreal.UnrealEditorSubsystem).get_editor_world()
    current = world.get_path_name() if world else ""
    if not current.startswith(MAP_PATH + "."):
        raise RuntimeError("open %s first (current=%s)" % (MAP_PATH, current))

    dirty = [p.get_name() for p in
             unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
    if dirty:
        raise RuntimeError("refusing to build over dirty packages: %s" % dirty)

    if any(label(a).startswith(PREFIX) for a in actors()):
        raise RuntimeError("lookdev stage already exists; inspect before rebuilding")

    mesh = unreal.load_asset(DANA_MESH_PATH)
    if mesh is None:
        raise RuntimeError("Dana skeletal mesh is missing")
    dana = spawn(unreal.SkeletalMeshActor, unreal.Vector(0.0, 0.0, 0.0),
                 unreal.Rotator(0.0, 0.0, -115.0), "Dana")
    component = dana.get_component_by_class(unreal.SkeletalMeshComponent)
    component.set_skeletal_mesh_asset(mesh)
    for index, slot in enumerate(mesh.materials):
        instance_name = SLOT_TO_INSTANCE.get(str(slot.material_slot_name).lower())
        material = unreal.load_asset(
            "/Game/Materials/Instances/%s" % instance_name) if instance_name else None
        if material is None:
            raise RuntimeError("missing material for Dana slot %s" % slot.material_slot_name)
        component.set_material(index, material)

    front = dana.get_actor_forward_vector()
    right = dana.get_actor_right_vector()
    actor_rotation = dana.get_actor_rotation()
    target_full = unreal.Vector(0.0, 0.0, 40.0)

    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    plane = unreal.load_asset("/Engine/BasicShapes/Plane")
    if cube is None or plane is None:
        raise RuntimeError("engine cube or plane is missing")

    backdrop_center = unreal.Vector(-front.x * 145.0,
                                    -front.y * 145.0,
                                    145.0)
    backdrop = spawn(unreal.StaticMeshActor, backdrop_center,
                     unreal.Rotator(0.0, 0.0, actor_rotation.yaw), "Backdrop")
    backdrop_component = backdrop.get_component_by_class(unreal.StaticMeshComponent)
    backdrop_component.set_static_mesh(cube)
    backdrop_component.set_world_scale3d(unreal.Vector(0.08, 4.8, 3.0))
    set_environment_tint(backdrop_component, 0,
                         (0.105, 0.145, 0.185), (0.15, 0.20, 0.25))

    floor = spawn(unreal.StaticMeshActor, unreal.Vector(0.0, 0.0, -1.0),
                  unreal.Rotator(0.0, 0.0, 0.0), "Floor")
    floor_component = floor.get_component_by_class(unreal.StaticMeshComponent)
    floor_component.set_static_mesh(plane)
    floor_component.set_world_scale3d(unreal.Vector(5.0, 5.0, 1.0))
    set_environment_tint(floor_component, 0,
                         (0.20, 0.21, 0.21), (0.28, 0.29, 0.29))

    key_location = unreal.Vector(front.x * 160.0 + right.x * 55.0,
                                 front.y * 160.0 + right.y * 55.0,
                                 132.0)
    fill_location = unreal.Vector(front.x * 145.0 - right.x * 100.0,
                                  front.y * 145.0 - right.y * 100.0,
                                  78.0)
    rim_location = unreal.Vector(-front.x * 95.0 + right.x * 30.0,
                                 -front.y * 95.0 + right.y * 30.0,
                                 125.0)
    make_light("Key", key_location, target_full, 2600.0,
               (255, 244, 229), 125.0, 155.0)
    make_light("Fill", fill_location, target_full, 750.0,
               (221, 233, 255), 170.0, 190.0)
    make_light("Rim", rim_location, target_full, 1100.0,
               (255, 249, 239), 110.0, 145.0)

    full_location = unreal.Vector(front.x * 300.0 + right.x * 24.0,
                                  front.y * 300.0 + right.y * 24.0,
                                  75.0)
    detail_location = unreal.Vector(front.x * 190.0 + right.x * 14.0,
                                    front.y * 190.0 + right.y * 14.0,
                                    92.0)
    make_camera("Camera_FullBody", full_location, target_full, 50.0)
    make_camera("Camera_MaterialDetail", detail_location,
                unreal.Vector(0.0, 0.0, 57.0), 72.0)

    slots = validate_materials(component, mesh)
    saved = unreal.EditorLoadingAndSavingUtils.save_current_level()
    if not saved:
        raise RuntimeError("lookdev map save failed")
    log(json.dumps({"event": "stage_built", "map": MAP_PATH,
                    "dana_count": 1, "material_slots": slots,
                    "actors": [label(a) for a in actors()
                               if label(a).startswith(PREFIX)],
                    "map_saved": True}))


def capture(shot: str):
    if shot == "full":
        camera_label = PREFIX + "Camera_FullBody"
        stem = "DANA_FILM_FULLBODY_v01"
    elif shot == "detail":
        camera_label = PREFIX + "Camera_MaterialDetail"
        stem = "DANA_FILM_MATERIAL_DETAIL_v01"
    else:
        raise RuntimeError("capture shot must be full or detail")

    world = unreal.get_editor_subsystem(
        unreal.UnrealEditorSubsystem).get_editor_world()
    if not world or not world.get_path_name().startswith(MAP_PATH + "."):
        raise RuntimeError("open the dedicated Dana lookdev map before capture")
    dana, component, mesh = find_dana()
    slots = validate_materials(component, mesh)
    camera = next((a for a in actors() if label(a) == camera_label), None)
    if camera is None:
        raise RuntimeError("missing capture camera: %s" % camera_label)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    task = unreal.AutomationLibrary.take_high_res_screenshot(
        res_x=1280, res_y=720, filename=str(OUT_DIR / stem), camera=camera,
        mask_enabled=False, capture_hdr=False, force_game_view=True)
    if task is None or not task.is_valid_task():
        raise RuntimeError("Unreal did not accept the high-resolution capture")
    setattr(builtins, "_dana_film_capture_task", task)
    record = {
        "shot": shot,
        "map": MAP_PATH,
        "camera": camera_label,
        "resolution": [1280, 720],
        "camera_location": [round(v, 3) for v in (
            camera.get_actor_location().x, camera.get_actor_location().y,
            camera.get_actor_location().z)],
        "camera_rotation": [round(v, 3) for v in (
            camera.get_actor_rotation().pitch, camera.get_actor_rotation().yaw,
            camera.get_actor_rotation().roll)],
        "dana_actor": label(dana),
        "dana_mesh": mesh.get_path_name(),
        "dana_count": 1,
        "material_slots": slots,
        "task_valid": task.is_valid_task(),
        "task_done_at_request": task.is_task_done(),
        "map_saved": True,
        "note": "film lookdev prototype; source rig pose and mesh unchanged",
    }
    pending = OUT_DIR / ("_pending_" + stem + ".json")
    pending.write_text(json.dumps(record, indent=2), encoding="utf-8")
    log(json.dumps({"event": "capture_requested", "shot": shot,
                    "png": str(OUT_DIR / (stem + ".png")),
                    "task_valid": task.is_valid_task(),
                    "task_done": task.is_task_done(),
                    "elapsed_seconds": round(time.time() - t0, 3)}))


def main():
    args = sys.argv[1:]
    action = args[0].lower() if args else "build"
    if action == "build":
        build()
    elif action in ("full", "detail"):
        capture(action)
    else:
        raise RuntimeError("expected build, full, or detail")


main()
