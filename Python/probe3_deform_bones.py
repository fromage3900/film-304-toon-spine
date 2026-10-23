"""Probe 3: deform-side bone names + every viable pose-write mechanism.

Findings so far:
  * SkeletalMeshComponent cannot write bones (no set_bone_*).
  * PoseableMeshComponent CAN (set_bone_rotation_by_name + BoneSpaces).
  * unreal.PoseableMeshActor is NOT exposed to Python in this build.

So this probe answers three questions that decide the implementation:
  1. which bones are on the DEFORM side (skinned) vs the FK control side;
  2. whether a PoseableMeshComponent can be created/registered in the world;
  3. whether the AnimSequence / data-controller route is exposed as a fallback.
"""
import unreal

KEY = ("shoulder", "arm", "elbow", "wrist", "hand", "finger", "thumb",
       "chest", "spine", "neck", "head", "thigh", "knee", "calf", "leg",
       "ankle", "foot", "toes", "root", "hip", "pelvis", "clavicle")
PREFIXES = ("fk", "sdk", "ik", "motion", "x", "fkparent", "pole", "curve",
            "grp", "group", "nurb", "locator", "loc", "blend")

print("=== POSE-RELATED MODULES ===")
print("POSE:", sorted(n for n in dir(unreal) if "ose" in n)[:70])
print()
print("ANIM:", sorted(n for n in dir(unreal)
                     if "nim" in n and any(k in n for k in
                                           ("Library", "Data", "Pose",
                                            "Sequence", "Controller")))[:70])
print()
print("ACTOR_COMPONENT_FNS:", [n for n in dir(unreal.Actor)
                               if "component" in n.lower()][:40])
print("NEW_OBJECT:", hasattr(unreal, "new_object"))
print("PMC_REGISTER:", [n for n in dir(unreal.PoseableMeshComponent)
                        if any(k in n.lower() for k in
                               ("register", "attach", "bounds", "owner",
                                "mesh"))][:40])
print("SMC_ANIM_FNS:", [n for n in dir(unreal.SkeletalMeshComponent)
                        if any(k in n.lower() for k in
                               ("animation_mode", "set_animation", "play",
                                "anim_instance", "poses"))][:40])
print()

print("=== DEFORM-SIDE BONE NAMES (controls filtered out) ===")
actor = None
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label().startswith("Film_Subject_Dana"):
        actor = a
        break
print("subject:", None if actor is None else actor.get_actor_label())
if actor is not None:
    comp = actor.get_component_by_class(unreal.SkeletalMeshComponent)
    n = comp.get_num_bones()
    deform, controls = [], 0
    for i in range(n):
        nm = str(comp.get_bone_name(i))
        low = nm.lower()
        if not any(k in low for k in KEY):
            continue
        if nm.lower().startswith(PREFIXES):
            controls += 1
            continue
        deform.append((i, nm))
    print("keyword matches on control side:", controls)
    print("keyword matches on deform side:", len(deform))
    for i, nm in deform[:220]:
        print("   %4d  %s" % (i, nm))
print("PROBE3_OK")
