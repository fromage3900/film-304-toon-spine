import unreal
import claireon
from pathlib import Path
import json

OUT = Path("G:/film-304-toon-spine/Saved/Audit/Showcase_20261018")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

cameras = {
    "shot1_ensemble_master.png": "Film_Cam_Showcase_Ensemble_v02",
    "shot2_dana_portrait.png": "Film_Cam_Showcase_DanaPortrait_v02",
    "shot3_lowangle_rake.png": "Film_Cam_Showcase_LowAngleRake_v02"
}

results = {}

for filename, cam_label in cameras.items():
    cam = None
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == cam_label:
            cam = a
            break
    if not cam:
        print(f"Error: Camera {cam_label} not found!")
        continue
    
    cloc = cam.get_actor_location()
    crot = cam.get_actor_rotation()
    
    # Pilot level editor viewport
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(cloc, crot)
    
    # Take high-resolution screenshot
    res = claireon.slate_screenshot(target="level_viewport", filename=filename, directory=str(OUT))
    results[cam_label] = res
    print(f"Rendered {filename} from {cam_label}:", res.get("summary"))

(OUT / "3shot_suite_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
print("All 3 showcase shots rendered successfully!")
