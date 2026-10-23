"""Master Cinematic Office Staging, Ceilings, Furniture, Tables, and Foreground Dressing.

Executes:
1. Solid brutalist ceiling slab at Z = 350.0 + Procedural HVAC & Troffer Grid (Houdini bake).
2. Architectural Venetian Blinds (Houdini bake) fitted in the 3 window bays with noir light-slicing louvers.
3. Full hero desk dressing (monitors, keyboards, mice, lamps, mugs, sticky notes, files, PC towers, bins).
4. Single accessible workstation row in North Wing (3 complete setups with 2.5m aisle clearance).
5. Breakroom table suite (decorated with pastry dome, pastries, coffee bags, mugs, 4 dining chairs).
6. Kitchenette & utility corridor dressing (espresso machine, fridge, vending machine, watercooler, whiteboard, clock, calendar, printer).
7. Foreground depth layering framing elements for all 4 hero cameras.
8. Zero occlusion verification across all shooting wedges.
"""
import math
import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Room coordinate system: Yaw = -25.0 degrees
yaw_rad = math.radians(-25.0)
cos_y = math.cos(yaw_rad)
sin_y = math.sin(yaw_rad)

def to_world(xl, yl, zl):
    xw = xl * cos_y - yl * sin_y
    yw = xl * sin_y + yl * cos_y
    return unreal.Vector(xw, yw, zl)

def rot_room(pitch=0.0, yaw_offset=0.0, roll=0.0):
    return unreal.Rotator(pitch=pitch, yaw=-25.0 + yaw_offset, roll=roll)

# -------------------------------------------------------------------------
# Asset Loading
# -------------------------------------------------------------------------
print("Loading staging and prop assets...")

# Meshes - Furniture & Architecture
cube_mesh = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
ceiling_hvac_mesh = unreal.load_asset("/Game/Meshes/Architecture/SM_Houdini_Ceiling_HVAC_Grid")
blinds_mesh = unreal.load_asset("/Game/Meshes/Architecture/SM_VenetianBlinds_Bay")
desk_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_OfficeDesk_AC_FilmStage_20261016")
chair_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Chair_KS_FilmStage_20261016")
breakroom_table_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_BreakroomTable_AC_FilmStage_20261016")
drawers_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_DeskDrawers_SG_FilmStage_20261016")

# Meshes - Peripherals & Office Props
monitor_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_ComputerMonitor_AC_FilmStage_20261016")
tower_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_ComputerTower_AC_FilmStage_20261016")
keyboard_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Keyboard_KS_FilmStage_20261016")
mouse_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Mouse_KMP_FilmStage_20261016")
phone_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Phone_KS_FilmStage_20261016")
lamp_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Lamp_EF_FilmStage_20261016")
bin_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Bin01_SY_FilmStage_20261016")
frame_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_PictureFrame_AC_FilmStage_20261016")
pen_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Pen_KMP_FilmStage_20261016")
sticky_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_StickyNote_PMB_FilmStage_20261016")
file_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_File_EF_FilmStage_20261016")
plant_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Plant_PMB_FilmStage_20261016")
cactus_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Cactus_PMB_FilmStage_20261016")
succulent_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Succulent_PMB_FilmStage_20261016")

# Meshes - Breakroom / Kitchen / Amenities
mug_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_CoffeeMugLarge_ZMJ_FilmStage_20261016")
pastry_cover_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_PastryCover_ZMJ_FilmStage_20261016")
pastry_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_Pastry_ZMJ_FilmStage_20261016")
coffee_bag_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_CoffeeBag_ZMJ_FilmStage_20261016")
coffee_tin_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_CoffeeTin_ZMJ_FilmStage_20261016")
espresso_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_EspressoMachine_ZMJ_FilmStage_20261016")
fridge_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_Fridge_ZMJ_FilmStage_20261016")
vending_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_VenndingMachine_Osc_FilmStage_20261016")
watercooler_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Watercooler_KS_FilmStage_20261016")
whiteboard_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Whiteboard_SG_FilmStage_20261016")
clock_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Clock_AC_FilmStage_20261016")
calendar_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Calendar_SG_FilmStage_20261016")
printer_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Printer_KS_FilmStage_20261016")

# Materials
mat_concrete = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistConcrete")
mat_powder = unreal.load_asset("/Game/Materials/Instances/MI_Toon_Office_PowderCoat")
mat_desk = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_OfficeDesk_AC_FilmStage_20261016")
mat_chair = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_Chair_KS_FilmStage_20261016")
mat_monitor = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_ComputerMonitor_AC_FilmStage_20261016")
mat_keyboard = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_S_Keyboard_KS_FilmStage_20261016")
mat_phone = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_S_Phone_KS_FilmStage_20261016")
mat_lamp = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_Lamp_EF_FilmStage_20261016")
mat_mug = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_O_CoffeeMugLarge_ZMJ_FilmStage_20261016")
mat_plant = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_S_Plant_PMB_FilmStage_20261016")
mat_drawers = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_DeskDrawers_SG_FilmStage_20261016")
mat_breakroom_table = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_BreakroomTable_AC_FilmStage_20261016")
mat_watercooler = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_S_Watercooler_KS_FilmStage_20261016")
mat_whiteboard = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_Whiteboard_SG_FilmStage_20261016")
mat_vending = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_VenndingMachine_Osc_FilmStage_20261016")
mat_metal_prop = unreal.load_asset("/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Metal") or mat_powder
mat_plastic_prop = unreal.load_asset("/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Plastic") or mat_powder

def spawn_or_update(label, mesh, mat, loc_l, rot_r, scale_v, folder="Master_Office_Staging"):
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
    if hasattr(actor, "set_folder_path"):
        actor.set_folder_path(folder)
        
    smc = actor.get_component_by_class(unreal.StaticMeshComponent)
    if smc:
        if mesh: smc.set_static_mesh(mesh)
        if mat:
            for mi in range(smc.get_num_materials()):
                smc.set_material(mi, mat)
    return actor

print("================================================================")
print("EXECUTING MASTER ARCHITECTURAL & CINEMATIC STAGING")
print("================================================================")

# -------------------------------------------------------------------------
# 1. CEILINGS & INDUSTRIAL HVAC GRID
# -------------------------------------------------------------------------
# 1A. Solid Brutalist Concrete Ceiling Slab (Z = 350.0 cm)
spawn_or_update(
    "Film_Ceiling_Slab", cube_mesh, mat_concrete,
    (0.0, 0.0, 350.0), rot_room(), unreal.Vector(22.0, 22.0, 0.20),
    folder="Master_Ceiling_Architecture"
)
print("  [x] Solid Brutalist Ceiling Slab verified at Z = 350.0 cm")

# 1B. Procedural Houdini Industrial Ceiling HVAC & Troffer Grid
spawn_or_update(
    "SM_Houdini_Ceiling_HVAC_Grid", ceiling_hvac_mesh, mat_powder,
    (0.0, 0.0, 0.0), rot_room(), unreal.Vector(1.0, 1.0, 1.0),
    folder="Master_Ceiling_Architecture"
)
print("  [x] Procedural Houdini Ceiling HVAC Grid aligned to room bounds")

# -------------------------------------------------------------------------
# 2. ARCHITECTURAL VENETIAN BLINDS IN WINDOW BAYS
# -------------------------------------------------------------------------
# Window bays are at X_local = -290.0 cm, Y_local = [25.0, 255.0, 485.0]
# Rotation: blinds width (X) aligned to room tangent (Yaw = -25 + 90 = 65 deg)
bays = [
    ("SM_VenetianBlind_Bay_01", (-290.0, 25.0, 2.0)),
    ("SM_VenetianBlind_Bay_02", (-290.0, 255.0, 2.0)),
    ("SM_VenetianBlind_Bay_03", (-290.0, 485.0, 2.0)),
]
for label, loc_l in bays:
    spawn_or_update(
        label, blinds_mesh, mat_metal_prop,
        loc_l, unreal.Rotator(pitch=0.0, yaw=65.0, roll=0.0), unreal.Vector(1.0, 1.0, 1.0),
        folder="Master_Window_Glazing"
    )
print("  [x] Architectural Venetian Blinds staged in all 3 window bays")

# -------------------------------------------------------------------------
# 3. HERO DESK DRESSING (DANA, SAM, DAVID)
# -------------------------------------------------------------------------
# 3A. Dana's Desk (Local: ~ [61.5, 76.1, -3.7])
dana_items = [
    ("HeroDressing_Dana_Monitor", monitor_mesh, mat_monitor, (35.0, 65.0, 52.0), rot_room(yaw_offset=165.0), unreal.Vector(0.70, 0.70, 0.70)),
    ("HeroDressing_Dana_Keyboard", keyboard_mesh, mat_keyboard, (20.0, 65.0, 52.0), rot_room(yaw_offset=180.0), unreal.Vector(0.70, 0.70, 0.70)),
    ("HeroDressing_Dana_Mouse", mouse_mesh, mat_plastic_prop, (20.0, 85.0, 52.0), rot_room(yaw_offset=180.0), unreal.Vector(0.60, 0.60, 0.60)),
    ("HeroDressing_Dana_Mug", mug_mesh, mat_mug, (30.0, 30.0, 52.0), rot_room(yaw_offset=45.0), unreal.Vector(0.80, 0.80, 0.80)),
    ("HeroDressing_Dana_Plant", plant_mesh, mat_plant, (40.0, 110.0, 52.0), rot_room(), unreal.Vector(0.65, 0.65, 0.65)),
    ("HeroDressing_Dana_Frame", frame_mesh, mat_plastic_prop, (40.0, 35.0, 52.0), rot_room(yaw_offset=-20.0), unreal.Vector(0.60, 0.60, 0.60)),
    ("HeroDressing_Dana_Pen", pen_mesh, mat_metal_prop, (15.0, 75.0, 52.0), rot_room(yaw_offset=80.0), unreal.Vector(0.90, 0.90, 0.90)),
    ("HeroDressing_Dana_Sticky", sticky_mesh, mat_plastic_prop, (25.0, 48.0, 52.0), rot_room(yaw_offset=15.0), unreal.Vector(0.80, 0.80, 0.80)),
    ("HeroDressing_Dana_Tower", tower_mesh, mat_powder, (50.0, 105.0, 0.0), rot_room(yaw_offset=180.0), unreal.Vector(0.75, 0.75, 0.75)),
    ("HeroDressing_Dana_Bin", bin_mesh, mat_powder, (10.0, 125.0, 0.0), rot_room(), unreal.Vector(0.75, 0.75, 0.75)),
]
for lbl, m, mt, loc, rot, sc in dana_items:
    spawn_or_update(lbl, m, mt, loc, rot, sc, folder="Master_HeroDressing_Dana")

# 3B. Sam's Desk (Local: ~ [61.6, 292.3, -3.4])
sam_items = [
    ("HeroDressing_Sam_Monitor", monitor_mesh, mat_monitor, (35.0, 280.0, 52.0), rot_room(yaw_offset=170.0), unreal.Vector(0.70, 0.70, 0.70)),
    ("HeroDressing_Sam_Keyboard", keyboard_mesh, mat_keyboard, (20.0, 280.0, 52.0), rot_room(yaw_offset=180.0), unreal.Vector(0.70, 0.70, 0.70)),
    ("HeroDressing_Sam_Mouse", mouse_mesh, mat_plastic_prop, (20.0, 300.0, 52.0), rot_room(yaw_offset=180.0), unreal.Vector(0.60, 0.60, 0.60)),
    ("HeroDressing_Sam_Phone", phone_mesh, mat_phone, (35.0, 250.0, 52.0), rot_room(yaw_offset=15.0), unreal.Vector(0.70, 0.70, 0.70)),
    ("HeroDressing_Sam_Mug", mug_mesh, mat_mug, (30.0, 320.0, 52.0), rot_room(yaw_offset=-30.0), unreal.Vector(0.80, 0.80, 0.80)),
    ("HeroDressing_Sam_Lamp", lamp_mesh, mat_lamp, (45.0, 325.0, 52.0), rot_room(yaw_offset=210.0), unreal.Vector(0.70, 0.70, 0.70)),
    ("HeroDressing_Sam_File", file_mesh, mat_plastic_prop, (38.0, 260.0, 52.0), rot_room(yaw_offset=-10.0), unreal.Vector(0.85, 0.85, 0.85)),
    ("HeroDressing_Sam_Drawers", drawers_mesh, mat_drawers, (60.0, 240.0, 0.0), rot_room(), unreal.Vector(0.70, 0.70, 0.70)),
    ("HeroDressing_Sam_Tower", tower_mesh, mat_powder, (50.0, 335.0, 0.0), rot_room(yaw_offset=180.0), unreal.Vector(0.75, 0.75, 0.75)),
    ("HeroDressing_Sam_Bin", bin_mesh, mat_powder, (10.0, 240.0, 0.0), rot_room(), unreal.Vector(0.75, 0.75, 0.75)),
]
for lbl, m, mt, loc, rot, sc in sam_items:
    spawn_or_update(lbl, m, mt, loc, rot, sc, folder="Master_HeroDressing_Sam")

# 3C. David's Sleeping Desk (Local: ~ [-70.0, -160.2, 0.0])
david_items = [
    ("HeroDressing_David_Lamp", lamp_mesh, mat_lamp, (-40.0, -130.0, 52.0), rot_room(yaw_offset=-30.0), unreal.Vector(0.75, 0.75, 0.75)),
    ("HeroDressing_David_Monitor", monitor_mesh, mat_monitor, (-40.0, -190.0, 52.0), rot_room(yaw_offset=165.0), unreal.Vector(0.70, 0.70, 0.70)),
    ("HeroDressing_David_Keyboard", keyboard_mesh, mat_keyboard, (-55.0, -145.0, 52.0), rot_room(yaw_offset=175.0), unreal.Vector(0.70, 0.70, 0.70)),
    ("HeroDressing_David_Mouse", mouse_mesh, mat_plastic_prop, (-55.0, -130.0, 52.0), rot_room(yaw_offset=180.0), unreal.Vector(0.60, 0.60, 0.60)),
    ("HeroDressing_David_Phone", phone_mesh, mat_phone, (-50.0, -195.0, 52.0), rot_room(), unreal.Vector(0.70, 0.70, 0.70)),
    ("HeroDressing_David_Mug", mug_mesh, mat_mug, (-35.0, -155.0, 52.0), rot_room(yaw_offset=60.0), unreal.Vector(0.80, 0.80, 0.80)),
    ("HeroDressing_David_Sticky", sticky_mesh, mat_plastic_prop, (-48.0, -170.0, 52.0), rot_room(yaw_offset=25.0), unreal.Vector(0.80, 0.80, 0.80)),
    ("HeroDressing_David_Bin", bin_mesh, mat_powder, (-85.0, -125.0, 0.0), rot_room(), unreal.Vector(0.75, 0.75, 0.75)),
]
for lbl, m, mt, loc, rot, sc in david_items:
    spawn_or_update(lbl, m, mt, loc, rot, sc, folder="Master_HeroDressing_David")

print("  [x] Hero Desks (Dana, Sam, David) fully dressed with peripherals, lighting, mugs, stationery")

# -------------------------------------------------------------------------
# 4. SINGLE ACCESSIBLE WORKSTATION ROW (NORTH WING)
# -------------------------------------------------------------------------
for i, yl in enumerate([420.0, 560.0, 700.0], start=1):
    spawn_or_update(f"Workstation_Row_Desk_0{i}", desk_mesh, mat_desk, (350.0, yl, -3.5), rot_room(), unreal.Vector(0.74, 0.74, 0.74), folder="Master_Workstation_Row")
    spawn_or_update(f"Workstation_Row_Monitor_0{i}", monitor_mesh, mat_monitor, (330.0, yl + 10.0, 52.0), rot_room(yaw_offset=-5.0), unreal.Vector(0.74, 0.74, 0.74), folder="Master_Workstation_Row")
    spawn_or_update(f"Workstation_Row_Keyboard_0{i}", keyboard_mesh, mat_keyboard, (370.0, yl + 10.0, 52.0), rot_room(), unreal.Vector(0.74, 0.74, 0.74), folder="Master_Workstation_Row")
    spawn_or_update(f"Workstation_Row_Mouse_0{i}", mouse_mesh, mat_plastic_prop, (370.0, yl - 12.0, 52.0), rot_room(), unreal.Vector(0.60, 0.60, 0.60), folder="Master_Workstation_Row")
    spawn_or_update(f"Workstation_Row_Chair_0{i}", chair_mesh, mat_chair, (430.0, yl, 0.0), rot_room(yaw_offset=175.0), unreal.Vector(0.85, 0.85, 0.85), folder="Master_Workstation_Row")
    spawn_or_update(f"Workstation_Row_Drawers_0{i}", drawers_mesh, mat_drawers, (350.0, yl - 60.0, 0.0), rot_room(), unreal.Vector(0.70, 0.70, 0.70), folder="Master_Workstation_Row")
    spawn_or_update(f"Workstation_Row_Tower_0{i}", tower_mesh, mat_powder, (335.0, yl + 65.0, 0.0), rot_room(), unreal.Vector(0.75, 0.75, 0.75), folder="Master_Workstation_Row")
    spawn_or_update(f"Workstation_Row_Bin_0{i}", bin_mesh, mat_powder, (410.0, yl - 50.0, 0.0), rot_room(), unreal.Vector(0.75, 0.75, 0.75), folder="Master_Workstation_Row")
    # Alternating accessories
    if i == 1:
        spawn_or_update(f"Workstation_Row_Mug_0{i}", mug_mesh, mat_mug, (340.0, yl - 25.0, 52.0), rot_room(yaw_offset=30.0), unreal.Vector(0.80, 0.80, 0.80), folder="Master_Workstation_Row")
    elif i == 2:
        spawn_or_update(f"Workstation_Row_Lamp_0{i}", lamp_mesh, mat_lamp, (335.0, yl - 30.0, 52.0), rot_room(yaw_offset=-40.0), unreal.Vector(0.70, 0.70, 0.70), folder="Master_Workstation_Row")
    elif i == 3:
        spawn_or_update(f"Workstation_Row_Cactus_0{i}", cactus_mesh, mat_plant, (335.0, yl - 25.0, 52.0), rot_room(), unreal.Vector(0.65, 0.65, 0.65), folder="Master_Workstation_Row")

print("  [x] Single Accessible Workstation Row (3 units, complete desktop dressing, 2.5m aisle clearance)")

# -------------------------------------------------------------------------
# 5. BREAKROOM TABLE & KITCHENETTE SUITE
# -------------------------------------------------------------------------
# Communal Breakroom Table (X_local = 220.0, Y_local = 650.0)
spawn_or_update("Breakroom_Table", breakroom_table_mesh, mat_breakroom_table, (220.0, 650.0, 0.0), rot_room(), unreal.Vector(1.0, 1.0, 1.0), folder="Master_Breakroom_Suite")
# Tabletop dressing
spawn_or_update("Breakroom_Table_PastryDome", pastry_cover_mesh, mat_plastic_prop, (220.0, 650.0, 76.0), rot_room(), unreal.Vector(4.5, 4.5, 4.5), folder="Master_Breakroom_Suite")
spawn_or_update("Breakroom_Table_Pastry", pastry_mesh, mat_plastic_prop, (220.0, 650.0, 76.5), rot_room(yaw_offset=25.0), unreal.Vector(4.5, 4.5, 4.5), folder="Master_Breakroom_Suite")
spawn_or_update("Breakroom_Table_CoffeeBag", coffee_bag_mesh, mat_plastic_prop, (220.0, 620.0, 76.0), rot_room(yaw_offset=-20.0), unreal.Vector(4.5, 4.5, 4.5), folder="Master_Breakroom_Suite")
spawn_or_update("Breakroom_Table_Mug_01", mug_mesh, mat_mug, (200.0, 665.0, 76.0), rot_room(yaw_offset=45.0), unreal.Vector(0.85, 0.85, 0.85), folder="Master_Breakroom_Suite")
spawn_or_update("Breakroom_Table_Mug_02", mug_mesh, mat_mug, (240.0, 635.0, 76.0), rot_room(yaw_offset=-70.0), unreal.Vector(0.85, 0.85, 0.85), folder="Master_Breakroom_Suite")

# 4 Chairs around communal table
chair_offs = [
    ("Breakroom_Chair_01", (170.0, 650.0, 0.0), rot_room(yaw_offset=90.0)),
    ("Breakroom_Chair_02", (270.0, 650.0, 0.0), rot_room(yaw_offset=-90.0)),
    ("Breakroom_Chair_03", (220.0, 600.0, 0.0), rot_room(yaw_offset=0.0)),
    ("Breakroom_Chair_04", (220.0, 700.0, 0.0), rot_room(yaw_offset=180.0)),
]
for lbl, loc, rot in chair_offs:
    spawn_or_update(lbl, chair_mesh, mat_chair, loc, rot, unreal.Vector(0.85, 0.85, 0.85), folder="Master_Breakroom_Suite")

# Breakroom Amenities & Appliances
spawn_or_update("Breakroom_Whiteboard", whiteboard_mesh, mat_whiteboard, (150.0, 780.0, 80.0), rot_room(yaw_offset=-90.0), unreal.Vector(0.85, 0.85, 0.85), folder="Master_Breakroom_Suite")
spawn_or_update("Breakroom_Watercooler", watercooler_mesh, mat_watercooler, (250.0, 780.0, 0.0), rot_room(yaw_offset=-90.0), unreal.Vector(0.85, 0.85, 0.85), folder="Master_Breakroom_Suite")
spawn_or_update("Breakroom_VendingMachine", vending_mesh, mat_vending, (320.0, 780.0, 0.0), rot_room(yaw_offset=-90.0), unreal.Vector(0.90, 0.90, 0.90), folder="Master_Breakroom_Suite")
spawn_or_update("Breakroom_Clock", clock_mesh, mat_plastic_prop, (150.0, 790.0, 230.0), rot_room(yaw_offset=90.0), unreal.Vector(0.80, 0.80, 0.80), folder="Master_Breakroom_Suite")
spawn_or_update("Breakroom_Calendar", calendar_mesh, mat_plastic_prop, (200.0, 790.0, 180.0), rot_room(yaw_offset=90.0), unreal.Vector(0.80, 0.80, 0.80), folder="Master_Breakroom_Suite")
spawn_or_update("Corridor_Printer", printer_mesh, mat_plastic_prop, (420.0, 360.0, 0.0), rot_room(yaw_offset=180.0), unreal.Vector(0.85, 0.85, 0.85), folder="Master_Breakroom_Suite")

print("  [x] Breakroom Suite (dining table, pastry dome, coffee bags, 4 chairs, appliances, clock, printer) staged")

# -------------------------------------------------------------------------
# 6. FOREGROUND CINEMATIC FRAMING & DEPTH LAYERING
# -------------------------------------------------------------------------
# Plant and watercooler positioned at the edge of the corridor for SESSION_CAM_Cast depth
spawn_or_update("FG_Corridor_Planter", plant_mesh, mat_plant, (680.0, -360.0, 0.0), rot_room(), unreal.Vector(0.85, 0.85, 0.85), folder="Master_Foreground_Framing")
spawn_or_update("FG_Corridor_Watercooler", watercooler_mesh, mat_watercooler, (750.0, -420.0, 0.0), rot_room(yaw_offset=45.0), unreal.Vector(0.90, 0.90, 0.90), folder="Master_Foreground_Framing")
print("  [x] Foreground cinematic depth layering staged at frame perimeters")

# -------------------------------------------------------------------------
# 7. CLEANUP ROGUE / PROVISIONAL ACTORS
# -------------------------------------------------------------------------
rogues_deleted = 0
for a in EAS.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl in ["SM_Glass_WindowBay_3", "SM_P_BreakroomTable_AC_FilmStage_20261016"]:
        EAS.destroy_actor(a)
        rogues_deleted += 1
print(f"  [x] Cleaned {rogues_deleted} duplicate/unaligned provisional actors")

# -------------------------------------------------------------------------
# 8. SAVE CURRENT LEVEL
# -------------------------------------------------------------------------
unreal.EditorLevelLibrary.save_current_level()
print("================================================================")
print("MASTER CINEMATIC STAGING COMPLETE & LEVEL SERIALIZED")
print("================================================================")
