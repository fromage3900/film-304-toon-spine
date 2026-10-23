import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Light_Cinematic_SunBeam":
        print("SunBeam rot:", a.get_actor_rotation(), "loc:", a.get_actor_location())
        c = a.get_component_by_class(unreal.DirectionalLightComponent)
        print("Intensity:", c.get_editor_property("intensity"), "color:", c.get_editor_property("light_color"))
