import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in EAS.get_all_level_actors():
    if a.get_actor_label() == "HDA_Breakroom_Sanctuary":
        comp = a.get_component_by_class(unreal.HoudiniAssetComponent)
        print("Breakroom comp:", comp)
        # Check all properties of comp
        for prop in ["houdini_asset", "asynchronous_cook", "b_never_cook", "b_cook_on_parameter_change"]:
            if hasattr(comp, prop):
                print(f"  {prop}: {getattr(comp, prop)}")
        
        # Check static meshes or children
        children = comp.get_children_components(True)
        print("  Children count:", len(children))
        for ch in children:
            print("    Child:", ch.get_name(), ch.get_class().get_name())
