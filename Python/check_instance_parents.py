"""Check parents and key parameter values for building & environment instances."""
import json
from pathlib import Path
import unreal

REPO = Path(__file__).resolve().parents[1]
OUT_FILE = REPO / "Saved" / "Audit" / "instance_parent_audit.json"

instances = [
    "/Game/Materials/Instances/MI_Concrete",
    "/Game/Materials/Instances/MI_Toon_Environment",
    "/Game/Materials/Instances/MI_Toon_Glass",
    "/Game/Materials/Instances/MI_Toon_Stone",
    "/Game/Materials/Instances/Film304/MI_Film304_Toon",
]

report = {}
me = unreal.MaterialEditingLibrary

for inst_path in instances:
    mi = unreal.load_asset(inst_path)
    if not mi:
        report[inst_path] = {"error": "not found"}
        continue
    parent = mi.get_editor_property("parent")
    parent_path = parent.get_path_name() if parent else "None"
    
    # Query key toon parameters
    params = {}
    for p in ["RampStrength", "TextureWeight", "Roughness", "Metallic", "bUsePaintedRamp"]:
        try:
            if p.startswith("b"):
                val = me.get_material_instance_static_switch_parameter_value(mi, p)
            else:
                val = me.get_material_instance_scalar_parameter_value(mi, p)
            params[p] = val
        except Exception as e:
            params[p] = f"error: {e}"
            
    report[inst_path] = {
        "parent": parent_path,
        "parameters": params
    }

OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
OUT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(f"Wrote audit to {OUT_FILE}")
