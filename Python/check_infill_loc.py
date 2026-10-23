import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Wall_NorthWest_Corner_Infill":
        print("Infill loc:", a.get_actor_location(), "scale:", a.get_actor_scale3d(), "bounds:", a.get_actor_bounds(False))
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        print("Infill mats:", [smc.get_material(i).get_name() if smc.get_material(i) else 'None' for i in range(smc.get_num_materials())])
