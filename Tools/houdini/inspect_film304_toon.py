import unreal

m = unreal.load_asset("/Game/Materials/Instances/Film304/MI_Film304_Toon")
if m:
    print("MI_Film304_Toon parent:", m.parent.get_path_name())
    for sp in m.scalar_parameter_values:
        print(f"  Scalar: {sp.parameter_info.name} = {sp.parameter_value}")
    for vp in m.vector_parameter_values:
        v = vp.parameter_value
        print(f"  Vector: {vp.parameter_info.name} = ({v.r}, {v.g}, {v.b})")
