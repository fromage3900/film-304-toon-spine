import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("=== CHECKING ALL DIRECTIONAL & SUN LIGHTS ===")
for a in eas.get_all_level_actors():
    dl = a.get_component_by_class(unreal.DirectionalLightComponent)
    if dl:
        print(f"DirectionalLight: {a.get_actor_label():30} | intensity={dl.intensity} | color={dl.light_color} | rot={a.get_actor_rotation()}")
    sl = a.get_component_by_class(unreal.SkyLightComponent)
    if sl:
        print(f"SkyLight: {a.get_actor_label():30} | intensity={sl.intensity} | color={sl.light_color}")
