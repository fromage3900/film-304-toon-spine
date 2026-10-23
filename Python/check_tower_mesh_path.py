import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in eas.get_all_level_actors():
    if "SM_Ext_Bay3" in a.get_actor_label():
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        if smc and smc.static_mesh:
            print(f"{a.get_actor_label()}: mesh={smc.static_mesh.get_path_name()}")
