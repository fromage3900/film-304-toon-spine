import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if "houdini" in lbl.lower() and "ceiling" in lbl.lower():
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        if smc and smc.static_mesh:
            print(f"Actor: {lbl}")
            print(f"  Mesh: {smc.static_mesh.get_path_name()}")
            print(f"  Actor Pos: {a.get_actor_location()}")
            print(f"  Actor Rot: {a.get_actor_rotation()}")
            print(f"  Actor Scale: {a.get_actor_scale3d()}")
