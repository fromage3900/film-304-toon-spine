import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in eas.get_all_level_actors():
    smc = a.get_component_by_class(unreal.StaticMeshComponent)
    if smc:
        scale = a.get_actor_scale3d()
        if scale.x > 3.0 or scale.y > 3.0 or scale.z > 3.0:
            loc = a.get_actor_location()
            mats = [smc.get_material(i).get_name() if smc.get_material(i) else "None" for i in range(smc.get_num_materials())]
            print(f"{a.get_actor_label():30} | scale=({scale.x:6.2f},{scale.y:6.2f},{scale.z:6.2f}) | loc=({loc.x:6.1f},{loc.y:6.1f},{loc.z:6.1f}) | mesh={smc.static_mesh.get_name() if smc.static_mesh else 'None'} | mats={mats}")
