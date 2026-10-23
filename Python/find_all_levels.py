import unreal

ar = unreal.AssetRegistryHelpers.get_asset_registry()
maps = ar.get_assets_by_path("/Game", recursive=True)

print("=== ALL MAPS (LEVELS) IN PROJECT ===")
for a in maps:
    cname = str(a.asset_class_path.asset_name if hasattr(a, "asset_class_path") else a.asset_class)
    if cname in ["World", "Level"]:
        print(f"Map: {a.package_name} ({cname})")
