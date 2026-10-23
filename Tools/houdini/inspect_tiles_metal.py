import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl in ["HOUDINI_SM_Houdini_Office_Ceiling_Tiles", "HOUDINI_SM_Houdini_Office_Ceiling_Metal"]:
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        m = smc.static_mesh
        print(f"Actor: {lbl}")
        print(f"  Mesh: {m.get_path_name()}")
        print(f"  Materials: {[smc.get_material(i).get_name() if smc.get_material(i) else 'None' for i in range(smc.get_num_materials())]}")
        print(f"  Transform: loc={a.get_actor_location()}, rot={a.get_actor_rotation()}, scale={a.get_actor_scale3d()}")
