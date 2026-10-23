import unreal

mat = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_GroundedFloor_Toon")
for p in unreal.MaterialEditingLibrary.get_scalar_parameter_names(mat):
    print(f"  {p}: {unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(mat, p)}")
