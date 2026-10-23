import unreal

# Load an existing instance
inst = unreal.load_asset("/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Ceramic")
if not inst:
    inst = unreal.load_asset("/Game/Materials/Instances/Film304/Scene/MI_Film304_Desk")

if inst:
    print(f"Loaded instance: {inst.get_path_name()} (Parent: {inst.parent.get_name()})")
    for s in inst.scalar_parameter_values:
        print(f"  Scalar: {s.parameter_info.name} = {s.parameter_value}")
    for v in inst.vector_parameter_values:
        val = v.parameter_value
        print(f"  Vector: {v.parameter_info.name} = ({val.r:.2f}, {val.g:.2f}, {val.b:.2f}, {val.a:.2f})")
