import unreal
import claireon
from pathlib import Path
import json

OUT = Path("G:/film-304-toon-spine/Saved/Audit/Showcase_20261018")
OUT.mkdir(parents=True, exist_ok=True)

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# 1. Update Bay 3 Barbican Tower
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SM_Ext_Bay3_Barbican":
        a.set_actor_location(unreal.Vector(-350.0, 3800.0, -213.5), False, False)
        a.set_actor_scale3d(unreal.Vector(1.6, 1.6, 1.4))
        a.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=25.0, roll=0.0), False)
        print("Updated SM_Ext_Bay3_Barbican transform to cover window opening")
        break

# 2. Update Sam pose to AS_Sam_ArmsCrossed_Polish01
sam_pose = unreal.load_asset("/Game/Staging/Film304Repaired_20261017/Poses_Headless/AS_Sam_ArmsCrossed_Polish01")
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cast_Sam":
        skc = a.get_component_by_class(unreal.SkeletalMeshComponent)
        skc.set_editor_property("animation_mode", unreal.AnimationMode.ANIMATION_SINGLE_NODE)
        anim_data = skc.get_editor_property("animation_data")
        anim_data.anim_to_play = sam_pose
        anim_data.saved_looping = True
        anim_data.saved_playing = True
        skc.set_editor_property("animation_data", anim_data)
        print("Assigned AS_Sam_ArmsCrossed_Polish01 to Sam")
        break

# 3. Pilot Film_Cam_Showcase_Ensemble_v01 and take proof
cam = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cam_Showcase_Ensemble_v01":
        cam = a
        break

if cam:
    cloc = cam.get_actor_location()
    crot = cam.get_actor_rotation()
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(cloc, crot)
    res = claireon.slate_screenshot(target="level_viewport", filename="phase2_ensemble_verified.png", directory=str(OUT))
    print("Screenshot result:", res)
