import unreal
import claireon
from pathlib import Path

OUT = Path("G:/film-304-toon-spine/Saved/Audit/Showcase_20261018")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
eas.set_selected_level_actors([])

# 1. Properly assign meshes and materials to Bay 3 infills
mesh_barbican = unreal.load_asset("/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_BarbicanScale")
mesh_slender = unreal.load_asset("/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_SlenderTower")
mat_concrete = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistConcrete")

print("Loaded Barbican:", mesh_barbican)
print("Loaded Slender:", mesh_slender)

for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl == "SM_Ext_Bay3_RightInfill":
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        if smc and mesh_barbican:
            smc.set_static_mesh(mesh_barbican)
            if mat_concrete:
                smc.set_material(0, mat_concrete)
        a.set_actor_location(unreal.Vector(450.0, 3200.0, -250.0), False, False)
        a.set_actor_scale3d(unreal.Vector(1.6, 1.6, 2.5))
        print("Updated SM_Ext_Bay3_RightInfill with Barbican mesh")
    elif lbl == "SM_Ext_Bay3_FarRightInfill":
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        if smc and mesh_slender:
            smc.set_static_mesh(mesh_slender)
            if mat_concrete:
                smc.set_material(0, mat_concrete)
        a.set_actor_location(unreal.Vector(1100.0, 3100.0, -200.0), False, False)
        a.set_actor_scale3d(unreal.Vector(2.2, 2.2, 3.2))
        print("Updated SM_Ext_Bay3_FarRightInfill with SlenderTower mesh")

# 2. Position Light_David_DeskLamp right at David's lamp
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Light_David_DeskLamp":
        a.set_actor_location(unreal.Vector(-98.1, -118.9, 85.0), False, False)
        c = a.get_component_by_class(unreal.PointLightComponent)
        if c:
            c.set_editor_property("intensity", 4.5)
            c.set_editor_property("attenuation_radius", 180.0)
            c.set_editor_property("light_color", unreal.Color(255, 215, 170, 255))
            c.set_editor_property("cast_shadows", True)
        print("Moved Light_David_DeskLamp to David's desk lamp")
        break

# 3. Add/update Light_Dana_DeskLamp
dana_lamp_light = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Light_Dana_DeskLamp":
        dana_lamp_light = a
        break

if not dana_lamp_light:
    dana_lamp_light = eas.spawn_actor_from_class(unreal.PointLight, unreal.Vector(120.3, 53.5, 95.0), unreal.Rotator(0.0, 0.0, 0.0))
    dana_lamp_light.set_actor_label("Light_Dana_DeskLamp")
    c = dana_lamp_light.get_component_by_class(unreal.PointLightComponent)
    if c:
        c.set_editor_property("intensity", 4.0)
        c.set_editor_property("attenuation_radius", 220.0)
        c.set_editor_property("light_color", unreal.Color(255, 220, 175, 255))
        c.set_editor_property("cast_shadows", True)
    print("Spawned Light_Dana_DeskLamp at Dana's desk")
else:
    dana_lamp_light.set_actor_location(unreal.Vector(120.3, 53.5, 95.0), False, False)
    c = dana_lamp_light.get_component_by_class(unreal.PointLightComponent)
    if c:
        c.set_editor_property("intensity", 4.0)
        c.set_editor_property("attenuation_radius", 220.0)
        c.set_editor_property("light_color", unreal.Color(255, 220, 175, 255))
    print("Updated Light_Dana_DeskLamp")

# 4. Update Film_Cam_Showcase_LowAngleRake_v02 to match the perfect desk sleep framing
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cam_Showcase_LowAngleRake_v02":
        a.set_actor_location(unreal.Vector(-235.0, -165.0, 104.0), False, False)
        a.set_actor_rotation(unreal.Rotator(pitch=-15.2, yaw=46.1, roll=0.0), False)
        c = a.get_cine_camera_component()
        if c:
            c.set_editor_property("current_focal_length", 38.0)
            c.set_editor_property("current_aperture", 2.8)
            c.focus_settings.manual_focus_distance = 130.0
        print("Updated Film_Cam_Showcase_LowAngleRake_v02 to David desk sleep framing")
        break

# Deselect all actors
eas.set_selected_level_actors([])

# Save level
unreal.EditorLoadingAndSavingUtils.save_current_level()

# Capture all 3 showcase shots
cams = [
    ("Film_Cam_Showcase_Ensemble_v02", "shot1_ensemble_master_v02.png"),
    ("Film_Cam_Showcase_DanaPortrait_v02", "shot2_dana_portrait_v02.png"),
    ("Film_Cam_Showcase_LowAngleRake_v02", "shot3_lowangle_rake_v02.png"),
]

for cam_name, out_file in cams:
    cam_actor = None
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == cam_name:
            cam_actor = a
            break
    if cam_actor:
        loc = cam_actor.get_actor_location()
        rot = cam_actor.get_actor_rotation()
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(loc, rot)
        res = claireon.slate_screenshot(target="level_viewport", filename=out_file, directory=str(OUT))
        print(f"Captured {cam_name} -> {out_file}: {res.get('summary') if isinstance(res, dict) else res}")
