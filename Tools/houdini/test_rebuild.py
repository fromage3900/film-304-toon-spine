import unreal
import time

api = unreal.HoudiniPublicAPIBlueprintLib.get_api()
hda = unreal.load_asset("/Game/Houdini/HDA_Brutalist_ShotComposer")
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

trans = unreal.Transform(location=[750.0, 600.0, 0.0], rotation=[0.0, 0.0, 0.0], scale=[1.0, 1.0, 1.0])
w = api.instantiate_asset(hda, trans, enable_auto_cook=True, enable_auto_bake=False)
actor = w.get_houdini_asset_actor()
w.process_component_synchronous()

print("Initial scene_mode:", w.get_int_parameter_value("scene_mode"))

# Set scene_mode = 3
w.set_int_parameter_value("scene_mode", 3)
print("Updated scene_mode:", w.get_int_parameter_value("scene_mode"))

# Let's call rebuild() or recook()
w.rebuild()
w.process_component_synchronous()

comps = actor.get_components_by_class(unreal.ActorComponent)
print(f"Total components on actor after rebuild: {len(comps)}")
for c in comps:
    mesh = c.get_editor_property("static_mesh") if hasattr(c, "get_editor_property") and hasattr(c, "static_mesh") else None
    print(f"  {c.get_name()} ({c.get_class().get_name()}) | Mesh={mesh.get_name() if mesh else 'None'}")

EAS.destroy_actor(actor)
