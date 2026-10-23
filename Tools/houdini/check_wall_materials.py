import unreal

mat_warm = unreal.load_asset("/Game/Materials/Instances/UniversalFilm_20261016/MI_Film_WarmWall")
mat_wall = unreal.load_asset("/Game/Materials/Instances/UniversalFilm_20261016/MI_Film_Wall")

print("Checking MI_Film_WarmWall:")
if mat_warm:
    print(f"Parent: {mat_warm.parent.get_name() if mat_warm.parent else 'None'}")
    # Print vector and scalar parameters
    for p in mat_warm.vector_parameter_values:
        print(f"  Vec param: {p.parameter_info.name} = {p.parameter_value}")
    for p in mat_warm.scalar_parameter_values:
        print(f"  Scalar param: {p.parameter_info.name} = {p.parameter_value}")

print("\nChecking MI_Film_Wall:")
if mat_wall:
    print(f"Parent: {mat_wall.parent.get_name() if mat_wall.parent else 'None'}")
    for p in mat_wall.vector_parameter_values:
        print(f"  Vec param: {p.parameter_info.name} = {p.parameter_value}")
    for p in mat_wall.scalar_parameter_values:
        print(f"  Scalar param: {p.parameter_info.name} = {p.parameter_value}")
