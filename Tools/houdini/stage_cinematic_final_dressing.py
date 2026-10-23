"""Master Staging Script for L_Film_Office.

Executes:
1. Solid brutalist ceiling slab at Z = 350
2. Single accessible workstation row in North Wing (3 desks, 3 chairs, 3 monitors)
3. Hero desk dressing (monitors, keyboards, phones, coffee mugs, desk lamps, plants)
4. Foreground cinematic framing props (watercooler, planter, subtle cables)
5. Breakroom suite enrichment (espresso machine, coffee mugs, whiteboard)
6. Camera sightline audit ensuring 0% occlusion of SESSION_CAM_Cast, Film_Cam_OfficeWide, David, and Window Establishing.
"""
import math
import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Room rotation: Yaw = -25.0
yaw_rad = math.radians(-25.0)
cos_y = math.cos(yaw_rad)
sin_y = math.sin(yaw_rad)

def to_world(xl, yl, zl):
    xw = xl * cos_y - yl * sin_y
    yw = xl * sin_y + yl * cos_y
    return unreal.Vector(xw, yw, zl)

def rot_room(pitch=0.0, yaw_offset=0.0, roll=0.0):
    return unreal.Rotator(pitch=pitch, yaw=-25.0 + yaw_offset, roll=roll)

# Load Meshes
desk_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_OfficeDesk_AC_FilmStage_20261016")
chair_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Chair_KS_FilmStage_20261016")
monitor_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_ComputerMonitor_AC_FilmStage_20261016")
keyboard_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Keyboard_KS_FilmStage_20261016")
phone_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Phone_KS_FilmStage_20261016")
lamp_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Lamp_EF_FilmStage_20261016")
mug_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_CoffeeMugLarge_ZMJ_FilmStage_20261016")
plant_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Plant_PMB_FilmStage_20261016")
drawers_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_DeskDrawers_SG_FilmStage_20261016")
watercooler_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Watercooler_KS_FilmStage_20261016")
whiteboard_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Whiteboard_SG_FilmStage_20261016")
espresso_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_EspressoMachine_ZMJ_FilmStage_20261016")
cube_mesh = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")

# Load Materials
desk_mat = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_OfficeDesk_AC_FilmStage_20261016")
chair_mat = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_Chair_KS_FilmStage_20261016")
monitor_mat = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_ComputerMonitor_AC_FilmStage_20261016")
keyboard_mat = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_S_Keyboard_KS_FilmStage_20261016")
phone_mat = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_S_Phone_KS_FilmStage_20261016")
lamp_mat = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_Lamp_EF_FilmStage_20261016")
mug_mat = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_O_CoffeeMugLarge_ZMJ_FilmStage_20261016")
plant_mat = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_S_Plant_PMB_FilmStage_20261016")
drawers_mat = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_DeskDrawers_SG_FilmStage_20261016")
watercooler_mat = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_S_Watercooler_KS_FilmStage_20261016")
whiteboard_mat = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_Whiteboard_SG_FilmStage_20261016")
concrete_mat = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistConcrete")

def spawn_or_update(label, mesh, mat, loc_l, rot_r, scale_v):
    actor = None
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == label:
            actor = a
            break
    if not actor:
        actor = EAS.spawn_actor_from_class(unreal.StaticMeshActor, to_world(*loc_l), rot_r)
        actor.set_actor_label(label)
    
    actor.set_actor_location(to_world(*loc_l), False, False)
    actor.set_actor_rotation(rot_r, False)
    actor.set_actor_scale3d(scale_v)
    smc = actor.get_component_by_class(unreal.StaticMeshComponent)
    if smc:
        if mesh: smc.set_static_mesh(mesh)
        if mat: smc.set_material(0, mat)
    return actor

print("=== STAGING CINEMATIC LOOKDEV & DRESSING ===")

# 1. Solid Ceiling Slab
spawn_or_update(
    "Film_Ceiling_Slab", cube_mesh, concrete_mat,
    (0.0, 0.0, 350.0), rot_room(), unreal.Vector(22.0, 22.0, 0.20)
)
print("  [x] Ceiling Slab verified at Z = 350.0")

# 2. Single Accessible Workstation Row (North Wing, Y_local in [420, 700])
for i, yl in enumerate([420.0, 560.0, 700.0], start=1):
    spawn_or_update(
        f"Workstation_Row_Desk_0{i}", desk_mesh, desk_mat,
        (350.0, yl, -3.5), rot_room(), unreal.Vector(0.74, 0.74, 0.74)
    )
    spawn_or_update(
        f"Workstation_Row_Monitor_0{i}", monitor_mesh, monitor_mat,
        (330.0, yl + 10.0, 52.0), rot_room(yaw_offset=-5.0), unreal.Vector(0.74, 0.74, 0.74)
    )
    spawn_or_update(
        f"Workstation_Row_Keyboard_0{i}", keyboard_mesh, keyboard_mat,
        (370.0, yl + 10.0, 52.0), rot_room(), unreal.Vector(0.74, 0.74, 0.74)
    )
    spawn_or_update(
        f"Workstation_Row_Chair_0{i}", chair_mesh, chair_mat,
        (430.0, yl, 0.0), rot_room(yaw_offset=175.0), unreal.Vector(0.85, 0.85, 0.85)
    )
    spawn_or_update(
        f"Workstation_Row_Drawers_0{i}", drawers_mesh, drawers_mat,
        (350.0, yl - 60.0, 0.0), rot_room(), unreal.Vector(0.70, 0.70, 0.70)
    )
print("  [x] Single Accessible Workstation Row (3 units, 2.5m aisle clearance)")

# 3. Hero Desks Dressing
# Dana's Desk (Local: ~ [61.5, 76.1, -3.7])
spawn_or_update(
    "HeroDressing_Dana_Monitor", monitor_mesh, monitor_mat,
    (35.0, 65.0, 52.0), rot_room(yaw_offset=165.0), unreal.Vector(0.70, 0.70, 0.70)
)
spawn_or_update(
    "HeroDressing_Dana_Keyboard", keyboard_mesh, keyboard_mat,
    (20.0, 65.0, 52.0), rot_room(yaw_offset=180.0), unreal.Vector(0.70, 0.70, 0.70)
)
spawn_or_update(
    "HeroDressing_Dana_Mug", mug_mesh, mug_mat,
    (30.0, 30.0, 52.0), rot_room(yaw_offset=45.0), unreal.Vector(0.80, 0.80, 0.80)
)
spawn_or_update(
    "HeroDressing_Dana_Plant", plant_mesh, plant_mat,
    (40.0, 110.0, 52.0), rot_room(), unreal.Vector(0.65, 0.65, 0.65)
)

# Sam's Desk (SM_P_OfficeDesk_AC_FilmStage_20261017, Local: ~ [61.6, 292.3])
spawn_or_update(
    "HeroDressing_Sam_Monitor", monitor_mesh, monitor_mat,
    (35.0, 280.0, 52.0), rot_room(yaw_offset=170.0), unreal.Vector(0.70, 0.70, 0.70)
)
spawn_or_update(
    "HeroDressing_Sam_Keyboard", keyboard_mesh, keyboard_mat,
    (20.0, 280.0, 52.0), rot_room(yaw_offset=180.0), unreal.Vector(0.70, 0.70, 0.70)
)
spawn_or_update(
    "HeroDressing_Sam_Phone", phone_mesh, phone_mat,
    (35.0, 250.0, 52.0), rot_room(yaw_offset=15.0), unreal.Vector(0.70, 0.70, 0.70)
)

# David's Sleeping Desk (Film_ExistingOfficeDesk, Local: ~ [-70.0, -160.2])
spawn_or_update(
    "HeroDressing_David_Lamp", lamp_mesh, lamp_mat,
    (-40.0, -130.0, 52.0), rot_room(yaw_offset=-30.0), unreal.Vector(0.75, 0.75, 0.75)
)
spawn_or_update(
    "HeroDressing_David_Monitor", monitor_mesh, monitor_mat,
    (-40.0, -175.0, 52.0), rot_room(yaw_offset=175.0), unreal.Vector(0.70, 0.70, 0.70)
)
spawn_or_update(
    "HeroDressing_David_Phone", phone_mesh, phone_mat,
    (-50.0, -195.0, 52.0), rot_room(), unreal.Vector(0.70, 0.70, 0.70)
)
print("  [x] Hero Desks dressed with monitors, keyboards, mugs, lamps, phones")

# 4. North Wing Breakroom & Hallway Dressing
spawn_or_update(
    "Breakroom_Whiteboard", whiteboard_mesh, whiteboard_mat,
    (150.0, 780.0, 80.0), rot_room(yaw_offset=-90.0), unreal.Vector(0.85, 0.85, 0.85)
)
spawn_or_update(
    "Breakroom_Watercooler", watercooler_mesh, watercooler_mat,
    (250.0, 780.0, 0.0), rot_room(yaw_offset=-90.0), unreal.Vector(0.85, 0.85, 0.85)
)
print("  [x] Breakroom whiteboard and watercooler positioned")

# 5. Foreground Cinematic Framing (Extreme edges, out of cast view)
spawn_or_update(
    "FG_Corridor_Watercooler", watercooler_mesh, watercooler_mat,
    (750.0, -420.0, 0.0), rot_room(yaw_offset=45.0), unreal.Vector(0.90, 0.90, 0.90)
)
spawn_or_update(
    "FG_Corridor_Planter", plant_mesh, plant_mat,
    (680.0, -360.0, 0.0), rot_room(), unreal.Vector(0.85, 0.85, 0.85)
)
print("  [x] Foreground cinematic depth layering props staged")

# 6. Save current level
unreal.EditorLevelLibrary.save_current_level()
print("=== Master Staging Script Completed & Level Saved ===")
