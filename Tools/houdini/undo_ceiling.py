import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
print("=== UNDOING CEILING CHANGES IMMEDIATELY ===")

mat_troffer = unreal.load_asset("/Game/Materials/Instances/MI_Toon_Office_Troffer")

for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    
    if lbl == "HOUDINI_SM_Houdini_Office_Ceiling_Tiles":
        a.set_actor_location(unreal.Vector(-8.0, 0.0, 0.0), False, False)
        a.set_actor_rotation(unreal.Rotator(0.0, -44.0, -90.0), False)
        print("  Reverted HOUDINI_SM_Houdini_Office_Ceiling_Tiles to Loc=(-8, 0, 0), Rot=(0, -44, -90)")
        
    elif lbl == "HOUDINI_SM_Houdini_Office_Ceiling_Metal":
        a.set_actor_location(unreal.Vector(0.0, 0.0, 0.0), False, False)
        a.set_actor_rotation(unreal.Rotator(0.0, -45.0, -90.0), False)
        print("  Reverted HOUDINI_SM_Houdini_Office_Ceiling_Metal to Loc=(0, 0, 0), Rot=(0, -45, -90)")
        
    elif lbl == "SM_Houdini_Ceiling_HVAC_Grid":
        a.set_actor_location(unreal.Vector(0.0, -24.0, -29.0), False, False)
        a.set_actor_rotation(unreal.Rotator(0.0, -20.0, 0.0), False)
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        if smc and mat_troffer:
            smc.set_material(2, mat_troffer)
        print("  Reverted SM_Houdini_Ceiling_HVAC_Grid to Loc=(0, -24, -29), Rot=(0, -20, 0), Slot 2 restored!")
        
    elif lbl == "Film_Troffer_2_Panel":
        a.set_actor_rotation(unreal.Rotator(0.0, -15.0, 0.0), False)
        print("  Reverted Film_Troffer_2_Panel to Rot=(0, -15, 0)")

unreal.EditorLevelLibrary.save_current_level()
print("SUCCESS: Ceiling completely reverted to its previous state!")
