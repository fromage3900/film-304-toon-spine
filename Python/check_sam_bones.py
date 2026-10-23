import unreal

mesh = unreal.load_asset("/Game/Staging/Film304Repaired_20261017/Sam/SK_Sam_Film304_v01")
skeleton = mesh.get_editor_property("skeleton")
bones = [str(unreal.SkeletonLibrary.get_bone_name(skeleton, i)) for i in range(15)]
print("First 15 bones of Sam skeleton:", bones)
arm_bones = [str(unreal.SkeletonLibrary.get_bone_name(skeleton, i)) for i in range(unreal.SkeletonLibrary.get_num_bones(skeleton)) if any(k in str(unreal.SkeletonLibrary.get_bone_name(skeleton, i)).lower() for k in ["arm", "shoulder", "hand", "clavicle", "elbow"])]
print("Arm/Hand bones:", arm_bones[:20])
