"""One-frame check after the revert. No changes, no save."""
import json
from pathlib import Path
import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EL = unreal.EditorLevelLibrary
OUT = Path(unreal.Paths.project_dir()) / "Saved/Audit/HeroLock20261018"
OUT.mkdir(parents=True, exist_ok=True)

actors = {a.get_actor_label(): a for a in EAS.get_all_level_actors()
          if a.get_class().get_name() in ("CineCameraActor", "Ultra_Dynamic_Sky_C")}

cam = actors.get("HERO01_Wide_Establishing")
uds = actors.get("Film_UDS_Daylight")
report = {"camera": "HERO01_Wide_Establishing",
          "uds_time": None, "shot": None, "errors": []}

if uds is not None:
    for name in ("time_of_day", "Time of Day"):
        try:
            report["uds_time"] = float(uds.get_editor_property(name))
            break
        except Exception:
            continue

if cam is None:
    report["errors"].append("HERO01 missing")
else:
    loc = cam.get_actor_location()
    rot = cam.get_actor_rotation()
    EL.set_level_viewport_camera_info(loc, rot)
    try:
        import claireon
        res = claireon.slate_screenshot(target="level_viewport",
                                       filename="after_revert_wide.png",
                                       directory=str(OUT))
        report["shot"] = res
    except Exception as exc:
        report["errors"].append("screenshot: " + str(exc)[:160])

(OUT / "after_revert.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"uds_time": report["uds_time"], "shot": report["shot"],
                  "errors": report["errors"]}, indent=1))
