import unreal

for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label() == "SpotLight":
        print("Found SpotLight:")
        print("  Class:", a.get_class().get_name())
        print("  Location:", a.get_actor_location())
        print("  Rotation:", a.get_actor_rotation())
        slc = a.get_component_by_class(unreal.SpotLightComponent)
        if slc:
            print("  Intensity:", slc.get_editor_property("intensity"))
            print("  LightColor:", slc.get_editor_property("light_color"))
            print("  InnerCone:", slc.get_editor_property("inner_cone_angle"))
            print("  OuterCone:", slc.get_editor_property("outer_cone_angle"))
            print("  AttenuationRadius:", slc.get_editor_property("attenuation_radius"))
