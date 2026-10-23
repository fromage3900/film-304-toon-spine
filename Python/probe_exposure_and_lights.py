import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("--- POST PROCESS VOLUMES ---")
for a in eas.get_all_level_actors():
    if isinstance(a, unreal.PostProcessVolume) or "ppv" in a.get_actor_label().lower():
        ppc = a.get_component_by_class(unreal.PostProcessComponent) if hasattr(a, "get_component_by_class") else None
        settings = a.settings
        print(f"PPV: {a.get_actor_label()} Enabled={a.get_editor_property('enabled')} Unbound={a.get_editor_property('unbound')}")
        for p in [
            "auto_exposure_method", "auto_exposure_bias", "auto_exposure_min_brightness",
            "auto_exposure_max_brightness", "auto_exposure_apply_physical_camera_exposure",
            "camera_shutter_speed", "camera_iso", "exposure_compensation"
        ]:
            if hasattr(settings, p):
                print(f"  {p}: {getattr(settings, p)}")

print("\n--- ACTIVE DIRECTIONAL & SKY LIGHTS ---")
for a in eas.get_all_level_actors():
    for c in a.get_components_by_class(unreal.LightComponentBase):
        if c.is_visible() and c.get_editor_property("intensity") > 0:
            print(f"Light: {a.get_actor_label()} ({c.get_class().get_name()}) Intensity={c.get_editor_property('intensity')}")

