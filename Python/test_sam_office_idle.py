import unreal
import claireon
from pathlib import Path

OUT = Path("G:/film-304-toon-spine/Saved/Audit/Showcase_20261018")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

anim = unreal.load_asset("/Game/Animations/Film304Idle_20261017/AS_Sam_OfficeIdle_48f_v01")
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cast_Sam":
        skc = a.get_component_by_class(unreal.SkeletalMeshComponent)
        skc.override_animation_data(anim, True, False, 0.0, 1.0)
        skc.set_update_animation_in_editor(True)
        skc.play_animation(anim, True)
        skc.set_position(0.0, False)
        print("Assigned AS_Sam_OfficeIdle_48f_v01 to Sam")
        break

# Capture screenshot focusing on Sam
cloc = unreal.Vector(120.0, -180.0, 110.0)
sam_loc = unreal.Vector(-55.2, -68.7, 100.0)
crot = unreal.MathLibrary.find_look_at_rotation(cloc, sam_loc)
unreal.EditorLevelLibrary.set_level_viewport_camera_info(cloc, crot)
res = claireon.slate_screenshot(target="level_viewport", filename="sam_office_idle_test.png", directory=str(OUT))
print("Screenshot result:", res)
