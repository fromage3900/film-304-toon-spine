import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if any(k in lbl.lower() for k in ["ceiling", "hvac"]):
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        if smc:
            origin, box_extent = a.get_actor_bounds(False)
            print(f"Actor: {lbl:42s} | Origin: ({origin.x:6.1f}, {origin.y:6.1f}, {origin.z:6.1f}) | Extent: ({box_extent.x:6.1f}, {box_extent.y:6.1f}, {box_extent.z:6.1f})")
