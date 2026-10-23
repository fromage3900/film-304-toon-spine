import unreal

ar = unreal.AssetRegistryHelpers.get_asset_registry()
assets = ar.get_assets_by_path("/Game", recursive=True)

print("=== FINDING MI_DUSK MATERIALS ===")
for a in assets:
    p = str(a.package_name)
    if "MI_Dusk" in p or "Dusk" in p:
        if "Material" in str(a.asset_class_path.asset_name if hasattr(a, 'asset_class_path') else a.asset_class):
            print(f"  {p}")
