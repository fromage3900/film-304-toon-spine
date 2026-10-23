import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
print("All actors with Sam:")
for a in eas.get_all_level_actors():
    if "sam" in a.get_actor_label().lower():
        print(f"  {a.get_actor_label()} ({a.get_class().get_name()}) Loc={a.get_actor_location()}")
