import unreal
import claireon
from pathlib import Path

OUT = Path("G:/film-304-toon-spine/Saved/Audit/Showcase_20261018")
OUT.mkdir(parents=True, exist_ok=True)

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Deselect all actors to avoid viewport gizmos and selection outlines
eas.set_selected_level_actors([])

# Check Sam
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cast_Sam":
        h = a.get_editor_property("hidden") if hasattr(a, "get_editor_property") else "unknown"
        print(f"Sam: hidden={h}, loc={a.get_actor_location()}")

# Pilot and shoot each of the 3 showcase cameras
cams = [
    ("Film_Cam_Showcase_Ensemble_v02", "shot1_ensemble_master.png"),
    ("Film_Cam_Showcase_DanaPortrait_v02", "shot2_dana_portrait.png"),
    ("Film_Cam_Showcase_LowAngleRake_v02", "shot3_lowangle_rake.png"),
]

for cam_name, out_file in cams:
    cam_actor = None
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == cam_name:
            cam_actor = a
            break
    
    if cam_actor:
        loc = cam_actor.get_actor_location()
        rot = cam_actor.get_actor_rotation()
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(loc, rot)
        # Pilot CineCamera in viewport if possible, or snap viewport camera info
        res = claireon.slate_screenshot(target="level_viewport", filename=out_file, directory=str(OUT))
        print(f"Captured {cam_name} -> {out_file}: {res.get('summary') if isinstance(res, dict) else res}")
    else:
        print(f"ERROR: Camera {cam_name} not found!")

unreal.EditorLoadingAndSavingUtils.save_current_level()
