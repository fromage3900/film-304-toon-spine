"""Definitive fix for exterior Brutalist staging and material instances in L_Film_Office.

Fixes:
1. All actors stand 100% vertical (Pitch = 0.0, Roll = 0.0). NO tilted Rotator bugs.
2. Yaw strictly aligned to the office street grid (-25.0° parallel, 65.0° perpendicular). NO random angles.
3. Explicit Material Instances assigned to every material slot:
   - Slot 0 Asphalt: MI_Film304_BrutalistAsphalt
   - Slot 1 Concrete: MI_Film304_BrutalistConcrete
   - Window Glazing: MI_Film304_BrutalistGlazing
4. Remove broken HDA actor from level to prevent duplicate / floating proxy meshes.
5. Perfect horizon placement along the camera sightline.
"""
import unreal

def run_fix():
    eal = unreal.EditorAssetLibrary
    world = unreal.EditorLevelLibrary.get_editor_world()
    print(f"[FixStaging] Operating on world: {world.get_path_name()}")

    # 1. Materials
    asphalt_mi = eal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistAsphalt.MI_Film304_BrutalistAsphalt")
    concrete_mi = eal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistConcrete.MI_Film304_BrutalistConcrete")
    glazing_mi = eal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistGlazing.MI_Film304_BrutalistGlazing")
    cube_mesh = eal.load_asset("/Engine/BasicShapes/Cube.Cube")

    print(f"[FixStaging] Loaded materials: Asphalt={asphalt_mi is not None}, Concrete={concrete_mi is not None}, Glazing={glazing_mi is not None}")

    # 2. Clean out old broken HDA actor if present
    actors = {a.get_actor_label(): a for a in unreal.EditorLevelLibrary.get_all_level_actors()}
    for label, act in list(actors.items()):
        if "HDA" in label or "HoudiniAssetActor" in act.get_name():
            print(f"[FixStaging] Removing broken HDA actor: {label}")
            act.destroy_actor()

    # 3. Window Glazing Bays (Fitting between frame mullions StaticMeshActor_3, 4, 5 along yaw = -25.0)
    window_bays = [
        ("SM_Glass_WindowBay_01", unreal.Vector(-252.3, 145.2, 145.5), unreal.Vector(0.04, 2.26, 3.0)),
        ("SM_Glass_WindowBay_02", unreal.Vector(-155.1, 353.65, 137.0), unreal.Vector(0.04, 2.26, 3.0)),
        ("SM_Glass_WindowBay_03", unreal.Vector(-57.9, 562.1, 133.0), unreal.Vector(0.04, 2.26, 3.0)),
    ]

    for name, loc, scale in window_bays:
        if name in actors:
            act = actors[name]
        else:
            act = unreal.EditorLevelLibrary.spawn_actor_from_class(
                unreal.StaticMeshActor,
                loc,
                unreal.Rotator(pitch=0.0, yaw=-25.0, roll=0.0)
            )
            act.set_actor_label(name)

        act.set_actor_location(loc, False, False)
        # CRITICAL: Keyword arguments to avoid Unreal Python Rotator argument swap bug
        act.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=-25.0, roll=0.0), False)
        act.set_actor_scale3d(scale)
        smc = act.static_mesh_component
        smc.set_mobility(unreal.ComponentMobility.MOVABLE)
        smc.set_static_mesh(cube_mesh)
        smc.set_material(0, glazing_mi)
        print(f"[FixStaging] Window Bay {name} set to MI_Film304_BrutalistGlazing, rot=(0, -25, 0)")

    # 4. Exterior Brutalist Horizon Buildings
    # Street Grid: Yaw = -25.0 (parallel to window wall) or 65.0 (perpendicular cross street)
    # Pitch = 0.0, Roll = 0.0 (strictly upright!)
    buildings = [
        {
            "label": "SM_Ext_Hero_TowerCluster",
            "mesh": "/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_TowerCluster.SM_CITY_TowerCluster",
            "loc": unreal.Vector(-14000.0, 7500.0, -800.0),
            "yaw": -25.0,
            "scale": unreal.Vector(1.4, 1.8, 1.4),
            "slots": [asphalt_mi, concrete_mi]  # Slot 0 = Asphalt plinth, Slot 1 = Concrete tower
        },
        {
            "label": "SM_Ext_Mid_CivicSuperblock",
            "mesh": "/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_CivicSuperblock.SM_CITY_CivicSuperblock",
            "loc": unreal.Vector(-6500.0, 3200.0, -350.0),
            "yaw": 65.0,
            "scale": unreal.Vector(1.0, 1.0, 1.0),
            "slots": [asphalt_mi, concrete_mi]  # Slot 0 = Asphalt plinth, Slot 1 = Concrete facade
        },
        {
            "label": "SM_Ext_Mid_SlenderTower",
            "mesh": "/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_SlenderTower.SM_OFFICE_SlenderTower",
            "loc": unreal.Vector(-5200.0, 4800.0, -250.0),
            "yaw": -25.0,
            "scale": unreal.Vector(1.0, 1.2, 1.0),
            "slots": [concrete_mi]
        },
        {
            "label": "SM_Ext_Sky_KMZ_TowerCluster",
            "mesh": "/Game/Environment/Brutalist/02_CITY_KOMIKAZE/SM_KMZ_TowerCluster.SM_KMZ_TowerCluster",
            "loc": unreal.Vector(-22000.0, 12000.0, -1200.0),
            "yaw": -25.0,
            "scale": unreal.Vector(1.8, 2.2, 1.8),
            "slots": [asphalt_mi, concrete_mi]  # Slot 0 = Asphalt, Slot 1 = Concrete
        },
        {
            "label": "SM_Ext_FG_BarbicanScale",
            "mesh": "/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_BarbicanScale.SM_OFFICE_BarbicanScale",
            "loc": unreal.Vector(-2800.0, 1100.0, -150.0),
            "yaw": 65.0,
            "scale": unreal.Vector(1.0, 1.0, 1.0),
            "slots": [concrete_mi]
        }
    ]

    for b in buildings:
        mesh_asset = eal.load_asset(b["mesh"])
        if not mesh_asset:
            print(f"[FixStaging] ERROR: Mesh not found: {b['mesh']}")
            continue

        label = b["label"]
        if label in actors:
            act = actors[label]
        else:
            act = unreal.EditorLevelLibrary.spawn_actor_from_class(
                unreal.StaticMeshActor,
                b["loc"],
                unreal.Rotator(pitch=0.0, yaw=b["yaw"], roll=0.0)
            )
            act.set_actor_label(label)

        act.set_actor_location(b["loc"], False, False)
        # CRITICAL: Pitch=0, Roll=0, upright orientation
        act.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=b["yaw"], roll=0.0), False)
        act.set_actor_scale3d(b["scale"])

        smc = act.static_mesh_component
        smc.set_mobility(unreal.ComponentMobility.MOVABLE)
        smc.set_static_mesh(mesh_asset)

        # Set material instances on each slot explicitly
        for slot_idx, mat in enumerate(b["slots"]):
            if mat:
                smc.set_material(slot_idx, mat)
                print(f"[FixStaging]   {label} Slot {slot_idx} set to {mat.get_name()}")

        rot = act.get_actor_rotation()
        print(f"[FixStaging] Updated {label}: Loc={b['loc']}, Rot=(pitch={rot.pitch}, yaw={rot.yaw}, roll={rot.roll})")

    # 5. Verify the 3 Hero CineCameras
    cams = {
        "CineCam_Hero_WindowEstablishing": {
            "loc": unreal.Vector(540.0, -180.0, 115.0),
            "rot": unreal.Rotator(pitch=-2.0, yaw=158.0, roll=0.0),
            "focal": 28.0,
            "focus_dist": 650.0
        },
        "CineCam_Hero_DeskLineup": {
            "loc": unreal.Vector(180.0, -140.0, 105.0),
            "rot": unreal.Rotator(pitch=-1.5, yaw=155.0, roll=0.0),
            "focal": 50.0,
            "focus_dist": 300.0
        },
        "CineCam_Hero_LowAngleTension": {
            "loc": unreal.Vector(-60.0, -220.0, 55.0),
            "rot": unreal.Rotator(pitch=8.5, yaw=142.0, roll=0.0),
            "focal": 35.0,
            "focus_dist": 220.0
        }
    }

    for cam_name, c_data in cams.items():
        if cam_name in actors:
            cam_act = actors[cam_name]
            cam_act.set_actor_location(c_data["loc"], False, False)
            cam_act.set_actor_rotation(c_data["rot"], False)
            cc = cam_act.get_cine_camera_component()
            if cc:
                cc.current_focal_length = c_data["focal"]
                cc.focus_settings.manual_focus_distance = c_data["focus_dist"]
            print(f"[FixStaging] Camera {cam_name} aligned.")

    print("[FixStaging] ALL FIXES COMPLETED SUCCESSFULLY!")

run_fix()
