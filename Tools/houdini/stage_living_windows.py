"""Creates and assigns warm and cool living-window emissive material instances for the skyline towers."""
import unreal

def stage_living_windows():
    print("Setting up living window illumination...")
    
    parent_master = unreal.load_asset("/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal")
    base_glazing = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistGlazing")
    
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialInstanceConstantFactoryNew()
    
    # 1. Warm Amber Window Material Instance (3000K Living Office)
    warm_path = "/Game/Materials/Instances/Film304/Environment/MI_Film304_Glazing_WarmOffice"
    if unreal.EditorAssetLibrary.does_asset_exist(warm_path):
        mi_warm = unreal.load_asset(warm_path)
    else:
        mi_warm = tools.create_asset("MI_Film304_Glazing_WarmOffice", "/Game/Materials/Instances/Film304/Environment", unreal.MaterialInstanceConstant, factory)
        
    mi_warm.set_editor_property("parent", base_glazing or parent_master)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi_warm, "GlowIntensity", 4.5)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi_warm, "BloomBoost", 2.0)
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi_warm, "GlowColor", unreal.LinearColor(r=1.0, g=0.68, b=0.28, a=1.0))
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi_warm, "BaseTint", unreal.LinearColor(r=0.22, g=0.15, b=0.08, a=1.0))
    unreal.EditorAssetLibrary.save_loaded_asset(mi_warm)
    print("Created/Configured MI_Film304_Glazing_WarmOffice (3000K amber glow)")

    # 2. Cool Fluorescent Window Material Instance (6500K Late Night Working)
    cool_path = "/Game/Materials/Instances/Film304/Environment/MI_Film304_Glazing_CoolOffice"
    if unreal.EditorAssetLibrary.does_asset_exist(cool_path):
        mi_cool = unreal.load_asset(cool_path)
    else:
        mi_cool = tools.create_asset("MI_Film304_Glazing_CoolOffice", "/Game/Materials/Instances/Film304/Environment", unreal.MaterialInstanceConstant, factory)
        
    mi_cool.set_editor_property("parent", base_glazing or parent_master)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi_cool, "GlowIntensity", 3.0)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi_cool, "BloomBoost", 1.5)
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi_cool, "GlowColor", unreal.LinearColor(r=0.72, g=0.88, b=1.0, a=1.0))
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi_cool, "BaseTint", unreal.LinearColor(r=0.06, g=0.12, b=0.18, a=1.0))
    unreal.EditorAssetLibrary.save_loaded_asset(mi_cool)
    print("Created/Configured MI_Film304_Glazing_CoolOffice (6500K fluorescent cyan glow)")

    # 3. Assign living window variations across the skyline actors
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    assigned = 0
    for a in actors:
        lbl = a.get_actor_label()
        smc = a.static_mesh_component if hasattr(a, "static_mesh_component") else None
        if not smc: continue
        
        # Midground Punched Estate -> Warm residential lighting on slot 1
        if lbl == "SM_Baked_Midground_PunchedEstate_01":
            if smc.get_num_materials() > 1:
                smc.set_material(1, mi_warm)
                assigned += 1
                print(f"  Assigned MI_Film304_Glazing_WarmOffice to {lbl}")
                
        # Midground Tower Ribbon 01 -> Cool late-night office glow on slot 1
        elif lbl == "SM_Baked_Midground_TowerRibbon_01":
            if smc.get_num_materials() > 1:
                smc.set_material(1, mi_cool)
                assigned += 1
                print(f"  Assigned MI_Film304_Glazing_CoolOffice to {lbl}")
                
        # Skyline Tower Ribbon 02 (Deep Hero) -> Warm executive floor glow on slot 1
        elif lbl == "SM_Baked_Skyline_TowerRibbon_02":
            if smc.get_num_materials() > 1:
                smc.set_material(1, mi_warm)
                assigned += 1
                print(f"  Assigned MI_Film304_Glazing_WarmOffice to {lbl}")

    print(f"Step 3 COMPLETE: {assigned} towers updated with living window illumination.")

if __name__ == "__main__":
    stage_living_windows()
