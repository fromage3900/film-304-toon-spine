import unreal

mat = unreal.load_asset("/Game/Materials/Masters/M_Master_Toon_Glass")
for n in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
    if "SubstrateToon" in type(n).__name__:
        print(f"Attrs of {type(n).__name__}:")
        for attr in dir(n):
            if not attr.startswith("_"):
                try:
                    val = getattr(n, attr)
                    if "input" in attr.lower():
                        print(f"  {attr}: {val}")
                except:
                    pass
