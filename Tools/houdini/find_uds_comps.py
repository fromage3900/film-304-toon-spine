import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_UDS_Daylight":
        # Check components or properties
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            print("DirectionalLightComponent in UDS:", c.get_name(), "intensity:", c.intensity, "rot:", c.get_world_rotation())
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            print("SkyLightComponent in UDS:", c.get_name(), "intensity:", c.intensity)
