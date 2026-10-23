import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in eas.get_all_level_actors():
    if a.get_actor_label() == "PPV_P4_CleanCinematic":
        ppc = a.get_component_by_class(unreal.PostProcessComponent)
        s = ppc.settings
        print("PPV_P4_CleanCinematic reflection settings:")
        for p in dir(s):
            if any(k in p.lower() for k in ["reflect", "translucen", "lumen", "ray"]):
                try:
                    val = getattr(s, p)
                    if not callable(val):
                        print(f"  {p}: {val}")
                except:
                    pass
        break
