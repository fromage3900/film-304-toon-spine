import unreal

api = unreal.HoudiniPublicAPIBlueprintLib.get_api()
hda = unreal.load_asset("/Game/Houdini/HDA_Brutalist_ShotComposer")
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for mode in [1, 3]:
    trans = unreal.Transform(location=[500.0, 500.0, 0.0], rotation=[0.0, 0.0, 0.0], scale=[1.0, 1.0, 1.0])
    w = api.instantiate_asset(hda, trans, enable_auto_cook=False, enable_auto_bake=False)
    actor = w.get_houdini_asset_actor()
    print(f"\n--- Testing Mode {mode} on {actor.get_name()} ---")
    
    # Try setting as int
    res_int = w.set_int_parameter_value("scene_mode", mode)
    print(f"  set_int_parameter_value('scene_mode', {mode}) -> {res_int}")
    print(f"  get_int_parameter_value('scene_mode') -> {w.get_int_parameter_value('scene_mode')}")
    
    w.recook()
    w.process_component_synchronous()
    
    print(f"  Last error message: '{w.get_last_error_message()}'")
    comps = actor.get_components_by_class(unreal.ActorComponent)
    mesh_comps = [c for c in comps if "Mesh" in c.get_class().get_name() or "Houdini" in c.get_class().get_name()]
    print(f"  Total relevant components: {len(mesh_comps)}")
    for c in mesh_comps:
        cnt = c.get_instance_count() if hasattr(c, "get_instance_count") else 1
        mesh = c.get_editor_property("static_mesh") if hasattr(c, "get_editor_property") and hasattr(c, "static_mesh") else None
        print(f"    - {c.get_name()} ({c.get_class().get_name()}) | Mesh={mesh.get_name() if mesh else 'None'} | Count={cnt}")
        
    EAS.destroy_actor(actor)
