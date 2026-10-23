import unreal

pa = unreal.load_asset("/Game/Staging/Film304Repaired_20261017/Sam/SK_Sam_Film304_v01_Skeleton_PoseAsset")
if pa:
    print("PoseAsset:", pa.get_name())
    if hasattr(unreal, "PoseAssetLibrary"):
        print("Pose names:", unreal.PoseAssetLibrary.get_pose_names(pa))
    else:
        print("PoseAsset dir:", [p for p in dir(pa) if "pose" in p.lower()])
