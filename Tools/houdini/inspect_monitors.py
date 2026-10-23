import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "HeroDressing_Dana_Monitor":
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        m = smc.static_mesh
        print("Monitor Mesh:", m.get_path_name())
        for i in range(smc.get_num_materials()):
            mat = smc.get_material(i)
            print(f"Slot {i}: {mat.get_path_name()} ({mat.get_class().get_name()})")
            if hasattr(mat, "parent") and mat.parent:
                print(f"  Parent: {mat.parent.get_path_name()}")
            if hasattr(mat, "scalar_parameter_values"):
                for sp in mat.scalar_parameter_values:
                    print(f"  Scalar: {sp.parameter_info.name} = {sp.parameter_value}")
                for vp in mat.vector_parameter_values:
                    v = vp.parameter_value
                    print(f"  Vector: {vp.parameter_info.name} = ({v.r}, {v.g}, {v.b})")
        break
