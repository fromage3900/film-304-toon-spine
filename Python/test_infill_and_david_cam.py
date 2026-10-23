import unreal
import claireon
from pathlib import Path

OUT = Path("G:/film-304-toon-spine/Saved/Audit/Showcase_20261018")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Deselect all
eas.set_selected_level_actors([])

# 1. Fill the horizon gap at Bay 3 / Dana's right shoulder
# Check if SM_Ext_Bay3_RightInfill exists
infill = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SM_Ext_Bay3_RightInfill":
        infill = a
        break

mesh_tower = unreal.load_asset("/Game/Meshes/Office/SM_OFFICE_BarbicanScale")
mat_concrete = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistConcrete")

if not infill:
    infill = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(500.0, 3200.0, -250.0), unreal.Rotator(0.0, 15.0, 0.0))
    infill.set_actor_label("SM_Ext_Bay3_RightInfill")
    smc = infill.static_mesh_component
    smc.set_static_mesh(mesh_tower)
    if mat_concrete:
        smc.set_material(0, mat_concrete)
    infill.set_actor_scale3d(unreal.Vector(1.4, 1.4, 2.2))
    print("Spawned SM_Ext_Bay3_RightInfill at (500, 3200, -250)")
else:
    infill.set_actor_location(unreal.Vector(500.0, 3200.0, -250.0), False, False)
    infill.set_actor_scale3d(unreal.Vector(1.4, 1.4, 2.2))
    print("Updated SM_Ext_Bay3_RightInfill")

# Also add a second companion tower slightly further right to seal any peripheral bleed
infill2 = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SM_Ext_Bay3_FarRightInfill":
        infill2 = a
        break

mesh_slender = unreal.load_asset("/Game/Meshes/Office/SM_OFFICE_SlenderTower")
if not infill2:
    infill2 = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(1200.0, 3300.0, -200.0), unreal.Rotator(0.0, -20.0, 0.0))
    infill2.set_actor_label("SM_Ext_Bay3_FarRightInfill")
    smc2 = infill2.static_mesh_component
    smc2.set_static_mesh(mesh_slender)
    if mat_concrete:
        smc2.set_material(0, mat_concrete)
    infill2.set_actor_scale3d(unreal.Vector(2.0, 2.0, 3.0))
    print("Spawned SM_Ext_Bay3_FarRightInfill at (1200, 3300, -200)")
else:
    infill2.set_actor_location(unreal.Vector(1200.0, 3300.0, -200.0), False, False)
    print("Updated SM_Ext_Bay3_FarRightInfill")

# 2. Check Film_Cam_David_DeskSleep framing vs Film_Cam_Showcase_LowAngleRake_v02
# Let's take a screenshot from Film_Cam_David_DeskSleep to see how David looks!
cam_david = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cam_David_DeskSleep":
        cam_david = a
        break

if cam_david:
    loc = cam_david.get_actor_location()
    rot = cam_david.get_actor_rotation()
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(loc, rot)
    res = claireon.slate_screenshot(target="level_viewport", filename="test_david_sleep_cam.png", directory=str(OUT))
    print("Shot Film_Cam_David_DeskSleep -> test_david_sleep_cam.png:", res.get("summary") if isinstance(res, dict) else res)

# Also test Shot 2 (Dana portrait) with the new infill tower!
cam_dana = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cam_Showcase_DanaPortrait_v02":
        cam_dana = a
        break

if cam_dana:
    loc = cam_dana.get_actor_location()
    rot = cam_dana.get_actor_rotation()
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(loc, rot)
    res = claireon.slate_screenshot(target="level_viewport", filename="test_dana_portrait_infill.png", directory=str(OUT))
    print("Shot Film_Cam_Showcase_DanaPortrait_v02 -> test_dana_portrait_infill.png:", res.get("summary") if isinstance(res, dict) else res)
