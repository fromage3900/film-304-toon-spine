import unreal

mat = unreal.load_asset("/Game/Melodia/_PROJECT/04_Materials/PostProcess/Render2026/MI_StorybookOutline_Render2026")
if mat:
    print("Parent:", mat.parent.get_path_name())
    for p in mat.scalar_parameter_values:
        print(f"  Scalar: {p.parameter_info.name} = {p.parameter_value}")
    for p in mat.vector_parameter_values:
        v = p.parameter_value
        print(f"  Vector: {p.parameter_info.name} = ({v.r:.2f}, {v.g:.2f}, {v.b:.2f}, {v.a:.2f})")
