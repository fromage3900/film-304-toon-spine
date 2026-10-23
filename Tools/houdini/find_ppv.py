import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in eas.get_all_level_actors():
    if "PostProcess" in a.get_class().get_name() or "PostProcess" in a.get_actor_label():
        print(f"Found PP: {a.get_actor_label()} ({a.get_class().get_name()})")
