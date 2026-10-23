import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for name in ["PPV_P4_CleanCinematic", "PPV_StorybookOutline"]:
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == name:
            ppc = a.get_component_by_class(unreal.PostProcessComponent) or a
            s = ppc.settings
            print(f"--- {name} ---")
            print(f"  enabled: {a.get_actor_enable_collision()}")
            print(f"  unbound: {getattr(a, 'unbound', None)}")
            # Check exposure
            print(f"  auto_exposure_method: {getattr(s, 'auto_exposure_method', None)}")
            print(f"  auto_exposure_min_brightness: {getattr(s, 'auto_exposure_min_brightness', None)}")
            print(f"  auto_exposure_max_brightness: {getattr(s, 'auto_exposure_max_brightness', None)}")
            print(f"  auto_exposure_bias: {getattr(s, 'auto_exposure_bias', None)}")
            print(f"  bloom_intensity: {getattr(s, 'bloom_intensity', None)}")
