"""Build the film PPV preset ladder from specs/film304_look/ppv_presets.v1.json.

Assets only: no actor, level or map change.

Existing MI_* whose name matches a preset id are rebuilt in place --
clear_all_material_instance_parameters() runs first, so the stale
BaseTint / PaletteRamp* / Cloth_* overrides left behind by a reparent are
removed rather than merely overwritten. That is why MI_Composite_Dither's
grain was 0.85 and nothing could change it from the editor.
"""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
SPEC_PATH = ROOT / "specs/film304_look/ppv_presets.v1.json"
OUT = ROOT / "Saved/Audit/PPV"
OUT.mkdir(parents=True, exist_ok=True)
MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()

spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
report = {"spec": str(SPEC_PATH), "built": [], "readback": [], "widths": [],
          "heavy_outline": {}, "errors": []}


def safe(fn, default=None):
    try:
        return fn()
    except Exception as exc:
        report["errors"].append(str(exc)[:200])
        return default


def get_or_create(folder, name, parent):
    path = folder + "/" + name
    if EAL.does_asset_exist(path):
        mi = unreal.load_asset(path)
        if mi is None:
            raise RuntimeError("loaded None: " + path)
        if mi.get_editor_property("parent") != parent:
            MEL.set_material_instance_parent(mi, parent)
        return mi, "updated"
    mi = AT.create_asset(name, folder, unreal.MaterialInstanceConstant,
                         unreal.MaterialInstanceConstantFactoryNew())
    if mi is None:
        raise RuntimeError("create_asset failed: " + path)
    MEL.set_material_instance_parent(mi, parent)
    return mi, "created"


def apply(mi, block):
    MEL.clear_all_material_instance_parameters(mi)
    for k, v in block.get("scalars", {}).items():
        MEL.set_material_instance_scalar_parameter_value(mi, k, float(v))
    for k, v in block.get("vectors", {}).items():
        MEL.set_material_instance_vector_parameter_value(mi, k, unreal.LinearColor(*v))
    for k, v in block.get("switch", {}).items():
        MEL.set_material_instance_static_switch_parameter_value(mi, k, bool(v))
    MEL.update_material_instance(mi)


def width_px(o, d):
    """Same arithmetic as the compiled shader, so the report can prove intent.

    The shader's round() is GPU round-half-away-from-zero; Python's round() is
    banker's rounding, so use floor(x + 0.5) to match it exactly.
    """
    w = (max(o["OutlineWidth"], 0.0001) * (o["RefDistance"] / max(d, 1.0))
         * max(o.get("InkBlurRadius", 1.0), 0.05))
    w = min(max(w, max(o["MinWidthPx"], 1.0)), max(o["MaxWidthPx"], 0.5))
    return max(int(w + 0.5), 1)


def read_vector(mi, name):
    fn = getattr(MEL, "get_material_instance_vector_parameter_value", None)
    if fn is not None:
        v = safe(lambda: fn(mi, name), None)
        if v is not None:
            return [v.r, v.g, v.b, v.a]
    for e in safe(lambda: mi.get_editor_property("vector_parameter_values"), []) or []:
        info = safe(lambda e=e: e.get_editor_property("parameter_info"), None)
        pn = safe(lambda: str(info.get_editor_property("name")), None)
        if pn == name:
            v = safe(lambda: e.get_editor_property("parameter_value"), None)
            if v is not None:
                return [v.r, v.g, v.b, v.a]
    return None


def verify(mi, block, label):
    row = {"asset": mi.get_path_name(), "checked": 0, "mismatch": []}
    for k, v in block.get("scalars", {}).items():
        got = safe(lambda k=k: MEL.get_material_instance_scalar_parameter_value(mi, k), None)
        row["checked"] += 1
        if got is None or abs(float(got) - float(v)) > 1e-3:
            row["mismatch"].append({k: [v, got]})
    for k, v in block.get("vectors", {}).items():
        got = read_vector(mi, k)
        row["checked"] += 1
        if got is None:
            row["mismatch"].append({k: [v, None]})
        else:
            delta = max(abs(a - b) for a, b in zip(got, v))
            if delta > 1e-3:
                row["mismatch"].append({k: [v, got]})
    for k, v in block.get("switch", {}).items():
        got = safe(lambda k=k: MEL.get_material_instance_static_switch_parameter_value(mi, k), None)
        row["checked"] += 1
        if got is None or bool(got) != bool(v):
            row["mismatch"].append({k: [v, got]})
    row["ok"] = not row["mismatch"]
    if not row["ok"]:
        report["errors"].append(label + " readback mismatch: " + json.dumps(row["mismatch"]))
    report["readback"].append(row)

outline_parent = unreal.load_asset(spec["masters"]["outline"])
composite_parent = unreal.load_asset(spec["masters"]["composite"])
if outline_parent is None or composite_parent is None:
    raise RuntimeError("a preset master did not load: " + json.dumps(spec["masters"]))

outline_dir = spec["destinations"]["outline"]
composite_dir = spec["destinations"]["composite"]

for preset in spec["presets"]:
    pid = preset["id"]
    try:
        om, ostate = get_or_create(outline_dir, "MI_Outline_" + pid, outline_parent)
        apply(om, preset["outline"])
        saved = bool(EAL.save_loaded_asset(om, only_if_is_dirty=False))
        reloaded = unreal.load_asset(om.get_path_name())
        verify(reloaded, preset["outline"], "MI_Outline_" + pid)
        report["built"].append({"preset": pid, "asset": om.get_path_name(),
                                "state": ostate, "saved": saved,
                                "parent_ok": reloaded.get_editor_property("parent") == outline_parent})
        for d in (200.0, 600.0, 1500.0, 4000.0, 8000.0, 20000.0):
            report["widths"].append({"preset": pid, "distance_cm": d,
                                     "width_px": width_px(preset["outline"]["scalars"], d)})
    except Exception as exc:  # noqa: BLE001
        report["errors"].append("outline " + pid + ": " + str(exc)[:200])

    try:
        cm, cstate = get_or_create(composite_dir, "MI_Composite_" + pid, composite_parent)
        apply(cm, preset["composite"])
        saved = bool(EAL.save_loaded_asset(cm, only_if_is_dirty=False))
        reloaded = unreal.load_asset(cm.get_path_name())
        verify(reloaded, preset["composite"], "MI_Composite_" + pid)
        report["built"].append({"preset": pid, "asset": cm.get_path_name(),
                                "state": cstate, "saved": saved,
                                "parent_ok": reloaded.get_editor_property("parent") == composite_parent})
    except Exception as exc:  # noqa: BLE001
        report["errors"].append("composite " + pid + ": " + str(exc)[:200])

# MI_Outline_Heavy lost its parent (audit: parent=None), which makes the MRQ
# gate item "outlines present and weighted correctly" false for architecture.
try:
    heavy = unreal.load_asset("/Game/Materials/Instances/MI_Outline_Heavy")
    hull = unreal.load_asset("/Game/Materials/Masters/M_Outline_InvertedHull")
    if heavy is None or hull is None:
        report["heavy_outline"] = {"ok": False, "why": "asset missing"}
    else:
        before_t = safe(lambda: MEL.get_material_instance_scalar_parameter_value(heavy, "Thickness"), None)
        before_c = safe(lambda: MEL.get_material_instance_vector_parameter_value(heavy, "InkColor"), None)
        MEL.set_material_instance_parent(heavy, hull)
        MEL.set_material_instance_scalar_parameter_value(heavy, "Thickness", 0.02)
        MEL.set_material_instance_scalar_parameter_value(heavy, "ThicknessScale", 1.6)
        MEL.set_material_instance_vector_parameter_value(
            heavy, "InkColor", unreal.LinearColor(0.02, 0.02, 0.04, 1.0))
        MEL.update_material_instance(heavy)
        ok = bool(EAL.save_loaded_asset(heavy, only_if_is_dirty=False))
        rl = unreal.load_asset("/Game/Materials/Instances/MI_Outline_Heavy")
        report["heavy_outline"] = {
            "ok": rl.get_editor_property("parent") == hull and ok,
            "before_Thickness": before_t,
            "after_parent": str(rl.get_editor_property("parent")),
            "Thickness": MEL.get_material_instance_scalar_parameter_value(rl, "Thickness"),
            "ThicknessScale": MEL.get_material_instance_scalar_parameter_value(rl, "ThicknessScale"),
        }
except Exception as exc:  # noqa: BLE001
    report["errors"].append("heavy outline: " + str(exc)[:200])

report["ok"] = (not report["errors"]
                and all(r["ok"] for r in report["readback"])
                and all(b["parent_ok"] for b in report["built"]))
(OUT / "preset_build.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

print("preset build ok=" + str(report["ok"]) + " built=" + str(len(report["built"]))
      + " readback=" + str(len(report["readback"]))
      + " errors=" + str(len(report["errors"])))
for b in report["built"]:
    print(" ", b["state"], b["asset"], "parent_ok=", b["parent_ok"])
for r in report["readback"]:
    print("  verify", r["asset"].split("/")[-1], "ok=", r["ok"], r["mismatch"] or "")
for e in report["errors"]:
    print("  ERROR", e)
print("heavy:", json.dumps(report["heavy_outline"]))
for w in report["widths"]:
    if w["preset"] in ("Clean", "Storybook", "SpiderMacro"):
        print("  width", w["preset"], "at", int(w["distance_cm"]), "cm =", w["width_px"], "px")

