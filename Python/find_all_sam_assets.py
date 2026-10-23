import unreal

eal = unreal.EditorAssetLibrary
assets = eal.list_assets("/Game", recursive=True, include_folder=False)
sam_anims = []
for a in assets:
    if "sam" in a.lower() and any(k in a.lower() for k in ["anim", "as_", "pose", "idle", "held", "walk", "stand"]):
        sam_anims.append(a)

print(f"Found {len(sam_anims)} animation assets for Sam:")
for a in sam_anims:
    print(" ", a)
