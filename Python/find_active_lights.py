import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    for c in a.get_components_by_class(unreal.LightComponentBase):
        if c.is_visible():
            intensity = c.get_editor_property("intensity")
            if intensity > 0:
                print(f"Active Light: {a.get_actor_label()} ({c.get_class().get_name()}) Intensity={intensity} Units={c.get_editor_property('intensity_units') if hasattr(c, 'intensity_units') else 'N/A'} CastShadows={c.get_editor_property('cast_shadows')}")
