import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if "Horizon" in a.get_actor_label():
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        loc = a.get_actor_location()
        scale = a.get_actor_scale3d()
        mats = [smc.get_material(i) for i in range(smc.get_num_materials())] if smc else []
        print(f"{a.get_actor_label()}: Loc={loc} Scale={scale} HiddenEd={a.is_hidden_ed()} HiddenGame={smc.get_editor_property('hidden_in_game') if smc else 'N/A'}")
        for i, m in enumerate(mats):
            print(f"  slot {i}: {m.get_name() if m else 'None'} ({m.get_path_name() if m else 'None'})")
