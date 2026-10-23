import unreal

ap = unreal.AnimPoseExtensions
mesh = unreal.load_asset("/Game/Staging/Film304Repaired_20261017/Sam/SK_Sam_Film304_v01")
anim = unreal.load_asset("/Game/Animations/Film304Idle_20261017/AS_Sam_OfficeIdle_48f_v01")

options = unreal.AnimPoseEvaluationOptions()
options.set_editor_properties({"should_retarget": False, "extract_root_motion": False, "optional_skeletal_mesh": mesh})
pose = ap.get_anim_pose_at_frame(anim, 0, options)
names = [str(n) for n in ap.get_bone_names(pose)]
print("Total bones:", len(names))
arm_bones = [n for n in names if any(k in n.lower() for k in ["arm", "shoulder", "clav", "elbow", "hand", "wrist"])]
print("Arm/Hand bones:", arm_bones)
