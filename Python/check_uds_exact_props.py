import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

uds = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_UDS_Daylight":
        uds = a
        break

if not uds:
    print("Film_UDS_Daylight not found")
else:
    print("Found UDS:", uds.get_name(), uds.get_class().get_name())
    # Iterate over all properties on UDS using unreal.Class or get_editor_property
    props = []
    # In UE python, we can inspect properties via class default object or iterating properties
    c = uds.get_class()
    # List all fields/properties
    try:
        # Check commonly used UDS property names
        for test_prop in [
            "Time of Day", "TimeOfDay", "Time of Day (0-2400)", "Time of Day (0 - 2400)",
            "Solar Time", "SolarTime", "Sun Angle", "SunAngle", "Animate Time of Day",
            "Color of Sun", "Sun Intensity", "Sun Directional Light", "Directional Light",
            "Day Length", "Night Length", "Cloud Coverage", "Fog Density", "Sky Mode",
            "Sky Atmosphere", "Sun Mobility", "Moon Mobility"
        ]:
            try:
                val = uds.get_editor_property(test_prop)
                print(f"  FOUND PROPERTY '{test_prop}': {val}")
            except Exception:
                pass
    except Exception as e:
        print("Error checking props:", e)
