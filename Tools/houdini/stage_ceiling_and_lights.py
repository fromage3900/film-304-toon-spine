import math
import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

yaw_rad = math.radians(-25.0)
cos_y = math.cos(yaw_rad)
sin_y = math.sin(yaw_rad)

def to_world(xl, yl, zl):
    xw = xl * cos_y - yl * sin_y
    yw = xl * sin_y + yl * cos_y
    return unreal.Vector(xw, yw, zl)

def rot_room(pitch=0.0, yaw_offset=0.0, roll=0.0):
    return unreal.Rotator(pitch=pitch, yaw=-25.0 + yaw_offset, roll=roll)

# Load Meshes & Materials
ceiling_hvac_mesh = unreal.load_asset("/Game/Meshes/Architecture/SM_Houdini_Ceiling_HVAC_Grid")
mat_concrete = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistConcrete")
mat_metal = unreal.load_asset("/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Metal")
mat_troffer = unreal.load_asset("/Game/Materials/Instances/MI_Toon_Office_Troffer")
cube_mesh = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
mat_wall = unreal.load_asset("/Game/Materials/Instances/UniversalFilm_20261016/MI_Film_Wall")

# 1. Update SM_Houdini_Ceiling_HVAC_Grid actor
hvac_actor = None
for a in EAS.get_all_level_actors():
    if a.get_actor_label() == "SM_Houdini_Ceiling_HVAC_Grid":
        hvac_actor = a
        break

if not hvac_actor:
    hvac_actor = EAS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0,0,0), rot_room())
    hvac_actor.set_actor_label("SM_Houdini_Ceiling_HVAC_Grid")

hvac_actor.set_actor_location(unreal.Vector(0,0,0), False, False)
hvac_actor.set_actor_rotation(rot_room(), False)
smc = hvac_actor.get_component_by_class(unreal.StaticMeshComponent)
if smc:
    smc.set_static_mesh(ceiling_hvac_mesh)
    smc.set_material(0, mat_concrete)
    smc.set_material(1, mat_metal)
    smc.set_material(2, mat_troffer)
    print("Assigned 3 materials to SM_Houdini_Ceiling_HVAC_Grid: Concrete, Metal, Troffer Emissive!")

# 2. Add Upward Ceiling Wash Lights
for idx, (lx, ly) in enumerate([(100.0, 100.0), (250.0, 500.0)], start=1):
    lbl = f"Light_Ceiling_Upwash_0{idx}"
    light_actor = None
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == lbl:
            light_actor = a
            break
    if not light_actor:
        light_actor = EAS.spawn_actor_from_class(unreal.RectLight, to_world(lx, ly, 260.0))
        light_actor.set_actor_label(lbl)
    
    light_actor.set_actor_location(to_world(lx, ly, 260.0), False, False)
    light_actor.set_actor_rotation(rot_room(pitch=85.0), False)
    rlc = light_actor.get_component_by_class(unreal.RectLightComponent)
    if rlc:
        rlc.set_intensity(12.0)
        rlc.set_light_color(unreal.LinearColor(r=0.92, g=0.95, b=1.0, a=1.0))
        rlc.set_attenuation_radius(450.0)
        rlc.set_source_width(160.0)
        rlc.set_source_height(160.0)
    print(f"Configured {lbl} pointing up at ceiling slab.")

# 3. Seal the wall gap on the left
wall_seam = None
for a in EAS.get_all_level_actors():
    if a.get_actor_label() == "Film_Wall_Seam_Infill":
        wall_seam = a
        break
if not wall_seam:
    wall_seam = EAS.spawn_actor_from_class(unreal.StaticMeshActor, to_world(-290.0, -85.0, 170.0), rot_room())
    wall_seam.set_actor_label("Film_Wall_Seam_Infill")

wall_seam.set_actor_location(to_world(-290.0, -85.0, 170.0), False, False)
wall_seam.set_actor_rotation(rot_room(), False)
wall_seam.set_actor_scale3d(unreal.Vector(0.20, 0.70, 3.40))
w_smc = wall_seam.get_component_by_class(unreal.StaticMeshComponent)
if w_smc:
    w_smc.set_static_mesh(cube_mesh)
    w_smc.set_material(0, mat_wall)
print("Sealed wall seam at Y_local = -85.0!")
