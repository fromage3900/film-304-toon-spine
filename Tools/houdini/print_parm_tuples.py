import unreal

api = unreal.HoudiniPublicAPIBlueprintLib.get_api()
hda = unreal.load_asset("/Game/Houdini/HDA_Brutalist_ShotComposer")
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

trans = unreal.Transform(location=[0.0, 0.0, 0.0], rotation=[0.0, 0.0, 0.0], scale=[1.0, 1.0, 1.0])
w = api.instantiate_asset(hda, trans, enable_auto_cook=False, enable_auto_bake=False)
actor = w.get_houdini_asset_actor()

tuples = w.get_parameter_tuples()
print(f"Total parameter tuples: {len(tuples)}")
for t in tuples:
    print(f"  Tuple: '{t}'")

EAS.destroy_actor(actor)
