import unreal

ar = unreal.AssetRegistryHelpers.get_asset_registry()
assets = ar.get_assets_by_path("/Game", recursive=True)

print("=== SPECIFIC OFFICE PROPS ===")
for a in assets:
    pname = str(a.package_name)
    cname = str(a.asset_class_path.asset_name if hasattr(a, 'asset_class_path') else a.asset_class)
    if cname == "StaticMesh":
        if any(w in pname.lower() for w in ["mug", "coffee", "pen", "plant", "succulent", "phone", "paper", "sticky", "lamp", "chair", "trash", "bin", "folder"]):
            print(f"  {pname}")
