import unreal

api = unreal.HoudiniPublicAPIBlueprintLib.get_api()
hda = unreal.load_asset("/Game/Houdini/HDA_Brutalist_ShotComposer")
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

trans = unreal.Transform(location=[0.0, 0.0, 0.0], rotation=[0.0, 0.0, 0.0], scale=[1.0, 1.0, 1.0])
w = api.instantiate_asset(hda, trans, enable_auto_cook=True, enable_auto_bake=False)
actor = w.get_houdini_asset_actor()
w.process_component_synchronous()

tuples = w.get_parameter_tuples()
print(f"Total parameter tuples after cook: {len(tuples)}")
for t in tuples:
    print(f"  Tuple: '{t}'")

# Now try setting scene_mode
res = w.set_int_parameter_value("scene_mode", 1)
print("set_int_parameter_value('scene_mode', 1):", res)
val = w.get_int_parameter_value("scene_mode")
print("get_int_parameter_value('scene_mode'):", val)

EAS.destroy_actor(actor)
