import unreal
import claireon
from pathlib import Path

OUT = Path("G:/film-304-toon-spine/Saved/Audit/Showcase_20261018")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

sam_actor = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cast_Sam":
        sam_actor = a
        break

anim_crossed = unreal.load_asset("/Game/Staging/Film304Repaired_20261017/Poses_Headless/AS_Sam_ArmsCrossed_Polish01")

if sam_actor and anim_crossed:
    skm = sam_actor.skeletal_mesh_component
    skm.set_editor_property("animation_mode", unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    skm.override_animation_data(anim_crossed, is_looping=True, is_playing=True)
    sam_actor.set_actor_hidden_in_game(False)
    # Check Sam mesh visibility
    skm.set_editor_property("hidden_in_game", False)
    
    # Place Sam near Dana's desk or in conversation stance
    sam_actor.set_actor_location(unreal.Vector(80.0, -20.0, 2.0), False, False)
    sam_actor.set_actor_rotation(unreal.Rotator(0.0, 140.0, 0.0), False)
    
    # Pilot camera to inspect Sam directly
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(unreal.Vector(140.0, -100.0, 95.0), unreal.Rotator(pitch=-5.0, yaw=135.0, roll=0.0))
    res = claireon.slate_screenshot(target="level_viewport", filename="test_sam_crossed_arms.png", directory=str(OUT))
    print("Screenshot result:", res)
