"""Probe the bone vocabulary of Dana v08 and the PoseableMesh write API.

Why: posing needs (a) the real bone names inside DeformationSystem, and (b) the
exact Python signatures of the poseable-mesh writers, docstrings included.
Guessing bone names on a 1,230-bone Maya rig is how a session burns an hour.
"""
import unreal

MESH = "/Game/Staging/DanaFilmRuntime_20261016/Dana_CleanSkin_v08"
KEY = ("shoulder", "arm", "elbow", "wrist", "hand", "finger", "thumb",
       "chest", "spine", "neck", "head", "thigh", "knee", "calf", "leg",
       "ankle", "foot", "root", "hip", "pelvis", "clavicle")

print("=== POSEABLE ACTOR / COMPONENT API ===")
print("has PoseableMeshActor:", hasattr(unreal, "PoseableMeshActor"))
for fn_name in ("set_bone_rotation_by_name", "set_bone_location_by_name",
                "set_bone_scale_by_name", "reset_bone_transform_by_name",
                "get_bone_transform_by_name", "set_skeletal_mesh_asset",
                "set_material", "set_animation_mode"):
    fn = getattr(unreal.PoseableMeshComponent, fn_name, None)
    doc = "" if fn is None else (fn.__doc__ or "")
    doc = " ".join(doc.split())[:260]
    print("  %-30s %s %s" % (fn_name, "OK " if fn else "MISSING", doc))

print("=== ENUM CANDIDATES ===")
for enum_name in ("BoneSpaces", "BoneRotationSpace", "BoneTransformSpace",
                  "RelativeTransformSpace", "BoneControlSpace"):
    print("  has %-24s : %s" % (enum_name, hasattr(unreal, enum_name)))

print("=== CURRENT SUBJECT ACTOR BONES ===")
actor = None
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl.startswith("Film_Subject_Dana"):
        actor = a
        break
print("subject:", None if actor is None else actor.get_actor_label())
if actor is not None:
    comp = actor.get_component_by_class(unreal.SkeletalMeshComponent)
    mesh = comp.get_skeletal_mesh_asset()
    print("mesh:", mesh.get_path_name() if mesh else None)
    n = comp.get_num_bones()
    print("bone count:", n)
    hits = []
    for i in range(n):
        name = str(comp.get_bone_name(i))
        low = name.lower()
        if any(k in low for k in KEY):
            hits.append(name)
    print("keyword bone matches:", len(hits))
    for name in hits[:150]:
        print("   ", name)
print("PROBE2_OK")
