import unreal

ar = unreal.AssetRegistryHelpers.get_asset_registry()
assets = ar.get_assets_by_path("/Game", recursive=True)

print("=== GLASS MATERIALS IN PROJECT ===")
for a in assets:
    p = str(a.package_name)
    if "glass" in p.lower() or "glazing" in p.lower():
        cname = str(a.asset_class_path.asset_name if hasattr(a, 'asset_class_path') else a.asset_class)
        if "Material" in cname:
            print(f"  [{cname}] {p}")
