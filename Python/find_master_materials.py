import unreal

ar = unreal.AssetRegistryHelpers.get_asset_registry()
assets = ar.get_assets_by_path("/Game", recursive=True)

print("=== MASTER MATERIALS IN PROJECT ===")
for a in assets:
    pname = str(a.package_name)
    cname = str(a.asset_class_path.asset_name if hasattr(a, 'asset_class_path') else a.asset_class)
    if cname == "Material" and ("master" in pname.lower() or "toon" in pname.lower()):
        print(f"  [{cname}] {pname}")
