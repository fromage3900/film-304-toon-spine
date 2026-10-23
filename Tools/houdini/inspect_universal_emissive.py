import unreal

mat_path = "/Game/Materials/Masters/M_Master_Toon_Universal"
mat = unreal.EditorAssetLibrary.load_asset(mat_path)
exprs = unreal.MaterialEditingLibrary.get_material_expressions(mat)
print(f"Master Material: {mat.get_name()}, expr count: {len(exprs)}")

for e in exprs:
    c = e.get_class().get_name()
    pname = e.get_editor_property("parameter_name") if hasattr(e, "parameter_name") else ""
    desc = e.get_editor_property("desc") if hasattr(e, "desc") else ""
    if any(k in str(pname).lower() or k in str(desc).lower() or k in c.lower() for k in ["emissive", "fresnel", "glow", "troffer", "bsdf"]):
        print(f"Expr: {c} | Param: {pname} | Desc: {desc}")
