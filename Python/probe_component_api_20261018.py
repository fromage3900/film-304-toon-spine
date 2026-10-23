"""Read-only: confirm the editor Python API for building an ISM/HISM at runtime."""
import unreal

print("Actor component methods:",
      sorted(n for n in dir(unreal.Actor) if "component" in n.lower()))
print("EditorLevelLibrary spawn methods:",
      sorted(n for n in dir(unreal.EditorLevelLibrary) if "spawn" in n.lower()))
print("has new_object:", hasattr(unreal, "new_object"))
print("has HISM class:", hasattr(unreal, "HierarchicalInstancedStaticMeshComponent"))
print("HISM methods:",
      sorted(n for n in dir(unreal.HierarchicalInstancedStaticMeshComponent)
             if n in ("add_instance", "add_instances", "set_static_mesh",
                      "set_mobility", "register_component", "set_collision_enabled")))
print("ActorSubsystem spawn:",
      sorted(n for n in dir(unreal.get_editor_subsystem(unreal.EditorActorSubsystem))
             if "spawn" in n.lower()))
