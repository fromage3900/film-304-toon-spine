import unreal

pa = unreal.load_asset("/Game/Staging/Film304Repaired_20261017/Sam/SK_Sam_Film304_v01_Skeleton_PoseAsset")
print("Poses in PoseAsset:", [str(n) for n in pa.get_pose_names()])
