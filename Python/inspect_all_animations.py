import unreal

ar = unreal.AssetRegistryHelpers.get_asset_registry()
# In UE 5.5, get_assets_by_class takes TopLevelAssetPath or we can use get_assets_by_path
assets = ar.get_assets_by_path("/Game", recursive=True)

anim_assets = []
for a in assets:
    cname = str(a.asset_class_path.asset_name if hasattr(a, "asset_class_path") else a.asset_class)
    pname = str(a.package_name)
    if "Anim" in cname or "AnimSequence" in cname or "Pose" in pname or "Anim" in pname:
        anim_assets.append((pname, cname))

print(f"Total matching animation assets: {len(anim_assets)}")
for p, c in sorted(anim_assets):
    if any(k in p for k in ["Sam", "Dana", "David", "Cast", "Pose", "Office"]):
        print(f"  [{c}] {p}")
