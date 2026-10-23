"""Probe 4: the exact math inputs for authoring a pose.

The pose plan: for a bone with bind local rotation L and bind component-space
rotation C, a desired WORLD-space rotation W becomes the new local rotation

        L' = L * (C^-1 * W * C)

which is identical to the classic parent-space form (P^-1 W P) L but needs no
parent bookkeeping -- only the bone's own two bind transforms. This probe
verifies the API signatures that feed that formula and prints a worked example
for one arm bone so the numbers can be sanity-checked before any asset is built.
"""
import unreal

print("=== SIGNATURES ===")
print("get_bone_transform:", unreal.SkeletalMeshComponent.get_bone_transform.__doc__)
for name in ("get_ref_pose_transform", "get_relative_transform"):
    fn = getattr(unreal.SkeletalMeshComponent, name, None)
    print("%s:" % name, "MISSING" if fn is None else fn.__doc__)
print("set_animation:", unreal.SkeletalMeshComponent.set_animation.__doc__)
print("set_animation_mode:", unreal.SkeletalMeshComponent.set_animation_mode.__doc__)
print()
print("=== ENUMS ===")
for enum in ("RelativeTransformSpace", "BoneSpaces", "AnimationMode"):
    print("%s:" % enum,
          [e for e in dir(getattr(unreal, enum)) if not e.startswith("_")])
print()
print("=== QUAT / TRANSFORM ===")
print("Quat:", [n for n in dir(unreal.Quat) if not n.startswith("_")][:36])
print("Transform:", [n for n in dir(unreal.Transform) if not n.startswith("_")][:24])
print("has AnimSequenceFactory:", hasattr(unreal, "AnimSequenceFactory"))
print()

print("=== WORKED EXAMPLE: bind transforms for one arm chain ===")
actor = None
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label().startswith("Film_Subject_Dana"):
        actor = a
        break
print("subject:", None if actor is None else actor.get_actor_label())
if actor is not None:
    comp = actor.get_component_by_class(unreal.SkeletalMeshComponent)
    for bone in ("Shoulder_R", "Elbow_R", "Wrist_R", "Chest_M", "Hip_L",
                 "Knee_L", "Head_M"):
        try:
            t = comp.get_bone_transform(bone, unreal.RelativeTransformSpace.RTS_COMPONENT)
            rot = t.rotation
            print("  %-12s C.loc=(%7.2f,%7.2f,%7.2f) C.rot quat=(%6.3f,%6.3f,%6.3f,%6.3f)"
                  % (bone, t.translation.x, t.translation.y, t.translation.z,
                     rot.x, rot.y, rot.z, rot.w))
        except Exception as exc:                                   # noqa: BLE001
            print("  %-12s FAILED: %s" % (bone, exc))
    # identity check: W = identity must reproduce the bind local rotation
    print()
    print("=== IDENTITY CHECK (W=identity -> L' must equal L) ===")
    for bone in ("Elbow_R", "Hip_L"):
        try:
            c = comp.get_bone_transform(bone, unreal.RelativeTransformSpace.RTS_COMPONENT)
            parent = comp.get_parent_bone(bone)
            pname = str(comp.get_bone_name(parent)) if parent >= 0 else None
            p = (comp.get_bone_transform(pname, unreal.RelativeTransformSpace.RTS_COMPONENT)
                 if pname else unreal.Transform())
            l_bind = p.rotation.inverse() * c.rotation
            w = unreal.Quat()                      # identity
            delta = c.rotation.inverse() * w * c.rotation
            l_new = l_bind * delta
            print("  %-10s parent=%-12s L=(%6.3f,%6.3f,%6.3f,%6.3f) L'=(%6.3f,%6.3f,%6.3f,%6.3f)"
                  % (bone, pname, l_bind.x, l_bind.y, l_bind.z, l_bind.w,
                     l_new.x, l_new.y, l_new.z, l_new.w))
        except Exception as exc:                                   # noqa: BLE001
            print("  %-10s FAILED: %s" % (bone, exc))
print("PROBE4_OK")
