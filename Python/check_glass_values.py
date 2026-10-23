import unreal

mat = unreal.load_asset("/Game/Materials/Instances/UniversalFilm_20261016/MI_Toon_Glass")
if not mat:
    mat = unreal.load_asset("/Game/Materials/Instances/MI_Toon_Glass")
print("Loaded mat:", mat.get_path_name() if mat else "None")
if mat:
    for p in ["OpacityBase", "FresnelPower", "RampStrength", "GlassSpecular", "PatternStrength", "RampLow", "RampMid", "RampHigh"]:
        val = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(mat, p)
        print(f"  {p}: {val}")
