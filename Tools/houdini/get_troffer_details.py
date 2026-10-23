import unreal

for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label() == "Film_Troffer_1_Panel":
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        mat = smc.get_material(0)
        print("Film_Troffer_1_Panel material path:", mat.get_path_name())
        print("Class:", mat.get_class().get_name())
        if hasattr(mat, 'parent') and mat.parent:
            print("Parent:", mat.parent.get_path_name())
        for sp in mat.scalar_parameter_values:
            print("  Scalar:", sp.parameter_info.name, "=", sp.parameter_value)
        for vp in mat.vector_parameter_values:
            v = vp.parameter_value
            print("  Vector:", vp.parameter_info.name, f"= ({v.r}, {v.g}, {v.b}, {v.a})")
        break
