"""Inspect and audit material slots on Brutalist static meshes."""
import json
from pathlib import Path
import unreal

REPO = Path(__file__).resolve().parents[1]
OUT_JSON = REPO / "Saved" / "Audit" / "brutalist_materials_audit.json"

meshes = [
    "/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_TowerCluster",
    "/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_CivicSuperblock",
    "/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_TightEstate",
    "/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_LowSprawl",
    "/Game/Environment/Brutalist/02_CITY_KOMIKAZE/SM_KMZ_TowerCluster",
    "/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_BarbicanScale",
    "/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_SlenderTower",
    "/Game/Environment/Brutalist/05_FACADE_VARIATION/SM_FAC_TowerRibbon",
]

report = {}
for p in meshes:
    sm = unreal.load_asset(p)
    if not sm:
        report[p] = {"error": "failed to load"}
        continue
    mats = sm.get_editor_property("static_materials")
    slots = []
    for idx, smat in enumerate(mats):
        slot_name = str(smat.get_editor_property("material_slot_name"))
        mat_iface = smat.get_editor_property("material_interface")
        mat_name = mat_iface.get_name() if mat_iface else "None"
        mat_path = mat_iface.get_path_name() if mat_iface else "None"
        slots.append({
            "index": idx,
            "slot_name": slot_name,
            "material_name": mat_name,
            "material_path": mat_path,
        })
    report[sm.get_name()] = {
        "asset": p,
        "slot_count": len(mats),
        "slots": slots
    }

OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"[MAT_CHECK] Wrote {len(report)} mesh audits to {OUT_JSON}")
