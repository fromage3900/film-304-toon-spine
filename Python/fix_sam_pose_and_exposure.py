import unreal
from pathlib import Path
import json

OUT = Path("G:/film-304-toon-spine/Saved/Audit/Showcase_20261018")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# =========================================================================
# 1. FIX SAM'S POSE PERMANENTLY (IN SEQUENCE + ACTOR COMPONENT)
# =========================================================================
sam_crossed = unreal.load_asset("/Game/Staging/Film304Repaired_20261017/Poses_Headless/AS_Sam_ArmsCrossed_Polish01")

# Disable AutoPlay on loop playback actor so it doesn't fight the scene
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_OfficeIdle_LoopPlayback":
        settings = a.get_editor_property("playback_settings")
        settings.auto_play = False
        a.set_editor_property("playback_settings", settings)
        print("Disabled AutoPlay on Film_OfficeIdle_LoopPlayback")

# Update Sam track inside the sequence itself
seq = unreal.load_asset("/Game/Sequences/Film304Idle_20261017/LS_OfficeCast_SleepFaces_48f_v03_SoftSnore")
for b in seq.get_possessables():
    if b.get_name() == "Film_Cast_Sam":
        for t in b.get_tracks():
            if isinstance(t, unreal.MovieSceneSkeletalAnimationTrack):
                for s in t.get_sections():
                    p = s.get_editor_property("params")
                    p.animation = sam_crossed
                    s.set_editor_property("params", p)
                    print("Updated Sam sequence track to AS_Sam_ArmsCrossed_Polish01")

unreal.EditorAssetLibrary.save_loaded_asset(seq)

# Now update Sam actor component
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cast_Sam":
        skc = a.get_component_by_class(unreal.SkeletalMeshComponent)
        skc.set_editor_property("animation_mode", unreal.AnimationMode.ANIMATION_SINGLE_NODE)
        skc.override_animation_data(sam_crossed, True, False, 0.0, 1.0)
        skc.set_update_animation_in_editor(True)
        skc.play_animation(sam_crossed, True)
        skc.set_position(0.0, False)
        print("Permanently set Film_Cast_Sam to AS_Sam_ArmsCrossed_Polish01")
        break

# =========================================================================
# 2. FIX CRAZY EXPOSURE & DISABLE COMPETING PPVs
# =========================================================================
# Disable all duplicate competing unbound PPVs
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl in [
        "PPV_ToonOutlineHalftoneStack", "PPV_ToonOutlineOnly",
        "PPV_ToonOutlineClean", "PPV_ToonOutlineRiso",
        "PPV_P2_WatercolourPaper", "PPV_P3_RisoPrint", "PPV_P4_CleanCinematic", "EST_PPV_Ink"
    ]:
        a.set_editor_property("enabled", False)
        print(f"Disabled competing PPV: {lbl}")

# Calibrate hero PPV_StorybookOutline
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "PPV_StorybookOutline":
        a.set_editor_property("enabled", True)
        s = a.settings
        # Set controlled auto-exposure
        s.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_HISTOGRAM)
        s.set_editor_property("auto_exposure_bias", -0.4) # Pull down from blown-out +0.9 to moody -0.4
        s.set_editor_property("auto_exposure_min_brightness", 0.01)
        s.set_editor_property("auto_exposure_max_brightness", 15.0)
        s.set_editor_property("auto_exposure_apply_physical_camera_exposure", False) # decouple from crazy physical camera multipliers
        # Bloom & tone
        s.set_editor_property("bloom_intensity", 0.25)
        print("Calibrated PPV_StorybookOutline exposure (bias=-0.4, physical=False, max=15.0)")
        break

# Kill the rogue unshadowed flood bounce that was milkying the floor
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Closeout_WindowBounce":
        c = a.get_component_by_class(unreal.LightComponentBase)
        if c:
            c.set_editor_property("intensity", 0.0)
            print("Turned off Film_Closeout_WindowBounce flood light")

# Save level
unreal.EditorLoadingAndSavingUtils.save_current_level()
print("Saved level state cleanly.")
