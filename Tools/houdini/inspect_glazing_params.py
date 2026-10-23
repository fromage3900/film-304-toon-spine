import unreal

mat = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistGlazing")
if mat:
    print("Glazing Material:", mat.get_name())
    parent = mat.get_editor_property("parent")
    print("  Parent:", parent.get_name() if parent else "None")
    
    # Print scalar parameters
    for sp in mat.get_editor_property("scalar_parameter_values"):
        pname = sp.get_editor_property("parameter_info").name
        val = sp.get_editor_property("parameter_value")
        print(f"  Scalar {pname}: {val}")
        
    for vp in mat.get_editor_property("vector_parameter_values"):
        pname = vp.get_editor_property("parameter_info").name
        val = vp.get_editor_property("parameter_value")
        print(f"  Vector {pname}: R={val.r:.2f}, G={val.g:.2f}, B={val.b:.2f}, A={val.a:.2f}")
