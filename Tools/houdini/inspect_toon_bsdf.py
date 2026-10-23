import unreal

mat_path = "/Game/Materials/Masters/M_Master_Toon_Universal"
mat = unreal.EditorAssetLibrary.load_asset(mat_path)
exprs = unreal.MaterialEditingLibrary.get_material_expressions(mat)

for e in exprs:
    if e.get_class().get_name() == "MaterialExpressionSubstrateToonBSDF":
        print("Found MaterialExpressionSubstrateToonBSDF:")
        # Let's inspect its properties
        for prop in ["diffuse_color", "roughness", "specular", "emissive_color"]:
            print(f"Has prop {prop}: {hasattr(e, prop)}")
        # Check all expressions that connect to it or search for emissive nodes
        break

# Let's find all parameter expressions in the material
print("\n--- ALL SCALAR AND VECTOR PARAMETERS ---")
for e in exprs:
    c = e.get_class().get_name()
    if "Parameter" in c:
        pname = e.get_editor_property("parameter_name")
        group = e.get_editor_property("group") if hasattr(e, "group") else ""
        print(f"{c}: {pname} (Group: {group})")
