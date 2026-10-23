import unreal
from pathlib import Path

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
eal = unreal.EditorAssetLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

PROPS_FOLDER = "/Game/Materials/Instances/Film304/Props/Clutter"
Path("G:/film-304-toon-spine/Content/Materials/Instances/Film304/Props/Clutter").mkdir(parents=True, exist_ok=True)

# Parent master/base instance
parent_mat = unreal.load_asset("/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Ceramic")
if not parent_mat:
    parent_mat = unreal.load_asset("/Game/Materials/Instances/Film304/Scene/MI_Film304_Toon")

factory = unreal.MaterialInstanceConstantFactoryNew()

def get_or_create_mi(name, base_tint, roughness=0.5, metallic=0.0):
    asset_path = f"{PROPS_FOLDER}/{name}"
    mi = unreal.load_asset(asset_path)
    if not mi:
        mi = at.create_asset(name, PROPS_FOLDER, unreal.MaterialInstanceConstant, factory)
        mi.set_editor_property("parent", parent_mat)
        print(f"Created material instance: {name}")
    
    # Set parameters
    mel.set_material_instance_vector_parameter_value(mi, "BaseTint", base_tint)
    mel.set_material_instance_scalar_parameter_value(mi, "Roughness", roughness)
    mel.set_material_instance_scalar_parameter_value(mi, "Metallic", metallic)
    mel.update_material_instance(mi)
    eal.save_loaded_asset(mi, only_if_is_dirty=False)
    return mi

# In-theme dusk palette colors:
# 1. Coffee Mug (Warm terracotta ceramic)
mi_mug = get_or_create_mi("MI_Film304_Clutter_CoffeeMug", unreal.LinearColor(0.706, 0.333, 0.235, 1.0), roughness=0.35)

# 2. Paper Sheet (Warm parchment off-white)
mi_paper = get_or_create_mi("MI_Film304_Clutter_Paper", unreal.LinearColor(0.929, 0.902, 0.839, 1.0), roughness=0.90)

# 3. Sticky Notes (Pastel canary amber)
mi_sticky = get_or_create_mi("MI_Film304_Clutter_StickyNotes", unreal.LinearColor(0.957, 0.816, 0.435, 1.0), roughness=0.85)

# 4. Pen (Deep slate teal body)
mi_pen = get_or_create_mi("MI_Film304_Clutter_Pen", unreal.LinearColor(0.180, 0.435, 0.420, 1.0), roughness=0.40)

# 5. Waste Bin (Dark industrial matte metal)
mi_bin = get_or_create_mi("MI_Film304_Clutter_Bin", unreal.LinearColor(0.239, 0.255, 0.275, 1.0), roughness=0.55, metallic=0.35)

# 6. Plant Leaves (Muted sage green)
mi_leaf = get_or_create_mi("MI_Film304_Clutter_PlantLeaf", unreal.LinearColor(0.310, 0.420, 0.290, 1.0), roughness=0.60)

# =========================================================================
# SPAWN PROPS INTO LEVEL
# =========================================================================
# Meshes
mesh_mug = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_CoffeMug_ZMJ_FilmStage_20261016")
mesh_paper = unreal.load_asset("/Game/Meshes/Office/Props/SM_Paper_PMB")
mesh_sticky = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_StickyNote_PMB_FilmStage_20261016")
mesh_pen = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Pen_KMP_FilmStage_20261016")
mesh_bin = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Bin01_SY_FilmStage_20261016")
mesh_plant = unreal.load_asset("/Game/Staging/OneDriveRigs_20261016/Environment/SM_S_Plant_PMB_FilmStage_20261016")

def spawn_clutter(label, mesh, mat, loc, rot, scale=unreal.Vector(1,1,1)):
    # Check if exists
    actor = None
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == label:
            actor = a
            break
    if not actor:
        actor = eas.spawn_actor_from_class(unreal.StaticMeshActor, loc, rot)
        actor.set_actor_label(label)
        actor.set_folder_path("Film304/Clutter_Curated")
    else:
        actor.set_actor_location(loc, False, False)
        actor.set_actor_rotation(rot, False)
    
    actor.set_actor_scale3d(scale)
    smc = actor.static_mesh_component
    if smc and mesh:
        smc.set_static_mesh(mesh)
        for i in range(smc.get_num_materials()):
            smc.set_material(i, mat)
    print(f"Placed {label} at {loc}")
    return actor

# 1. David's Desk: Coffee Mug (Sitting cleanly beside keyboard)
spawn_clutter("Clutter_David_CoffeeMug", mesh_mug, mi_mug, unreal.Vector(-138.0, -135.0, 56.5), unreal.Rotator(0.0, 35.0, 0.0))

# 2. David's Desk: Loose Paper Draft
spawn_clutter("Clutter_David_PaperNote", mesh_paper, mi_paper, unreal.Vector(-165.0, -95.0, 56.2), unreal.Rotator(0.0, 18.0, 0.0))

# 3. Dana's Desk: Pastel Sticky Notes
spawn_clutter("Clutter_Dana_StickyNotes", mesh_sticky, mi_sticky, unreal.Vector(45.0, 42.0, 57.0), unreal.Rotator(0.0, -12.0, 0.0))

# 4. Dana's Desk: Pen
spawn_clutter("Clutter_Dana_Pen", mesh_pen, mi_pen, unreal.Vector(48.0, 44.0, 57.6), unreal.Rotator(0.0, 40.0, 0.0))

# 5. Floor Grounding: Waste Bin under David's desk return
spawn_clutter("Clutter_David_WasteBin", mesh_bin, mi_bin, unreal.Vector(-165.0, -155.0, 0.0), unreal.Rotator(0.0, 15.0, 0.0))

# 6. Floor Corner Grounding: Potted Plant
p_actor = spawn_clutter("Clutter_Office_CornerPlant", mesh_plant, mi_leaf, unreal.Vector(145.0, 120.0, 0.0), unreal.Rotator(0.0, 45.0, 0.0), unreal.Vector(1.1, 1.1, 1.1))
# If plant has 2 materials (leaf & pot):
if p_actor and p_actor.static_mesh_component and p_actor.static_mesh_component.get_num_materials() > 1:
    p_actor.static_mesh_component.set_material(0, mi_mug)  # pot
    p_actor.static_mesh_component.set_material(1, mi_leaf) # foliage

unreal.EditorLoadingAndSavingUtils.save_current_level()
print("All curated props and material instances created and saved cleanly!")
