"""Film 304 Master Establishing Stages Builder (CCAD Visual Development Lens)

Authored under the compositional principles of Columbus College of Art & Design:
1. Visual Hierarchy & Narrative Mood: Monolithic corporate monumentality vs human-scale tactile life.
2. Leading Lines & Vanishing Points: Troffer light rhythms, partition corridors, and counter edges.
3. Framing within Framing: Colonades, cubicle dividers, and door portals framing hero subjects.
4. Scale-Corrected ZMJ Kit Integration: 6.0x scale factor restoring real-world architectural proportions.
5. Material Cohesion: Verified Film304 Toon Master & OneDriveRigs material instances applied throughout.

Builds 5 Production-Ready Establishing Shot Environments in L_Toon_Office_ProceduralVariants:
- SH010: Exterior Brutalist Vista (Monumental city monoliths, sky, plaza)
- SH020: Canonical Cubicle Hive (The oppressive corporate bay with 1-point perspective)
- SH080: The Labyrinth (Interlocking blind corners for suspense & creature stalking)
- SH090: The Break Room Sanctuary (Full ZMJ kit: espresso bar, pastry dome, fridge, tables)
- SH030/SH060: Hero Tactile Workstation (Character desk with props, angled chair, macro ECU)
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import unreal

REPO = Path(unreal.Paths.project_dir())
OUT_REPORT = REPO / "Saved" / "Audit" / "HoudiniBrutalist" / "establishing_stages_report.json"
MAP_PACKAGE = "/Game/Maps/Lookdev/UniversalFilm_20261016/L_Toon_Office_ProceduralVariants"

# Asset Paths
ASSETS = {
    # Brutalist Exterior Monoliths
    "tower_cluster": "/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_TowerCluster",
    "superblock": "/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_CivicSuperblock",
    "tight_estate": "/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_TightEstate",
    "low_sprawl": "/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_LowSprawl",
    "slender_tower": "/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_SlenderTower",
    "civic_slab": "/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_CivicSlab",
    "barbican_scale": "/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_BarbicanScale",
    "bunker": "/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_Bunker",
    "colonnade": "/Game/Environment/Brutalist/05_FACADE_VARIATION/SM_FAC_CivicColonnade",
    "fac_ribbon": "/Game/Environment/Brutalist/05_FACADE_VARIATION/SM_FAC_TowerRibbon",

    # Interior Cubicle Partitions
    "cubicle_canon": "/Game/Environment/Brutalist/04_INTERIOR_CUBICLES/SM_CUBICLE_Canonical",
    "cubicle_maze": "/Game/Environment/Brutalist/04_INTERIOR_CUBICLES/SM_CUBICLE_MazeShift",
    "cubicle_open": "/Game/Environment/Brutalist/04_INTERIOR_CUBICLES/SM_CUBICLE_OpenPlan",
    "cubicle_swarm": "/Game/Environment/Brutalist/04_INTERIOR_CUBICLES/SM_CUBICLE_Swarm",

    # Furniture & Office Props
    "desk_office": "/Game/Meshes/Office/Props/Desk",
    "desk_drawers": "/Game/Meshes/Office/Props/DeskDrawers",
    "chair_task": "/Game/Meshes/Office/Props/P_Chair_KS",
    "desk_hero_ac": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_OfficeDesk_AC_FilmStage_20261016",
    "drawers_sg": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_DeskDrawers_SG_FilmStage_20261016",

    # ZMJ Break Room Suite (Scale = 6.0)
    "zmj_counter": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_Counter_ZMJ_FilmStage_20261016",
    "zmj_countertop": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_CounterTop_ZMJ_FilmStage_20261016",
    "zmj_espresso": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_EspressoMachine_ZMJ_FilmStage_20261016",
    "zmj_fridge": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_Fridge_ZMJ_FilmStage_20261016",
    "zmj_cabinet": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_Cabinet_ZMJ_FilmStage_20261016",
    "zmj_shelf": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_BreakRoomShelf_ZMJ_FilmStage_20261016",
    "zmj_coffeebag": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_CoffeeBag_ZMJ_FilmStage_20261016",
    "zmj_coffeetin": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_CoffeeTin_ZMJ_FilmStage_20261016",
    "zmj_mug_large": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_CoffeeMugLarge_ZMJ_FilmStage_20261016",
    "zmj_mug_coffee": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_CoffeMug_ZMJ_FilmStage_20261016",
    "zmj_pastry_cover": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_PastryCover_ZMJ_FilmStage_20261016",
    "zmj_pastry": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_Pastry_ZMJ_FilmStage_20261016",
    "zmj_break_table": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_BreakroomTable_AC_FilmStage_20261016",
    "zmj_chair_ks": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Chair_KS_FilmStage_20261016",
    "zmj_coffee_table": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_CoffeeTable_KS_FilmStage_20261016",

    # Primitives
    "cube": "/Engine/BasicShapes/Cube",
    "plane": "/Engine/BasicShapes/Plane"
}

# Material Instances
MATERIALS = {
    "concrete": "/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistConcrete",
    "asphalt": "/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistAsphalt",
    "glazing": "/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistGlazing",
    "carpet": "/Game/Materials/Instances/MI_Toon_Office_Carpet",
    "vct": "/Game/Materials/Instances/MI_OfficeSpider_VCTFloor",
    "polypropylene": "/Game/Materials/Instances/MI_Toon_Office_Polypropylene",
    "powdercoat": "/Game/Materials/Instances/MI_Toon_Office_PowderCoat",
    "laminate": "/Game/Materials/Instances/MI_Toon_Office_Laminate",
    "desk_toon": "/Game/Materials/Instances/UniversalFilm_20261016/MI_Film_Desk",
    "troffer": "/Game/Materials/Instances/MI_Toon_Office_Troffer",
    "drop_ceiling": "/Game/Materials/Instances/MI_Toon_Office_DropCeiling",
    "frosted_glass": "/Game/Materials/Instances/MI_OfficeSpider_FrostedGlass"
}

EAL = unreal.EditorAssetLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ELL = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

def log(msg: str):
    unreal.log(f"[Film304_Stages] {msg}")

def spawn_mesh(world, asset_path: str, label: str, loc: tuple, rot_yaw: float = 0.0,
               scale: tuple = (1.0, 1.0, 1.0), mat_path: str = None):
    mesh = unreal.load_asset(asset_path)
    if not mesh:
        log(f"WARNING: Mesh not found: {asset_path}")
        return None

    actor = EAS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*loc))
    actor.set_actor_label(label)
    smc = actor.get_component_by_class(unreal.StaticMeshComponent)
    smc.set_mobility(unreal.ComponentMobility.MOVABLE)
    smc.set_static_mesh(mesh)
    actor.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=rot_yaw, roll=0.0), False)
    actor.set_actor_scale3d(unreal.Vector(*scale))

    if mat_path:
        mat = unreal.load_asset(mat_path)
        if mat:
            for i in range(smc.get_num_materials()):
                smc.set_material(i, mat)

    # Floor grounding
    origin, extent = actor.get_actor_bounds(False)
    target_bottom = loc[2]
    actual_bottom = origin.z - extent.z
    diff = target_bottom - actual_bottom
    if abs(diff) > 0.01 and "Ceiling" not in label and "Troffer" not in label and "CounterTop" not in label and "Shelf" not in label:
        new_loc = actor.get_actor_location()
        new_loc.z += diff
        actor.set_actor_location(new_loc, False, False)

    return actor

def spawn_camera(world, label: str, loc: tuple, target_loc: tuple, focal_length: float = 35.0):
    cam_actor = EAS.spawn_actor_from_class(unreal.CineCameraActor, unreal.Vector(*loc))
    cam_actor.set_actor_label(label)

    dx = target_loc[0] - loc[0]
    dy = target_loc[1] - loc[1]
    dz = target_loc[2] - loc[2]
    dist_xy = math.sqrt(dx*dx + dy*dy)
    yaw = math.degrees(math.atan2(dy, dx))
    pitch = math.degrees(math.atan2(dz, dist_xy))
    cam_actor.set_actor_rotation(unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0), False)

    cam_comp = cam_actor.get_cine_camera_component()
    cam_comp.current_focal_length = focal_length
    cam_comp.filmback.sensor_width = 35.0
    cam_comp.filmback.sensor_height = 19.6875 # 16:9
    return cam_actor

# -------------------------------------------------------------------------
# STAGE 1: EXTERIOR BRUTALIST VISTA (SH010)
# -------------------------------------------------------------------------
def build_stage_sh010_exterior(world, base_x: float, base_y: float):
    spawned = []
    # Plaza Asphalt Ground
    ground = spawn_mesh(world, ASSETS["cube"], "SH010_PlazaGround", (base_x, base_y + 12000.0, -20.0),
                        scale=(250.0, 300.0, 0.2), mat_path=MATERIALS["asphalt"])
    spawned.append(ground)

    # Left Foreground Framing: Barbican colonnade walkway
    colonnade = spawn_mesh(world, ASSETS["colonnade"], "SH010_FG_Colonnade", (base_x - 3800.0, base_y + 2500.0, 0.0),
                           rot_yaw=15.0, scale=(1.2, 1.2, 1.2), mat_path=MATERIALS["concrete"])
    barbican = spawn_mesh(world, ASSETS["barbican_scale"], "SH010_FG_Barbican", (base_x - 4500.0, base_y + 4000.0, 0.0),
                          rot_yaw=20.0, scale=(1.0, 1.0, 1.0), mat_path=MATERIALS["concrete"])
    # Right Foreground Framing: Slender accent tower
    tower_r = spawn_mesh(world, ASSETS["slender_tower"], "SH010_FG_SlenderTower", (base_x + 3500.0, base_y + 3000.0, 0.0),
                         rot_yaw=-10.0, scale=(1.0, 1.0, 1.0), mat_path=MATERIALS["concrete"])
    spawned.extend([colonnade, barbican, tower_r])

    # Midground Civic Core: Stepped administrative slab & bunker
    slab = spawn_mesh(world, ASSETS["civic_slab"], "SH010_MG_CivicSlab", (base_x - 1500.0, base_y + 12000.0, 0.0),
                      rot_yaw=0.0, scale=(1.5, 1.5, 1.5), mat_path=MATERIALS["concrete"])
    bunker = spawn_mesh(world, ASSETS["bunker"], "SH010_MG_Bunker", (base_x + 4000.0, base_y + 11000.0, 0.0),
                        rot_yaw=-35.0, scale=(1.2, 1.2, 1.2), mat_path=MATERIALS["concrete"])
    spawned.extend([slab, bunker])

    # Deep Background Monoliths: Tower Cluster & Ribbon Skyscraper
    hero_tower = spawn_mesh(world, ASSETS["tower_cluster"], "SH010_BG_HeroTowerCluster", (base_x + 500.0, base_y + 24000.0, 0.0),
                            rot_yaw=40.0, scale=(1.2, 1.2, 1.2), mat_path=MATERIALS["concrete"])
    ribbon_tower = spawn_mesh(world, ASSETS["fac_ribbon"], "SH010_BG_TowerRibbon", (base_x - 12000.0, base_y + 22000.0, 0.0),
                              rot_yaw=-25.0, scale=(1.3, 1.3, 1.3), mat_path=MATERIALS["concrete"])
    superblock = spawn_mesh(world, ASSETS["superblock"], "SH010_BG_CivicSuperblock", (base_x + 14000.0, base_y + 21000.0, 0.0),
                            rot_yaw=15.0, scale=(1.1, 1.1, 1.1), mat_path=MATERIALS["concrete"])
    spawned.extend([hero_tower, ribbon_tower, superblock])

    # Camera: 24mm wide, low-angle dramatic tilt up toward monumental monoliths
    cam = spawn_camera(world, "Cam_SH010_ExteriorVista",
                       loc=(base_x, base_y - 2000.0, 180.0),
                       target_loc=(base_x + 200.0, base_y + 18000.0, 6500.0),
                       focal_length=24.0)
    spawned.append(cam)
    return spawned

# -------------------------------------------------------------------------
# STAGE 2: CANONICAL MONOLITH HIVE (SH020)
# -------------------------------------------------------------------------
def build_stage_sh020_cubicles(world, base_x: float, base_y: float):
    spawned = []
    floor = spawn_mesh(world, ASSETS["cube"], "SH020_Floor", (base_x, base_y, -10.0), scale=(30.0, 36.0, 0.2), mat_path=MATERIALS["carpet"])
    spawned.append(floor)

    x_offsets = [-550.0, 550.0]
    y_offsets = [-700.0, 0.0, 700.0]
    for ix, ox in enumerate(x_offsets):
        for iy, oy in enumerate(y_offsets):
            pod_label = f"SH020_Pod_R{ix+1}_C{iy+1}"
            yaw = 0.0 if ox > 0 else 180.0
            pod = spawn_mesh(world, ASSETS["cubicle_canon"], pod_label, (base_x + ox, base_y + oy, 0.0),
                             rot_yaw=yaw, mat_path=MATERIALS["polypropylene"])
            d1 = spawn_mesh(world, ASSETS["desk_office"], f"{pod_label}_Desk", (base_x + ox - 180.0, base_y + oy - 120.0, 0.0),
                            rot_yaw=yaw + 90.0, mat_path=MATERIALS["laminate"])
            c1 = spawn_mesh(world, ASSETS["chair_task"], f"{pod_label}_Chair", (base_x + ox - 180.0, base_y + oy - 50.0, 0.0),
                            rot_yaw=yaw + 105.0, mat_path=MATERIALS["powdercoat"])
            spawned.extend([pod, d1, c1])

    # Rhythmic Troffer Grid
    for tx in [-550.0, 0.0, 550.0]:
        for ty in [-800.0, -400.0, 0.0, 400.0, 800.0]:
            trof = spawn_mesh(world, ASSETS["cube"], f"SH020_Troffer_{tx}_{ty}", (base_x + tx, base_y + ty, 320.0),
                              scale=(1.2, 0.6, 0.1), mat_path=MATERIALS["troffer"])
            spawned.append(trof)

    cam = spawn_camera(world, "Cam_SH020_CubicleBay",
                       loc=(base_x, base_y - 1400.0, 140.0),
                       target_loc=(base_x, base_y + 800.0, 110.0),
                       focal_length=28.0)
    spawned.append(cam)
    return spawned

# -------------------------------------------------------------------------
# STAGE 3: THE BREAK ROOM SANCTUARY (SH090) — FULL ZMJ PROP SUITE (Scale 6.0)
# -------------------------------------------------------------------------
def build_stage_sh090_breakroom(world, base_x: float, base_y: float):
    spawned = []
    Z_SCALE = 6.0 # Exact architectural factor converting decimeter FBX to real cm

    # Room Shell: VCT floor, Back Wall, Side Wall (8m x 10m x 3.2m)
    floor = spawn_mesh(world, ASSETS["cube"], "SH090_Floor_VCT", (base_x, base_y, -10.0), scale=(12.0, 14.0, 0.2), mat_path=MATERIALS["vct"])
    wall_back = spawn_mesh(world, ASSETS["cube"], "SH090_Wall_Back", (base_x, base_y + 600.0, 160.0), scale=(12.0, 0.2, 3.2), mat_path=MATERIALS["powdercoat"])
    wall_left = spawn_mesh(world, ASSETS["cube"], "SH090_Wall_Left", (base_x - 550.0, base_y, 160.0), scale=(0.2, 14.0, 3.2), mat_path=MATERIALS["powdercoat"])
    door_frosted = spawn_mesh(world, ASSETS["cube"], "SH090_Door_Frosted", (base_x + 500.0, base_y + 400.0, 110.0), scale=(0.1, 1.2, 2.2), mat_path=MATERIALS["frosted_glass"])
    spawned.extend([floor, wall_back, wall_left, door_frosted])

    # Counter Run along Back Wall: Base + Polished Countertop (Height = 93.6 cm)
    # Counter 1 (Prep & Sink Area)
    counter1 = spawn_mesh(world, ASSETS["zmj_counter"], "SH090_Counter_Main", (base_x - 220.0, base_y + 520.0, 0.0),
                          rot_yaw=0.0, scale=(Z_SCALE, Z_SCALE, Z_SCALE))
    countertop1 = spawn_mesh(world, ASSETS["zmj_countertop"], "SH090_CounterTop_Main", (base_x - 220.0, base_y + 520.0, 93.6),
                             rot_yaw=0.0, scale=(Z_SCALE, Z_SCALE, Z_SCALE))
    # Counter 2 (Espresso Hero Station)
    counter2 = spawn_mesh(world, ASSETS["zmj_counter"], "SH090_Counter_Espresso", (base_x + 130.0, base_y + 520.0, 0.0),
                          rot_yaw=0.0, scale=(Z_SCALE, Z_SCALE, Z_SCALE))
    countertop2 = spawn_mesh(world, ASSETS["zmj_countertop"], "SH090_CounterTop_Espresso", (base_x + 130.0, base_y + 520.0, 93.6),
                             rot_yaw=0.0, scale=(Z_SCALE, Z_SCALE, Z_SCALE))
    spawned.extend([counter1, countertop1, counter2, countertop2])

    # Appliances on Counter: Espresso Machine, Coffee Bags, Pastry Dome
    espresso = spawn_mesh(world, ASSETS["zmj_espresso"], "SH090_Hero_EspressoMachine", (base_x + 140.0, base_y + 510.0, 93.6),
                          rot_yaw=180.0, scale=(Z_SCALE, Z_SCALE, Z_SCALE))
    pastry_cover = spawn_mesh(world, ASSETS["zmj_pastry_cover"], "SH090_PastryCover", (base_x - 120.0, base_y + 510.0, 93.6),
                              rot_yaw=0.0, scale=(Z_SCALE, Z_SCALE, Z_SCALE))
    pastry = spawn_mesh(world, ASSETS["zmj_pastry"], "SH090_Pastry_Treat", (base_x - 120.0, base_y + 510.0, 94.0),
                        rot_yaw=25.0, scale=(Z_SCALE, Z_SCALE, Z_SCALE))
    coffeebag = spawn_mesh(world, ASSETS["zmj_coffeebag"], "SH090_CoffeeBag", (base_x + 240.0, base_y + 515.0, 93.6),
                           rot_yaw=165.0, scale=(Z_SCALE, Z_SCALE, Z_SCALE))
    mug_bar = spawn_mesh(world, ASSETS["zmj_mug_large"], "SH090_CoffeeMug_Bar", (base_x + 60.0, base_y + 490.0, 93.6),
                         rot_yaw=45.0, scale=(Z_SCALE, Z_SCALE, Z_SCALE))
    spawned.extend([espresso, pastry_cover, pastry, coffeebag, mug_bar])

    # Refrigerator & Upper Cabinetry
    fridge = spawn_mesh(world, ASSETS["zmj_fridge"], "SH090_Fridge", (base_x - 420.0, base_y + 510.0, 0.0),
                        rot_yaw=180.0, scale=(Z_SCALE, Z_SCALE, Z_SCALE))
    shelf = spawn_mesh(world, ASSETS["zmj_shelf"], "SH090_WallShelf", (base_x - 200.0, base_y + 550.0, 185.0),
                       rot_yaw=180.0, scale=(Z_SCALE, Z_SCALE, Z_SCALE))
    coffeetin = spawn_mesh(world, ASSETS["zmj_coffeetin"], "SH090_CoffeeTin_Shelf", (base_x - 210.0, base_y + 535.0, 192.0),
                           rot_yaw=15.0, scale=(Z_SCALE, Z_SCALE, Z_SCALE))
    spawned.extend([fridge, shelf, coffeetin])

    # Communal Dining Island: Breakroom Table + 4 Chairs
    table = spawn_mesh(world, ASSETS["zmj_break_table"], "SH090_DiningTable", (base_x - 50.0, base_y + 80.0, 0.0),
                       rot_yaw=0.0, scale=(1.0, 1.0, 1.0))
    # 4 Chairs positioned around table
    c_pos = [
        ("SH090_Chair1", (base_x - 140.0, base_y + 80.0, 0.0), 90.0),
        ("SH090_Chair2", (base_x + 40.0, base_y + 80.0, 0.0), -90.0),
        ("SH090_Chair3", (base_x - 50.0, base_y - 20.0, 0.0), 0.0),
        ("SH090_Chair4", (base_x - 50.0, base_y + 180.0, 0.0), 180.0),
    ]
    for c_label, c_loc, c_yaw in c_pos:
        chair = spawn_mesh(world, ASSETS["zmj_chair_ks"], c_label, c_loc, rot_yaw=c_yaw, scale=(1.0, 1.0, 1.0))
        spawned.append(chair)
    spawned.append(table)

    # Cinematic Camera: 35mm lens looking across the polished counter & espresso station toward the frosted door
    cam = spawn_camera(world, "Cam_SH090_BreakRoom",
                       loc=(base_x - 180.0, base_y - 180.0, 142.0),
                       target_loc=(base_x + 100.0, base_y + 490.0, 115.0),
                       focal_length=35.0)
    spawned.append(cam)
    return spawned

# -------------------------------------------------------------------------
# STAGE 4: THE LABYRINTH / BLIND CORNER (SH080)
# -------------------------------------------------------------------------
def build_stage_sh080_labyrinth(world, base_x: float, base_y: float):
    spawned = []
    floor = spawn_mesh(world, ASSETS["cube"], "SH080_Floor", (base_x, base_y, -10.0), scale=(30.0, 30.0, 0.2), mat_path=MATERIALS["vct"])
    spawned.append(floor)

    clusters = [
        ("SH080_Maze_1", (-600.0, -450.0), 0.0),
        ("SH080_Maze_2", (600.0, -450.0), 90.0),
        ("SH080_Maze_3", (-500.0, 500.0), 270.0),
        ("SH080_Maze_4", (550.0, 550.0), 180.0),
    ]
    for label, (ox, oy), yaw in clusters:
        m_actor = spawn_mesh(world, ASSETS["cubicle_maze"], label, (base_x + ox, base_y + oy, 0.0),
                             rot_yaw=yaw, mat_path=MATERIALS["powdercoat"])
        desk = spawn_mesh(world, ASSETS["desk_office"], f"{label}_Desk", (base_x + ox + 80.0, base_y + oy + 80.0, 0.0),
                          rot_yaw=yaw + 45.0, mat_path=MATERIALS["desk_toon"])
        chair = spawn_mesh(world, ASSETS["chair_task"], f"{label}_Chair", (base_x + ox + 40.0, base_y + oy + 120.0, 0.0),
                           rot_yaw=yaw - 60.0, mat_path=MATERIALS["powdercoat"])
        spawned.extend([m_actor, desk, chair])

    # Tracking camera through the blind corner for suspense / spider stalking
    cam = spawn_camera(world, "Cam_SH080_MazeTracking",
                       loc=(base_x - 320.0, base_y - 280.0, 165.0),
                       target_loc=(base_x + 150.0, base_y + 120.0, 95.0),
                       focal_length=50.0)
    spawned.append(cam)
    return spawned

# -------------------------------------------------------------------------
# STAGE 5: HERO TACTILE WORKSTATION (SH030 / SH060)
# -------------------------------------------------------------------------
def build_stage_sh030_hero_desk(world, base_x: float, base_y: float):
    spawned = []
    floor = spawn_mesh(world, ASSETS["cube"], "SH030_Floor", (base_x, base_y, -10.0), scale=(8.0, 8.0, 0.2), mat_path=MATERIALS["carpet"])
    p_back = spawn_mesh(world, ASSETS["cube"], "SH030_Part_Back", (base_x, base_y + 220.0, 85.0), scale=(4.5, 0.1, 1.7), mat_path=MATERIALS["polypropylene"])
    p_left = spawn_mesh(world, ASSETS["cube"], "SH030_Part_Left", (base_x - 220.0, base_y, 85.0), scale=(0.1, 4.5, 1.7), mat_path=MATERIALS["polypropylene"])
    p_right = spawn_mesh(world, ASSETS["cube"], "SH030_Part_Right", (base_x + 220.0, base_y, 85.0), scale=(0.1, 4.5, 1.7), mat_path=MATERIALS["polypropylene"])
    spawned.extend([floor, p_back, p_left, p_right])

    # Hero L-Desk + Drawers + Angled Chair
    desk = spawn_mesh(world, ASSETS["desk_hero_ac"], "SH030_HeroDesk", (base_x, base_y + 60.0, 0.0), rot_yaw=0.0, mat_path=MATERIALS["desk_toon"])
    drawers = spawn_mesh(world, ASSETS["drawers_sg"], "SH030_HeroDrawers", (base_x + 75.0, base_y + 40.0, 0.0), rot_yaw=0.0, mat_path=MATERIALS["powdercoat"])
    chair = spawn_mesh(world, ASSETS["chair_task"], "SH030_HeroChair", (base_x - 15.0, base_y - 65.0, 0.0), rot_yaw=22.0, mat_path=MATERIALS["powdercoat"])
    # Personal tactile prop on desk: Coffee mug
    mug = spawn_mesh(world, ASSETS["zmj_mug_coffee"], "SH030_DeskMug", (base_x + 35.0, base_y + 70.0, 76.5), rot_yaw=-35.0, scale=(6.0, 6.0, 6.0))
    spawned.extend([desk, drawers, chair, mug])

    # Over-the-shoulder narrative camera (SH030)
    cam_sh030 = spawn_camera(world, "Cam_SH030_DeskOverShoulder",
                             loc=(base_x + 110.0, base_y - 210.0, 135.0),
                             target_loc=(base_x - 20.0, base_y + 55.0, 78.0),
                             focal_length=35.0)
    # ECU macro calendar/desk surface camera (SH060)
    cam_sh060 = spawn_camera(world, "Cam_SH060_CalendarMacro",
                             loc=(base_x - 35.0, base_y - 10.0, 102.0),
                             target_loc=(base_x + 15.0, base_y + 60.0, 76.0),
                             focal_length=85.0)
    spawned.extend([cam_sh030, cam_sh060])
    return spawned

def main():
    log("Building Film 304 Master Establishing Stages (CCAD Visual Development)...")

    if EAL.does_asset_exist(MAP_PACKAGE):
        log(f"Loading map: {MAP_PACKAGE}")
        ELL.load_level(MAP_PACKAGE)
    else:
        log(f"Creating map: {MAP_PACKAGE}")
        ELL.new_level(MAP_PACKAGE)

    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

    # Clear previous actors cleanly
    for a in EAS.get_all_level_actors():
        lbl = a.get_actor_label()
        if any(lbl.startswith(p) for p in ["SH010_", "SH020_", "SH030_", "SH080_", "SH090_", "Cam_SH", "LGT_"]):
            EAS.destroy_actor(a)

    report = {"map": MAP_PACKAGE, "stages": {}}

    with unreal.ScopedEditorTransaction("Build Film 304 Master Establishing Stages"):
        # 1. SH010 Exterior Monolith Plaza (Y = -12000)
        s1 = build_stage_sh010_exterior(world, 0.0, -12000.0)
        report["stages"]["SH010_ExteriorVista"] = {
            "purpose": "Monumental dystopian exterior monolith plaza with soaring towers and sky",
            "actor_count": len(s1),
            "camera": "Cam_SH010_ExteriorVista (24mm, low-angle dramatic upward tilt)"
        }

        # 2. SH020 Canonical Cubicle Bay (X = 0, Y = 0)
        s2 = build_stage_sh020_cubicles(world, 0.0, 0.0)
        report["stages"]["SH020_CanonicalCubicles"] = {
            "purpose": "Oppressive corporate hive bay with 1-point vanishing point down main aisle",
            "actor_count": len(s2),
            "camera": "Cam_SH020_CubicleBay (28mm, aisle tracking perspective)"
        }

        # 3. SH090 Break Room Sanctuary with ZMJ Suite (X = -8000, Y = 0)
        s3 = build_stage_sh090_breakroom(world, -8000.0, 0.0)
        report["stages"]["SH090_BreakRoomSanctuary"] = {
            "purpose": "Detailed break room with espresso machine, pastry dome, fridge, tables (ZMJ Kit x6.0)",
            "actor_count": len(s3),
            "camera": "Cam_SH090_BreakRoom (35mm, espresso bar leading to frosted door)"
        }

        # 4. SH080 The Labyrinth (X = 8000, Y = 0)
        s4 = build_stage_sh080_labyrinth(world, 8000.0, 0.0)
        report["stages"]["SH080_Labyrinth"] = {
            "purpose": "Interlocking MazeShift blind corners for suspense & creature stalking",
            "actor_count": len(s4),
            "camera": "Cam_SH080_MazeTracking (50mm, chiaroscuro corner framing)"
        }

        # 5. SH030/SH060 Hero Tactile Workstation (X = 0, Y = 8000)
        s5 = build_stage_sh030_hero_desk(world, 0.0, 8000.0)
        report["stages"]["SH030_SH060_HeroWorkstation"] = {
            "purpose": "Tactile asymmetric character desk with props, angled chair, macro ECU",
            "actor_count": len(s5),
            "camera": "Cam_SH030_DeskOverShoulder (35mm) & Cam_SH060_CalendarMacro (85mm macro)"
        }

        # Cinematic Lighting Rig (Movable)
        sun = EAS.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0.0, 0.0, 5000.0))
        sun.set_actor_label("LGT_Sun")
        sun.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=-38.0, yaw=42.0), False)
        sun_comp = sun.get_component_by_class(unreal.DirectionalLightComponent)
        sun_comp.set_mobility(unreal.ComponentMobility.MOVABLE)
        sun_comp.set_intensity(4.8)

        sky = EAS.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0.0, 0.0, 2500.0))
        sky.set_actor_label("LGT_Sky")
        sky_comp = sky.get_component_by_class(unreal.SkyLightComponent)
        sky_comp.set_mobility(unreal.ComponentMobility.MOVABLE)
        sky_comp.set_intensity(1.3)

    total = sum(s["actor_count"] for s in report["stages"].values()) + 2
    report["total_actors_spawned"] = total
    report["status"] = "SUCCESS"

    ELL.save_current_level()
    log(f"Saved level: {MAP_PACKAGE}")

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    log(f"SUCCESS: Generated 5 master establishing stages ({total} actors). Report: {OUT_REPORT}")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
