import unreal

for name in ["SM_Houdini_Office_Ceiling_Tiles", "SM_Houdini_Office_Ceiling_Metal", "SM_Houdini_Ceiling_HVAC_Grid"]:
    m = unreal.load_asset(f"/Game/Meshes/{name}")
    if not m:
        m = unreal.load_asset(f"/Game/HoudiniEngine/{name}")
    if not m:
        # Search asset registry
        ar = unreal.AssetRegistryHelpers.get_asset_registry()
        ad = ar.get_asset_by_object_path(f"/Game/{name}.{name}")
        if ad.is_valid():
            m = ad.get_asset()
    if m:
        b = m.get_bounds()
        print(f"Mesh: {m.get_path_name()} | BoxOrigin: {b.origin} | BoxExtent: {b.box_extent}")
    else:
        print(f"Mesh {name} not found by direct path, searching...")
        ar = unreal.AssetRegistryHelpers.get_asset_registry()
        matches = ar.get_assets_by_class("StaticMesh")
        for match in matches:
            if name.lower() in match.asset_name.lower():
                mesh_obj = match.get_asset()
                b = mesh_obj.get_bounds()
                print(f"Found: {mesh_obj.get_path_name()} | BoxOrigin: {b.origin} | BoxExtent: {b.box_extent}")
