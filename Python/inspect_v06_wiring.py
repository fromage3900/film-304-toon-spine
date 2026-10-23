"""Inspect texture samples and wiring on M_UniversalToon_Film304_v06."""
import json
from pathlib import Path
import unreal

REPO = Path(__file__).resolve().parents[1]
MAT_PATH = "/Game/Materials/Masters/Film304/M_UniversalToon_Film304_v06"
OUT_FILE = REPO / "Saved" / "Audit" / "film304_v06_wiring_audit.json"

mat = unreal.load_asset(MAT_PATH)
if not mat:
    raise RuntimeError(f"Could not load {MAT_PATH}")

me = unreal.MaterialEditingLibrary
nodes = list(me.get_material_expressions(mat))

report = {
    "material": MAT_PATH,
    "expression_count": len(nodes),
    "null_texture_samples": [],
    "island_expressions": [],
    "root_inputs": {},
}

for node in nodes:
    name = node.get_name()
    cname = node.get_class().get_name()
    
    # Check texture on texture samples
    if hasattr(node, "get_editor_property"):
        try:
            if "texture" in [p.get_name() for p in node.get_class().get_properties()]:
                tex = node.get_editor_property("texture")
                if tex is None:
                    param_name = ""
                    try:
                        param_name = str(node.get_editor_property("parameter_name"))
                    except Exception:
                        pass
                    report["null_texture_samples"].append({
                        "node": name,
                        "class": cname,
                        "parameter_name": param_name,
                    })
        except Exception:
            pass

# Check inputs of the material itself (Root Node)
prop_names = ["base_color", "metallic", "roughness", "normal", "emissive_color", 
              "opacity", "opacity_mask", "anisotropy", "ambient_occlusion"]
for p in prop_names:
    try:
        expr = mat.get_editor_property(p)
        if expr:
            report["root_inputs"][p] = str(expr)
    except Exception:
        pass

OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
OUT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(f"Wrote wiring audit to {OUT_FILE}")
