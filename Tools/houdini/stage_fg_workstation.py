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

# Load meshes and materials
desk_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_OfficeDesk_AC_FilmStage_20261016")
chair_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Chair_KS_FilmStage_20261016")
monitor_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_ComputerMonitor_AC_FilmStage_20261016")
lamp_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Lamp_EF_FilmStage_20261016")
plant_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Plant_PMB_FilmStage_20261016")
drawers_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_DeskDrawers_SG_FilmStage_20261016")

mat_desk = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_OfficeDesk_AC_FilmStage_20261016")
mat_chair = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_Chair_KS_FilmStage_20261016")
mat_monitor = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_ComputerMonitor_AC_FilmStage_20261016")
mat_lamp = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_Lamp_EF_FilmStage_20261016")
mat_plant = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_S_Plant_PMB_FilmStage_20261016")
mat_drawers = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_DeskDrawers_SG_FilmStage_20261016")

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

# Foreground Workstation Framing on the bottom right (X_local = 820.0, Y_local = -270.0)
# This sits directly in the foreground corner of SESSION_CAM_Cast without touching the sightline to Dana or David
spawn_or_upd("FG_Workstation_Desk", desk_mesh, mat_desk, (820.0, -270.0, -3.5), rot_room(yaw_offset=90.0), unreal.Vector(0.74, 0.74, 0.74))
spawn_or_upd("FG_Workstation_Monitor", monitor_mesh, mat_monitor, (820.0, -285.0, 52.56), rot_room(yaw_offset=80.0), unreal.Vector(0.70, 0.70, 0.70))
spawn_or_upd("FG_Workstation_Chair", chair_mesh, mat_chair, (820.0, -225.0, 0.0), rot_room(yaw_offset=-95.0), unreal.Vector(0.85, 0.85, 0.85))
spawn_or_upd("FG_Workstation_Drawers", drawers_mesh, mat_drawers, (860.0, -270.0, 0.0), rot_room(yaw_offset=90.0), unreal.Vector(0.70, 0.70, 0.70))

unreal.EditorLevelLibrary.save_current_level()
print("Staged rich foreground workstation corner and saved level!")
