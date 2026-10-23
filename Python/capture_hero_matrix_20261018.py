"""Tonight's hero comparison matrix. Temporarily switches PPV + UDS, then restores.

12 look frames: HERO01..04 x Clean / Dither / Riso
 4 sky frames:  HERO02 x UDS 700 / 1200 / 1730 / 2130 with Clean
Ends on Clean + the authored UDS time, saves, and writes a manifest.
"""
import json
from pathlib import Path
import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EL = unreal.EditorLevelLibrary
OUT = Path(unreal.Paths.project_dir()) / "Saved/Audit/HeroLock20261018"
OUT.mkdir(parents=True, exist_ok=True)

SHOTS = ["HERO01_Wide_Establishing", "HERO02_Medium_TwoShot",
         "HERO03_Close_Portrait", "HERO04_Macro_Insert"]
SHORT = {"HERO01_Wide_Establishing": "01_wide",
         "HERO02_Medium_TwoShot": "02_medium",
         "HERO03_Close_Portrait": "03_close",
         "HERO04_Macro_Insert": "04_macro"}
LOOKS = {
    "Clean": "PPV_ToonOutlineClean",
    "Dither": "PPV_ToonOutlineHalftoneStack",
    "Riso": "PPV_ToonOutlineRiso",
}
UDS_TIMES = [700.0, 1200.0, 1730.0, 2130.0]
UDS_SHOT = "HERO02_Medium_TwoShot"

report = {"frames": [], "uds": [], "restored": {}, "errors": []}


def safe(fn, default=None):
    try:
        return fn()
    except Exception as exc:
        report["errors"].append(str(exc)[:180])
        return default


def prop(o, n, d=None):
    return safe(lambda: o.get_editor_property(n), d)


actors = {}
for a in EAS.get_all_level_actors():
    actors[safe(lambda: a.get_actor_label(), "")] = a


def set_active(look):
    for name, label in LOOKS.items():
        a = actors.get(label)
        if a is not None:
            a.set_editor_property("blend_weight", 1.0 if name == look else 0.0)


def frame(shot, tag):
    a = actors.get(shot)
    if a is None:
        report["errors"].append("camera missing: " + shot)
        return None
    loc = a.get_actor_location()
    rot = a.get_actor_rotation()
    EL.set_level_viewport_camera_info(loc, rot)
    # Touch the transform again so the viewport redraws after a PPV change.
    EL.set_level_viewport_camera_info(loc, rot)
    name = "hero_%s_%s.png" % (SHORT.get(shot, shot), tag)
    try:
        import claireon
        res = claireon.slate_screenshot(target="level_viewport", filename=name,
                                       directory=str(OUT))
        return res
    except Exception as exc:
        report["errors"].append("screenshot " + name + ": " + str(exc)[:150])
        return None


start_loc, start_rot = EL.get_level_viewport_camera_info()
uds = actors.get("Film_UDS_Daylight")
uds_path = safe(lambda: uds.get_path_name(), None)
uds_start = safe(lambda: float(uds.get_editor_property("time_of_day")), None)
if uds_start is None:
    uds_start = safe(lambda: float(uds.get_editor_property("Time of Day")), None)


def set_uds(value):
    if uds is None:
        return False
    try:
        import claireon
        claireon.uobject_set_property(object_path=uds_path,
                                      property_path="Time of Day", value=float(value))
        return True
    except Exception:
        ok = safe(lambda: uds.set_editor_property("time_of_day", float(value)), None)
        if ok is None:
            ok = safe(lambda: uds.set_editor_property("Time of Day", float(value)), None)
        return ok is not None


for look in LOOKS:
    set_active(look)
    for shot in SHOTS:
        res = frame(shot, look.lower())
        report["frames"].append({"shot": shot, "look": look,
                                 "file": (res or {}).get("data", {}).get("file_path")
                                 if isinstance(res, dict) else None,
                                 "ok": res is not None})

set_active("Clean")
for t in UDS_TIMES:
    ok = set_uds(t)
    res = frame(UDS_SHOT, "uds%d" % int(t))
    report["uds"].append({"time_of_day": t, "applied": ok, "file":
                          (res or {}).get("data", {}).get("file_path")
                          if isinstance(res, dict) else None, "ok": res is not None})

if uds_start is not None:
    set_uds(uds_start)
set_active("Clean")
EL.set_level_viewport_camera_info(start_loc, start_rot)
report["restored"] = {"uds": uds_start, "active_look": "Clean",
                      "viewport": [[round(v, 2) for v in start_loc.to_tuple()],
                                   [round(v, 2) for v in start_rot.to_tuple()]]}
report["saved"] = bool(safe(lambda: unreal.EditorLoadingAndSavingUtils.save_current_level(), False))
report["dirty_after"] = sorted(safe(lambda: [p.get_name() for p in
    unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()], []) or [])
report["ok"] = (not report["errors"] and len(report["frames"]) == 12
                and len(report["uds"]) == 4 and report["saved"])
(OUT / "hero_matrix.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

print("matrix ok=" + str(report["ok"]), "frames=" + str(len(report["frames"])),
      "uds=" + str(len(report["uds"])), "saved=" + str(report["saved"]))
for f in report["frames"]:
    print("  ", f["shot"], f["look"], "->", f["file"])
for u in report["uds"]:
    print("   uds", u["time_of_day"], "applied=", u["applied"], "->", u["file"])
print("  restored", report["restored"], "dirty=", report["dirty_after"])
for e in report["errors"]:
    print("  ERROR", e)
