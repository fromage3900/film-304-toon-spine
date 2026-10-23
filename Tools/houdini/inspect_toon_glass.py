import unreal

mat = unreal.load_asset("/Game/Materials/Instances/MI_Toon_Glass")
if mat:
    print(f"MI_Toon_Glass parent: {mat.parent.get_name() if mat.parent else 'None'}")
    for sp in mat.scalar_parameter_values:
        print(f"  Scalar: {sp.parameter_info.name} = {sp.parameter_value}")
    for vp in mat.vector_parameter_values:
        print(f"  Vector: {vp.parameter_info.name} = {vp.parameter_value}")
else:
    print("MI_Toon_Glass not found!")
