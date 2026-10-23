import unreal

mat_path = "/Game/Materials/Masters/M_Master_Toon_Universal"
mat = unreal.EditorAssetLibrary.load_asset(mat_path)
print(f"Master Material: {mat.get_name()}")

# Inspect material expressions or parameters
for expr in mat.expressions:
    desc = expr.get_class().get_name()
    if "emissive" in desc.lower() or "fresnel" in desc.lower():
        print(f"Expression: {desc} - {expr.get_editor_property('desc') if hasattr(expr, 'desc') else ''}")
    elif hasattr(expr, 'parameter_name'):
        pname = str(expr.parameter_name)
        if any(k in pname.lower() for k in ["emissive", "glow", "fresnel", "rim"]):
            print(f"Param: {pname} ({desc})")
