import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if "Wall" in lbl or "Header" in lbl:
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        vis = smc.is_visible() if smc else False
        hidden_in_game = smc.get_editor_property("hidden_in_game") if smc else False
        print(f"{lbl:30} | visible={vis} | hidden_in_game={hidden_in_game}")
