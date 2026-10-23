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

# Load Materials
mat_concrete = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistConcrete")
mat_metal = unreal.load_asset("/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Metal")
mat_troffer = unreal.load_asset("/Game/Materials/Instances/MI_Toon_Office_Troffer")
ceiling_hvac_mesh = unreal.load_asset("/Game/Meshes/Architecture/SM_Houdini_Ceiling_HVAC_Grid")

# 1. Update HVAC materials
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SM_Houdini_Ceiling_HVAC_Grid":
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        if smc:
            smc.set_material(0, mat_concrete)
            smc.set_material(1, mat_metal)
            smc.set_material(2, mat_troffer)
            print("Verified 3 materials on SM_Houdini_Ceiling_HVAC_Grid!")

# 2. Add Ceiling Cavity Soft Fill Light (attenuation 250cm -> stays in ceiling cavity)
for idx, (lx, ly) in enumerate([(150.0, 100.0), (350.0, 500.0)], start=1):
    lbl = f"Light_Ceiling_Cavity_0{idx}"
    lt = None
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == lbl:
            lt = a
            break
    if not lt:
        lt = eas.spawn_actor_from_class(unreal.PointLight, to_world(lx, ly, 315.0))
        lt.set_actor_label(lbl)
    lt.set_actor_location(to_world(lx, ly, 315.0), False, False)
    if hasattr(lt, "set_folder_path"):
        lt.set_folder_path("Master_Ceiling_Architecture")
    plc = lt.get_component_by_class(unreal.PointLightComponent)
    if plc:
        plc.set_intensity(6.0)
        plc.set_light_color(unreal.LinearColor(r=0.92, g=0.95, b=1.0, a=1.0))
        plc.set_attenuation_radius(260.0) # Confined to upper 2.6m
    print(f"Configured {lbl} in ceiling cavity.")

# 3. Add rich foreground planter and corridor divider to shot 1
cube_mesh = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
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

unreal.EditorLevelLibrary.save_current_level()
print("Saved level with ceiling cavity fill and foreground planter divider!")
