import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Cast_RimKicker_Light":
        c = a.get_component_by_class(unreal.DirectionalLightComponent)
        print("Cast_RimKicker_Light:")
        print("  Intensity:", c.get_editor_property("intensity"))
        print("  LightColor:", c.get_editor_property("light_color"))
        print("  IndirectLightingIntensity:", c.get_editor_property("indirect_lighting_intensity"))
        print("  VolumetricScatteringIntensity:", c.get_editor_property("volumetric_scattering_intensity"))
        print("  SpecularScale:", c.get_editor_property("specular_scale") if hasattr(c, "specular_scale") else "N/A")
