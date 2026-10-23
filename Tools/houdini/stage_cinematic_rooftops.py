"""Stages cinematic Brutalist rooftop crowns, plant decks, and radio spires on skyline towers in L_Film_Office."""
import unreal

def stage_rooftops():
    world = unreal.EditorLevelLibrary.get_editor_world()
    print(f"Staging rooftops in: {world.get_path_name()}")
    
    # 1. Clean previous staged roofs if any
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if a.get_folder_path() == "Baked_Skyline_Rooftops":
            unreal.EditorLevelLibrary.destroy_actor(a)
            
    # Materials
    mat_concrete = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistConcrete")
    mat_asphalt = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistAsphalt")
    cylinder_mesh = unreal.load_asset("/Engine/BasicShapes/Cylinder")
    cone_mesh = unreal.load_asset("/Engine/BasicShapes/Cone")
    
    # Roof meshes
    mesh_plant = unreal.load_asset("/Game/Environment/Brutalist/06_ROOFS/SM_ROOF_PlantDeck")
    mesh_sawtooth = unreal.load_asset("/Game/Environment/Brutalist/06_ROOFS/SM_ROOF_Sawtooth")
    mesh_barrel = unreal.load_asset("/Game/Environment/Brutalist/06_ROOFS/SM_ROOF_BarrelVault")
    mesh_pyramid = unreal.load_asset("/Game/Environment/Brutalist/06_ROOFS/SM_ROOF_PyramidHip")
    
    roof_configs = [
        # 1. Punched Estate roof: Sawtooth industrial roof bays
        {
            "label": "SM_Roof_PunchedEstate_Sawtooth_01",
            "mesh": mesh_sawtooth,
            "loc": unreal.Vector(-3200.0, 1600.0, 3100.0),
            "rot": unreal.Rotator(pitch=0.0, yaw=-25.0, roll=0.0),
            "scale": unreal.Vector(2.0, 2.0, 2.0),
            "mats": [mat_concrete]
        },
        # 2. Midground Tower Ribbon roof: Industrial Plant Deck with HVAC machinery
        {
            "label": "SM_Roof_MidgroundRibbon_PlantDeck_01",
            "mesh": mesh_plant,
            "loc": unreal.Vector(-4800.0, 3100.0, 8150.0),
            "rot": unreal.Rotator(pitch=0.0, yaw=65.0, roll=0.0),
            "scale": unreal.Vector(2.2, 2.2, 2.2),
            "mats": [mat_concrete]
        },
        # 3. Skyline Tower Ribbon 02 (Deep Hero): Massive Plant Deck + Slender Radio Transmission Spire
        {
            "label": "SM_Roof_DeepSkyline_PlantDeck_01",
            "mesh": mesh_plant,
            "loc": unreal.Vector(-8500.0, 4800.0, 9675.0),
            "rot": unreal.Rotator(pitch=0.0, yaw=-25.0, roll=0.0),
            "scale": unreal.Vector(2.6, 2.6, 2.6),
            "mats": [mat_concrete]
        },
        # Radio transmission antenna spire (reaching 25 meters higher)
        {
            "label": "SM_Roof_Spire_HeroAntenna_01",
            "mesh": cylinder_mesh,
            "loc": unreal.Vector(-8500.0, 4800.0, 10800.0),
            "rot": unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0),
            "scale": unreal.Vector(0.4, 0.4, 24.0),
            "mats": [mat_asphalt]
        },
        # 4. Civic Colonnade: Classic Romanesque/Brutalist Barrel Vault Crown
        {
            "label": "SM_Roof_CivicColonnade_Barrel_01",
            "mesh": mesh_barrel,
            "loc": unreal.Vector(-5500.0, 600.0, 2020.0),
            "rot": unreal.Rotator(pitch=0.0, yaw=-25.0, roll=0.0),
            "scale": unreal.Vector(2.4, 2.4, 2.4),
            "mats": [mat_concrete]
        },
        # 5. Distant Tower Cluster: Monumental Pyramid Hip Parapet
        {
            "label": "SM_Roof_DistantCluster_Pyramid_01",
            "mesh": mesh_pyramid,
            "loc": unreal.Vector(-11500.0, 7200.0, 7950.0),
            "rot": unreal.Rotator(pitch=0.0, yaw=65.0, roll=0.0),
            "scale": unreal.Vector(2.8, 2.8, 2.8),
            "mats": [mat_concrete]
        }
    ]
    
    spawned_actors = []
    for cfg in roof_configs:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_object(cfg["mesh"], cfg["loc"], cfg["rot"])
        if actor:
            actor.set_actor_label(cfg["label"])
            actor.set_actor_scale3d(cfg["scale"])
            actor.set_folder_path("Baked_Skyline_Rooftops")
            smc = actor.static_mesh_component
            if smc and cfg.get("mats"):
                for idx, m in enumerate(cfg["mats"]):
                    if m and idx < smc.get_num_materials():
                        smc.set_material(idx, m)
            spawned_actors.append(actor)
            print(f"Spawned {cfg['label']} at {cfg['loc']}")

    # 6. Red Aviation Warning Beacon on top of Hero Antenna Spire
    beacon = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PointLight,
        unreal.Vector(-8500.0, 4800.0, 12000.0),
        unreal.Rotator(0.0, 0.0, 0.0)
    )
    beacon.set_actor_label("Light_AviationBeacon_HeroSpire")
    beacon.set_folder_path("Baked_Skyline_Rooftops")
    plc = beacon.point_light_component
    plc.set_intensity(2500000.0) # visible across 80m horizon in fog
    plc.set_attenuation_radius(4000.0)
    plc.set_light_color(unreal.LinearColor(r=1.0, g=0.05, b=0.05, a=1.0)) # intense aviation ruby red
    plc.set_editor_property("cast_shadows", False)
    spawned_actors.append(beacon)
    print("Spawned Light_AviationBeacon_HeroSpire ruby beacon at Z=12000!")

    print(f"Step 2 COMPLETE: {len(spawned_actors)} rooftop assets active in Baked_Skyline_Rooftops.")

if __name__ == "__main__":
    stage_rooftops()
