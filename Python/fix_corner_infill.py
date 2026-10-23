import unreal
import claireon
from pathlib import Path

OUT = Path("G:/film-304-toon-spine/Saved/Audit/Showcase_20261018")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Check if already spawned
infill = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Wall_NorthWest_Corner_Infill":
        infill = a
        break

cube_mesh = unreal.load_asset("/Engine/BasicShapes/Cube")
wall_mat = unreal.load_asset("/Game/Materials/Instances/UniversalFilm_20261016/MI_Dusk_Wall")
if not wall_mat:
    wall_mat = unreal.load_asset("/Game/Materials/Instances/Film304/Scene/Dusk20261018/MI_Dusk_Wall")

if not infill and cube_mesh:
    infill = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(28.5, 874.8, 175.0))
    infill.set_actor_label("Film_Wall_NorthWest_Corner_Infill")
    infill.set_folder_path("Film304/Environment/Walls")
    smc = infill.get_component_by_class(unreal.StaticMeshComponent)
    smc.set_static_mesh(cube_mesh)
    if wall_mat:
        smc.set_material(0, wall_mat)
    infill.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=-25.0, roll=0.0), False)
    # Gap is ~125cm with overlap, cube is 100cm base, so scale X = 1.35, Y = 0.3, Z = 3.5
    infill.set_actor_scale3d(unreal.Vector(1.35, 0.3, 3.5))
    print("Spawned Film_Wall_NorthWest_Corner_Infill at (28.5, 874.8, 175.0)")

# Also let's recheck Sam's pose!
# To make sure Sam's pose is evaluated, let's refresh or re-set animation on Sam
sam_pose = unreal.load_asset("/Game/Staging/Film304Repaired_20261017/Poses_Headless/AS_Sam_ArmsCrossed_Polish01")
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cast_Sam":
        skc = a.get_component_by_class(unreal.SkeletalMeshComponent)
        skc.set_editor_property("animation_mode", unreal.AnimationMode.ANIMATION_SINGLE_NODE)
        skc.play_animation(sam_pose, True)
        print("Called play_animation on Sam with AS_Sam_ArmsCrossed_Polish01")
        break

# Pilot camera and take screenshot
cam = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cam_Showcase_Ensemble_v01":
        cam = a
        break

if cam:
    cloc = cam.get_actor_location()
    crot = cam.get_actor_rotation()
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(cloc, crot)
    res = claireon.slate_screenshot(target="level_viewport", filename="phase2_infill_fixed.png", directory=str(OUT))
    print("Screenshot result:", res)
