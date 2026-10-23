import unreal

api = unreal.HoudiniPublicAPIBlueprintLib.get_api()
print("Houdini Engine session valid?", api.is_session_valid())
if not api.is_session_valid():
    print("Creating/restarting session...")
    api.create_session()
    print("Session valid now?", api.is_session_valid())

hda = unreal.load_asset("/Game/Houdini/HDA_Brutalist_ShotComposer")
print("HDA asset loaded:", hda)

trans = unreal.Transform(location=[825.0, -400.0, 0.0], rotation=[0.0, 0.0, 0.0], scale=[1.0, 1.0, 1.0])
w = api.instantiate_asset(hda, trans, enable_auto_cook=False, enable_auto_bake=False)
print("Wrapper created:", w)

if w:
    print("Wrapper methods:")
    for attr in dir(w):
        if not attr.startswith("_"):
            print(f"  {attr}")
            
    actor = w.get_houdini_asset_actor()
    print("Spawned actor:", actor.get_name())
    unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(actor)
