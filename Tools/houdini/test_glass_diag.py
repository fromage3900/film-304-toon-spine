import unreal

print("=== CHECKING GLASS OPACITY & GLOW TEST ===")
glass_mi = unreal.EditorAssetLibrary.load_asset("/Game/Materials/Instances/MI_Toon_Glass")
if glass_mi:
    # Test what parameters it has
    for sp in glass_mi.scalar_parameter_values:
        print(f"Scalar: {sp.parameter_info.name} = {sp.parameter_value}")
    for vp in glass_mi.vector_parameter_values:
        print(f"Vector: {vp.parameter_info.name} = ({vp.parameter_value.r}, {vp.parameter_value.g}, {vp.parameter_value.b})")
