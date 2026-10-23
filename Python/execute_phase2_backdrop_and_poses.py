import unreal
from pathlib import Path
import json

OUT = Path("G:/film-304-toon-spine/Saved/Audit/Showcase_20261018")
OUT.mkdir(parents=True, exist_ok=True)

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

report = {}

# 1. Fix HorizonWindows2 material
horizon_fixed = False
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "EST_HorizonWindows2":
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        dusk_mat = unreal.load_asset("/Game/Materials/Instances/Film304/Scene/Dusk20261018/MI_Dusk_HorizonWindows")
        if dusk_mat and smc:
            smc.set_material(0, dusk_mat)
            horizon_fixed = True
            print("Set EST_HorizonWindows2 material to MI_Dusk_HorizonWindows")
report["horizon_windows2_fixed"] = horizon_fixed

# 2. Check or Spawn Bay 3 Backdrop Tower
bay3_tower = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SM_Ext_Bay3_Barbican":
        bay3_tower = a
        break

barbican_mesh = unreal.load_asset("/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_BarbicanScale")
concrete_mat = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistConcrete")

if not bay3_tower and barbican_mesh:
    # Spawn at location continuing the Barbican building across Bay 3
    # EST_EstablishingE1_01_SM_OFFICE_BarbicanScale is at (-1658.7, 3079.0, -213.5), yaw=25.0, scale=(1.2, 1.2, 1.3)
    # The wall angle yaw is 25 deg. Along that axis: dx = +cos(25)*1500 = +1359, dy = +sin(25)*1500 = +634
    # Let's place it at (-600.0, 3600.0, -213.5)
    bay3_tower = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(-600.0, 3600.0, -213.5))
    bay3_tower.set_actor_label("SM_Ext_Bay3_Barbican")
    bay3_tower.set_folder_path("Film304/Environment/Exterior")
    smc = bay3_tower.get_component_by_class(unreal.StaticMeshComponent)
    smc.set_static_mesh(barbican_mesh)
    if concrete_mat:
        for i in range(smc.get_num_materials()):
            smc.set_material(i, concrete_mat)
    bay3_tower.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=25.0, roll=0.0), False)
    bay3_tower.set_actor_scale3d(unreal.Vector(1.2, 1.2, 1.3))
    print("Spawned SM_Ext_Bay3_Barbican at (-600, 3600, -213.5)")

report["bay3_tower_placed"] = bay3_tower is not None

# 3. Apply Dana Lean Desk Pose
dana_actor = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Subject_Dana_v08_CleanSkin":
        dana_actor = a
        break

dana_pose = unreal.load_asset("/Game/Staging/Film304Repaired_20261017/Poses_Headless/AS_Dana_LeanDesk_Polish01")
if dana_actor and dana_pose:
    skc = dana_actor.get_component_by_class(unreal.SkeletalMeshComponent)
    skc.set_editor_property("animation_mode", unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    anim_data = skc.get_editor_property("animation_data")
    anim_data.anim_to_play = dana_pose
    anim_data.saved_looping = True
    anim_data.saved_playing = True
    skc.set_editor_property("animation_data", anim_data)
    print("Assigned AS_Dana_LeanDesk_Polish01 to Dana")
    report["dana_pose_assigned"] = True
else:
    report["dana_pose_assigned"] = False

# 4. Save audit receipt
(OUT / "phase2_backdrop_and_poses.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("Phase 2 setup complete:", report)
