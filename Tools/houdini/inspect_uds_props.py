import unreal

uds = None
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label() == "Film_UDS_Daylight":
        uds = a
        break

if uds:
    print(f"Found UDS actor: {uds.get_actor_label()} ({uds.get_class().get_name()})")
    # Check properties
    for p in ["sun_light_intensity", "sun_intensity", "sun_brightness", "sun_color", "skylight_intensity", "cloud_coverage"]:
        if hasattr(uds, p):
            print(f"  Property {p} = {getattr(uds, p)}")
        else:
            try:
                val = uds.get_editor_property(p)
                print(f"  get_editor_property('{p}') = {val}")
            except Exception as e:
                pass
