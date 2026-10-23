"""Compare the root wiring and shading model between original Universal and Film304 v06."""
import json
from pathlib import Path
import unreal

REPO = Path(__file__).resolve().parents[1]
OUT_FILE = REPO / "Saved" / "Audit" / "master_comparison_audit.json"

ORIGINAL = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
FILM_V06 = "/Game/Materials/Masters/Film304/M_UniversalToon_Film304_v06"

report = {}

for path in [ORIGINAL, FILM_V06]:
    mat = unreal.load_asset(path)
    if not mat:
        report[path] = {"error": "not found"}
        continue
    
    props = {
        "shading_model": str(mat.get_editor_property("shading_model")),
        "blend_mode": str(mat.get_editor_property("blend_mode")),
        "two_sided": bool(mat.get_editor_property("two_sided")),
        "used_with_skeletal_mesh": bool(mat.get_editor_property("used_with_skeletal_mesh")),
    }
    try:
        props["toon_profile"] = str(mat.get_editor_property("toon_profile"))
    except Exception as e:
        props["toon_profile"] = f"error: {e}"
        
    try:
        props["substrate"] = bool(mat.get_editor_property("substrate"))
    except Exception:
        pass
        
    report[path] = props

OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
OUT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(f"Wrote comparison to {OUT_FILE}")
