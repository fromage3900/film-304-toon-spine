import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in eas.get_all_level_actors():
    if a.get_actor_label() == "PPV_P4_CleanCinematic":
        s = a.settings
        try:
            print("reflections_type:", s.get_editor_property("reflections_type"))
        except Exception as e:
            print("reflections_type error:", e)
        try:
            print("translucency_type:", s.get_editor_property("translucency_type"))
        except Exception as e:
            print("translucency_type error:", e)
