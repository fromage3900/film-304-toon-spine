"""Undo ONLY the light/exposure change from the hero-lock pass.

Guarded: each property is reverted only if it still holds the value this pass
wrote. If you changed it in the editor since, it is left alone and reported.

Does not touch cameras, materials, the outline, or UDS.
"""
import json
from pathlib import Path
import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EL = unreal.EditorLevelLibrary
OUT = Path(unreal.Paths.project_dir()) / "Saved/Audit/HeroLock20261018"
OUT.mkdir(parents=True, exist_ok=True)
LEVEL = "/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office"

# label -> {property: (value_this_pass_wrote, value_before_this_pass)}
LIGHTS = {
    "Cast_RimKicker_Light": {"intensity": (5.0, 0.85)},
    "Light_Cinematic_SunBeam": {"volumetric_scattering_intensity": (0.8, 2.5)},
    "EST_Fill_E1": {"intensity": (0.15, 0.0)},
    "Light_Workstation_Row_Troffer": {"intensity": (8.0, 3.5)},
    "Light_Hero_CharacterFill": {"intensity": (4.0, 3.5)},
}
PPV_LABEL = "PPV_ToonOutlineClean"
PPV_MINE = {"auto_exposure_min_brightness": 0.8,
            "auto_exposure_max_brightness": 1.2,
            "auto_exposure_bias": 0.0}
PPV_RESTORE = {"auto_exposure_min_brightness": 0.03,
               "auto_exposure_max_brightness": 8.0,
               "auto_exposure_bias": 1.0,
               "bloom_intensity": 0.675,
               "vignette_intensity": 0.4}
OVERRIDE_KEYS = ["override_auto_exposure_method",
                 "override_auto_exposure_min_brightness",
                 "override_auto_exposure_max_brightness",
                 "override_auto_exposure_bias",
                 "override_bloom_intensity",
                 "override_vignette_intensity"]

report = {"world": None, "reverted": [], "skipped": [], "ppv": {}, "errors": []}


def safe(fn, default=None):
    try:
        return fn()
    except Exception as exc:
        report["errors"].append(str(exc)[:160])
        return default


def prop(o, n, d=None):
    return safe(lambda: o.get_editor_property(n), d)


world = safe(lambda: unreal.get_editor_subsystem(
    unreal.UnrealEditorSubsystem).get_editor_world(), None)
if world is None or "L_Film_Office" not in world.get_path_name():
    safe(lambda: unreal.EditorLoadingAndSavingUtils.load_map(LEVEL))
    world = safe(lambda: unreal.get_editor_subsystem(
        unreal.UnrealEditorSubsystem).get_editor_world(), None)
report["world"] = world.get_path_name() if world else None
if report["world"] is None or "L_Film_Office" not in report["world"]:
    raise RuntimeError("wrong level: " + str(report["world"]))

actors = {}
for a in EAS.get_all_level_actors():
    actors[safe(lambda: a.get_actor_label(), "")] = a

for label, props in LIGHTS.items():
    actor = actors.get(label)
    comp = safe(lambda: actor.get_component_by_class(unreal.LightComponent), None) if actor else None
    if comp is None:
        report["errors"].append("missing light: " + label)
        continue
    for key, (mine, before) in props.items():
        current = prop(comp, key)
        if current is not None and abs(float(current) - float(mine)) < 1e-3:
            safe(lambda key=key, before=before: comp.set_editor_property(key, float(before)))
            report["reverted"].append({"light": label, "property": key,
                                       "from": current, "to": prop(comp, key)})
        else:
            report["skipped"].append({"light": label, "property": key,
                                      "current": current, "expected_mine": mine})

ppv = actors.get(PPV_LABEL)
if ppv is None:
    report["errors"].append("missing PPV: " + PPV_LABEL)
else:
    s = prop(ppv, "settings")
    still_mine = all(
        s is not None
        and bool(prop(s, "override_" + k, True))
        and abs(float(prop(s, k, -1)) - float(v)) < 1e-3
        for k, v in PPV_MINE.items())
    report["ppv"]["still_mine"] = still_mine
    if still_mine:
        for key in OVERRIDE_KEYS:
            safe(lambda key=key: s.set_editor_property(key, False))
        for key, value in PPV_RESTORE.items():
            safe(lambda key=key, value=value: s.set_editor_property(key, float(value)))
        ppv.set_editor_property("settings", s)
        report["ppv"]["reverted"] = True
        report["ppv"]["after"] = {k: str(prop(s, k)) for k in
                                  OVERRIDE_KEYS + list(PPV_RESTORE)}
    else:
        report["ppv"]["reverted"] = False
        report["ppv"]["current"] = {k: str(prop(s, k)) for k in PPV_MINE}

report["saved"] = bool(safe(lambda: unreal.EditorLoadingAndSavingUtils.save_current_level(), False))
report["dirty_after"] = sorted(safe(lambda: [p.get_name() for p in
    unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()], []) or [])
report["ok"] = report["saved"] and not report["errors"] and not report["dirty_after"]
(OUT / "revert_light.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

print("revert ok=" + str(report["ok"]), "saved=" + str(report["saved"]),
      "dirty=" + str(report["dirty_after"]))
for r in report["reverted"]:
    print("  reverted", r["light"], r["property"], r["from"], "->", r["to"])
for s in report["skipped"]:
    print("  SKIPPED (not my value)", s)
print("  ppv", json.dumps(report["ppv"]))
for e in report["errors"]:
    print("  ERROR", e)
