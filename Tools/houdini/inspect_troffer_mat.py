import unreal

mat = unreal.load_asset("/Game/Materials/Instances/MI_Toon_Office_Troffer")
if mat:
    print(f"Loaded {mat.get_name()}, parent: {mat.parent.get_name() if mat.parent else 'None'}")
    # Inspect scalar and vector parameters
    for sp in mat.scalar_parameter_values:
        print(f"  Scalar: {sp.parameter_info.name} = {sp.parameter_value}")
    for vp in mat.vector_parameter_values:
        print(f"  Vector: {vp.parameter_info.name} = {vp.parameter_value}")
else:
    print("Could not load MI_Toon_Office_Troffer")
