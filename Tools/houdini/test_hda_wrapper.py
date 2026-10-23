import unreal

api = unreal.HoudiniPublicAPIBlueprintLib.get_api()
hda = unreal.load_asset("/Game/Houdini/HDA_Brutalist_ShotComposer")

trans = unreal.Transform(location=[750.0, 600.0, 0.0], rotation=[0.0, 0.0, 0.0], scale=[1.0, 1.0, 1.0])
w = api.instantiate_asset(hda, trans, enable_auto_cook=False, enable_auto_bake=False)
if w:
    actor = w.get_houdini_asset_actor()
    print("Methods on HoudiniPublicAPIAssetWrapper:")
    for m in dir(w):
        if not m.startswith('_'):
            print(f"  {m}")
    unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(actor)
