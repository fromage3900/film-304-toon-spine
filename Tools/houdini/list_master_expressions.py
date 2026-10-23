import unreal

mat_path = "/Game/Materials/Masters/M_Master_Toon_Universal"
mat = unreal.EditorAssetLibrary.load_asset(mat_path)
print(f"Master Material: {mat.get_name()}, Num expressions: {len(mat.expressions)}")
for i, expr in enumerate(mat.expressions):
    cname = expr.get_class().get_name()
    pname = ""
    if hasattr(expr, 'parameter_name'):
        pname = str(expr.parameter_name)
    print(f"[{i}] {cname} : {pname}")
