import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in eas.get_all_level_actors():
    if "UDS" in a.get_actor_label() or "Dynamic" in a.get_class().get_name():
        print("Found UDS actor:", a.get_actor_label(), a.get_class().get_name())
        # Check time of day property
        for p in ["time_of_day", "Time_of_Day", "TimeOfDay"]:
            if hasattr(a, p):
                print(f"  {p} = {getattr(a, p)}")
            try:
                val = a.get_editor_property(p)
                print(f"  editor_property {p} = {val}")
            except:
                pass
