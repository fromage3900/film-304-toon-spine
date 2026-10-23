"""Capture HERO01 twice: with editor visuals on, then off. Viewport state only."""
import json
from pathlib import Path
import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EL = unreal.EditorLevelLibrary
OUT = Path(unreal.Paths.project_dir()) / "Saved/Audit/HeroLock20261018"
OUT.mkdir(parents=True, exist_ok=True)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

cam = next((a for a in EAS.get_all_level_actors()
            if a.get_actor_label() == "HERO01_Wide_Establishing"), None)
report = {"world": world.get_path_name(), "shots": {}, "errors": []}

if cam is None:
    report["errors"].append("HERO01 missing")
else:
    loc, rot = cam.get_actor_location(), cam.get_actor_rotation()
    EL.set_level_viewport_camera_info(loc, rot)
    try:
        import claireon
        report["shots"]["editor_on"] = claireon.slate_screenshot(
            target="level_viewport", filename="check_editor_on.png", directory=str(OUT))
        unreal.SystemLibrary.execute_console_command(world, "ShowFlag.Editor 0")
        EL.set_level_viewport_camera_info(loc, rot)
        report["shots"]["editor_off"] = claireon.slate_screenshot(
            target="level_viewport", filename="check_editor_off.png", directory=str(OUT))
    except Exception as exc:
        report["errors"].append(str(exc)[:200])
    finally:
        unreal.SystemLibrary.execute_console_command(world, "ShowFlag.Editor 1")
        EL.set_level_viewport_camera_info(loc, rot)

(OUT / "editor_flag_check.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=1))
