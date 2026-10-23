import unreal
import claireon
from pathlib import Path

OUT = Path("G:/film-304-toon-spine/Saved/Audit/Showcase_20261018")
OUT.mkdir(parents=True, exist_ok=True)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Deselect all actors
eas.set_selected_level_actors([])

# 1. 100% Seal all exterior horizon gaps
mesh_barbican = unreal.load_asset("/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_BarbicanScale")
mesh_slender = unreal.load_asset("/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_SlenderTower")
mat_concrete = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistConcrete")

for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl == "SM_Ext_Bay3_RightInfill":
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        if smc and mesh_barbican:
            smc.set_static_mesh(mesh_barbican)
            if mat_concrete:
                smc.set_material(0, mat_concrete)
        a.set_actor_location(unreal.Vector(250.0, 2700.0, -600.0), False, False)
        a.set_actor_scale3d(unreal.Vector(2.8, 2.8, 5.0))
        print("Updated SM_Ext_Bay3_RightInfill: sealed horizon completely")
    elif lbl == "SM_Ext_Bay3_FarRightInfill":
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        if smc and mesh_slender:
            smc.set_static_mesh(mesh_slender)
            if mat_concrete:
                smc.set_material(0, mat_concrete)
        a.set_actor_location(unreal.Vector(850.0, 2900.0, -600.0), False, False)
        a.set_actor_scale3d(unreal.Vector(3.5, 3.5, 6.0))
        print("Updated SM_Ext_Bay3_FarRightInfill: sealed peripheral bleed")

# 2. Add subtle warm key fill on David so his shirt/arms cel shading reads
david_fill = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Light_David_KeyFill":
        david_fill = a
        break

if not david_fill:
    david_fill = eas.spawn_actor_from_class(unreal.PointLight, unreal.Vector(-170.0, -80.0, 95.0), unreal.Rotator(0.0, 0.0, 0.0))
    david_fill.set_actor_label("Light_David_KeyFill")
    c = david_fill.get_component_by_class(unreal.PointLightComponent)
    if c:
        c.set_editor_property("intensity", 2.2)
        c.set_editor_property("attenuation_radius", 140.0)
        c.set_editor_property("light_color", unreal.Color(255, 215, 175, 255))
        c.set_editor_property("cast_shadows", False)
    print("Spawned Light_David_KeyFill")
else:
    david_fill.set_actor_location(unreal.Vector(-170.0, -80.0, 95.0), False, False)
    c = david_fill.get_component_by_class(unreal.PointLightComponent)
    if c:
        c.set_editor_property("intensity", 2.2)
        c.set_editor_property("attenuation_radius", 140.0)
    print("Updated Light_David_KeyFill")

# 3. Ensure Sam is hidden and far away
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cast_Sam":
        a.set_actor_hidden_in_game(True)
        a.set_actor_location(unreal.Vector(5000.0, 5000.0, -1000.0), False, False)

# Save current level cleanly
unreal.EditorLoadingAndSavingUtils.save_current_level()

# 4. Render Final 3-Shot Showcase Suite
showcase_shots = [
    ("Film_Cam_Showcase_Ensemble_v02", "Shot_01_NarrativeMaster_Dusk.png"),
    ("Film_Cam_Showcase_DanaPortrait_v02", "Shot_02_DanaPortrait_Dusk.png"),
    ("Film_Cam_Showcase_LowAngleRake_v02", "Shot_03_DavidLateNightRake_Dusk.png"),
]

for cam_name, filename in showcase_shots:
    cam_actor = None
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == cam_name:
            cam_actor = a
            break
    if cam_actor:
        loc = cam_actor.get_actor_location()
        rot = cam_actor.get_actor_rotation()
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(loc, rot)
        res = claireon.slate_screenshot(target="level_viewport", filename=filename, directory=str(OUT))
        print(f"Delivered {cam_name} -> {filename}: {res.get('summary') if isinstance(res, dict) else res}")
