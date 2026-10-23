import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in eas.get_all_level_actors():
    if isinstance(a, unreal.PostProcessVolume):
        lbl = a.get_actor_label()
        ppc = a.get_component_by_class(unreal.PostProcessComponent)
        if ppc:
            s = ppc.settings
            method = s.get_editor_property("auto_exposure_method")
            bias = s.get_editor_property("auto_exposure_bias")
            min_b = s.get_editor_property("auto_exposure_min_brightness")
            max_b = s.get_editor_property("auto_exposure_max_brightness")
            print(f"PPV: {lbl:30} | enabled={a.get_editor_property('b_enabled')} | unbounded={a.get_editor_property('b_unbound')} | method={method} | bias={bias} | min={min_b} | max={max_b}")
