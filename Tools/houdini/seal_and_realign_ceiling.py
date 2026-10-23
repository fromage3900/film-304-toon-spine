import math
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
yaw_rad = math.radians(-25.0)
cos_y = math.cos(yaw_rad)
sin_y = math.sin(yaw_rad)

def to_world(xl, yl, zl):
    return unreal.Vector(xl * cos_y - yl * sin_y, xl * sin_y + yl * cos_y, zl)

def rot_room(pitch=0.0, yaw_offset=0.0, roll=0.0):
    return unreal.Rotator(pitch=pitch, yaw=-25.0 + yaw_offset, roll=roll)

# 1. Destroy and cleanly respawn SM_Houdini_Ceiling_HVAC_Grid
ceiling_hvac_mesh = unreal.load_asset("/Game/Meshes/Architecture/SM_Houdini_Ceiling_HVAC_Grid")
mat_concrete = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistConcrete")
mat_metal = unreal.load_asset("/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Metal")
mat_troffer = unreal.load_asset("/Game/Materials/Instances/MI_Toon_Office_Troffer")
cube_mesh = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
mat_wall = unreal.load_asset("/Game/Materials/Instances/UniversalFilm_20261016/MI_Film_Wall")

for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SM_Houdini_Ceiling_HVAC_Grid":
        eas.destroy_actor(a)
        print("Destroyed old misaligned SM_Houdini_Ceiling_HVAC_Grid")

# Spawn fresh at (0,0,0)
hvac = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0.0, 0.0, 0.0), rot_room())
hvac.set_actor_label("SM_Houdini_Ceiling_HVAC_Grid")
if hasattr(hvac, "set_folder_path"):
    hvac.set_folder_path("Master_Ceiling_Architecture")
smc = hvac.get_component_by_class(unreal.StaticMeshComponent)
if smc:
    smc.set_mobility(unreal.ComponentMobility.MOVABLE)
    smc.set_static_mesh(ceiling_hvac_mesh)
    smc.set_material(0, mat_concrete)
    smc.set_material(1, mat_metal)
    smc.set_material(2, mat_troffer)
    print("Spawned fresh SM_Houdini_Ceiling_HVAC_Grid at (0,0,0) with 3 materials!")

loc = hvac.get_actor_location()
b = hvac.get_actor_bounds(False)
print(f"  New location: {loc}")
print(f"  New bounds origin: {b[0]}, ext: {b[1]}")

# 2. Seal the 85cm gap above the breakroom wall (Z = 265..350cm, Y_local ~ 830, X_local from -600 to 0)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Breakroom_UpperHeader":
        eas.destroy_actor(a)

header = eas.spawn_actor_from_class(unreal.StaticMeshActor, to_world(-320.0, 830.0, 307.5), rot_room())
header.set_actor_label("Film_Breakroom_UpperHeader")
header.set_actor_scale3d(unreal.Vector(6.50, 0.30, 0.85))
if hasattr(header, "set_folder_path"):
    header.set_folder_path("Master_Perimeter_Enclosure")
h_smc = header.get_component_by_class(unreal.StaticMeshComponent)
if h_smc:
    h_smc.set_static_mesh(cube_mesh)
    h_smc.set_material(0, mat_wall)
print("Sealed upper header above breakroom: Film_Breakroom_UpperHeader staged!")

# Also seal the North-East corridor boundary at Y_local = 830, X_local = 0..500
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_NorthEast_UpperHeader":
        eas.destroy_actor(a)

ne_header = eas.spawn_actor_from_class(unreal.StaticMeshActor, to_world(250.0, 830.0, 307.5), rot_room())
ne_header.set_actor_label("Film_NorthEast_UpperHeader")
ne_header.set_actor_scale3d(unreal.Vector(5.50, 0.30, 0.85))
if hasattr(ne_header, "set_folder_path"):
    ne_header.set_folder_path("Master_Perimeter_Enclosure")
ne_smc = ne_header.get_component_by_class(unreal.StaticMeshComponent)
if ne_smc:
    ne_smc.set_static_mesh(cube_mesh)
    ne_smc.set_material(0, mat_wall)
print("Sealed North-East upper header!")

# 3. Add rich foreground planter and corridor framing for shot 1
plant_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Plant_PMB_FilmStage_20261016")
mat_plant = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_S_Plant_PMB_FilmStage_20261016")

# Low architectural planter divider in foreground right
def spawn_or_upd(label, mesh, mat, loc_l, rot_r, scale_v, folder="Master_Foreground_Framing"):
    actor = None
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == label:
            actor = a
            break
    if not actor:
        actor = eas.spawn_actor_from_class(unreal.StaticMeshActor, to_world(*loc_l), rot_r)
        actor.set_actor_label(label)
    actor.set_actor_location(to_world(*loc_l), False, False)
    actor.set_actor_rotation(rot_r, False)
    actor.set_actor_scale3d(scale_v)
    if hasattr(actor, "set_folder_path"):
        actor.set_folder_path(folder)
    smc = actor.get_component_by_class(unreal.StaticMeshComponent)
    if smc:
        if mesh: smc.set_static_mesh(mesh)
        if mat: smc.set_material(0, mat)
    return actor

# Low brutalist planter box along circulation edge (foreground of SESSION_CAM_Cast)
spawn_or_upd("FG_Planter_Box_Edge", cube_mesh, mat_concrete, (650.0, -220.0, 25.0), rot_room(), unreal.Vector(2.40, 0.50, 0.50))
spawn_or_upd("FG_Planter_Foliage_01", plant_mesh, mat_plant, (600.0, -220.0, 50.0), rot_room(), unreal.Vector(1.10, 1.10, 1.10))
spawn_or_upd("FG_Planter_Foliage_02", plant_mesh, mat_plant, (700.0, -220.0, 50.0), rot_room(yaw_offset=45.0), unreal.Vector(1.10, 1.10, 1.10))

# Save the level
unreal.EditorLevelLibrary.save_current_level()
print("Saved level with all seals and ceiling architecture!")
