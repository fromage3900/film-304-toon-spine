import unreal

# We can query the asset registry or open the levels without saving the current one if not dirty,
# or we can inspect package exports or use EditorLoadingAndSavingUtils
maps_to_check = [
    "/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office_Assembly_20261018_v02",
    "/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_HeroTonight_20261018",
    "/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office_Dusk_20261018_v06",
    "/Game/Maps/Establishing/L_Film_Establishing_Closeout_20261018_v01"
]

ar = unreal.AssetRegistryHelpers.get_asset_registry()

for mpath in maps_to_check:
    a = ar.get_asset_by_object_path(mpath + "." + mpath.split("/")[-1])
    print(f"\nMap: {mpath}")
    print(f"  Valid: {a.is_valid()}, Class: {a.asset_class_path.asset_name if hasattr(a, 'asset_class_path') else a.asset_class}")
    # Print tags/metadata
    if a.is_valid():
        print(f"  TagKeys: {list(a.asset_tags.keys()) if hasattr(a, 'asset_tags') else 'N/A'}")
