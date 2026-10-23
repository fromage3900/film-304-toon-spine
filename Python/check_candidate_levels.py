import unreal

ar = unreal.AssetRegistryHelpers.get_asset_registry()

candidates = [
    "/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office",
    "/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office_Dusk_20261018_v06",
    "/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_HeroTonight_20261018",
    "/Game/Maps/L_Toon_Shot_Office",
    "/Game/Maps/L_Toon_Shot_BreakRoom",
    "/Game/Maps/L_Toon_Shot_Hallway",
    "/Game/Maps/Establishing/L_Film_Establishing"
]

print("=== CHECKING LEVEL ASSETS ===")
for path in candidates:
    a = ar.get_asset_by_object_path(path + "." + path.split("/")[-1])
    if a.is_valid():
        print(f"VALID: {path}")
    else:
        print(f"NOT FOUND: {path}")
