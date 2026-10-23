import unreal

mat = unreal.load_asset("/Game/Materials/Masters/M_Master_Toon_Glass")
for n in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
    if "SubstrateToon" in type(n).__name__:
        pins = unreal.MaterialEditingLibrary.get_material_expression_input_names(n)
        print(f"PINS ON {type(n).__name__}:")
        for p in pins:
            print(f"  - {p}")
