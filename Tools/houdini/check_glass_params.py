import unreal

print("=== CHECKING MI_Toon_Glass PARAMETERS ===")
glass_mat = unreal.EditorAssetLibrary.load_asset("/Game/Materials/Instances/MI_Toon_Glass")
if glass_mat:
    print(f"Parent: {glass_mat.parent.get_path_name()}")
    for sp in glass_mat.scalar_parameter_values:
        print(f"  Scalar: {sp.parameter_info.name} = {sp.parameter_value}")
    for vp in glass_mat.vector_parameter_values:
        v = vp.parameter_value
        print(f"  Vector: {vp.parameter_info.name} = ({v.r}, {v.g}, {v.b}, {v.a})")

print("\n=== CHECKING CHARACTERS LOCATIONS ===")
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    lbl = a.get_actor_label()
    if any(k in lbl.lower() for k in ["dana", "sam", "david", "cast", "character"]):
        print(f"Character: {lbl} at {a.get_actor_location()}")
