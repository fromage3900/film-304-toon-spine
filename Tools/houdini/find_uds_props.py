import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_UDS_Daylight":
        print("Film_UDS_Daylight properties:")
        for attr in dir(a):
            if any(k in attr.lower() for k in ["sun", "time", "bright", "intens", "sky"]):
                try:
                    val = getattr(a, attr)
                    print(f"  {attr} = {val}")
                except:
                    pass
        break
