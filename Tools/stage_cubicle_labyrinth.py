"""Stage the Bureaucratic Cubicle Labyrinth & Establishing Cameras in L_Film_Office.

Authored under the compositional principles of Film 304:
- Monolithic corporate repetition vs tactile human detail.
- Geometric 1-point and diagonal vanishing lines across modular partition pods.
- Fully dressed with desks, swivel chairs, monitors, keyboards, desk lamps, paper, and wastebaskets.
- Overhead troffers providing cool rhythmic down-pools contrasting warm desk lamps.
- Two dedicated CineCameras:
  * CineCam_Hero_CubicleEstablishing: 24mm wide high-angle overhead establishing shot.
  * CineCam_Hero_CubicleTrench: 35mm low-angle claustrophobic aisle perspective.
"""
import math
import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ELL = unreal.EditorLevelLibrary
FOLDER = "Baked_Cubicle_Labyrinth"

ASSETS = {
    "cubicle_canon": "/Game/Environment/Brutalist/04_INTERIOR_CUBICLES/SM_CUBICLE_Canonical",
    "cubicle_maze": "/Game/Environment/Brutalist/04_INTERIOR_CUBICLES/SM_CUBICLE_MazeShift",
    "desk": "/Game/Meshes/Office/Props/Desk",
    "drawers": "/Game/Meshes/Office/Props/DeskDrawers",
    "chair": "/Game/Meshes/Office/Props/P_Chair_KS",
    "monitor": "/Game/Meshes/Office/Props/P_ComputerMonitor_AC",
    "keyboard": "/Game/Meshes/Office/Props/P_Keyboard_KS",
    "lamp": "/Game/Meshes/Office/Props/P_Lamp_EF",
    "bin": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Bin01_SY_FilmStage_20261016",
    "filing": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_FilingCabinets_SG_FilmStage_20261016",
    "plant": "/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Plant_PMB_FilmStage_20261016",
    "cube": "/Engine/BasicShapes/Cube"
}

MATERIALS = {
    "polypropylene": "/Game/Materials/Instances/MI_Toon_Office_Polypropylene",
    "powdercoat": "/Game/Materials/Instances/MI_Toon_Office_PowderCoat",
    "desk_toon": "/Game/Materials/Instances/UniversalFilm_20261016/MI_Film_Desk",
    "troffer": "/Game/Materials/Instances/MI_Toon_Office_Troffer"
}

def spawn_mesh(asset_path: str, label: str, loc: tuple, rot_yaw: float = 0.0,
               scale: tuple = (1.0, 1.0, 1.0), mat_path: str = None):
    # Check if actor already exists to avoid duplicates
    for a in ELL.get_all_level_actors():
        if a.get_actor_label() == label:
            ELL.destroy_actor(a)
            break

    mesh = unreal.load_asset(asset_path)
    if not mesh:
        unreal.log_warning(f"[CubicleStage] Mesh missing: {asset_path}")
        return None

    actor = EAS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*loc))
    actor.set_actor_label(label)
    smc = actor.get_component_by_class(unreal.StaticMeshComponent)
    smc.set_mobility(unreal.ComponentMobility.MOVABLE)
    smc.set_static_mesh(mesh)
    actor.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=rot_yaw, roll=0.0), False)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    if hasattr(actor, "set_folder_path"):
        actor.set_folder_path(FOLDER)

    if mat_path:
        mat = unreal.load_asset(mat_path)
        if mat:
            for i in range(smc.get_num_materials()):
                smc.set_material(i, mat)
    return actor

def spawn_cine_camera(label: str, loc: tuple, target_loc: tuple, focal_length: float = 24.0, f_stop: float = 3.2):
    for a in ELL.get_all_level_actors():
        if a.get_actor_label() == label:
            ELL.destroy_actor(a)
            break

    cam_actor = EAS.spawn_actor_from_class(unreal.CineCameraActor, unreal.Vector(*loc))
    cam_actor.set_actor_label(label)
    if hasattr(cam_actor, "set_folder_path"):
        cam_actor.set_folder_path(FOLDER)

    dx = target_loc[0] - loc[0]
    dy = target_loc[1] - loc[1]
    dz = target_loc[2] - loc[2]
    dist_xy = math.sqrt(dx*dx + dy*dy)
    yaw = math.degrees(math.atan2(dy, dx))
    pitch = math.degrees(math.atan2(dz, dist_xy))
    cam_actor.set_actor_rotation(unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0), False)

    cam_comp = cam_actor.get_cine_camera_component()
    cam_comp.current_focal_length = focal_length
    cam_comp.filmback.sensor_width = 36.0
    cam_comp.filmback.sensor_height = 20.25 # 16:9 widescreen
    cam_comp.lens_settings.min_f_stop = 1.2
    cam_comp.lens_settings.max_f_stop = 22.0
    cam_comp.current_aperture = f_stop
    
    # Set manual focus distance to target
    dist_3d = math.sqrt(dx*dx + dy*dy + dz*dz)
    cam_comp.focus_settings.focus_method = unreal.CameraFocusMethod.MANUAL
    cam_comp.focus_settings.manual_focus_distance = dist_3d
    return cam_actor

def build_cubicle_labyrinth():
    unreal.log("[CubicleStage] Staging Bureaucratic Cubicle Labyrinth in L_Film_Office...")
    spawned_count = 0

    # 4 Major Pod Clusters
    # Pod A (West-South): (550, -420)
    # Pod B (West-North): (550, 240)
    # Pod C (East-South): (1100, -420)
    # Pod D (East-North): (1100, 240)
    pod_configs = [
        ("Pod_WS", 550.0, -420.0, 0.0),
        ("Pod_WN", 550.0, 240.0, 0.0),
        ("Pod_ES", 1100.0, -420.0, 180.0),
        ("Pod_EN", 1100.0, 240.0, 180.0),
    ]

    for p_name, px, py, pyaw in pod_configs:
        # Spawn Cubicle Partition Cluster
        pod_actor = spawn_mesh(ASSETS["cubicle_canon"], f"Cubicle_{p_name}", (px, py, 0.0),
                               rot_yaw=pyaw, mat_path=MATERIALS["polypropylene"])
        spawned_count += 1

        # In each pod, dress 4 workstation quadrants
        # Local offsets relative to pod center
        offsets = [
            ("Q1", -180.0, -120.0, 0.0),
            ("Q2", -180.0, 120.0, 180.0),
            ("Q3", 180.0, -120.0, 0.0),
            ("Q4", 180.0, 120.0, 180.0)
        ]
        for q_name, ox, oy, qyaw in offsets:
            wx = px + ox
            wy = py + oy
            full_yaw = pyaw + qyaw
            
            # Desk
            d_actor = spawn_mesh(ASSETS["desk"], f"Desk_{p_name}_{q_name}", (wx, wy, 0.0),
                                 rot_yaw=full_yaw + 90.0, mat_path=MATERIALS["desk_toon"])
            # Swivel Task Chair
            c_yaw = full_yaw + 95.0 + ((hash(q_name) % 25) - 12)
            c_actor = spawn_mesh(ASSETS["chair"], f"Chair_{p_name}_{q_name}", (wx + 30.0, wy + 25.0, 0.0),
                                 rot_yaw=c_yaw, mat_path=MATERIALS["powdercoat"])
            # Computer Monitor on Desk (Desk top is Z ~ 76)
            m_actor = spawn_mesh(ASSETS["monitor"], f"Monitor_{p_name}_{q_name}", (wx - 10.0, wy, 76.0),
                                 rot_yaw=full_yaw + 85.0)
            # Keyboard
            k_actor = spawn_mesh(ASSETS["keyboard"], f"Keyboard_{p_name}_{q_name}", (wx + 15.0, wy, 76.5),
                                 rot_yaw=full_yaw + 90.0)
            # Desk Lamp on selected desks
            if "Q1" in q_name or "Q4" in q_name:
                l_actor = spawn_mesh(ASSETS["lamp"], f"Lamp_{p_name}_{q_name}", (wx - 25.0, wy - 30.0, 76.0),
                                     rot_yaw=full_yaw + 45.0)
                # Small warm glow point light for the lamp
                lp = EAS.spawn_actor_from_class(unreal.PointLight, unreal.Vector(wx - 25.0, wy - 30.0, 105.0))
                lp.set_actor_label(f"Light_Lamp_{p_name}_{q_name}")
                if hasattr(lp, "set_folder_path"):
                    lp.set_folder_path(FOLDER)
                comp = lp.get_component_by_class(unreal.PointLightComponent)
                comp.set_intensity(25.0)
                comp.set_light_color(unreal.LinearColor(r=1.0, g=0.84, b=0.61, a=1.0)) # 3200K warm incandescent
                comp.set_attenuation_radius(180.0)

            spawned_count += 5

    # Filing Cabinets & Wastebaskets along Corridor Aisle
    aisle_dressing = [
        (ASSETS["filing"], "Filing_Aisle_01", (825.0, -550.0, 0.0), 90.0, MATERIALS["powdercoat"]),
        (ASSETS["filing"], "Filing_Aisle_02", (825.0, 380.0, 0.0), -90.0, MATERIALS["powdercoat"]),
        (ASSETS["bin"], "Wastebasket_Aisle_01", (800.0, -200.0, 0.0), 15.0, None),
        (ASSETS["bin"], "Wastebasket_Aisle_02", (850.0, 100.0, 0.0), -25.0, None),
        (ASSETS["plant"], "PottedPlant_Aisle_Corner", (825.0, -80.0, 0.0), 45.0, None),
    ]
    for m_path, lbl, loc, yaw, mat_p in aisle_dressing:
        spawn_mesh(m_path, lbl, loc, rot_yaw=yaw, mat_path=mat_p)
        spawned_count += 1

    # Overhead Troffer Lights along the Cubicle Aisle
    troffer_coords = [
        (550.0, -420.0), (550.0, -90.0), (550.0, 240.0),
        (825.0, -420.0), (825.0, -90.0), (825.0, 240.0),
        (1100.0, -420.0), (1100.0, -90.0), (1100.0, 240.0)
    ]
    for tx, ty in troffer_coords:
        # Troffer Mesh Box
        trof = spawn_mesh(ASSETS["cube"], f"Troffer_Mesh_{int(tx)}_{int(ty)}", (tx, ty, 310.0),
                          scale=(1.2, 0.6, 0.08), mat_path=MATERIALS["troffer"])
        # Rect Light casting cool neutral white down-pool
        rl = EAS.spawn_actor_from_class(unreal.RectLight, unreal.Vector(tx, ty, 305.0))
        rl.set_actor_label(f"Light_Troffer_{int(tx)}_{int(ty)}")
        rl.set_actor_rotation(unreal.Rotator(pitch=-90.0, yaw=0.0, roll=0.0), False)
        if hasattr(rl, "set_folder_path"):
            rl.set_folder_path(FOLDER)
        comp = rl.get_component_by_class(unreal.RectLightComponent)
        comp.set_intensity(4.5)
        comp.set_light_color(unreal.LinearColor(r=0.92, g=0.95, b=1.0, a=1.0)) # 4500K neutral fluorescent
        comp.set_attenuation_radius(350.0)
        comp.set_source_width(120.0)
        comp.set_source_height(60.0)
        spawned_count += 2

    # --- CAMERAS ---
    # Camera 1: High-Angle Wide Establishing Shot (The grand corporate labyrinth)
    cam_est = spawn_cine_camera(
        label="CineCam_Hero_CubicleEstablishing",
        loc=(220.0, -950.0, 420.0),
        target_loc=(825.0, -90.0, 95.0),
        focal_length=24.0,
        f_stop=3.2
    )
    # Camera 2: Low-Angle Claustrophobic Trench Dolly Shot
    cam_trench = spawn_cine_camera(
        label="CineCam_Hero_CubicleTrench",
        loc=(825.0, -780.0, 95.0),
        target_loc=(825.0, 200.0, 95.0),
        focal_length=35.0,
        f_stop=2.4
    )

    unreal.log(f"[CubicleStage] SUCCESS: Staged {spawned_count} actors + 2 CineCameras in {FOLDER}.")
    return spawned_count

if __name__ == "__main__":
    build_cubicle_labyrinth()
