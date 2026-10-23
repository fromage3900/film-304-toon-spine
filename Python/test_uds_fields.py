import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_UDS_Daylight":
        print("=== UDS BLUEPRINT FIELDS ===")
        cls = a.get_class()
        # Find all field names
        fields = []
        for prop in unreal.SystemLibrary.get_object_name(cls):
            pass
        # We can check specific known UDS properties
        candidates = [
            "Fog_Density_Multiplier", "Fog_Density", "Apply_Settings_To_Fog",
            "Horizon_Falloff", "Horizon_Fog_Addition", "Horizon_Height",
            "Night_Horizon_Color", "Dusk_Horizon_Color", "Sun_Angle",
            "Sun_Inclination", "Sun_Yaw", "Cloud_Speed", "Cloud_Density",
            "Sky_Light_Intensity", "Sun_Light_Intensity", "Light_Source",
            "Directional_Light", "Sky_Light", "Atmosphere", "Sky_Atmosphere",
            "Post_Process", "Exposure", "Extend_Horizon", "Horizon_Blur",
            "Color_Dusk_Horizon", "Color_Night_Horizon", "Color_Day_Horizon"
        ]
        for c in candidates:
            try:
                v = a.get_editor_property(c)
                print(f"  {c} = {v}")
            except Exception:
                pass
        break
