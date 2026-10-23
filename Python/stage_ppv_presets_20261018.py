"""Stage the single-writer PPV choice in the open level. Does NOT save the map.

Two volumes were active at BlendWeight 1 and both applied an outline
(PPV_StorybookOutline via MI_StorybookOutline_Render2026, and
PPV_ToonOutlineHalftoneStack via MI_Outline_Storybook), so every edge was
ininked twice. This keeps exactly one active volume.

Save is deliberately left to the owner: the editor may hold unrelated unsaved
work, and the repo rule is no Save All without checking dirty maps.
"""
import json
from pathlib import Path
import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
OUT = Path(unreal.Paths.project_dir()) / "Saved/Audit/PPV"
OUT.mkdir(parents=True, exist_ok=True)

# One active look. Clean is the hero default from the research note; the
# others stay present and staged at weight 0 so a shot can switch in one click.
TARGET = {
    "PPV_ToonOutlineClean": 1.0,
    "PPV_StorybookOutline": 0.0,
    "PPV_ToonOutlineHalftoneStack": 0.0,
    "PPV_ToonOutlineOnly": 0.0,
    "PPV_ToonOutlineRiso": 0.0,
    "PPV_P2_WatercolourPaper": 0.0,
    "PPV_P3_RisoPrint": 0.0,
    "PPV_P4_CleanCinematic": 0.0,
    "EST_PPV_Ink": 0.0,
}


def safe(fn, default=None):
    try:
        return fn()
    except Exception as exc:
        report["errors"].append(str(exc)[:160])
        return default


def dirty():
    return sorted(safe(lambda: [p.get_name() for p in
                                unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()], []) or [])


report = {"world": None, "before": [], "after": [], "dirty_before": [], "dirty_after": [],
          "errors": [], "saved": False}

world = safe(lambda: unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(), None)
report["world"] = world.get_path_name() if world else None
report["dirty_before"] = dirty()

for a in EAS.get_all_level_actors():
    label = safe(lambda: a.get_actor_label(), "")
    if a.get_class().get_name() != "PostProcessVolume":
        continue
    before = safe(lambda: a.get_editor_property("blend_weight"), None)
    report["before"].append({"label": label, "weight": before,
                             "priority": safe(lambda: a.get_editor_property("priority"), None)})
    if label in TARGET:
        a.set_editor_property("blend_weight", TARGET[label])
    elif before:
        # Unknown active volume: turn it off and name it, rather than silently
        # leaving a second writer in the stack.
        a.set_editor_property("blend_weight", 0.0)
        report["errors"].append("unknown active PPV dimmed: " + label)

for a in EAS.get_all_level_actors():
    if a.get_class().get_name() != "PostProcessVolume":
        continue
    label = safe(lambda: a.get_actor_label(), "")
    report["after"].append({"label": label,
                            "weight": safe(lambda: a.get_editor_property("blend_weight"), None),
                            "priority": safe(lambda: a.get_editor_property("priority"), None)})

report["dirty_after"] = dirty()
report["active"] = [r["label"] for r in report["after"] if r["weight"] and r["weight"] > 0]
report["ok"] = len(report["active"]) == 1 and report["active"][0] == "PPV_ToonOutlineClean"
(OUT / "stage_ppv.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

print("stage ok=" + str(report["ok"]) + " active=" + str(report["active"]))
print("dirty before:", report["dirty_before"])
print("dirty after :", report["dirty_after"])
for r in report["after"]:
    print("  ", r["label"], "w=", r["weight"], "pri=", r["priority"])
for e in report["errors"]:
    print("  ERROR", e)
