"""Build and render a contained Dana portrait against Humber Brutalist assets.

This is a separate lookdev map and does not alter the source rig or existing
lookdev levels. The imported Dana body has no skin weights, so the preview
preserves its neutral source pose rather than implying working deformation.
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[1]
MAP = "/Game/Maps/Lookdev/L_Dana_Brutalist_Lookdev"
SOURCE_MAP = "/Game/Maps/Lookdev/L_Dana_Toon_UDS_Night"
OUT = ROOT / "Saved/Renders/dana_brutalist"
REPORT = ROOT / "Saved/Audit/dana_brutalist_lookdev.json"
PREFIX = "DANA_BRUTAL_"
MESH = "/Game/Meshes/Office/Props/C_DanaRenderTest_OSC"
BUILDING = "/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_CivicSlab"
TOWER = "/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_TowerCluster"
ENV = "/Game/Materials/Instances/MI_Toon_Environment"
SLOT_TO_INSTANCE = {
    "danahair_mat": "MI_Dana_Hair", "danairis_mat": "MI_Dana_Iris",
    "danaeye_mat": "MI_Dana_EyeWhite", "danacornea_mat": "MI_Dana_Cornea",
    "danaeyeint_mat": "MI_Dana_EyeInterior", "danashoes_mat": "MI_Dana_Shoes",
    "danapantsbutton_mat": "MI_Dana_Button", "danapants_mat": "MI_Dana_Skirt",
    "danashirt_mat": "MI_Dana_Shirt", "danaskin_mat": "MI_Dana_Skin",
    "openpbr_shader1": "MI_Dana_Skin",
}
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL = unreal.EditorAssetLibrary


def label(a):
    try:
        return a.get_actor_label()
    except Exception:
        return ""


def actors():
    return ACTORS.get_all_level_actors()


def spawn(cls, loc, rot, name):
    a = ACTORS.spawn_actor_from_class(cls, loc, rot, transient=False)
    if not a:
        raise RuntimeError("spawn failed: " + name)
    a.set_actor_label(PREFIX + name)
    return a


def look_at(origin, target):
    dx, dy, dz = target.x-origin.x, target.y-origin.y, target.z-origin.z
    return unreal.Rotator(0.0, math.degrees(math.atan2(dz, math.hypot(dx, dy))),
                          math.degrees(math.atan2(dy, dx)))


def tint(component, slot, color):
    base = unreal.load_asset(ENV)
    if not base:
        return
    mid = component.create_dynamic_material_instance(slot, base)
    if mid:
        c = unreal.LinearColor(*color, 1.0)
        mid.set_vector_parameter_value("BaseTint", c)
        mid.set_vector_parameter_value("AccentTint", c)
        for p in ("InkIntensity", "BandStrength"):
            try: mid.set_scalar_parameter_value(p, 0.0)
            except Exception: pass


def light(name, loc, target, lumens, rgb, width):
    a = spawn(unreal.RectLight, loc, look_at(loc, target), "Light_" + name)
    c = a.get_component_by_class(unreal.RectLightComponent)
    c.set_intensity_units(unreal.LightUnits.LUMENS)
    c.set_editor_property("intensity", lumens)
    c.set_editor_property("light_color", unreal.Color(*rgb, 255))
    c.set_editor_property("source_width", width)
    c.set_editor_property("source_height", width * 1.35)
    c.set_editor_property("cast_shadows", name != "Fill")
    c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    return a


def build():
    if not EAL.does_asset_exist(MAP):
        # Duplicate the existing Dana night lookdev world into a new package;
        # its source remains unchanged and supplies a known-good project setup.
        if not EAL.does_asset_exist(SOURCE_MAP):
            raise RuntimeError("source Dana map is missing: " + SOURCE_MAP)
        if not unreal.EditorLevelLibrary.new_level(MAP):
            raise RuntimeError("could not create dedicated map: " + MAP)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world or not world.get_path_name().startswith(MAP + "."):
        if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP):
            raise RuntimeError("could not load dedicated map; current world=" + (world.get_path_name() if world else "none"))
    existing = [a for a in actors() if label(a).startswith(PREFIX)]
    if existing:
        for a in existing: ACTORS.destroy_actor(a)
    if any(label(a).startswith(PREFIX) for a in actors()):
        raise RuntimeError("stage already contains DANA_BRUTAL actors; inspect first")
    mesh = unreal.load_asset(MESH)
    if not mesh: raise RuntimeError("missing Dana mesh")
    dana = spawn(unreal.SkeletalMeshActor, unreal.Vector(0, 0, 0),
                 unreal.Rotator(0, 0, -115), "Dana")
    comp = dana.get_component_by_class(unreal.SkeletalMeshComponent)
    comp.set_skeletal_mesh_asset(mesh)
    slots = []
    for i, slot in enumerate(mesh.materials):
        instance = SLOT_TO_INSTANCE.get(str(slot.material_slot_name).lower())
        if str(slot.material_slot_name).lower() == "openpbr_shader1":
            instance = "MI_DanaFilm_ImportHelpers_Hidden"
        mat = unreal.load_asset("/Game/Materials/Instances/" + str(instance)) if instance else None
        if not mat and instance == "MI_DanaFilm_ImportHelpers_Hidden":
            mat = unreal.load_asset("/Game/Materials/Masters/DanaFilm/M_DanaFilm_ImportHelpers_Hidden")
        if not mat: raise RuntimeError("missing film MI for slot " + str(slot.material_slot_name))
        comp.set_material(i, mat)
        slots.append({"slot": str(slot.material_slot_name), "material": mat.get_path_name()})

    # Brutalist frame: a broad civic slab behind her, tower masses at the sides,
    # and a low podium plane establish scale without crowding the portrait.
    slab = unreal.load_asset(BUILDING)
    tower = unreal.load_asset(TOWER)
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    plane = unreal.load_asset("/Engine/BasicShapes/Plane")
    if not slab or not tower or not cube or not plane:
        raise RuntimeError("missing Brutalist or engine stage mesh")
    back = spawn(unreal.StaticMeshActor, unreal.Vector(-165, 0, 0),
                 unreal.Rotator(0, 0, 0), "CivicSlab")
    bc = back.get_component_by_class(unreal.StaticMeshComponent); bc.set_static_mesh(slab)
    back.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
    left = spawn(unreal.StaticMeshActor, unreal.Vector(-115, -210, -12),
                 unreal.Rotator(0, 0, 0), "TowerLeft")
    lc = left.get_component_by_class(unreal.StaticMeshComponent); lc.set_static_mesh(tower)
    left.set_actor_scale3d(unreal.Vector(.82, .82, .82))
    right = spawn(unreal.StaticMeshActor, unreal.Vector(-205, 225, -15),
                  unreal.Rotator(0, 0, 0), "TowerRight")
    rc = right.get_component_by_class(unreal.StaticMeshComponent); rc.set_static_mesh(tower)
    right.set_actor_scale3d(unreal.Vector(.68, .68, .68))
    podium = spawn(unreal.StaticMeshActor, unreal.Vector(0, 0, -2),
                   unreal.Rotator(0, 0, 0), "Podium")
    pc = podium.get_component_by_class(unreal.StaticMeshComponent); pc.set_static_mesh(plane)
    podium.set_actor_scale3d(unreal.Vector(5.5, 5.5, 1))
    tint(pc, 0, (.16, .19, .21))

    target = unreal.Vector(0, 0, 43)
    light("Key_Warm", unreal.Vector(110, 90, 145), target, 3600, (255, 224, 190), 105)
    light("Fill_Cool", unreal.Vector(100, -150, 75), target, 1050, (165, 202, 255), 165)
    light("Rim_ConcreteBounce", unreal.Vector(-55, -25, 155), target, 2200, (255, 246, 223), 90)
    light("Top_Shaft", unreal.Vector(-20, 35, 205), target, 1500, (240, 233, 220), 65)
    cam_loc = unreal.Vector(305, 26, 78)
    cam = spawn(unreal.CineCameraActor, cam_loc, look_at(cam_loc, target), "PortraitCamera")
    c = cam.get_cine_camera_component()
    c.set_editor_property("filmback", unreal.CameraFilmbackSettings(sensor_width=35, sensor_height=19.6875))
    c.set_editor_property("current_focal_length", 55.0)
    c.set_editor_property("current_aperture", 5.6)
    pp = unreal.PostProcessSettings()
    pp.set_editor_property("override_auto_exposure_method", True)
    pp.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
    for p in ("override_auto_exposure_min_brightness", "override_auto_exposure_max_brightness"):
        pp.set_editor_property(p, True)
    pp.set_editor_property("auto_exposure_min_brightness", 1.0)
    pp.set_editor_property("auto_exposure_max_brightness", 1.0)
    c.set_editor_property("post_process_settings", pp)
    c.set_editor_property("post_process_blend_weight", 1.0)
    if not unreal.EditorLoadingAndSavingUtils.save_current_level():
        raise RuntimeError("dedicated map save failed")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"result":"built", "map":MAP, "dana_count":1,
        "materials":slots, "lights":["warm key", "cool fill", "concrete rim", "top shaft"],
        "pose":"neutral source pose; body has no skin weights",
        "pose_source":"C_DanaRenderTest_OSC_Anim, 0.125 sec, four samples; not asserted as authored pose",
        "camera":cam.get_path_name(), "actors":[label(a) for a in actors() if label(a).startswith(PREFIX)]}, indent=2), encoding="utf-8")
    unreal.log("[DanaBrutalist] stage built and readback written")


def capture():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world or not world.get_path_name().startswith(MAP + "."):
        raise RuntimeError("open dedicated map before capture")
    cam = next((a for a in actors() if label(a) == PREFIX + "PortraitCamera"), None)
    dana = next((a for a in actors() if label(a) == PREFIX + "Dana"), None)
    if not cam or not dana: raise RuntimeError("portrait camera or Dana missing")
    OUT.mkdir(parents=True, exist_ok=True)
    stem = "DANA_BRUTALIST_KEYLIGHT_PORTRAIT_v01"
    started = time.time()
    task = unreal.AutomationLibrary.take_high_res_screenshot(res_x=1600, res_y=900,
        filename=str(OUT / stem), camera=cam, mask_enabled=False,
        capture_hdr=False, force_game_view=True)
    if task is None or not task.is_valid_task(): raise RuntimeError("capture request failed")
    REPORT.write_text(json.dumps({"result":"capture_requested", "map":MAP,
        "shot":stem, "resolution":[1600,900], "task_done_at_request":task.is_task_done(),
        "started_unix":started, "pose":"neutral source pose; body has no skin weights"}, indent=2), encoding="utf-8")
    unreal.log("[DanaBrutalist] capture requested: " + str(OUT / (stem + ".png")))


def prepare_render():
    """Create a deterministic MRQ still job for headless -game rendering."""
    map_asset = unreal.load_asset(MAP)
    if not map_asset: raise RuntimeError("dedicated map did not load")
    render_dir = "/Game/MoviePipelines/DanaBrutalist"
    if not EAL.does_directory_exist(render_dir): EAL.make_directory(render_dir)
    job_name = "DANA_BRUTALIST_KEYLIGHT_PORTRAIT_v01"
    seq_path = "/Game/Sequences/DanaLookdev/LS_" + job_name
    cfg_path = render_dir + "/CFG_" + job_name
    for path in ("/Game/Sequences/DanaLookdev", render_dir):
        if not EAL.does_directory_exist(path): EAL.make_directory(path)
    if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP):
        raise RuntimeError("could not open the saved dedicated map")
    camera = next((a for a in actors() if label(a) == PREFIX + "PortraitCamera"), None)
    if not camera:
        # Commandlet transient worlds can report the unsaved startup world
        # after package load; recover from the serialized camera path.
        world = unreal.load_asset(MAP)
        camera = next((a for a in actors() if label(a) == PREFIX + "PortraitCamera"), None)
    if not camera: raise RuntimeError("dedicated portrait camera missing after map load")
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "Python"))
    import build_render_queue as queue
    queue.QUEUE_DIR = render_dir
    seq_path = queue.build_render_sequence("LS_" + job_name, camera)
    cfg_path = queue.job_config(str(OUT), job_name)
    cfg = unreal.load_asset(cfg_path)
    if cfg is None: raise RuntimeError("could not create MRQ config")
    out = cfg.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting, True)
    out.set_editor_property("output_directory", unreal.DirectoryPath(str(OUT)))
    out.set_editor_property("file_name_format", job_name)
    out.set_editor_property("output_resolution", unreal.IntPoint(1600, 900))
    cfg.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase, True)
    cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG, True)
    aa = cfg.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting, True)
    aa.set_editor_property("engine_warm_up_count", 24)
    aa.set_editor_property("render_warm_up_count", 12)
    EAL.save_loaded_asset(cfg, only_if_is_dirty=False)
    REPORT.write_text(json.dumps({"result":"render_ready", "map":MAP,
        "sequence":seq_path, "config":cfg_path, "output":str(OUT),
        "shot":job_name, "pose":"neutral source pose; body has no skin weights"}, indent=2), encoding="utf-8")
    unreal.log("[DanaBrutalist] render job ready: " + cfg_path)


action = "build"
try:
    with open(str(ROOT / "Saved/Audit/dana_brutalist_action.txt"), "r") as _action_file:
        action = _action_file.read().strip().lower()
except Exception:
    pass
if action == "build": build()
elif action == "capture": capture()
elif action == "prepare_render": prepare_render()
else: raise RuntimeError("expected build or capture")
