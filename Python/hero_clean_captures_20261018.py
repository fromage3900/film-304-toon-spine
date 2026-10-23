"""Clean hero captures with editor-only visuals hidden. No look change, no save.

ShowFlag.Editor hides the 21 CineCamera actor bodies, gizmos and icons that were
covering the window in viewport captures. The render itself never contained them.
"""
import json
from pathlib import Path
import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EL = unreal.EditorLevelLibrary
OUT = Path(unreal.Paths.project_dir()) / "Saved/Audit/HeroLock20261018"
OUT.mkdir(parents=True, exist_ok=True)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

SHOTS = [("HERO01_Wide_Establishing", "clean_01_wide"),
         ("HERO02_Medium_TwoShot", "clean_02_medium"),
         ("HERO03_Close_Portrait", "clean_03_close"),
         ("HERO04_Macro_Insert", "clean_04_macro")]
report = {"world": world.get_path_name(), "frames": [], "errors": [], "saved": False}

actors = {a.get_actor_label(): a for a in EAS.get_all_level_actors()}
start_loc, start_rot = EL.get_level_viewport_camera_info()

try:
    unreal.SystemLibrary.execute_console_command(world, "ShowFlag.Editor 0")
    import claireon
    for label, stem in SHOTS:
        cam = actors.get(label)
        if cam is None:
            report["errors"].append("missing " + label)
            continue
        EL.set_level_viewport_camera_info(cam.get_actor_location(), cam.get_actor_rotation())
        res = claireon.slate_screenshot(target="level_viewport",
                                       filename=stem + ".png", directory=str(OUT))
        report["frames"].append({"camera": label, "stem": stem,
                                 "file": (res or {}).get("data", {}).get("file_path"),
                                 "ok": res is not None})
except Exception as exc:
    report["errors"].append(str(exc)[:200])
finally:
    unreal.SystemLibrary.execute_console_command(world, "ShowFlag.Editor 1")
    EL.set_level_viewport_camera_info(start_loc, start_rot)

report["dirty_maps"] = sorted(p.get_name() for p in
    unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())
report["ok"] = not report["errors"] and len(report["frames"]) == 4
(OUT / "clean_captures.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"ok": report["ok"], "frames": report["frames"],
                  "dirty": report["dirty_maps"], "errors": report["errors"]}, indent=1))
