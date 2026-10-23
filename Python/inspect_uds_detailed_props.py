import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_UDS_Daylight":
        print("=== UDS BLUEPRINT PROPERTIES ===")
        # Look at properties
        for prop_name in dir(a):
            low = prop_name.lower()
            if any(k in low for k in ["fog", "horizon", "cloud", "dust", "haze", "sky", "atmosphere"]):
                try:
                    val = a.get_editor_property(prop_name)
                    print(f"  {prop_name}: {val}")
                except Exception:
                    pass
        break
