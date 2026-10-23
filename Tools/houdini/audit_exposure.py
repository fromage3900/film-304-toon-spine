import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("--- LIGHT AUDIT ---")
for a in eas.get_all_level_actors():
    c = a.get_component_by_class(unreal.LightComponentBase)
    if c:
        lbl = a.get_actor_label()
        inten = getattr(c, "intensity", None)
        color = getattr(c, "light_color", None)
        atten = getattr(c, "attenuation_radius", None)
        print(f"{lbl:35} | class={c.get_class().get_name():25} | inten={inten} | atten={atten}")

print("\n--- PPV EXPOSURE AUDIT ---")
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "PostProcessVolume_1":
        ppc = a.get_component_by_class(unreal.PostProcessComponent) or a
        s = ppc.settings
        print("PPV Settings:")
        print("  auto_exposure_method:", getattr(s, "auto_exposure_method", None))
        print("  auto_exposure_min_brightness:", getattr(s, "auto_exposure_min_brightness", None))
        print("  auto_exposure_max_brightness:", getattr(s, "auto_exposure_max_brightness", None))
        print("  auto_exposure_bias:", getattr(s, "auto_exposure_bias", None))
