import unreal
import claireon
from pathlib import Path

OUT = Path("G:/film-304-toon-spine/Saved/Audit/Showcase_20261018")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Deselect all actors to avoid gizmos
eas.set_selected_level_actors([])

# Verify Sam is intact - DO NOT MODIFY TRANSFORM
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cast_Sam":
        print(f"Sam Transform Untouched: Loc={a.get_actor_location()}, Rot={a.get_actor_rotation()}")
        break

# Capture the 3 showcase shots to inspect framing
shots = [
    ("Film_Cam_Showcase_Ensemble_v02", "Shot_01_UserSam_MasterEnsemble.png"),
    ("Film_Cam_Showcase_DanaPortrait_v02", "Shot_02_UserSam_DanaPortrait.png"),
    ("Film_Cam_Showcase_LowAngleRake_v02", "Shot_03_UserSam_DavidRake.png"),
]

for cam_name, fname in shots:
    cam_actor = None
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == cam_name:
            cam_actor = a
            break
    if cam_actor:
        loc = cam_actor.get_actor_location()
        rot = cam_actor.get_actor_rotation()
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(loc, rot)
        res = claireon.slate_screenshot(target="level_viewport", filename=fname, directory=str(OUT))
        print(f"Delivered {cam_name} -> {fname}: {res.get('summary') if isinstance(res, dict) else res}")

# Save level state cleanly
unreal.EditorLoadingAndSavingUtils.save_current_level()
