import unreal

def push_to_horizon():
    actors = {a.get_actor_label(): a for a in unreal.EditorLevelLibrary.get_all_level_actors()}

    # Move manually staged buildings out into true monumental horizon distances
    # Looking from the office window (-200, 200) along sightline yaw ~ 160 deg (towards -X, +Y)
    updates = {
        'SM_Ext_Hero_TowerCluster': {
            'loc': unreal.Vector(-18000.0, 9500.0, -1200.0),
            'scale': unreal.Vector(1.4, 1.8, 1.4),
            'rot': unreal.Rotator(0.0, -15.0, 0.0)
        },
        'SM_Ext_Mid_CivicSuperblock': {
            'loc': unreal.Vector(-9500.0, 4200.0, -600.0),
            'scale': unreal.Vector(1.0, 1.0, 1.0),
            'rot': unreal.Rotator(0.0, 25.0, 0.0)
        },
        'SM_Ext_Mid_SlenderTower': {
            'loc': unreal.Vector(-7800.0, 6800.0, -400.0),
            'scale': unreal.Vector(1.0, 1.2, 1.0),
            'rot': unreal.Rotator(0.0, -25.0, 0.0)
        },
        'SM_Ext_Sky_KMZ_TowerCluster': {
            'loc': unreal.Vector(-28000.0, 15000.0, -1800.0),
            'scale': unreal.Vector(1.8, 2.2, 1.8),
            'rot': unreal.Rotator(0.0, 10.0, 0.0)
        },
        'SM_Ext_FG_BarbicanScale': {
            'loc': unreal.Vector(-4200.0, 800.0, -200.0),
            'scale': unreal.Vector(1.0, 1.0, 1.0),
            'rot': unreal.Rotator(0.0, 65.0, 0.0)
        }
    }

    for name, xf in updates.items():
        if name in actors:
            act = actors[name]
            act.set_actor_location(xf['loc'], False, False)
            act.set_actor_rotation(xf['rot'], False)
            act.set_actor_scale3d(xf['scale'])
            print(f"Pushed {name} to horizon: {xf['loc']}")

    if 'HDA_Brutalist_ShotComposer_OfficeLevel' in actors:
        hda = actors['HDA_Brutalist_ShotComposer_OfficeLevel']
        hda.set_actor_location(unreal.Vector(-12000.0, 7000.0, -800.0), False, False)
        print("Pushed HDA actor to horizon at (-12000, 7000, -800)")

push_to_horizon()
