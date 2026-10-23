import unreal

mat = unreal.load_asset("/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal")
if mat:
    print("M_Master_Toon_Universal parameters:")
    for sp in mat.get_editor_property("scalar_parameter_values") if hasattr(mat, "scalar_parameter_values") else []:
        pass
    # Get parameters via MaterialEditingLibrary
    scalars = unreal.MaterialEditingLibrary.get_scalar_parameter_names(mat)
    print("Scalars:", scalars)
    vectors = unreal.MaterialEditingLibrary.get_vector_parameter_names(mat)
    print("Vectors:", vectors)
