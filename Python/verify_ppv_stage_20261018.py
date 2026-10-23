"""Verify + persist the single-writer PPV change, then A/B it visually.

Sequence: confirm one active volume -> save the level (dirty set was empty
before the change, so only this edit is persisted) -> screenshot the clean
single-writer frame -> re-enable the duplicate stack for one capture -> restore
-> confirm the on-disk state is the single-writer one.
"""
import json
from pathlib import Path
import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
OUT = Path(unreal.Paths.project_dir()) / "Saved/Audit/PPV"
OUT.mkdir(parents=True, exist_ok=True)
report = {"steps": [], "errors": [], "shots": {}}


def safe(fn, default=None):
    try:
        return fn()
    except Exception as exc:
        report["errors"].append(str(exc)[:180])
        return default


def volumes():
    out = {}
    for a in EAS.get_all_level_actors():
        if a.get_class().get_name() == "PostProcessVolume":
            out[safe(lambda: a.get_actor_label(), "?")] = a
    return out


def weights():
    return {k: safe(lambda a=a: a.get_editor_property("blend_weight"), None)
            for k, a in volumes().items()}


def dirty():
    return sorted(safe(lambda: [p.get_name() for p in
                                unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()], []) or [])


def shot(name):
    try:
        import claireon
        res = claireon.slate_screenshot(target="level_viewport", filename=name,
                                       directory=str(OUT))
        report["shots"][name] = res
        return True
    except Exception as exc:
        report["shots"][name] = "unavailable: " + str(exc)[:140]
        return False


world = safe(lambda: unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(), None)
report["world"] = world.get_path_name() if world else None
report["weights_before_save"] = weights()
report["dirty_before_save"] = dirty()

saved = bool(safe(lambda: unreal.EditorLoadingAndSavingUtils.save_current_level(), False))
report["saved"] = saved
report["dirty_after_save"] = dirty()
report["steps"].append({"save_current_level": saved, "dirty_after": report["dirty_after_save"]})

shot("ppv_single_writer_clean.png")

vols = volumes()
stack = vols.get("PPV_ToonOutlineHalftoneStack")
if stack is not None:
    stack.set_editor_property("blend_weight", 1.0)
    report["steps"].append({"ab": "duplicate stack re-enabled for one capture"})
    shot("ppv_double_stack_ab.png")
    stack.set_editor_property("blend_weight", 0.0)
    report["steps"].append({"ab": "restored to 0"})
else:
    report["errors"].append("PPV_ToonOutlineHalftoneStack missing for A/B")

report["weights_final"] = weights()
report["active_final"] = [k for k, v in report["weights_final"].items() if v and v > 0]
report["dirty_final"] = dirty()
report["ok"] = (saved and report["active_final"] == ["PPV_ToonOutlineClean"]
                and not report["dirty_final"])
(OUT / "verify_stage.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("ok=" + str(report["ok"]), "saved=" + str(saved),
      "active=" + str(report["active_final"]), "dirty_final=" + str(report["dirty_final"]))
for k, v in report["shots"].items():
    print(" shot", k, "->", v)
for e in report["errors"]:
    print(" ERROR", e)
