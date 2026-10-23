import unreal
import claireon
from pathlib import Path

OUT = Path("G:/film-304-toon-spine/Saved/Audit/Showcase_20261018")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
eas.set_selected_level_actors([])
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

cam = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "HERO04_Macro_Insert":
        cam = a
        break

if cam:
    loc = cam.get_actor_location()
    rot = cam.get_actor_rotation()
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(loc, rot)
    try:
        unreal.SystemLibrary.execute_console_command(world, "ShowFlag.Editor 0")
        res = claireon.slate_screenshot(target="level_viewport", filename="macro_desk_clutter.png", directory=str(OUT))
        print("Captured HERO04:", res)
    finally:
        unreal.SystemLibrary.execute_console_command(world, "ShowFlag.Editor 1")
