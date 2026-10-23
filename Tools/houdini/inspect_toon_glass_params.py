import unreal

mat = unreal.load_asset("/Game/Materials/Instances/MI_Toon_Glass")
if mat:
    print("Glass Material:", mat.get_name())
    parent = mat.get_editor_property("parent")
    print("  Parent:", parent.get_name() if parent else "None")
    
    for sp in mat.get_editor_property("scalar_parameter_values"):
        pname = sp.get_editor_property("parameter_info").name
        val = sp.get_editor_property("parameter_value")
        print(f"  Scalar {pname}: {val}")
        
    for vp in mat.get_editor_property("vector_parameter_values"):
        pname = vp.get_editor_property("parameter_info").name
        val = vp.get_editor_property("parameter_value")
        print(f"  Vector {pname}: {val}")
