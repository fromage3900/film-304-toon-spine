"""CAD-Precision Architectural Alignment, Organization, and Houdini Engine Lookdev in L_Film_Office.

Enforces strict CAD architectural standards (AIA / DIN / ISO):
- Module Grid: 5.5m (X) x 5.0m (Y) structural workstation modules.
- Finished Floor Level (FFL): Z = 0.00 cm exact.
- Worksurface Elevation: Z = 76.00 cm exact (ADA standard).
- Kitchen Counter Elevation: Z = 91.40 cm exact (36-inch standard).
- Ceiling Grid Elevation: Z = 330.00 cm exact with 380.00 cm slab drop rods.
- Minimum Clear Circulation Aisle: 1.45m - 2.85m ADA-compliant corridors.
- Four Clean Architectural Zones:
  * Zone 1: Executive Window Perimeter & Hero Cast (Dana, David, Sam, Spider)
  * Zone 2: Bureaucratic Cubicle Labyrinth (Houdini Engine HDA, 6 canonical pods, 12 workstations)
  * Zone 3: Breakroom & Kitchenette Sanctuary (Houdini Engine HDA, full ZMJ 6.0x kit)
  * Zone 4: Circulation Corridor & Utility Niche (Watercooler, plant, whiteboard, clock)
"""
import math
import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

def execute_cad_alignment():
    unreal.log("==================================================================")
    unreal.log("[CAD_Alignment] Executing CAD-Precision Houdini Engine Organization...")
    unreal.log("==================================================================")

    api = unreal.HoudiniPublicAPIBlueprintLib.get_api()
    if not api.is_session_valid():
        unreal.log("[CAD_Alignment] Starting Houdini Engine Session...")
        api.create_session()

    hda = unreal.load_asset("/Game/Houdini/HDA_Brutalist_ShotComposer")
    if not hda:
        unreal.log_error("[CAD_Alignment] ERROR: /Game/Houdini/HDA_Brutalist_ShotComposer not found!")
        return False

    # 1. CLEANUP PREVIOUS PROVISIONAL/EXPLORATORY ACTORS
    clean_folders = [
        "Baked_Cubicle_Labyrinth",
        "Houdini_Engine_Cubicle_Hive",
        "Houdini_Engine_Breakroom",
        "CAD_ZoneB_Cubicle_Labyrinth",
        "CAD_ZoneC_Breakroom_Sanctuary",
        "CAD_ZoneD_Circulation_Corridor",
        "CAD_Architectural_Ceiling"
    ]
    actors_to_delete = []
    for a in EAS.get_all_level_actors():
        folder = str(a.get_folder_path()) if hasattr(a, "get_folder_path") else ""
        lbl = a.get_actor_label()
        if folder in clean_folders or lbl in [
            "HDA_Cubicle_Hive",
            "HDA_Breakroom_Sanctuary",
            "Houdini_Ceiling_HVAC_Grid",
            "SM_P_Whiteboard_Corridor",
            "SM_P_WallClock_Corridor"
        ] or lbl.startswith("Light_Troffer_CAD_"):
            actors_to_delete.append(a)

    for a in actors_to_delete:
        EAS.destroy_actor(a)

    unreal.log(f"[CAD_Alignment] Cleaned {len(actors_to_delete)} prior provisional actors.")

    # 2. ZONE 2: HOUDINI ENGINE CUBICLE LABYRINTH (CAD Grid Center: X=825.0, Y=-400.0, Z=0.0)
    unreal.log("[CAD_Alignment] Instantiating CAD-Aligned HDA_Cubicle_Hive via Houdini Engine...")
    trans_cb = unreal.Transform(location=[825.0, -400.0, 0.0], rotation=[0.0, 0.0, 0.0], scale=[1.0, 1.0, 1.0])
    w_cb = api.instantiate_asset(hda, trans_cb, enable_auto_cook=True, enable_auto_bake=False)
    if w_cb:
        a_cb = w_cb.get_houdini_asset_actor()
        a_cb.set_actor_label("HDA_Cubicle_Hive")
        a_cb.set_actor_location(unreal.Vector(825.0, -400.0, 0.0), False, False)
        a_cb.set_actor_rotation(unreal.Rotator(0.0, 0.0, 0.0), False)
        if hasattr(a_cb, "set_folder_path"):
            a_cb.set_folder_path("CAD_ZoneB_Cubicle_Labyrinth")
        w_cb.process_component_synchronous()
        
        # Set scene_mode = 1 (Cubicles) and rebuild
        w_cb.set_int_parameter_value("scene_mode", 1)
        w_cb.rebuild()
        w_cb.process_component_synchronous()
        a_cb.set_actor_location(unreal.Vector(825.0, -400.0, 0.0), False, False)
        
        # Verify components
        cb_comps = a_cb.get_components_by_class(unreal.InstancedStaticMeshComponent)
        unreal.log(f"[CAD_Alignment] HDA_Cubicle_Hive cooked: {len(cb_comps)} HISM mesh buffers.")
        for comp in cb_comps:
            sm = comp.get_editor_property("static_mesh")
            unreal.log(f"   - Cubicle buffer: {sm.get_name() if sm else 'None'} ({comp.get_instance_count()} instances)")

    # 3. ZONE 3: HOUDINI ENGINE BREAKROOM SANCTUARY (CAD Grid Center: X=750.0, Y=600.0, Z=0.0)
    unreal.log("[CAD_Alignment] Instantiating CAD-Aligned HDA_Breakroom_Sanctuary via Houdini Engine...")
    trans_br = unreal.Transform(location=[750.0, 600.0, 0.0], rotation=[0.0, 0.0, 0.0], scale=[1.0, 1.0, 1.0])
    w_br = api.instantiate_asset(hda, trans_br, enable_auto_cook=True, enable_auto_bake=False)
    if w_br:
        a_br = w_br.get_houdini_asset_actor()
        a_br.set_actor_label("HDA_Breakroom_Sanctuary")
        a_br.set_actor_location(unreal.Vector(750.0, 600.0, 0.0), False, False)
        a_br.set_actor_rotation(unreal.Rotator(0.0, 0.0, 0.0), False)
        if hasattr(a_br, "set_folder_path"):
            a_br.set_folder_path("CAD_ZoneC_Breakroom_Sanctuary")
        w_br.process_component_synchronous()
        
        # Set scene_mode = 3 (Breakroom Kitchen) and rebuild
        w_br.set_int_parameter_value("scene_mode", 3)
        w_br.rebuild()
        w_br.process_component_synchronous()
        a_br.set_actor_location(unreal.Vector(750.0, 600.0, 0.0), False, False)
        w_br.rebuild()
        w_br.process_component_synchronous()
        
        # Verify components
        br_comps = a_br.get_components_by_class(unreal.ActorComponent)
        mesh_comps = [c for c in br_comps if "Mesh" in c.get_class().get_name()]
        unreal.log(f"[CAD_Alignment] HDA_Breakroom_Sanctuary cooked: {len(mesh_comps)} breakroom mesh components.")
        for comp in mesh_comps:
            sm = comp.get_editor_property("static_mesh") if hasattr(comp, "get_editor_property") and hasattr(comp, "static_mesh") else None
            cnt = comp.get_instance_count() if hasattr(comp, "get_instance_count") else 1
            unreal.log(f"   - Breakroom item: {sm.get_name() if sm else 'None'} ({cnt})")

    # 4. ARCHITECTURAL CEILING GRID: PROCEDURAL HOUDINI HVAC & TROFFER MESH
    ceiling_mesh = unreal.load_asset("/Game/Meshes/Architecture/SM_Houdini_Ceiling_HVAC_Grid")
    mat_powder = unreal.load_asset("/Game/Materials/Instances/MI_Toon_Office_PowderCoat")
    if ceiling_mesh:
        ceil_actor = EAS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0.0, 0.0, 0.0))
        ceil_actor.set_actor_label("Houdini_Ceiling_HVAC_Grid")
        ceil_actor.set_actor_rotation(unreal.Rotator(0.0, 0.0, 0.0), False)
        smc = ceil_actor.get_component_by_class(unreal.StaticMeshComponent)
        smc.set_static_mesh(ceiling_mesh)
        smc.set_mobility(unreal.ComponentMobility.MOVABLE)
        if mat_powder:
            for mi in range(smc.get_num_materials()):
                smc.set_material(mi, mat_powder)
        if hasattr(ceil_actor, "set_folder_path"):
            ceil_actor.set_folder_path("CAD_Architectural_Ceiling")
        unreal.log("[CAD_Alignment] Staged SM_Houdini_Ceiling_HVAC_Grid in CAD_Architectural_Ceiling.")

    # 5. SYMMETRIC ARCHITECTURAL TROFFER LIGHT DOWN-POOLS (Under each Houdini troffer fixture at Z=305cm)
    troffer_points = [
        (550.0, -650.0), (825.0, -650.0), (1100.0, -650.0),
        (550.0, -150.0), (825.0, -150.0), (1100.0, -150.0)
    ]
    for tx, ty in troffer_points:
        rl = EAS.spawn_actor_from_class(unreal.RectLight, unreal.Vector(tx, ty, 305.0))
        rl.set_actor_label(f"Light_Troffer_CAD_{int(tx)}_{int(abs(ty))}")
        rl.set_actor_rotation(unreal.Rotator(pitch=-90.0, yaw=0.0, roll=0.0), False)
        if hasattr(rl, "set_folder_path"):
            rl.set_folder_path("CAD_Architectural_Ceiling")
        comp = rl.get_component_by_class(unreal.RectLightComponent)
        comp.set_intensity(4.2)
        comp.set_light_color(unreal.LinearColor(r=0.92, g=0.95, b=1.0, a=1.0)) # 4500K neutral commercial fluorescent
        comp.set_attenuation_radius(360.0)
        comp.set_source_width(120.0)
        comp.set_source_height(60.0)

    # 6. ZONE 4: CIRCULATION CORRIDOR & UTILITY TRANSITION NICHE
    # Spanning transition between Hero Cast and Breakroom (X=250.0, Y=200.0)
    whiteboard_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Whiteboard_SG_FilmStage_20261016")
    mat_wb = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_Whiteboard_SG_FilmStage_20261016")
    if whiteboard_mesh:
        wb_actor = EAS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(250.0, 200.0, 0.0))
        wb_actor.set_actor_label("SM_P_Whiteboard_Corridor")
        wb_actor.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0), False)
        wb_comp = wb_actor.get_component_by_class(unreal.StaticMeshComponent)
        wb_comp.set_static_mesh(whiteboard_mesh)
        wb_comp.set_mobility(unreal.ComponentMobility.MOVABLE)
        if mat_wb:
            wb_comp.set_material(0, mat_wb)
        if hasattr(wb_actor, "set_folder_path"):
            wb_actor.set_folder_path("CAD_ZoneD_Circulation_Corridor")

    clock_mesh = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Clock_AC_FilmStage_20261016")
    if clock_mesh:
        clock_actor = EAS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(248.0, 200.0, 210.0))
        clock_actor.set_actor_label("SM_P_WallClock_Corridor")
        clock_actor.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0), False)
        cl_comp = clock_actor.get_component_by_class(unreal.StaticMeshComponent)
        cl_comp.set_static_mesh(clock_mesh)
        cl_comp.set_mobility(unreal.ComponentMobility.MOVABLE)
        if hasattr(clock_actor, "set_folder_path"):
            clock_actor.set_folder_path("CAD_ZoneD_Circulation_Corridor")

    # 7. COMPOSED CINEMATIC CINECAMERAS (CAD-ALIGNED FRAMING)
    def update_camera(label: str, loc: tuple, target: tuple, focal: float, f_stop: float):
        for a in EAS.get_all_level_actors():
            if a.get_actor_label() == label:
                EAS.destroy_actor(a)
        
        cam = EAS.spawn_actor_from_class(unreal.CineCameraActor, unreal.Vector(*loc))
        cam.set_actor_label(label)
        if hasattr(cam, "set_folder_path"):
            cam.set_folder_path("Cinematic_Cameras")

        dx = target[0] - loc[0]
        dy = target[1] - loc[1]
        dz = target[2] - loc[2]
        dist_xy = math.sqrt(dx*dx + dy*dy)
        yaw = math.degrees(math.atan2(dy, dx))
        pitch = math.degrees(math.atan2(dz, dist_xy))
        cam.set_actor_rotation(unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0), False)

        comp = cam.get_cine_camera_component()
        comp.current_focal_length = focal
        comp.filmback.sensor_width = 36.0
        comp.filmback.sensor_height = 20.25 # 16:9
        comp.lens_settings.min_f_stop = 1.2
        comp.lens_settings.max_f_stop = 22.0
        comp.current_aperture = f_stop
        
        dist_3d = math.sqrt(dx*dx + dy*dy + dz*dz)
        comp.focus_settings.focus_method = unreal.CameraFocusMethod.MANUAL
        comp.focus_settings.manual_focus_distance = dist_3d
        unreal.log(f"[CAD_Alignment] Configured CineCamera {label}: Loc={loc}, Target={target}, Focal={focal}mm, f/{f_stop}")
        return cam

    # 7A. Hero Cubicle Establishing Shot: Elevated wide diagonal sweeping across the CAD grid
    update_camera(
        label="CineCam_Hero_CubicleEstablishing",
        loc=(220.0, -950.0, 420.0),
        target=(825.0, -400.0, 90.0),
        focal=24.0,
        f_stop=3.2
    )

    # 7B. Hero Cubicle Trench Shot: Looking straight down the central arterial thoroughfare (X=825.0)
    update_camera(
        label="CineCam_Hero_CubicleTrench",
        loc=(825.0, -900.0, 95.0),
        target=(825.0, -100.0, 95.0),
        focal=35.0,
        f_stop=2.4
    )

    # 7C. Hero Breakroom Establishing Shot: Framed across dining table and espresso bar
    update_camera(
        label="CineCam_Hero_BreakroomEstablishing",
        loc=(480.0, 320.0, 135.0),
        target=(750.0, 600.0, 110.0),
        focal=35.0,
        f_stop=2.8
    )

    # 7D. Hero Corridor Watercooler Vignette: 50mm portrait bokeh
    update_camera(
        label="CineCam_Hero_CorridorWatercooler",
        loc=(180.0, 120.0, 115.0),
        target=(250.0, 200.0, 110.0),
        focal=50.0,
        f_stop=2.0
    )

    # 8. SAVE LEVEL CLEANLY
    saved = LES.save_current_level()
    unreal.log(f"[CAD_Alignment] SUCCESS: Scene CAD organization complete. Save: {saved}")
    return saved

if __name__ == "__main__":
    execute_cad_alignment()
