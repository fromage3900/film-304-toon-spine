"""Capture and verify the two saved Dana film lookdev cameras in Unreal."""
from __future__ import annotations

import json
from pathlib import Path

import unreal


MAP_PATH = "/Game/Maps/Lookdev/L_Dana_Film_Lookdev"
MESH_PATH = "/Game/Meshes/Office/Props/C_DanaRenderTest_OSC"
OUT_DIR = Path(unreal.Paths.project_saved_dir()) / "Renders" / "dana_lookdev"
REPORT_PATH = Path(unreal.Paths.project_saved_dir()) / "Audit" / \
    "dana_film_render_verification.json"
SHOTS = (
    ("full", "DANA_FILM_Camera_FullBody", "DANA_FILM_FULLBODY_v01"),
    ("detail", "DANA_FILM_Camera_MaterialDetail",
     "DANA_FILM_MATERIAL_DETAIL_v01"),
)
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


@unreal.AutomationScheduler.add_latent_command
def capture_dana_film_views():
    # Allow the loaded lookdev map and materials to render before the first grab.
    yield
    world = unreal.get_editor_subsystem(
        unreal.UnrealEditorSubsystem).get_editor_world()
    if not world or not world.get_path_name().startswith(MAP_PATH + "."):
        raise RuntimeError("dedicated Dana film lookdev map is not open")

    all_actors = unreal.get_editor_subsystem(
        unreal.EditorActorSubsystem).get_all_level_actors()
    dana_rows = []
    for actor in all_actors:
        if actor.get_actor_label() != "DANA_FILM_Dana":
            continue
        for component in actor.get_components_by_class(
                unreal.SkeletalMeshComponent):
            mesh = component.get_skeletal_mesh_asset()
            if mesh and mesh.get_path_name().split(".")[0] == MESH_PATH:
                dana_rows.append((actor, component, mesh))
    if len(dana_rows) != 1:
        raise RuntimeError("expected one staged Dana mesh component; found %d"
                           % len(dana_rows))

    dana, component, mesh = dana_rows[0]
    slots = []
    for index, slot in enumerate(mesh.materials):
        slot_name = str(slot.material_slot_name)
        instance_name = SLOT_TO_INSTANCE.get(slot_name.lower())
        material = component.get_material(index)
        expected = "/Game/Materials/Instances/%s.%s" % (
            instance_name, instance_name) if instance_name else None
        actual = material.get_path_name() if material else None
        row = {"index": index, "slot": slot_name,
               "expected": expected, "actual": actual,
               "ok": bool(expected and actual == expected)}
        slots.append(row)
    if len(slots) != len(SLOT_TO_INSTANCE) or not all(r["ok"] for r in slots):
        raise RuntimeError("Dana material assignment verification failed")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    completed = []
    for shot, camera_label, stem in SHOTS:
        camera = next((a for a in all_actors
                       if a.get_actor_label() == camera_label), None)
        if camera is None:
            raise RuntimeError("missing Dana lookdev camera %s" % camera_label)
        task = unreal.AutomationLibrary.take_high_res_screenshot(
            res_x=1280, res_y=720, filename=str(OUT_DIR / stem), camera=camera,
            mask_enabled=False, capture_hdr=False, force_game_view=True)
        if task is None or not task.is_valid_task():
            raise RuntimeError("Unreal rejected the %s camera capture" % shot)
        while not task.is_task_done():
            yield
        yield
        image_path = OUT_DIR / (stem + ".png")
        if not image_path.exists() or image_path.stat().st_size <= 0:
            raise RuntimeError("capture task completed without %s" % image_path)
        completed.append({
            "shot": shot,
            "camera": camera_label,
            "image": str(image_path),
            "bytes": image_path.stat().st_size,
            "resolution": [1280, 720],
            "task_done": task.is_task_done(),
        })

    report = {
        "result": "pass",
        "map": MAP_PATH,
        "dana_actor": dana.get_actor_label(),
        "mesh": mesh.get_path_name(),
        "dana_component_count": 1,
        "material_slots": slots,
        "captures": completed,
        "qualification": "lookdev prototype; source rig pose and mesh unchanged",
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("[DanaFilmCapture] " + json.dumps(report))
