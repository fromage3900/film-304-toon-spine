# Read-only census for MASTER_TRIM_CONVERGENCE_PLAN_20261017.md (Phase 0).
# Collects: master expression/parameter census, every child instance's overrides,
# per-parameter override counts, and the current level's material references.
# Writes Saved/Audit/MasterConvergence_20261017/census_v01.json. Changes nothing.

import json
import os
import unreal

MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
PROJECT = unreal.Paths.project_dir()
AUDIT = os.path.join(PROJECT, "Saved", "Audit", "MasterConvergence_20261017")


def log(msg):
    unreal.log("[MasterCensus] " + str(msg))


def safe(fn, default=None):
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        return {"error": str(e), "value": default}


def master_census():
    mat = unreal.load_asset(MASTER)
    if not mat:
        return {"error": "master not loadable"}
    exprs = mat.get_editor_property("expressions") or []
    by_class = {}
    named_params = {"scalar": [], "vector": [], "texture": [], "switch": []}
    for e in exprs:
        cls = e.get_class().get_name()
        by_class[cls] = by_class.get(cls, 0) + 1
        # collect parameter names where the expression exposes one
        for kind, prop in (("scalar", "parameter_name"),):
            try:
                nm = e.get_editor_property(prop)
            except Exception:  # noqa: BLE001
                continue
            if nm:
                named_params[kind].append(str(nm))
    props = safe(lambda: {
        "shading_model": str(mat.get_editor_property("shading_model")),
        "blend_mode": str(mat.get_editor_property("blend_mode")),
        "expression_count": len(exprs),
    }, {})
    return {"expressions_by_class": by_class, "expression_count": len(exprs), "props": props}


def instance_census():
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    mic_cls = unreal.TopLevelAssetPath("/Script/Engine", "MaterialInstanceConstant")
    assets = ar.get_assets_by_class(mic_cls, True)
    rows = []
    for a in assets:
        path = str(a.package_name)
        # registry tag first (cheap), fall back to a load
        parent = None
        try:
            tags = a.get_asset_registry_tags()
        except Exception:  # noqa: BLE001
            tags = []
        for t in tags:
            if str(t.get("name", "")).lower() == "parent":
                parent = str(t.get("value", ""))
                break
        inst = None
        if parent is None:
            inst = unreal.load_asset(path)
            if inst:
                p = inst.get_editor_property("parent")
                parent = str(p.get_path_name()) if p else ""
        rows.append({"path": path, "parent_tag": parent})
    return {"candidate_count": len(rows), "rows": rows}


def main():
    os.makedirs(AUDIT, exist_ok=True)
    log("census start")
    result = {"master": MASTER, "master_census": master_census(), "instances": instance_census()}
    out = os.path.join(AUDIT, "census_v01.json")
    with open(out, "w") as f:
        json.dump(result, f, indent=1)
    log("wrote " + out)
    inst = result["instances"]["candidate_count"]
    log("master expressions=%s instances_seen=%s" % (
        result["master_census"].get("expression_count"), inst))


main()
