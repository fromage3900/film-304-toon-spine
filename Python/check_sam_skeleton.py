import unreal

anim = unreal.load_asset("/Game/Staging/Film304Repaired_20261017/Poses_Headless/AS_Sam_ArmsCrossed_Polish01")
mesh = unreal.load_asset("/Game/Staging/Film304Repaired_20261017/Sam/SK_Sam_Film304_v01")

print("Anim skeleton:", anim.get_editor_property("skeleton").get_name())
print("Mesh skeleton:", mesh.get_editor_property("skeleton").get_name())
print("Anim length:", anim.get_play_length(), "num frames:", unreal.AnimationLibrary.get_num_frames(anim))
print("Track count:", len(unreal.AnimationLibrary.get_animation_track_names(anim)))
