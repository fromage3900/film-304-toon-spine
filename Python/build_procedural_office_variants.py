"""Procedural Office & Cubicle Layout Generator — Film 304 (CCAD Artist Lens)

Authored under the compositional principles of Columbus College of Art & Design:
1. Visual Hierarchy & Scale: Endless modular rhythm vs tactile character desk.
2. Leading Lines & Vanishing Points: Partition spines and troffer light grids directing the eye.
3. Framing within Framing: Foreground partition dividers framing the hero character action.
4. Chiaroscuro & Suspense: Labyrinthine blind corners for thriller/stalking beats (SH080).
5. Window Framing: Exterior Brutalist monoliths visible through curtain glass backdrops.

Generates 4 distinct procedural layout variants for shot staging:
- Variant A: BAY_CANONICAL_ORDER (The Monolith Hive — SH020/SH030 tracking)
- Variant B: BAY_MAZE_STALKER (The Claustrophobic Labyrinth — SH080 suspense)
- Variant C: BAY_OPEN_PANOPTICON (The Endless Floor — establishing wide with exterior vistas)
- Variant D: HERO_WORKSTATION_FOCUS (The Character Workspace — SH060 macro & over-the-shoulder)
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import unreal

REPO = Path(unreal.Paths.project_dir())
OUT_REPORT = REPO / "Saved" / "Audit" / "HoudiniBrutalist" / "office_cubicle_variants_report.json"
MAP_PACKAGE = "/Game/Maps/Lookdev/UniversalFilm_20261016/L_Toon_Office_ProceduralVariants"

# Asset Paths
ASSETS = {
    "cubicle_canon": "/Game/Environment/Brutalist/04_INTERIOR_CUBICLES/SM_CUBICLE_Canonical",
    "cubicle_maze": "/Game/Environment/Brutalist/04_INTERIOR_CUBICLES/SM_CUBICLE_MazeShift",
    "cubicle_open": "/Game/Environment/Brutalist/04_INTERIOR_CUBICLES/SM_CUBICLE_OpenPlan",
    "cubicle_swarm": "/Game/Environment/Brutalist/04_INTERIOR_CUBICLES/SM_CUBICLE_Swarm",
    "desk": "/Game/Meshes/Office/Props/Desk",
    "desk_hero": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_OfficeDesk_AC_FilmStage_20261016",
    "drawers": "/Game/Meshes/Office/Props/DeskDrawers",
    "chair": "/Game/Meshes/Office/Props/P_Chair_KS",
    "table_break": "/Game/Meshes/BreakRoom/Props/P_BreakroomTable_AC",
    "cube": "/Engine/BasicShapes/Cube",
    "plane": "/Engine/BasicShapes/Plane",
    # Exterior backdrop monoliths
    "tower_cluster": "/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_TowerCluster",
    "slender_tower": "/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_SlenderTower",
    "fac_ribbon": "/Game/Environment/Brutalist/05_FACADE_VARIATION/SM_FAC_TowerRibbon"
}

MATERIALS = {
    "carpet": "/Game/Materials/Instances/MI_Toon_Office_Carpet",
    "vct": "/Game/Materials/Instances/MI_OfficeSpider_VCTFloor",
    "polypropylene": "/Game/Materials/Instances/MI_Toon_Office_Polypropylene",
    "powdercoat": "/Game/Materials/Instances/MI_Toon_Office_PowderCoat",
    "laminate": "/Game/Materials/Instances/MI_Toon_Office_Laminate",
    "desk_toon": "/Game/Materials/Instances/UniversalFilm_20261016/MI_Film_Desk",
    "troffer": "/Game/Materials/Instances/MI_Toon_Office_Troffer",
    "drop_ceiling": "/Game/Materials/Instances/MI_Toon_Office_DropCeiling",
    "frosted_glass": "/Game/Materials/Instances/MI_OfficeSpider_FrostedGlass",
    "concrete": "/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistConcrete",
    "glazing": "/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistGlazing"
}

EAL = unreal.EditorAssetLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ELL = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

def log(msg: str):
    unreal.log(f"[CCAD_OfficeBuilder] {msg}")

def spawn_mesh(world, asset_path: str, label: str, loc: tuple, rot_yaw: float = 0.0,
               scale: tuple = (1.0, 1.0, 1.0), mat_path: str = None):
    """Spawns and configures a StaticMeshActor with exact transforms and materials."""
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

    # Floor grounding correction: ensure bounds bottom touches Z=loc[2]
    origin, extent = actor.get_actor_bounds(False)
    target_bottom = loc[2]
    actual_bottom = origin.z - extent.z
    diff = target_bottom - actual_bottom
    if abs(diff) > 0.01 and "Ceiling" not in label and "Troffer" not in label:
        new_loc = actor.get_actor_location()
        new_loc.z += diff
        actor.set_actor_location(new_loc, False, False)

    return actor

def spawn_camera(world, label: str, loc: tuple, target_loc: tuple, focal_length: float = 35.0):
    """Spawns a CineCameraActor with declared composition aim."""
    cam_actor = EAS.spawn_actor_from_class(unreal.CineCameraActor, unreal.Vector(*loc))
    cam_actor.set_actor_label(label)

    # Aim math
    dx = target_loc[0] - loc[0]
    dy = target_loc[1] - loc[1]
    dz = target_loc[2] - loc[2]
    dist_xy = math.sqrt(dx*dx + dy*dy)
    yaw = math.degrees(math.atan2(dy, dx))
    pitch = math.degrees(math.atan2(dz, dist_xy))
    cam_actor.set_actor_rotation(unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0), False)

    # Settings
    cam_comp = cam_actor.get_cine_camera_component()
    cam_comp.current_focal_length = focal_length
    cam_comp.filmback.sensor_width = 35.0
    cam_comp.filmback.sensor_height = 19.6875 # 16:9 Academy aspect
    return cam_actor

def build_variant_a_canonical_hive(world, base_x: float, base_y: float):
    """Variant A: The Monolith Hive (Oppressive parallel order for SH020/SH030 tracking)."""
    spawned = []
    # Floor: 24m x 36m Corporate Carpet
    floor = spawn_mesh(world, ASSETS["cube"], "A_Floor_Carpet", (base_x, base_y, -10.0), scale=(24.0, 36.0, 0.2), mat_path=MATERIALS["carpet"])
    spawned.append(floor)

    # Cubicle Row Grid: 2 rows of 3 Canonical Pods (each 10.2m x 6.6m)
    # Aisle width: 3.5m central walking corridor
    x_offsets = [-550.0, 550.0]
    y_offsets = [-700.0, 0.0, 700.0]

    for ix, ox in enumerate(x_offsets):
        for iy, oy in enumerate(y_offsets):
            pod_label = f"A_Cubicle_Row{ix+1}_Pod{iy+1}"
            yaw = 0.0 if ox > 0 else 180.0
            pod = spawn_mesh(world, ASSETS["cubicle_canon"], pod_label, (base_x + ox, base_y + oy, 0.0),
                             rot_yaw=yaw, mat_path=MATERIALS["polypropylene"])
            spawned.append(pod)

            # Inside each pod, place 2 desks + task chairs
            d1 = spawn_mesh(world, ASSETS["desk"], f"{pod_label}_Desk1", (base_x + ox - 180.0, base_y + oy - 120.0, 0.0),
                            rot_yaw=yaw + 90.0, mat_path=MATERIALS["laminate"])
            c1 = spawn_mesh(world, ASSETS["chair"], f"{pod_label}_Chair1", (base_x + ox - 180.0, base_y + oy - 50.0, 0.0),
                            rot_yaw=yaw + 105.0, mat_path=MATERIALS["powdercoat"])
            spawned.extend([d1, c1])

    # Overhead Troffer Lighting: Rhythmic ceiling light grid
    for tx in [-550.0, 0.0, 550.0]:
        for ty in [-800.0, -400.0, 0.0, 400.0, 800.0]:
            trof = spawn_mesh(world, ASSETS["cube"], f"A_Troffer_{tx}_{ty}", (base_x + tx, base_y + ty, 320.0),
                              scale=(1.2, 0.6, 0.1), mat_path=MATERIALS["troffer"])
            spawned.append(trof)

    # Camera: Oppressive wide one-point perspective looking down central corridor
    cam = spawn_camera(world, "Cam_A_BayWide_SH020",
                       loc=(base_x, base_y - 1400.0, 140.0),
                       target_loc=(base_x, base_y + 800.0, 110.0),
                       focal_length=28.0)
    spawned.append(cam)
    return spawned

def build_variant_b_maze_stalker(world, base_x: float, base_y: float):
    """Variant B: The Claustrophobic Labyrinth (Interlocking blind corners for SH080 tension)."""
    spawned = []
    # Floor: High-contrast VCT tile
    floor = spawn_mesh(world, ASSETS["cube"], "B_Floor_VCT", (base_x, base_y, -10.0), scale=(30.0, 30.0, 0.2), mat_path=MATERIALS["vct"])
    spawned.append(floor)

    # 4 Interlocking MazeShift units (17.6m x 10.6m) rotated to form winding blind corners
    maze_configs = [
        ("B_Maze_Cluster1", (-600.0, -450.0), 0.0),
        ("B_Maze_Cluster2", (600.0, -450.0), 90.0),
        ("B_Maze_Cluster3", (-500.0, 500.0), 270.0),
        ("B_Maze_Cluster4", (550.0, 550.0), 180.0),
    ]
    for label, (ox, oy), yaw in maze_configs:
        m_actor = spawn_mesh(world, ASSETS["cubicle_maze"], label, (base_x + ox, base_y + oy, 0.0),
                             rot_yaw=yaw, mat_path=MATERIALS["powdercoat"])
        spawned.append(m_actor)

        # Staggered task desks inside blind pockets
        desk = spawn_mesh(world, ASSETS["desk"], f"{label}_Desk", (base_x + ox + 80.0, base_y + oy + 80.0, 0.0),
                          rot_yaw=yaw + 45.0, mat_path=MATERIALS["desk_toon"])
        drawers = spawn_mesh(world, ASSETS["drawers"], f"{label}_Drawers", (base_x + ox + 110.0, base_y + oy + 40.0, 0.0),
                             rot_yaw=yaw + 45.0, mat_path=MATERIALS["powdercoat"])
        chair = spawn_mesh(world, ASSETS["chair"], f"{label}_Chair", (base_x + ox + 40.0, base_y + oy + 120.0, 0.0),
                           rot_yaw=yaw - 60.0, mat_path=MATERIALS["powdercoat"])
        spawned.extend([desk, drawers, chair])

    # Camera: Over-the-partition corner framing looking through blind junction
    cam = spawn_camera(world, "Cam_B_MazeTracking_SH080",
                       loc=(base_x - 320.0, base_y - 280.0, 165.0),
                       target_loc=(base_x + 150.0, base_y + 120.0, 95.0),
                       focal_length=50.0)
    spawned.append(cam)
    return spawned

def build_variant_c_panopticon_window(world, base_x: float, base_y: float):
    """Variant C: The Panopticon with Exterior Monolith Window Backdrop (SH015 establishing)."""
    spawned = []
    # Floor
    floor = spawn_mesh(world, ASSETS["cube"], "C_Floor_Carpet", (base_x, base_y, -10.0), scale=(36.0, 40.0, 0.2), mat_path=MATERIALS["carpet"])
    spawned.append(floor)

    # Low-partition Open Plan units (1.22m height) allowing sightlines to back wall
    open_configs = [
        ("C_Open_FrontL", (-750.0, -600.0), 0.0),
        ("C_Open_FrontR", (750.0, -600.0), 0.0),
        ("C_Swarm_Mid", (0.0, 150.0), 0.0),
    ]
    for label, (ox, oy), yaw in open_configs:
        asset_key = "cubicle_swarm" if "Swarm" in label else "cubicle_open"
        actor = spawn_mesh(world, ASSETS[asset_key], label, (base_x + ox, base_y + oy, 0.0),
                           rot_yaw=yaw, mat_path=MATERIALS["polypropylene"])
        spawned.append(actor)

    # Curtain Glass Wall at the rear: 36m wide x 6m high
    glass_wall = spawn_mesh(world, ASSETS["cube"], "C_CurtainWall_Glass", (base_x, base_y + 1950.0, 300.0),
                            scale=(36.0, 0.2, 6.0), mat_path=MATERIALS["glazing"])
    spawned.append(glass_wall)

    # Exterior Brutalist Monoliths framed directly through the window glass!
    tower1 = spawn_mesh(world, ASSETS["tower_cluster"], "C_Ext_CityTower", (base_x - 6000.0, base_y + 14000.0, 0.0),
                        rot_yaw=25.0, scale=(1.0, 1.0, 1.0), mat_path=MATERIALS["concrete"])
    tower2 = spawn_mesh(world, ASSETS["slender_tower"], "C_Ext_SlenderTower", (base_x + 3500.0, base_y + 11000.0, 0.0),
                        rot_yaw=-15.0, scale=(1.2, 1.2, 1.2), mat_path=MATERIALS["concrete"])
    spawned.extend([tower1, tower2])

    # Wide camera looking across low cubicles toward the monumental window view
    cam = spawn_camera(world, "Cam_C_Panopticon_SH015",
                       loc=(base_x, base_y - 1600.0, 180.0),
                       target_loc=(base_x - 400.0, base_y + 12000.0, 3200.0),
                       focal_length=24.0)
    spawned.append(cam)
    return spawned

def build_variant_d_hero_workstation(world, base_x: float, base_y: float):
    """Variant D: The Tactile Character Workspace (Asymmetric hero desk for SH030/SH060 macro)."""
    spawned = []
    # Hero workstation bay surrounded by 3 partition slabs
    floor = spawn_mesh(world, ASSETS["cube"], "D_Floor_Pod", (base_x, base_y, -10.0), scale=(8.0, 8.0, 0.2), mat_path=MATERIALS["carpet"])
    p_back = spawn_mesh(world, ASSETS["cube"], "D_Partition_Back", (base_x, base_y + 220.0, 85.0), scale=(4.5, 0.1, 1.7), mat_path=MATERIALS["polypropylene"])
    p_left = spawn_mesh(world, ASSETS["cube"], "D_Partition_Left", (base_x - 220.0, base_y, 85.0), scale=(0.1, 4.5, 1.7), mat_path=MATERIALS["polypropylene"])
    p_right = spawn_mesh(world, ASSETS["cube"], "D_Partition_Right", (base_x + 220.0, base_y, 85.0), scale=(0.1, 4.5, 1.7), mat_path=MATERIALS["polypropylene"])
    spawned.extend([floor, p_back, p_left, p_right])

    # Hero Desk: L-desk assembly with separate drawer unit
    desk = spawn_mesh(world, ASSETS["desk_hero"], "D_HeroDesk_AC", (base_x, base_y + 60.0, 0.0), rot_yaw=0.0, mat_path=MATERIALS["desk_toon"])
    drawers = spawn_mesh(world, ASSETS["drawers"], "D_HeroDrawers_SG", (base_x + 75.0, base_y + 40.0, 0.0), rot_yaw=0.0, mat_path=MATERIALS["powdercoat"])
    # Task chair angled naturally (22 degrees) as if recently pushed back by the worker
    chair = spawn_mesh(world, ASSETS["chair"], "D_HeroChair_KS", (base_x - 15.0, base_y - 65.0, 0.0), rot_yaw=22.0, mat_path=MATERIALS["powdercoat"])
    spawned.extend([desk, drawers, chair])

    # Over-the-shoulder medium shot (SH030)
    cam_med = spawn_camera(world, "Cam_D_OverShoulder_SH030",
                           loc=(base_x + 110.0, base_y - 210.0, 135.0),
                           target_loc=(base_x - 20.0, base_y + 55.0, 78.0),
                           focal_length=35.0)
    # ECU macro camera (SH060) targeting the calendar/paper region on the desk
    cam_macro = spawn_camera(world, "Cam_D_CalendarMacro_SH060",
                             loc=(base_x - 35.0, base_y - 10.0, 102.0),
                             target_loc=(base_x + 15.0, base_y + 60.0, 76.0),
                             focal_length=85.0)
    spawned.extend([cam_med, cam_macro])
    return spawned

def main():
    log("Starting CCAD-grade procedural office & cubicle layout generation...")

    # Load or create dedicated staging map
    world = None
    if EAL.does_asset_exist(MAP_PACKAGE):
        log(f"Loading existing map: {MAP_PACKAGE}")
        world = EAL.load_asset(MAP_PACKAGE)
        ELL.load_level(MAP_PACKAGE)
    else:
        log(f"Creating clean procedural staging map: {MAP_PACKAGE}")
        world = ELL.new_level(MAP_PACKAGE)

    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

    # Clear previous procedural actors in this map
    existing_actors = EAS.get_all_level_actors()
    removed_count = 0
    for a in existing_actors:
        label = a.get_actor_label()
        if any(label.startswith(p) for p in ["A_", "B_", "C_", "D_", "Cam_A_", "Cam_B_", "Cam_C_", "Cam_D_"]):
            EAS.destroy_actor(a)
            removed_count += 1
    log(f"Pruned {removed_count} previous procedural actors.")

    # Four Distinct Spatial Zones (spaced 80m apart so each shot has a clean, independent visual cone)
    report = {
        "map": MAP_PACKAGE,
        "variants": {}
    }

    with unreal.ScopedEditorTransaction("Build CCAD Procedural Office Variants"):
        # Variant A at X = 0, Y = 0
        spawned_a = build_variant_a_canonical_hive(world, 0.0, 0.0)
        report["variants"]["Variant_A_CanonicalHive"] = {
            "purpose": "Oppressive monolithic cubicle rows for SH020/SH030 tracking",
            "actor_count": len(spawned_a),
            "camera": "Cam_A_BayWide_SH020 (28mm, 1-point perspective)"
        }

        # Variant B at X = 8000, Y = 0
        spawned_b = build_variant_b_maze_stalker(world, 8000.0, 0.0)
        report["variants"]["Variant_B_MazeStalker"] = {
            "purpose": "Interlocking labyrinth blind corners for SH080 thriller/spider stalking",
            "actor_count": len(spawned_b),
            "camera": "Cam_B_MazeTracking_SH080 (50mm, chiaroscuro corner framing)"
        }

        # Variant C at X = 0, Y = 8000
        spawned_c = build_variant_c_panopticon_window(world, 0.0, 8000.0)
        report["variants"]["Variant_C_PanopticonWindow"] = {
            "purpose": "Open-plan floor with exterior Brutalist skyscraper vistas through curtain glass",
            "actor_count": len(spawned_c),
            "camera": "Cam_C_Panopticon_SH015 (24mm, deep horizon perspective)"
        }

        # Variant D at X = 8000, Y = 8000
        spawned_d = build_variant_d_hero_workstation(world, 8000.0, 8000.0)
        report["variants"]["Variant_D_HeroWorkstation"] = {
            "purpose": "Tactile asymmetric character desk for SH030 dialogue & SH060 macro ECU",
            "actor_count": len(spawned_d),
            "camera": "Cam_D_OverShoulder_SH030 (35mm) & Cam_D_CalendarMacro_SH060 (85mm macro)"
        }

        # Add cinematic key sun + fill sky so the layout reads immediately
        sun = EAS.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0.0, 0.0, 5000.0))
        sun.set_actor_label("LGT_Sun")
        sun.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=-45.0, yaw=35.0), False)
        sun_comp = sun.get_component_by_class(unreal.DirectionalLightComponent)
        sun_comp.set_mobility(unreal.ComponentMobility.MOVABLE)
        sun_comp.set_intensity(4.5)

        sky = EAS.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0.0, 0.0, 2500.0))
        sky.set_actor_label("LGT_Sky")
        sky_comp = sky.get_component_by_class(unreal.SkyLightComponent)
        sky_comp.set_mobility(unreal.ComponentMobility.MOVABLE)
        sky_comp.set_intensity(1.2)

    total_actors = sum(v["actor_count"] for v in report["variants"].values()) + 2
    report["total_actors_spawned"] = total_actors
    report["status"] = "SUCCESS"

    # Save level package
    unreal.EditorLoadingAndSavingUtils.save_packages([world.get_package()], False)
    log(f"Saved level package: {MAP_PACKAGE}")

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    log(f"Successfully generated 4 office layout variants ({total_actors} actors). Report saved to: {OUT_REPORT}")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
