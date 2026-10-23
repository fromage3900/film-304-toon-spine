import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if any(k in lbl for k in ["Glass", "Window", "Glazing"]):
        loc = a.get_actor_location()
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        mats = []
        if smc:
            for i in range(smc.get_num_materials()):
                m = smc.get_material(i)
                mats.append(m.get_name() if m else "None")
        print(f"{lbl:30} | class={a.get_class().get_name()} | loc=({loc.x:6.1f},{loc.y:6.1f},{loc.z:6.1f}) | mats={mats}")
