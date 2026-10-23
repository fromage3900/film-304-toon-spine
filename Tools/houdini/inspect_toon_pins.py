import unreal

mat = unreal.load_asset("/Game/Materials/Masters/M_Master_Toon_Glass")
for n in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
    if "SubstrateToon" in type(n).__name__:
        print(f"Inputs of {type(n).__name__}:")
        for i in range(25):
            try:
                name = n.get_input_name(i)
                if name:
                    print(f"  pin {i}: {name}")
            except Exception as e:
                pass
