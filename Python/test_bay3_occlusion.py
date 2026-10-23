import unreal
import claireon
from pathlib import Path

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
el = unreal.EditorLevelLibrary
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

OUT = Path("G:/film-304-toon-spine/Saved/Audit/GapTest_20261018")
OUT.mkdir(parents=True, exist_ok=True)

# Find SM_Ext_Mid_SlenderTower or spawn a tower directly in Bay 3 sightline
# Cam: (400, -370, 150), Bay 3: (-176.8, 562.1, 150)
# Ray: Cam + t * dir. For t=12000 from Cam:
# X = 400 - 0.5262 * 12000 = -5914
# Y = -370 + 0.8504 * 12000 = 9835
# Z = 150 - 0.05 * 12000 = -450

bay3_tower = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SM_Ext_Bay3_OcclusionTower":
        bay3_tower = a
        break

mesh_slender = unreal.load_asset("/Game/Meshes/Architecture/SM_OFFICE_SlenderTower")
if not mesh_slender:
    mesh_slender = unreal.load_asset("/Game/Meshes/City/SM_OFFICE_SlenderTower")
if not mesh_slender:
    # Look for any tower mesh
    for a in eas.get_all_level_actors():
        if "SlenderTower" in a.get_actor_label():
            smc = a.get_component_by_class(unreal.StaticMeshComponent)
            if smc and smc.static_mesh:
                mesh_slender = smc.static_mesh
                break

mat_concrete = unreal.load_asset("/Game/Materials/Instances/UniversalFilm_20261016/MI_Film304_BrutalistConcrete")
if not mat_concrete:
    mat_concrete = unreal.load_asset("/Game/Materials/Recovery_Office_20261018/City/MI_CityConcrete_Night_v01")

if not bay3_tower and mesh_slender:
    bay3_tower = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(-6500.0, 10500.0, -1800.0))
    bay3_tower.set_actor_label("SM_Ext_Bay3_OcclusionTower")
    bay3_tower.set_folder_path("Film304/Environment/Exterior")
    smc = bay3_tower.get_component_by_class(unreal.StaticMeshComponent)
    smc.set_static_mesh(mesh_slender)
    if mat_concrete:
        for i in range(smc.get_num_materials()):
            smc.set_material(i, mat_concrete)
    bay3_tower.set_actor_scale3d(unreal.Vector(1.4, 1.4, 1.2))
    bay3_tower.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=45.0, roll=0.0), False)
    print("Spawned SM_Ext_Bay3_OcclusionTower at (-6500, 10500, -1800)")
elif bay3_tower:
    bay3_tower.set_actor_location(unreal.Vector(-6500.0, 10500.0, -1800.0), False, False)
    bay3_tower.set_actor_scale3d(unreal.Vector(1.4, 1.4, 1.2))
    print("Updated SM_Ext_Bay3_OcclusionTower location")

# Capture from Film_Cam_Showcase_Ensemble_v02
cam = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cam_Showcase_Ensemble_v02":
        cam = a
        break

if cam:
    start_loc, start_rot = el.get_level_viewport_camera_info()
    eas.set_selected_level_actors([])
    unreal.SystemLibrary.execute_console_command(world, "ShowFlag.Editor 0")
    el.set_level_viewport_camera_info(cam.get_actor_location(), cam.get_actor_rotation())
    res = claireon.slate_screenshot(target="level_viewport", filename="test_bay3_sealed.png", directory=str(OUT))
    unreal.SystemLibrary.execute_console_command(world, "ShowFlag.Editor 1")
    el.set_level_viewport_camera_info(start_loc, start_rot)
    print("Screenshot result:", res)
