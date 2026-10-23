import unreal

api = unreal.HoudiniPublicAPIBlueprintLib.get_api()
hda = unreal.load_asset("/Game/Houdini/HDA_Brutalist_ShotComposer")
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

trans = unreal.Transform(location=[750.0, 600.0, 0.0], rotation=[0.0, 0.0, 0.0], scale=[1.0, 1.0, 1.0])
w = api.instantiate_asset(hda, trans, enable_auto_cook=True, enable_auto_bake=False)
actor = w.get_houdini_asset_actor()
w.process_component_synchronous()

# Set scene_mode = 3 (Breakroom)
res = w.set_int_parameter_value("scene_mode", 3)
print("set_int_parameter_value('scene_mode', 3):", res)
w.recook()
w.process_component_synchronous()

print("Last error:", w.get_last_error_message())
comps = actor.get_components_by_class(unreal.ActorComponent)
print(f"Total components on actor: {len(comps)}")
for c in comps:
    cnt = c.get_instance_count() if hasattr(c, "get_instance_count") else 1
    mesh = c.get_editor_property("static_mesh") if hasattr(c, "get_editor_property") and hasattr(c, "static_mesh") else None
    print(f"  {c.get_name()} ({c.get_class().get_name()}) | Mesh={mesh.get_name() if mesh else 'None'} | Count={cnt}")

EAS.destroy_actor(actor)
