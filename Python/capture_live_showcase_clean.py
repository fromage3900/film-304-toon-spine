import json
from pathlib import Path
import unreal
import claireon

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
el = unreal.EditorLevelLibrary
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

OUT = Path("G:/film-304-toon-spine/Saved/Audit/LiveAudit_20261018")
OUT.mkdir(parents=True, exist_ok=True)

SHOWCASE_CAMS = [
    ("Film_Cam_Showcase_Ensemble_v02", "live_showcase_01_ensemble"),
    ("Film_Cam_Showcase_DanaPortrait_v02", "live_showcase_02_portrait"),
    ("Film_Cam_Showcase_LowAngleRake_v02", "live_showcase_03_rake"),
]

actors = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
start_loc, start_rot = el.get_level_viewport_camera_info()

# Deselect all actors to avoid blue/yellow wireframe selection highlights
eas.set_selected_level_actors([])

results = []
try:
    unreal.SystemLibrary.execute_console_command(world, "ShowFlag.Editor 0")
    for cam_label, stem in SHOWCASE_CAMS:
        cam = actors.get(cam_label)
        if not cam:
            results.append({"camera": cam_label, "error": "Not found"})
            continue
        el.set_level_viewport_camera_info(cam.get_actor_location(), cam.get_actor_rotation())
        res = claireon.slate_screenshot(target="level_viewport", filename=f"{stem}.png", directory=str(OUT))
        results.append({
            "camera": cam_label,
            "stem": stem,
            "res": res,
            "loc": [cam.get_actor_location().x, cam.get_actor_location().y, cam.get_actor_location().z],
            "rot": [cam.get_actor_rotation().pitch, cam.get_actor_rotation().yaw, cam.get_actor_rotation().roll],
        })
finally:
    unreal.SystemLibrary.execute_console_command(world, "ShowFlag.Editor 1")
    el.set_level_viewport_camera_info(start_loc, start_rot)

print("Capture results:")
print(json.dumps(results, indent=2))
