import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Floor":
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        mats = [smc.get_material(i) for i in range(smc.get_num_materials())]
        print("Film_Floor mats:", [m.get_path_name() if m else 'None' for m in mats])
        if mats and mats[0] and isinstance(mats[0], unreal.MaterialInstance):
            m = mats[0]
            print("  BaseTint:", unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(m, "BaseTint"))
            print("  RampLow:", unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(m, "RampLow"))
            print("  RampMid:", unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(m, "RampMid"))
            print("  RampHigh:", unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(m, "RampHigh"))
