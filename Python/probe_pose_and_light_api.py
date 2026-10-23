"""Probe the live editor's posing + local-lighting API surface.

Why: "pose the meshes" needs a bone-write path that actually exists in this
build, and "play with local lighting intensely" needs the real light actor
classes. Guessing either wastes an editor session, so ask the reflection glue.
"""
import unreal

print("=== POSING SURFACE ===")
smc = [n for n in dir(unreal.SkeletalMeshComponent)
       if any(k in n.lower() for k in ("bone", "pose"))]
print("SMC_BONE_POSE:", smc)
for name in ("set_bone_rotation", "set_bone_location", "set_bone_transform",
             "get_bone_transform", "set_bone_transform_by_name",
             "set_bone_rotation_by_name", "set_bone_location_by_name"):
    print("  has %-32s : %s" % (name, hasattr(unreal.SkeletalMeshComponent, name)))

print("=== POSEABLE MESH ===")
print("has PoseableMeshComponent:", hasattr(unreal, "PoseableMeshComponent"))
if hasattr(unreal, "PoseableMeshComponent"):
    print("  PM:", [n for n in dir(unreal.PoseableMeshComponent)
                    if "bone" in n.lower()][:20])

print("=== SUBSYSTEMS ===")
print("SKELETAL_MESH_EDITOR_SUBSYSTEM:", hasattr(unreal, "SkeletalMeshEditorSubsystem"))
if hasattr(unreal, "SkeletalMeshEditorSubsystem"):
    print("  SMES:", [n for n in dir(unreal.SkeletalMeshEditorSubsystem)
                      if "pose" in n.lower() or "bone" in n.lower()])
print("EDITOR_ACTOR_SUBSYSTEM:", hasattr(unreal, "EditorActorSubsystem"))

print("=== LOCAL LIGHTERY ===")
for name in ("PointLight", "SpotLight", "RectLight", "DirectionalLight"):
    print("  has %-18s : %s" % (name, hasattr(unreal, name)))
print("=== LEVEL ACTOR COUNT ===")
actors = unreal.EditorLevelLibrary.get_all_level_actors()
print("actors:", len(actors))
for a in actors:
    lbl = a.get_actor_label()
    if lbl.startswith("SESSION_"):
        print("  session actor present:", lbl, a.get_class().get_name())
print("PROBE_OK")
