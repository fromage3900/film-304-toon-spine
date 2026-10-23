"""Configure MI_Toon_Glass with film-grade glossy reflections & transparency,
and unify all 3 window glass bay actors in L_Film_Office.
"""
import math
import unreal

ME = unreal.MaterialEditingLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

yaw_rad = math.radians(-25.0)
cos_y = math.cos(yaw_rad)
sin_y = math.sin(yaw_rad)

def to_world(xl, yl, zl):
    return unreal.Vector(xl * cos_y - yl * sin_y, xl * sin_y + yl * cos_y, zl)

def rot_room(pitch=0.0, yaw_offset=0.0, roll=0.0):
    return unreal.Rotator(pitch=pitch, yaw=-25.0 + yaw_offset, roll=roll)

cube_mesh = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
mat_glass = unreal.load_asset("/Game/Materials/Instances/MI_Toon_Glass")

if mat_glass:
    print("Setting overrides on MI_Toon_Glass...")
    ME.set_material_instance_scalar_parameter_value(mat_glass, "OpacityBase", 0.06)
    ME.set_material_instance_scalar_parameter_value(mat_glass, "DryRoughness", 0.02)
    ME.set_material_instance_scalar_parameter_value(mat_glass, "GlassSpecular", 1.0)
    ME.set_material_instance_scalar_parameter_value(mat_glass, "FresnelPower", 2.2)
    ME.set_material_instance_scalar_parameter_value(mat_glass, "RampStrength", 0.50)
    ME.set_material_instance_vector_parameter_value(mat_glass, "BaseTint", unreal.LinearColor(0.01, 0.02, 0.03, 1.0))
    ME.set_material_instance_vector_parameter_value(mat_glass, "AccentTint", unreal.LinearColor(0.08, 0.15, 0.22, 1.0))
    ME.set_material_instance_vector_parameter_value(mat_glass, "FresnelColor", unreal.LinearColor(0.85, 0.95, 1.0, 1.0))
    ME.update_material_instance(mat_glass)
    print("SUCCESS: MI_Toon_Glass updated with film-grade parameters!")

# Unify all 3 window bays
bays = [
    ("SM_Glass_WindowBay_01", 25.0),
    ("SM_Glass_WindowBay_02", 255.0),
    ("SM_Glass_WindowBay_03", 485.0)
]

for name, y_pos in bays:
    actor = None
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == name:
            actor = a
            break
    if not actor:
        actor = EAS.spawn_actor_from_class(unreal.StaticMeshActor, to_world(-290.0, y_pos, 150.0), rot_room())
        actor.set_actor_label(name)
        if hasattr(actor, "set_folder_path"):
            actor.set_folder_path("Master_Perimeter_Enclosure")
            
    actor.set_actor_location(to_world(-290.0, y_pos, 150.0), False, False)
    actor.set_actor_rotation(rot_room(), False)
    actor.set_actor_scale3d(unreal.Vector(0.04, 2.26, 3.00))
    smc = actor.get_component_by_class(unreal.StaticMeshComponent)
    if smc:
        smc.set_static_mesh(cube_mesh)
        smc.set_material(0, mat_glass)
    print(f"  Unified {name} at Y_local = {y_pos:.1f} with Cube mesh and MI_Toon_Glass")

unreal.EditorLevelLibrary.save_current_level()
print("Saved level with unified window bays.")
