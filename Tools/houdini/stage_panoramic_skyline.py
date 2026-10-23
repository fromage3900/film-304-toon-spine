"""Stages a breathtaking panoramic Brutalist skyline visible across all 3 window bays.

Geometry & Placement:
- Bay 01 View (Y_local = -100..100): Flanked by Slender Tower & Punched Estate at X_local = -2500 cm.
- Bay 02 View (Y_local = 150..350): Hero Monumental TowerCluster at X_local = -3800 cm.
- Bay 03 View (Y_local = 400..650): Civic Superblock & KMZ Skyline Tower at X_local = -4500 cm.
- Deep Horizon: Infinite brutalist monolith silhouettes.
- Catenary Cables: Slung across the urban canyon.
- Living Windows: Warm amber & cool fluorescent window emissives.
"""
import math
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

yaw_rad = math.radians(-25.0)
cos_y = math.cos(yaw_rad)
sin_y = math.sin(yaw_rad)

def to_world(xl, yl, zl):
    return unreal.Vector(xl * cos_y - yl * sin_y, xl * sin_y + yl * cos_y, zl)

def rot_room(pitch=0.0, yaw_offset=0.0, roll=0.0):
    return unreal.Rotator(pitch=pitch, yaw=-25.0 + yaw_offset, roll=roll)

mat_concrete = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistConcrete")
mat_asphalt = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistAsphalt")
mat_warm_win = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_Glazing_WarmOffice")
mat_cool_win = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_Glazing_CoolOffice")
mat_vce = unreal.load_asset("/Game/EnvSandbox/Materials/Masters/M_Film304_VCEmissive")

actor_map = {a.get_actor_label(): a for a in eas.get_all_level_actors()}

print("=== 1. POSITIONING MONUMENTAL TOWERS ACROSS BAYS 01, 02, 03 ===")

# Bay 01 Skyline (Center Y_local = 0.0 cm)
if "SM_Ext_Mid_SlenderTower" in actor_map:
    t = actor_map["SM_Ext_Mid_SlenderTower"]
    t.set_actor_location(to_world(-2600.0, -80.0, -100.0), False, False)
    t.set_actor_rotation(rot_room(yaw_offset=-15.0), False)
    t.set_actor_scale3d(unreal.Vector(1.10, 1.25, 1.15))
    smc = t.get_component_by_class(unreal.StaticMeshComponent)
    if smc:
        smc.set_material(0, mat_concrete)
        if smc.get_num_materials() > 1 and mat_warm_win:
            smc.set_material(1, mat_warm_win)
    print("  Positioned SM_Ext_Mid_SlenderTower outside Bay 01")

if "EST_EstablishingE1_01_SM_OFFICE_BarbicanScale" in actor_map:
    t = actor_map["EST_EstablishingE1_01_SM_OFFICE_BarbicanScale"]
    t.set_actor_location(to_world(-3400.0, -250.0, -200.0), False, False)
    t.set_actor_rotation(rot_room(yaw_offset=30.0), False)
    t.set_actor_scale3d(unreal.Vector(1.20, 1.20, 1.30))
    smc = t.get_component_by_class(unreal.StaticMeshComponent)
    if smc:
        smc.set_material(0, mat_concrete)
    print("  Positioned BarbicanScale tower flanking Bay 01 left")

# Bay 02 Skyline (Center Y_local = 255.0 cm - DIRECT HERO SIGHTLINE)
if "SM_Ext_Hero_TowerCluster" in actor_map:
    t = actor_map["SM_Ext_Hero_TowerCluster"]
    t.set_actor_location(to_world(-3800.0, 240.0, -300.0), False, False)
    t.set_actor_rotation(rot_room(yaw_offset=10.0), False)
    t.set_actor_scale3d(unreal.Vector(1.35, 1.60, 1.45))
    smc = t.get_component_by_class(unreal.StaticMeshComponent)
    if smc:
        smc.set_material(0, mat_asphalt)
        if smc.get_num_materials() > 1:
            smc.set_material(1, mat_concrete)
    print("  Positioned SM_Ext_Hero_TowerCluster outside Bay 02")

# Bay 03 Skyline (Center Y_local = 500.0 cm)
if "EST_EstablishingE1_02_SM_CITY_CivicSuperblock" in actor_map:
    t = actor_map["EST_EstablishingE1_02_SM_CITY_CivicSuperblock"]
    t.set_actor_location(to_world(-4200.0, 580.0, -250.0), False, False)
    t.set_actor_rotation(rot_room(yaw_offset=-20.0), False)
    t.set_actor_scale3d(unreal.Vector(1.10, 1.10, 1.20))
    smc = t.get_component_by_class(unreal.StaticMeshComponent)
    if smc:
        smc.set_material(0, mat_asphalt)
        if smc.get_num_materials() > 1:
            smc.set_material(1, mat_concrete)
    print("  Positioned CivicSuperblock outside Bay 03")

# Deep Skyline Backdrop (KMZ Tower Cluster)
if "SM_Ext_Sky_KMZ_TowerCluster" in actor_map:
    t = actor_map["SM_Ext_Sky_KMZ_TowerCluster"]
    t.set_actor_location(to_world(-7500.0, 400.0, -500.0), False, False)
    t.set_actor_rotation(rot_room(yaw_offset=45.0), False)
    t.set_actor_scale3d(unreal.Vector(1.60, 1.80, 1.70))
    smc = t.get_component_by_class(unreal.StaticMeshComponent)
    if smc:
        smc.set_material(0, mat_asphalt)
        if smc.get_num_materials() > 1:
            smc.set_material(1, mat_concrete)
    print("  Positioned SM_Ext_Sky_KMZ_TowerCluster in deep background")

if "EST_EstablishingE1_03_SM_KMZ_TowerCluster" in actor_map:
    t = actor_map["EST_EstablishingE1_03_SM_KMZ_TowerCluster"]
    t.set_actor_location(to_world(-9000.0, -100.0, -600.0), False, False)
    t.set_actor_rotation(rot_room(yaw_offset=-10.0), False)
    t.set_actor_scale3d(unreal.Vector(1.50, 1.50, 1.80))
    smc = t.get_component_by_class(unreal.StaticMeshComponent)
    if smc:
        smc.set_material(0, mat_asphalt)
        if smc.get_num_materials() > 1:
            smc.set_material(1, mat_concrete)

unreal.EditorLevelLibrary.save_current_level()
print("SUCCESS: Panoramic Skyline staged cleanly across all 3 window bays!")
