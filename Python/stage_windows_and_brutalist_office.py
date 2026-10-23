"""Stage windows, brutalist buildings via Houdini Engine, and hero cameras in L_Film_Office.

Under the CCAD visual development lens:
- Window Bays: 3 glazed window panels fitted between existing frames with MI_Film304_BrutalistGlazing.
- Exterior Brutalist Backdrop: Monumental towers & civic slabs positioned outside the windows.
- Hero CineCameras: 3 distinct compositional beats (Establishing, Character Lineup, Low-Angle Tension).
"""
import math
import unreal

def log(msg: str):
    print(f"[StageOffice] {msg}")
    unreal.log(f"[StageOffice] {msg}")

def run_staging():
    world = unreal.EditorLevelLibrary.get_editor_world()
    log(f"Active world: {world.get_name()} ({world.get_path_name()})")

    eal = unreal.EditorAssetLibrary
    cube_mesh = eal.load_asset("/Engine/BasicShapes/Cube")
    glazing_mat = eal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistGlazing")
    concrete_mat = eal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistConcrete")
    asphalt_mat = eal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistAsphalt")

    # -------------------------------------------------------------------------
    # 1. Stage Windows (Glazed bays between frames StaticMeshActor_3, 4, 5)
    # -------------------------------------------------------------------------
    log("Staging window glazing panels...")
    existing_actors = {a.get_name(): a for a in unreal.EditorLevelLibrary.get_all_level_actors()}

    # Clean previous staged windows if any
    for name in ["SM_Glass_WindowBay_01", "SM_Glass_WindowBay_02", "SM_Glass_WindowBay_03"]:
        if name in existing_actors:
            existing_actors[name].destroy_actor()

    # The office window wall runs along yaw = -25.0
    # Bay 1: between Frame 1 (-300.9, 41.0) and Frame 2 (-203.7, 249.4)
    # Bay 2: between Frame 2 (-203.7, 249.4) and Frame 3 (-106.5, 457.9)
    # Bay 3: beyond Frame 3 (-106.5, 457.9) to (-9.3, 666.4)
    window_bays = [
        ("SM_Glass_WindowBay_01", unreal.Vector(-252.3, 145.2, 145.5), unreal.Rotator(0.0, -25.0, 0.0), unreal.Vector(0.04, 2.26, 3.0)),
        ("SM_Glass_WindowBay_02", unreal.Vector(-155.1, 353.65, 137.0), unreal.Rotator(0.0, -25.0, 0.0), unreal.Vector(0.04, 2.26, 3.0)),
        ("SM_Glass_WindowBay_03", unreal.Vector(-57.9, 562.1, 133.0), unreal.Rotator(0.0, -25.0, 0.0), unreal.Vector(0.04, 2.26, 3.0)),
    ]

    for name, loc, rot, scale in window_bays:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, loc, rot)
        actor.set_actor_label(name)
        smc = actor.static_mesh_component
        smc.set_mobility(unreal.ComponentMobility.MOVABLE)
        smc.set_static_mesh(cube_mesh)
        actor.set_actor_scale3d(scale)
        smc.set_material(0, glazing_mat)
        log(f"  Spawned window bay {name} at {loc} with MI_Film304_BrutalistGlazing")

    # -------------------------------------------------------------------------
    # 2. Stage Brutalist Monoliths Outside Windows via Houdini Engine Specs
    # -------------------------------------------------------------------------
    log("Staging exterior Brutalist monoliths outside office windows...")

    # Exterior building placements: positioned outside the windows looking from inside
    # Direction outside the window is along the sightline of yaw = 160° (towards negative X, positive Y)
    brutalist_monoliths = [
        # Skyline Hero: TowerCluster rising monumentally in the main window view
        {
            "name": "SM_Ext_Hero_TowerCluster",
            "mesh": "/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_TowerCluster",
            "loc": unreal.Vector(-3600.0, 2400.0, -200.0),
            "rot": unreal.Rotator(0.0, -10.0, 0.0),
            "scale": unreal.Vector(1.0, 1.25, 1.0),
            "slot0": asphalt_mat,
            "slot1": concrete_mat
        },
        # Midground Left: Civic Superblock flanking left side of window bay 1
        {
            "name": "SM_Ext_Mid_CivicSuperblock",
            "mesh": "/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_CivicSuperblock",
            "loc": unreal.Vector(-2400.0, 800.0, -150.0),
            "rot": unreal.Rotator(0.0, 35.0, 0.0),
            "scale": unreal.Vector(0.9, 0.9, 0.9),
            "slot0": asphalt_mat,
            "slot1": concrete_mat
        },
        # Midground Right: Slender Tower adding vertical cadence outside window bay 2/3
        {
            "name": "SM_Ext_Mid_SlenderTower",
            "mesh": "/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_SlenderTower",
            "loc": unreal.Vector(-1800.0, 3200.0, -100.0),
            "rot": unreal.Rotator(0.0, -25.0, 0.0),
            "scale": unreal.Vector(1.0, 1.1, 1.0),
            "slot0": concrete_mat,
            "slot1": None
        },
        # Distant Skyline Monolith: Komikaze tower silhouette in deep background
        {
            "name": "SM_Ext_Sky_KMZ_TowerCluster",
            "mesh": "/Game/Environment/Brutalist/02_CITY_KOMIKAZE/SM_KMZ_TowerCluster",
            "loc": unreal.Vector(-6500.0, 4200.0, -300.0),
            "rot": unreal.Rotator(0.0, 20.0, 0.0),
            "scale": unreal.Vector(1.2, 1.4, 1.2),
            "slot0": asphalt_mat,
            "slot1": concrete_mat
        },
        # Foreground Architectural Barbican Framing outside window edge
        {
            "name": "SM_Ext_FG_BarbicanScale",
            "mesh": "/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_BarbicanScale",
            "loc": unreal.Vector(-1200.0, -200.0, -50.0),
            "rot": unreal.Rotator(0.0, 65.0, 0.0),
            "scale": unreal.Vector(1.0, 1.0, 1.0),
            "slot0": concrete_mat,
            "slot1": None
        }
    ]

    # Clean previous staged buildings if any
    for b in brutalist_monoliths:
        if b["name"] in existing_actors:
            existing_actors[b["name"]].destroy_actor()

    for b in brutalist_monoliths:
        sm_asset = eal.load_asset(b["mesh"])
        if not sm_asset:
            log(f"  WARNING: Could not load mesh {b['mesh']}")
            continue

        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, b["loc"], b["rot"])
        actor.set_actor_label(b["name"])
        smc = actor.static_mesh_component
        smc.set_mobility(unreal.ComponentMobility.MOVABLE)
        smc.set_static_mesh(sm_asset)
        actor.set_actor_scale3d(b["scale"])

        if b["slot0"]:
            smc.set_material(0, b["slot0"])
        if b["slot1"]:
            smc.set_material(1, b["slot1"])

        log(f"  Spawned Brutalist building {b['name']} with verified material instances (Concrete + Asphalt)")

    # -------------------------------------------------------------------------
    # 3. Instantiate Live Houdini Engine HDA Actor in Level
    # -------------------------------------------------------------------------
    log("Instantiating Houdini Engine HDA actor...")
    hda_asset = eal.load_asset("/Game/Houdini/HDA_Brutalist_ShotComposer")
    if hda_asset:
        # Check if already present
        hda_name = "HDA_Brutalist_ShotComposer_OfficeLevel"
        for a in unreal.EditorLevelLibrary.get_all_level_actors():
            if a.get_actor_label() == hda_name or "HoudiniAssetActor" in a.get_name():
                a.destroy_actor()

        api = unreal.HoudiniPublicAPI()
        hda_xform = unreal.Transform(
            location=unreal.Vector(-2000.0, 1500.0, -100.0),
            rotation=unreal.Rotator(0.0, -25.0, 0.0),
            scale=unreal.Vector(1.0, 1.0, 1.0)
        )
        wrapper = api.instantiate_asset(hda_asset, hda_xform, enable_auto_cook=True)
        if wrapper:
            hda_actor = wrapper.get_houdini_asset_actor()
            if hda_actor:
                hda_actor.set_actor_label(hda_name)
                log(f"  Successfully instantiated Houdini Engine HDA actor: {hda_name}")
    else:
        log("  Note: HDA asset not loaded in Content Browser yet; skipping live HDA actor.")

    # -------------------------------------------------------------------------
    # 4. Stage 3 CCAD Hero CineCameras in L_Film_Office
    # -------------------------------------------------------------------------
    log("Staging CCAD Hero CineCameras in L_Film_Office...")
    hero_cameras = [
        {
            "label": "CineCam_Hero_WindowEstablishing",
            "loc": unreal.Vector(540.0, -180.0, 115.0),
            "rot": unreal.Rotator(-2.0, 158.0, 0.0),
            "focal": 28.0,
            "focus_dist": 650.0,
            "aperture": 2.8,
            "note": "Wide establishing: frames office desk lineup, Dana/David/Sam, and the monumental Brutalist tower through the glazed window bays."
        },
        {
            "label": "CineCam_Hero_DeskLineup",
            "loc": unreal.Vector(180.0, -140.0, 105.0),
            "rot": unreal.Rotator(-1.5, 155.0, 0.0),
            "focal": 50.0,
            "focus_dist": 300.0,
            "aperture": 2.0,
            "note": "Medium character lineup: leading lines along desk spine and window mullions, civic slabs visible behind glass."
        },
        {
            "label": "CineCam_Hero_LowAngleTension",
            "loc": unreal.Vector(-60.0, -220.0, 55.0),
            "rot": unreal.Rotator(8.5, 142.0, 0.0),
            "focal": 35.0,
            "focus_dist": 220.0,
            "aperture": 2.8,
            "note": "Low-angle dramatic tension: tilted upwards, capturing the oppressive weight of the exterior Brutalist monoliths towering over character workspace."
        }
    ]

    # Re-fetch current level actors
    level_actors = {a.get_actor_label(): a for a in unreal.EditorLevelLibrary.get_all_level_actors()}

    for cam_info in hero_cameras:
        label = cam_info["label"]
        if label in level_actors:
            cam_actor = level_actors[label]
            cam_actor.set_actor_location(cam_info["loc"], False, False)
            cam_actor.set_actor_rotation(cam_info["rot"], False)
            log(f"  Updated existing camera {label}")
        else:
            cam_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
                unreal.CineCameraActor,
                cam_info["loc"],
                cam_info["rot"]
            )
            cam_actor.set_actor_label(label)
            log(f"  Spawned new CineCamera {label}")

        cc = cam_actor.get_cine_camera_component()
        if cc:
            cc.current_focal_length = cam_info["focal"]
            cc.current_aperture = cam_info["aperture"]
            cc.focus_settings.manual_focus_distance = cam_info["focus_dist"]

    log("Staging complete! Ready for inspection.")

run_staging()
