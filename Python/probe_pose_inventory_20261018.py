"""Read-only inventory of pose / control-rig assets that actually exist."""
import json
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
OUT = Path(unreal.Paths.project_dir()) / "Saved/Audit/Poses"
OUT.mkdir(parents=True, exist_ok=True)

ROOTS = [
    "/Game/Staging/Film304Repaired_20261017",
    "/Game/Animations",
    "/Game/Rigs/Film304",
]
report = {"roots": {}, "poses": [], "rigs": [], "errors": []}


def safe(fn, default=None):
    try:
        return fn()
    except Exception as exc:
        report["errors"].append(str(exc)[:160])
        return default


for root in ROOTS:
    assets = safe(lambda r=root: [str(a) for a in EAL.list_assets(r, recursive=True)], []) or []
    report["roots"][root] = len(assets)
    for a in assets:
        name = a.split("/")[-1].split(".")[0]
        if name.startswith("AS_"):
            row = {"path": a.split(".")[0], "name": name}
            anim = safe(lambda p=a: unreal.load_asset(p), None)
            if anim is not None:
                row["class"] = type(anim).__name__
                row["length_s"] = safe(lambda: float(anim.get_play_length()), None)
                row["num_keys"] = safe(
                    lambda: int(unreal.AnimationLibrary.get_num_keys(anim))
                    if hasattr(unreal, "AnimationLibrary") else None, None)
            report["poses"].append(row)
        elif name.startswith("CR_"):
            report["rigs"].append({"path": a.split(".")[0], "name": name})

report["pose_count"] = len(report["poses"])
report["rig_count"] = len(report["rigs"])
(OUT / "inventory.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"roots": report["roots"], "poses": report["poses"],
                  "rigs": report["rigs"], "errors": report["errors"]}, indent=2))
