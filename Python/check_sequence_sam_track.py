import unreal

seq = unreal.load_asset("/Game/Sequences/Film304Idle_20261017/LS_OfficeCast_SleepFaces_48f_v03_SoftSnore")
for b in seq.get_possessables():
    print(f"Possessable: {b.get_name()}")
    for t in b.get_tracks():
        print(f"  Track: {t.get_class().get_name()}")
        if isinstance(t, unreal.MovieSceneSkeletalAnimationTrack):
            for s in t.get_sections():
                anim_params = s.get_editor_property("params")
                print(f"    Anim: {anim_params.animation.get_name() if anim_params.animation else 'None'}")
