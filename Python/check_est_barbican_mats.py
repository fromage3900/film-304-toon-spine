import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "EST_EstablishingE1_01_SM_OFFICE_BarbicanScale":
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        mats = [smc.get_material(i) for i in range(smc.get_num_materials())]
        print("EST Barbican mats:")
        for i, m in enumerate(mats):
            print(f"  slot {i}: {m.get_path_name() if m else 'None'}")
            if m and isinstance(m, unreal.MaterialInstance):
                for p in ["BaseColor", "BaseTint", "RampLow", "RampMid", "RampHigh"]:
                    v = unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(m, p) if hasattr(unreal.MaterialEditingLibrary, "get_material_instance_vector_parameter_value") else None
                    if v and (v.r > 0 or v.g > 0 or v.b > 0):
                        print(f"    {p}: {v}")
                    s = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(m, p) if hasattr(unreal.MaterialEditingLibrary, "get_material_instance_scalar_parameter_value") else None
                    if s is not None and s > 0:
                        print(f"    {p}: {s}")
