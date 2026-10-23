import unreal
import claireon
from pathlib import Path

OUT = Path("G:/film-304-toon-spine/Saved/Audit/Showcase_20261018")
OUT.mkdir(parents=True, exist_ok=True)

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
cam = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cam_Showcase_Ensemble_v01":
        cam = a
        break

if cam:
    cloc = cam.get_actor_location()
    crot = cam.get_actor_rotation()
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(cloc, crot)
    res = claireon.slate_screenshot(target="level_viewport", filename="phase2_ensemble_check.png", directory=str(OUT))
    print("Screenshot result:", res)
else:
    print("Camera not found!")
