import unreal

for path in [
    "/Game/Materials/Masters/Film304/M_Film304_VCEmissive",
    "/Game/Materials/Instances/Film304/Scene/Dusk20261018/MI_Dusk_HorizonWindows"
]:
    m = unreal.load_asset(path)
    if m:
        print(f"\n{m.get_name()} ({m.get_class().get_name()}):")
        if isinstance(m, unreal.MaterialInstance):
            print(f"  Parent: {m.parent.get_name()}")
            for p in unreal.MaterialEditingLibrary.get_scalar_parameter_names(m):
                print(f"    Scalar: {p} = {unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(m, p)}")
            for p in unreal.MaterialEditingLibrary.get_vector_parameter_names(m):
                print(f"    Vector: {p} = {unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(m, p)}")
