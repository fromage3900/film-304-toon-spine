import unreal

eal = unreal.EditorAssetLibrary
assets = eal.list_assets("/Game/Environment/Brutalist", recursive=True, include_folder=False)
for a in assets:
    if "SM_" in a:
        print("Brutalist Mesh:", a)
