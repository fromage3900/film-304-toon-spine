import unreal

mat = unreal.load_asset("/Game/Materials/Instances/Film304/Scene/Dusk20261018/MI_Dusk_Glazing")
if mat:
    print(f"Material: {mat.get_name()}")
    print(f"Parent: {mat.get_editor_property('parent').get_name() if mat.get_editor_property('parent') else 'None'}")
    # Inspect scalars
    for sp in mat.get_editor_property("scalar_parameter_values"):
        pname = sp.get_editor_property("parameter_info").name
        val = sp.get_editor_property("parameter_value")
        print(f"  Scalar {pname}: {val}")
    for vp in mat.get_editor_property("vector_parameter_values"):
        pname = vp.get_editor_property("parameter_info").name
        val = vp.get_editor_property("parameter_value")
        print(f"  Vector {pname}: {val}")
else:
    print("MI_Dusk_Glazing not found!")
