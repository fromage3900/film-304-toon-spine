import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl in ["SM_Glass_WindowBay_01", "SM_Glass_WindowBay_02", "SM_Glass_WindowBay_03"]:
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        bounds = a.get_actor_bounds(False)
        mats = [smc.get_material(i) for i in range(smc.get_num_materials())]
        print(f"{lbl}: Origin={bounds[0]} Extent={bounds[1]}")
        for i, m in enumerate(mats):
            if m:
                print(f"  slot {i}: {m.get_name()} parent={m.parent.get_name() if hasattr(m, 'parent') and m.parent else 'None'}")
                # check scalar/vector params
                if isinstance(m, unreal.MaterialInstance):
                    s_params = unreal.MaterialEditingLibrary.get_scalar_parameter_names(m) if hasattr(unreal, 'MaterialEditingLibrary') else []
                    print(f"  params: {s_params}")
