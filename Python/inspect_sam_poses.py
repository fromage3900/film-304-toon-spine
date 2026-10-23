import unreal

ap = unreal.AnimPoseExtensions
mesh = unreal.load_asset("/Game/Staging/Film304Repaired_20261017/Sam/SK_Sam_Film304_v01")

anims = [
    "/Game/Animations/Film304Idle_20261017/AS_Sam_OfficeIdle_48f_v01",
    "/Game/Retarget/Film304Idle_20261017/RawRetarget/Sam/Sam_UAL_Idle_Loop_48f_Anim",
    "/Game/Staging/Film304Repaired_20261017/Sam/Poses/AS_Sam_Pose_Shrug",
]

for p in anims:
    a = unreal.load_asset(p)
    if not a:
        print("Missing:", p)
        continue
    options = unreal.AnimPoseEvaluationOptions()
    options.set_editor_properties({"should_retarget": False, "extract_root_motion": False, "optional_skeletal_mesh": mesh})
    pose = ap.get_anim_pose_at_frame(a, 0, options)
    # Check wrist and shoulder locations
    for side in ["l", "r"]:
        wrist = ap.get_bone_pose(pose, unreal.Name("Wrist_" + side), unreal.AnimPoseSpaces.LOCAL)
        arm = ap.get_bone_pose(pose, unreal.Name("UpperArm_" + side), unreal.AnimPoseSpaces.LOCAL)
        print(f"{a.get_name()} {side}: UpperArm Rot={arm.rotation.rotator()} Wrist Trans={wrist.translation}")
