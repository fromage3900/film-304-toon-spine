import unreal

screen_mat = unreal.load_asset("/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Screen")
if screen_mat:
    print("Screen Mat Parent:", screen_mat.parent.get_path_name())
    for sp in screen_mat.scalar_parameter_values:
        print(f"  Scalar: {sp.parameter_info.name} = {sp.parameter_value}")
    for vp in screen_mat.vector_parameter_values:
        v = vp.parameter_value
        print(f"  Vector: {vp.parameter_info.name} = ({v.r}, {v.g}, {v.b})")
