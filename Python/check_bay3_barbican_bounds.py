import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SM_Ext_Bay3_Barbican":
        bounds = a.get_actor_bounds(False)
        print("SM_Ext_Bay3_Barbican:")
        print("  Loc:", a.get_actor_location())
        print("  Rot:", a.get_actor_rotation())
        print("  Scale:", a.get_actor_scale3d())
        print("  Origin:", bounds[0])
        print("  BoxExtent:", bounds[1])
