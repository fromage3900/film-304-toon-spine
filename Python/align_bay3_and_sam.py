import unreal
import claireon
from pathlib import Path

OUT = Path("G:/film-304-toon-spine/Saved/Audit/Showcase_20261018")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# 1. Position SM_Ext_Bay3_Barbican exactly along Bay 3 sightline (X = -900, Y = 3600)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SM_Ext_Bay3_Barbican":
        a.set_actor_location(unreal.Vector(-900.0, 3600.0, -213.5), False, False)
        a.set_actor_scale3d(unreal.Vector(2.0, 2.0, 1.5))
        a.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=25.0, roll=0.0), False)
        print("Set SM_Ext_Bay3_Barbican to (-900, 3600, -213.5)")
        break

# 2. Position SM_Ext_Bay3_TowerCluster at (-1300, 4800, -400)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SM_Ext_Bay3_TowerCluster":
        a.set_actor_location(unreal.Vector(-1300.0, 4800.0, -400.0), False, False)
        a.set_actor_scale3d(unreal.Vector(1.5, 1.5, 1.5))
        print("Set SM_Ext_Bay3_TowerCluster to (-1300, 4800, -400)")
        break

# 3. Canonical Sam animation evaluation
sam_pose = unreal.load_asset("/Game/Staging/Film304Repaired_20261017/Poses_Headless/AS_Sam_ArmsCrossed_Polish01")
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cast_Sam":
        skc = a.get_component_by_class(unreal.SkeletalMeshComponent)
        skc.override_animation_data(sam_pose, True, False, 0.0, 1.0)
        skc.set_update_animation_in_editor(True)
        skc.play_animation(sam_pose, True)
        skc.set_position(0.0, False)
        print("Applied AS_Sam_ArmsCrossed_Polish01 canonically to Sam")
        break

# 4. Pilot camera and take screenshot
cam = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cam_Showcase_Ensemble_v01":
        cam = a
        break

if cam:
    cloc = cam.get_actor_location()
    crot = cam.get_actor_rotation()
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(cloc, crot)
    res = claireon.slate_screenshot(target="level_viewport", filename="phase2_bay3_aligned.png", directory=str(OUT))
    print("Screenshot result:", res)
