import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in eas.get_all_level_actors():
    if "HVAC" in a.get_actor_label() or "Ceiling" in a.get_actor_label():
        loc = a.get_actor_location()
        print(f"{a.get_actor_label():30} | loc={loc}")
