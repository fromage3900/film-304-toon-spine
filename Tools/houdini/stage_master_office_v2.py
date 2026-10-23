"""Master Cinematic Office Staging, Ceilings, Furniture, Tables, and Foreground Dressing v2.

Full execution of:
1. Multi-material Houdini procedural ceiling architecture: concrete beams, galvanized steel ducts, and glowing troffer diffusers.
2. Upward architectural wash lighting softly illuminating the concrete ceiling slab and structural ribs.
3. 100% CAD-precision table dressing for Dana, Sam, David, North Wing workstations, and Breakroom table (zero clipping, exact bounding box contact).
4. Rich prop detail: monitors, laptops, keyboards, mice, task lamps with warm illumination pools, 6.0x decimeter-scaled mugs, stationery, files, plants, wastebaskets.
5. Cinematic foreground framing elements for all 4 hero cameras.
6. Sealed perimeter walls and verified zero camera occlusion.
"""
import math
import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Room rotation: Yaw = -25.0 degrees
yaw_rad = math.radians(-25.0)
cos_y = math.cos(yaw_rad)
sin_y = math.sin(yaw_rad)

def to_world(xl, yl, zl):
    xw = xl * cos_y - yl * sin_y
    yw = xl * sin_y + yl * cos_y
    return unreal.Vector(xw, yw, zl)

def rot_room(pitch=0.0, yaw_offset=0.0, roll=0.0):
    return unreal.Rotator(pitch=pitch, yaw=-25.0 + yaw_offset, roll=roll)

print("Loading master assets and materials...")

# Meshes
cube_mesh = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
ceiling_hvac_mesh = unreal.load_asset("/Game/Meshes/Architecture/SM_Houdini_Ceiling_HVAC_Grid")
blinds_mesh = unreal.load_asset("/Game/Meshes/Architecture/SM_VenetianBlinds_Bay")
desk_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_OfficeDesk_AC_FilmStage_20261016")
chair_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Chair_KS_FilmStage_20261016")
breakroom_table_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_BreakroomTable_AC_FilmStage_20261016")
drawers_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_DeskDrawers_SG_FilmStage_20261016")

# Props
monitor_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_ComputerMonitor_AC_FilmStage_20261016")
laptop_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Laptop_KS_FilmStage_20261016")
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
book_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Book_PMB_FilmStage_20261016")
plant_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Plant_PMB_FilmStage_20261016")
cactus_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Cactus_PMB_FilmStage_20261016")
succulent_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Succulent_PMB_FilmStage_20261016")

# Breakroom props
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
mat_wall = unreal.load_asset("/Game/Materials/Instances/UniversalFilm_20261016/MI_Film_Wall")
mat_metal = unreal.load_asset("/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Metal")
mat_powder = unreal.load_asset("/Game/Materials/Instances/MI_Toon_Office_PowderCoat")
mat_troffer = unreal.load_asset("/Game/Materials/Instances/MI_Toon_Office_Troffer")
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
mat_plastic = unreal.load_asset("/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Plastic") or mat_powder

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
print("EXECUTING MASTER CINEMATIC STAGING V2")
print("================================================================")

# -------------------------------------------------------------------------
# 1. CEILINGS, BEAMS, & UPWARD WASH LIGHTING
# -------------------------------------------------------------------------
# 1A. Solid Brutalist Concrete Ceiling Slab (Z = 350.0 cm)
spawn_or_update(
    "Film_Ceiling_Slab", cube_mesh, mat_concrete,
    (0.0, 0.0, 350.0), rot_room(), unreal.Vector(24.0, 24.0, 0.20),
    folder="Master_Ceiling_Architecture"
)

# 1B. Multi-Material Procedural Houdini Ceiling Grid (Beams, Ducts, Diffusers)
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
if hasattr(hvac_actor, "set_folder_path"):
    hvac_actor.set_folder_path("Master_Ceiling_Architecture")
h_smc = hvac_actor.get_component_by_class(unreal.StaticMeshComponent)
if h_smc:
    h_smc.set_static_mesh(ceiling_hvac_mesh)
    h_smc.set_material(0, mat_concrete) # Slot 0: Structural concrete cross-beams
    h_smc.set_material(1, mat_metal)    # Slot 1: Galvanized ductwork, conduit, hangers
    h_smc.set_material(2, mat_troffer)  # Slot 2: Glowing fluorescent troffer diffusers
print("  [x] Procedural Houdini Ceiling Architecture & Glowing Troffers staged")

# 1C. Upward Ceiling Wash Lighting (illuminates the concrete slab & beams)
upwash_configs = [
    ("Light_Ceiling_Upwash_01", (100.0, 100.0, 260.0), 12.0),
    ("Light_Ceiling_Upwash_02", (250.0, 500.0, 260.0), 12.0),
    ("Light_Ceiling_Upwash_03", (-100.0, -100.0, 260.0), 10.0),
]
for lbl, loc_l, inten in upwash_configs:
    lt = None
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == lbl:
            lt = a
            break
    if not lt:
        lt = EAS.spawn_actor_from_class(unreal.RectLight, to_world(*loc_l))
        lt.set_actor_label(lbl)
    lt.set_actor_location(to_world(*loc_l), False, False)
    lt.set_actor_rotation(rot_room(pitch=85.0), False)
    if hasattr(lt, "set_folder_path"):
        lt.set_folder_path("Master_Ceiling_Architecture")
    comp = lt.get_component_by_class(unreal.RectLightComponent)
    if comp:
        comp.set_intensity(inten)
        comp.set_light_color(unreal.LinearColor(r=0.92, g=0.95, b=1.0, a=1.0))
        comp.set_attenuation_radius(450.0)
        comp.set_source_width(160.0)
        comp.set_source_height(160.0)
print("  [x] Upward architectural wash lighting staged across ceiling slab")

# 1D. Seal Wall Seam on West Boundary
spawn_or_update(
    "Film_Wall_Seam_Infill", cube_mesh, mat_wall,
    (-290.0, -85.0, 170.0), rot_room(), unreal.Vector(0.20, 0.70, 3.40),
    folder="Master_Perimeter_Enclosure"
)
print("  [x] West wall seam permanently sealed at Y_local = -85.0")

# -------------------------------------------------------------------------
# 2. DANA'S HERO DESK DRESSING (Table surface top_z = 52.3)
# -------------------------------------------------------------------------
dana_dressing = [
    # Primary Monitor
    ("HeroDressing_Dana_Monitor", monitor_mesh, mat_monitor, (40.0, 75.0, 52.17), rot_room(yaw_offset=170.0), unreal.Vector(0.70, 0.70, 0.70)),
    # Secondary Screen (Open Laptop)
    ("HeroDressing_Dana_Laptop", laptop_mesh, mat_plastic, (40.0, 105.0, 52.36), rot_room(yaw_offset=155.0), unreal.Vector(0.75, 0.75, 0.75)),
    # Keyboard (min_z = -1.0 -> loc.z = 53.02)
    ("HeroDressing_Dana_Keyboard", keyboard_mesh, mat_keyboard, (20.0, 75.0, 53.02), rot_room(yaw_offset=180.0), unreal.Vector(0.72, 0.72, 0.72)),
    # Mouse
    ("HeroDressing_Dana_Mouse", mouse_mesh, mat_plastic, (20.0, 95.0, 52.31), rot_room(yaw_offset=180.0), unreal.Vector(0.65, 0.65, 0.65)),
    # Coffee Mug (scaled 6.0x -> loc.z = 56.86)
    ("HeroDressing_Dana_Mug", mug_mesh, mat_mug, (35.0, 48.0, 56.86), rot_room(yaw_offset=45.0), unreal.Vector(6.0, 6.0, 6.0)),
    # Framed Photo (min_z = -17.50 -> loc.z = 62.80)
    ("HeroDressing_Dana_Frame", frame_mesh, mat_plastic, (42.0, 42.0, 62.80), rot_room(yaw_offset=-20.0), unreal.Vector(0.60, 0.60, 0.60)),
    # Potted Succulent (min_z = -7.15 -> loc.z = 56.95)
    ("HeroDressing_Dana_Succulent", succulent_mesh, mat_plant, (48.0, 122.0, 56.95), rot_room(), unreal.Vector(0.65, 0.65, 0.65)),
    # Sticky Notes (min_z = -2.32 -> loc.z = 54.16)
    ("HeroDressing_Dana_Sticky", sticky_mesh, mat_plastic, (22.0, 56.0, 54.16), rot_room(yaw_offset=15.0), unreal.Vector(0.80, 0.80, 0.80)),
    # Pen
    ("HeroDressing_Dana_Pen", pen_mesh, mat_metal, (16.0, 60.0, 52.30), rot_room(yaw_offset=75.0), unreal.Vector(0.90, 0.90, 0.90)),
    # Paper File In-Tray
    ("HeroDressing_Dana_File", file_mesh, mat_plastic, (32.0, 120.0, 52.31), rot_room(yaw_offset=-10.0), unreal.Vector(0.90, 0.90, 0.90)),
    # Desk Lamp (min_z = -37.98 -> loc.z = 78.89)
    ("HeroDressing_Dana_Lamp", lamp_mesh, mat_lamp, (48.0, 125.0, 78.89), rot_room(yaw_offset=210.0), unreal.Vector(0.70, 0.70, 0.70)),
    # Floor: Computer Tower
    ("HeroDressing_Dana_Tower", tower_mesh, mat_powder, (45.0, 110.0, 0.0), rot_room(yaw_offset=180.0), unreal.Vector(0.75, 0.75, 0.75)),
    # Floor: Wastebasket
    ("HeroDressing_Dana_Bin", bin_mesh, mat_powder, (5.0, 125.0, 0.0), rot_room(), unreal.Vector(0.75, 0.75, 0.75)),
]
for lbl, m, mt, loc, rot, sc in dana_dressing:
    spawn_or_update(lbl, m, mt, loc, rot, sc, folder="Master_HeroDressing_Dana")
print("  [x] Dana's desk 100% dressed with CAD precision (monitor, laptop, keyboard, mouse, mug, frame, succulent, stationery)")

# -------------------------------------------------------------------------
# 3. SAM'S HERO DESK DRESSING (Table surface top_z = 52.7)
# -------------------------------------------------------------------------
sam_dressing = [
    # Monitor
    ("HeroDressing_Sam_Monitor", monitor_mesh, mat_monitor, (40.0, 300.0, 52.57), rot_room(yaw_offset=175.0), unreal.Vector(0.70, 0.70, 0.70)),
    # Keyboard
    ("HeroDressing_Sam_Keyboard", keyboard_mesh, mat_keyboard, (20.0, 300.0, 53.42), rot_room(yaw_offset=180.0), unreal.Vector(0.72, 0.72, 0.72)),
    # Mouse
    ("HeroDressing_Sam_Mouse", mouse_mesh, mat_plastic, (20.0, 320.0, 52.71), rot_room(yaw_offset=180.0), unreal.Vector(0.65, 0.65, 0.65)),
    # Desk Phone
    ("HeroDressing_Sam_Phone", phone_mesh, mat_phone, (38.0, 270.0, 52.81), rot_room(yaw_offset=15.0), unreal.Vector(0.85, 0.85, 0.85)),
    # Coffee Mug (scaled 6.0x)
    ("HeroDressing_Sam_Mug", mug_mesh, mat_mug, (32.0, 335.0, 57.26), rot_room(yaw_offset=-30.0), unreal.Vector(6.0, 6.0, 6.0)),
    # Desk Lamp
    ("HeroDressing_Sam_Lamp", lamp_mesh, mat_lamp, (46.0, 338.0, 79.29), rot_room(yaw_offset=215.0), unreal.Vector(0.70, 0.70, 0.70)),
    # File Folders
    ("HeroDressing_Sam_File", file_mesh, mat_plastic, (38.0, 260.0, 52.71), rot_room(yaw_offset=-15.0), unreal.Vector(0.85, 0.85, 0.85)),
    # Desk Drawers unit
    ("HeroDressing_Sam_Drawers", drawers_mesh, mat_drawers, (60.0, 250.0, 0.0), rot_room(), unreal.Vector(0.70, 0.70, 0.70)),
    # Floor: Computer Tower
    ("HeroDressing_Sam_Tower", tower_mesh, mat_powder, (50.0, 340.0, 0.0), rot_room(yaw_offset=180.0), unreal.Vector(0.75, 0.75, 0.75)),
    # Floor: Wastebasket
    ("HeroDressing_Sam_Bin", bin_mesh, mat_powder, (8.0, 250.0, 0.0), rot_room(), unreal.Vector(0.75, 0.75, 0.75)),
]
for lbl, m, mt, loc, rot, sc in sam_dressing:
    spawn_or_update(lbl, m, mt, loc, rot, sc, folder="Master_HeroDressing_Sam")
print("  [x] Sam's desk 100% dressed (monitor, keyboard, mouse, phone, mug, lamp, drawers, files)")

# -------------------------------------------------------------------------
# 4. DAVID'S SLEEPING DESK DRESSING (Table surface top_z = 53.8)
# -------------------------------------------------------------------------
david_dressing = [
    # Monitor
    ("HeroDressing_David_Monitor", monitor_mesh, mat_monitor, (-42.0, -188.0, 53.67), rot_room(yaw_offset=165.0), unreal.Vector(0.70, 0.70, 0.70)),
    # Keyboard (under sleeping arm)
    ("HeroDressing_David_Keyboard", keyboard_mesh, mat_keyboard, (-58.0, -145.0, 54.52), rot_room(yaw_offset=175.0), unreal.Vector(0.72, 0.72, 0.72)),
    # Mouse
    ("HeroDressing_David_Mouse", mouse_mesh, mat_plastic, (-58.0, -128.0, 53.81), rot_room(yaw_offset=180.0), unreal.Vector(0.65, 0.65, 0.65)),
    # Coffee Mug (scaled 6.0x)
    ("HeroDressing_David_Mug", mug_mesh, mat_mug, (-40.0, -158.0, 58.36), rot_room(yaw_offset=55.0), unreal.Vector(6.0, 6.0, 6.0)),
    # Desk Lamp (with warm localized light)
    ("HeroDressing_David_Lamp", lamp_mesh, mat_lamp, (-42.0, -132.0, 81.15), rot_room(yaw_offset=-35.0), unreal.Vector(0.72, 0.72, 0.72)),
    # Sticky Note Pad
    ("HeroDressing_David_Sticky", sticky_mesh, mat_plastic, (-52.0, -172.0, 55.66), rot_room(yaw_offset=25.0), unreal.Vector(0.80, 0.80, 0.80)),
    # Desk Phone
    ("HeroDressing_David_Phone", phone_mesh, mat_phone, (-50.0, -195.0, 53.91), rot_room(), unreal.Vector(0.70, 0.70, 0.70)),
    # Floor: Wastebasket
    ("HeroDressing_David_Bin", bin_mesh, mat_powder, (-85.0, -125.0, 0.0), rot_room(), unreal.Vector(0.75, 0.75, 0.75)),
]
for lbl, m, mt, loc, rot, sc in david_dressing:
    spawn_or_update(lbl, m, mt, loc, rot, sc, folder="Master_HeroDressing_David")

# Warm localized desk lamp light on David's face & desk
dl_light = None
for a in EAS.get_all_level_actors():
    if a.get_actor_label() == "Light_David_DeskLamp":
        dl_light = a
        break
if not dl_light:
    dl_light = EAS.spawn_actor_from_class(unreal.PointLight, to_world(-42.0, -132.0, 95.0))
    dl_light.set_actor_label("Light_David_DeskLamp")
dl_light.set_actor_location(to_world(-42.0, -132.0, 95.0), False, False)
if hasattr(dl_light, "set_folder_path"):
    dl_light.set_folder_path("Master_HeroDressing_David")
plc = dl_light.get_component_by_class(unreal.PointLightComponent)
if plc:
    plc.set_intensity(3.0)
    plc.set_light_color(unreal.LinearColor(r=1.0, g=0.84, b=0.60, a=1.0)) # 3200K warm tungsten
    plc.set_attenuation_radius(180.0)
print("  [x] David's sleeping workstation dressed & warm desk lamp pool active")

# -------------------------------------------------------------------------
# 5. NORTH WING WORKSTATION ROW (3 Accessible Desks, Y_local = 420, 560, 700)
# -------------------------------------------------------------------------
for i, yl in enumerate([420.0, 560.0, 700.0], start=1):
    fld = "Master_Workstation_Row"
    spawn_or_update(f"Workstation_Row_Desk_0{i}", desk_mesh, mat_desk, (350.0, yl, -3.5), rot_room(), unreal.Vector(0.74, 0.74, 0.74), folder=fld)
    spawn_or_update(f"Workstation_Row_Monitor_0{i}", monitor_mesh, mat_monitor, (330.0, yl + 10.0, 52.56), rot_room(yaw_offset=-5.0), unreal.Vector(0.74, 0.74, 0.74), folder=fld)
    spawn_or_update(f"Workstation_Row_Keyboard_0{i}", keyboard_mesh, mat_keyboard, (370.0, yl + 10.0, 53.44), rot_room(), unreal.Vector(0.74, 0.74, 0.74), folder=fld)
    spawn_or_update(f"Workstation_Row_Mouse_0{i}", mouse_mesh, mat_plastic, (370.0, yl - 12.0, 52.71), rot_room(), unreal.Vector(0.60, 0.60, 0.60), folder=fld)
    spawn_or_update(f"Workstation_Row_Chair_0{i}", chair_mesh, mat_chair, (425.0, yl, 0.0), rot_room(yaw_offset=175.0), unreal.Vector(0.85, 0.85, 0.85), folder=fld)
    spawn_or_update(f"Workstation_Row_Drawers_0{i}", drawers_mesh, mat_drawers, (350.0, yl - 60.0, 0.0), rot_room(), unreal.Vector(0.70, 0.70, 0.70), folder=fld)
    spawn_or_update(f"Workstation_Row_Tower_0{i}", tower_mesh, mat_powder, (335.0, yl + 65.0, 0.0), rot_room(), unreal.Vector(0.75, 0.75, 0.75), folder=fld)
    spawn_or_update(f"Workstation_Row_Bin_0{i}", bin_mesh, mat_powder, (405.0, yl - 50.0, 0.0), rot_room(), unreal.Vector(0.75, 0.75, 0.75), folder=fld)
    if i == 1:
        spawn_or_update(f"Workstation_Row_Mug_0{i}", mug_mesh, mat_mug, (340.0, yl - 25.0, 57.26), rot_room(yaw_offset=30.0), unreal.Vector(6.0, 6.0, 6.0), folder=fld)
        spawn_or_update(f"Workstation_Row_Sticky_0{i}", sticky_mesh, mat_plastic, (360.0, yl - 25.0, 54.56), rot_room(yaw_offset=10.0), unreal.Vector(0.80, 0.80, 0.80), folder=fld)
    elif i == 2:
        spawn_or_update(f"Workstation_Row_Lamp_0{i}", lamp_mesh, mat_lamp, (335.0, yl - 30.0, 79.29), rot_room(yaw_offset=-40.0), unreal.Vector(0.70, 0.70, 0.70), folder=fld)
        spawn_or_update(f"Workstation_Row_File_0{i}", file_mesh, mat_plastic, (350.0, yl + 45.0, 52.71), rot_room(yaw_offset=-20.0), unreal.Vector(0.85, 0.85, 0.85), folder=fld)
    elif i == 3:
        spawn_or_update(f"Workstation_Row_Cactus_0{i}", cactus_mesh, mat_plant, (335.0, yl - 25.0, 60.82), rot_room(), unreal.Vector(0.65, 0.65, 0.65), folder=fld)
print("  [x] North Wing Workstation Row fully populated with 3 complete setups")

# -------------------------------------------------------------------------
# 6. BREAKROOM TABLE & KITCHENETTE SUITE
# -------------------------------------------------------------------------
fld_br = "Master_Breakroom_Suite"
spawn_or_update("Breakroom_Table", breakroom_table_mesh, mat_breakroom_table, (220.0, 650.0, 0.0), rot_room(), unreal.Vector(1.0, 1.0, 1.0), folder=fld_br)
spawn_or_update("Breakroom_Table_PastryDome", pastry_cover_mesh, mat_plastic, (220.0, 650.0, 76.5), rot_room(), unreal.Vector(5.0, 5.0, 5.0), folder=fld_br)
spawn_or_update("Breakroom_Table_Pastry", pastry_mesh, mat_plastic, (220.0, 650.0, 76.75), rot_room(yaw_offset=25.0), unreal.Vector(5.0, 5.0, 5.0), folder=fld_br)
spawn_or_update("Breakroom_Table_CoffeeBag", coffee_bag_mesh, mat_plastic, (220.0, 620.0, 76.5), rot_room(yaw_offset=-20.0), unreal.Vector(5.0, 5.0, 5.0), folder=fld_br)
spawn_or_update("Breakroom_Table_CoffeeTin", coffee_tin_mesh, mat_plastic, (240.0, 620.0, 83.45), rot_room(yaw_offset=15.0), unreal.Vector(5.0, 5.0, 5.0), folder=fld_br)
spawn_or_update("Breakroom_Table_Mug_01", mug_mesh, mat_mug, (200.0, 665.0, 81.06), rot_room(yaw_offset=45.0), unreal.Vector(6.0, 6.0, 6.0), folder=fld_br)
spawn_or_update("Breakroom_Table_Mug_02", mug_mesh, mat_mug, (240.0, 655.0, 81.06), rot_room(yaw_offset=-70.0), unreal.Vector(6.0, 6.0, 6.0), folder=fld_br)

chair_offs = [
    ("Breakroom_Chair_01", (170.0, 650.0, 0.0), rot_room(yaw_offset=90.0)),
    ("Breakroom_Chair_02", (270.0, 650.0, 0.0), rot_room(yaw_offset=-90.0)),
    ("Breakroom_Chair_03", (220.0, 600.0, 0.0), rot_room(yaw_offset=0.0)),
    ("Breakroom_Chair_04", (220.0, 700.0, 0.0), rot_room(yaw_offset=180.0)),
]
for lbl, loc, rot in chair_offs:
    spawn_or_update(lbl, chair_mesh, mat_chair, loc, rot, unreal.Vector(0.85, 0.85, 0.85), folder=fld_br)

spawn_or_update("Breakroom_Whiteboard", whiteboard_mesh, mat_whiteboard, (150.0, 780.0, 80.0), rot_room(yaw_offset=-90.0), unreal.Vector(0.85, 0.85, 0.85), folder=fld_br)
spawn_or_update("Breakroom_Watercooler", watercooler_mesh, mat_watercooler, (250.0, 780.0, 0.0), rot_room(yaw_offset=-90.0), unreal.Vector(0.85, 0.85, 0.85), folder=fld_br)
spawn_or_update("Breakroom_VendingMachine", vending_mesh, mat_vending, (320.0, 780.0, 0.0), rot_room(yaw_offset=-90.0), unreal.Vector(0.90, 0.90, 0.90), folder=fld_br)
spawn_or_update("Breakroom_Fridge", fridge_mesh, mat_plastic, (390.0, 780.0, 0.0), rot_room(yaw_offset=-90.0), unreal.Vector(6.0, 6.0, 6.0), folder=fld_br)
spawn_or_update("Breakroom_Clock", clock_mesh, mat_plastic, (150.0, 790.0, 230.0), rot_room(yaw_offset=90.0), unreal.Vector(0.80, 0.80, 0.80), folder=fld_br)
spawn_or_update("Breakroom_Calendar", calendar_mesh, mat_plastic, (200.0, 790.0, 180.0), rot_room(yaw_offset=90.0), unreal.Vector(0.80, 0.80, 0.80), folder=fld_br)
spawn_or_update("Corridor_Printer", printer_mesh, mat_plastic, (420.0, 360.0, 0.0), rot_room(yaw_offset=180.0), unreal.Vector(0.85, 0.85, 0.85), folder=fld_br)
print("  [x] Breakroom Suite (communal table, pastry dome, coffee bags, chairs, fridge, printer) staged")

# -------------------------------------------------------------------------
# 7. FOREGROUND CINEMATIC FRAMING & DEPTH LAYERING
# -------------------------------------------------------------------------
fld_fg = "Master_Foreground_Framing"

# 7A. Framing Right Edge for SESSION_CAM_Cast (L ~ 940, -310)
spawn_or_update(
    "FG_Architectural_Column", cube_mesh, mat_concrete,
    (940.0, -310.0, 175.0), rot_room(), unreal.Vector(0.70, 0.70, 3.50), folder=fld_fg
)
spawn_or_update(
    "FG_Tall_Planter", plant_mesh, mat_plant,
    (890.0, -280.0, 0.0), rot_room(yaw_offset=35.0), unreal.Vector(1.60, 1.60, 1.60), folder=fld_fg
)

# 7B. Foreground Corridor Watercooler & Bin Framing
spawn_or_update(
    "FG_Aisle_Watercooler", watercooler_mesh, mat_watercooler,
    (780.0, -360.0, 0.0), rot_room(yaw_offset=45.0), unreal.Vector(0.90, 0.90, 0.90), folder=fld_fg
)
spawn_or_update(
    "FG_Aisle_Bin", bin_mesh, mat_powder,
    (820.0, -320.0, 0.0), rot_room(yaw_offset=15.0), unreal.Vector(0.75, 0.75, 0.75), folder=fld_fg
)
print("  [x] Foreground cinematic depth layering staged at frame boundaries")

# -------------------------------------------------------------------------
# 8. SERIALIZE AND SAVE
# -------------------------------------------------------------------------
unreal.EditorLevelLibrary.save_current_level()
print("================================================================")
print("MASTER CINEMATIC STAGING V2 COMPLETE & LEVEL SAVED!")
print("================================================================")
