import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("=== ALL LIGHT ACTORS IN LEVEL ===")
for a in eas.get_all_level_actors():
    c = a.get_component_by_class(unreal.LightComponentBase)
    if c:
        intensity = c.get_editor_property("intensity")
        light_color = c.get_editor_property("light_color")
        is_hidden = a.is_hidden_ed() if hasattr(a, "is_hidden_ed") else False
        print(f"Actor: {a.get_actor_label()} | Class: {c.get_class().get_name()} | Intensity: {intensity} | HiddenEd: {is_hidden} | Color: ({light_color.r:.2f}, {light_color.g:.2f}, {light_color.b:.2f})")

print("\n=== POST PROCESS VOLUMES ===")
for a in eas.get_all_level_actors():
    if isinstance(a, unreal.PostProcessVolume):
        unbound = a.get_editor_property("unbound")
        enabled = a.get_editor_property("enabled")
        priority = a.get_editor_property("priority")
        bias = a.settings.get_editor_property("auto_exposure_bias")
        print(f"PPV: {a.get_actor_label()} | Unbound: {unbound} | Enabled: {enabled} | Priority: {priority} | Bias: {bias}")
