import unreal

api = unreal.HoudiniPublicAPIBlueprintLib.get_api()
hda = unreal.load_asset("/Game/Houdini/HDA_Brutalist_ShotComposer")
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

trans = unreal.Transform(location=[750.0, 600.0, 0.0], rotation=[0.0, 0.0, 0.0], scale=[1.0, 1.0, 1.0])
w = api.instantiate_asset(hda, trans, enable_auto_cook=True, enable_auto_bake=False)
actor = w.get_houdini_asset_actor()
w.process_component_synchronous()

w.set_int_parameter_value("scene_mode", 3)
w.rebuild()
w.process_component_synchronous()

print("Calling bake_all_outputs()...")
baked_res = w.bake_all_outputs()
print("bake_all_outputs result:", baked_res)

# Check what actors exist in level now with 'bake' or in world
actors_after = EAS.get_all_level_actors()
new_actors = [a for a in actors_after if "bake" in a.get_actor_label().lower() or "zmj" in a.get_actor_label().lower()]
print(f"Baked actors found: {len(new_actors)}")
for na in new_actors:
    print(f"  {na.get_actor_label()} ({na.get_class().get_name()})")

# Cleanup test actor
EAS.destroy_actor(actor)
for na in new_actors:
    EAS.destroy_actor(na)
