import unreal
import claireon
from pathlib import Path

OUT = Path("G:/film-304-toon-spine/Saved/Audit/Showcase_20261018")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Check or spawn SM_Ext_Bay3_CompanionTower
companion = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SM_Ext_Bay3_CompanionTower":
        companion = a
        break

tower_mesh = unreal.load_asset("/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_SlenderTower")
concrete_mat = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistConcrete")

if not companion and tower_mesh:
    companion = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(-300.0, 3100.0, -300.0))
    companion.set_actor_label("SM_Ext_Bay3_CompanionTower")
    companion.set_folder_path("Film304/Environment/Exterior")
    smc = companion.get_component_by_class(unreal.StaticMeshComponent)
    smc.set_static_mesh(tower_mesh)
    if concrete_mat:
        for i in range(smc.get_num_materials()):
            smc.set_material(i, concrete_mat)
    companion.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=25.0, roll=0.0), False)
    companion.set_actor_scale3d(unreal.Vector(1.8, 1.8, 1.6))
    print("Spawned SM_Ext_Bay3_CompanionTower at (-300, 3100, -300)")
elif companion:
    companion.set_actor_location(unreal.Vector(-300.0, 3100.0, -300.0), False, False)
    companion.set_actor_scale3d(unreal.Vector(1.8, 1.8, 1.6))
    companion.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=25.0, roll=0.0), False)
    print("Updated SM_Ext_Bay3_CompanionTower")

# Pilot camera and take screenshot
cloc = unreal.Vector(240.0, -220.0, 115.0)
crot = unreal.Rotator(pitch=-2.272323, yaw=142.523820, roll=0.0)

unreal.EditorLevelLibrary.set_level_viewport_camera_info(cloc, crot)
res = claireon.slate_screenshot(target="level_viewport", filename="phase2_bay3_sealed.png", directory=str(OUT))
print("Screenshot result:", res)
