import unreal

api = unreal.HoudiniPublicAPIBlueprintLib.get_api()
print("API Dir:", [m for m in dir(api) if not m.startswith('_')])

hda_actors = [a for a in unreal.EditorActorSubsystem().get_all_level_actors() if 'HDA' in a.get_actor_label()]
for a in hda_actors:
    print(f"\nActor: {a.get_actor_label()} (Class: {a.get_class().get_name()})")
    print("Actor Dir:", [m for m in dir(a) if 'houdini' in m.lower()])
    comp = a.get_component_by_class(unreal.HoudiniAssetComponent)
    if comp:
        print("Comp Dir:", [m for m in dir(comp) if not m.startswith('_')][:25])
        print("Comp params:", comp.get_editor_property("parameters") if hasattr(comp, "get_editor_property") else "None")
