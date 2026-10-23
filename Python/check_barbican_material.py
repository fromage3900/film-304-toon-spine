import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "EST_EstablishingE1_01_SM_OFFICE_BarbicanScale":
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        hidden_ed = a.is_hidden_ed()
        hidden_game = smc.get_editor_property("hidden_in_game")
        mats = [smc.get_material(i) for i in range(smc.get_num_materials())]
        print(f"Barbican: hidden_ed={hidden_ed} hidden_game={hidden_game}")
        for i, m in enumerate(mats):
            print(f"  slot {i}: {m.get_name() if m else 'None'} ({m.get_path_name() if m else 'None'})")
            if m and isinstance(m, unreal.MaterialInstance):
                base_color = unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(m, "BaseColor")
                print(f"    BaseColor: {base_color}")
