import unreal

eal = unreal.EditorAssetLibrary
anims = eal.list_assets("/Game/Staging", recursive=True, include_folder=False)
for a in anims:
    if "Sam" in a and ("AS_" in a or "AnimSequence" in a or "Pose" in a):
        print("Sam Anim:", a)
