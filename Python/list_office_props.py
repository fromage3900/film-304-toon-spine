import unreal

ar = unreal.AssetRegistryHelpers.get_asset_registry()
assets = ar.get_assets_by_path("/Game", recursive=True)

print("=== OFFICE PROPS IN PROJECT ===")
props = []
for a in assets:
    pname = str(a.package_name)
    cname = str(a.asset_class_path.asset_name if hasattr(a, 'asset_class_path') else a.asset_class)
    if cname == "StaticMesh":
        if any(k in pname.lower() for k in ["prop", "clutter", "office", "desk", "cup", "mug", "paper", "book", "plant", "pen", "folder", "trash", "bin"]):
            props.append(pname)

print(f"Total office/prop static meshes: {len(props)}")
for p in sorted(props)[:40]:
    print(f"  {p}")
