import unreal

print("=== DIAGNOSE HDA COOK ===")
api = unreal.HoudiniPublicAPIBlueprintLib.get_api()
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in EAS.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl in ["HDA_Cubicle_Hive", "HDA_Breakroom_Sanctuary"]:
        print(f"\nFound Actor: {lbl}")
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        print(f"  Transform: Loc=({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f}) Rot=({rot.pitch:.1f}, {rot.yaw:.1f}, {rot.roll:.1f})")
        
        comp = a.get_component_by_class(unreal.HoudiniAssetComponent)
        if comp:
            print(f"  HoudiniAssetComponent found: {comp.get_name()}")
            # Check wrapper from API
            # How does HoudiniPublicAPI get or create wrapper?
            # Let's inspect api methods:
            # api.instantiate_asset_with_existing_wrapper
        for c in a.get_components_by_class(unreal.ActorComponent):
            c_name = c.get_class().get_name()
            if "Mesh" in c_name:
                print(f"  Component: {c.get_name()} ({c_name})")
