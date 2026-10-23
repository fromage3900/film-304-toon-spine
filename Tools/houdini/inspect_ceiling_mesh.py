import unreal

mesh = unreal.load_asset("/Game/Meshes/Architecture/SM_Houdini_Ceiling_HVAC_Grid")
if mesh:
    bounds = mesh.get_bounds()
    print("Ceiling Mesh Bounds:")
    print("  Origin:", bounds.origin)
    print("  Box Extent:", bounds.box_extent)
