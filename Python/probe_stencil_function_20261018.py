"""Read-only dump of MF_StencilDepthAlpha so preset values are grounded."""
import json
from pathlib import Path
import unreal

MEL = unreal.MaterialEditingLibrary
OUT = Path(unreal.Paths.project_dir()) / "Saved/Audit/PPV"
OUT.mkdir(parents=True, exist_ok=True)

CANDIDATES = [
    "/Game/ArtOfShader/Common/MaterialFunctions/MF_StencilDepthAlpha",
    "/Game/Materials/Functions/Film304/MF_StencilDepthAlpha",
]

report = {"loaded": None, "expressions": [], "custom_code": [], "errors": []}


def safe(fn, default=None):
    try:
        return fn()
    except Exception as exc:
        report["errors"].append(str(exc)[:160])
        return default


mf = None
for path in CANDIDATES:
    obj = safe(lambda p=path: unreal.load_asset(p), None)
    if obj is not None:
        mf = obj
        report["loaded"] = path
        break

if mf is not None:
    exprs = safe(lambda: MEL.get_material_expressions(mf), []) or []
    for e in exprs:
        row = {"class": type(e).__name__,
               "desc": safe(lambda: str(e.get_editor_property("desc")), None),
               "name": safe(lambda: str(e.get_editor_property("parameter_name")), None)}
        report["expressions"].append(row)
        if "Custom" in row["class"]:
            code = safe(lambda: str(e.get_editor_property("code")), None)
            inputs = safe(lambda: [str(n) for n in
                                   MEL.get_material_expression_input_names(e)], [])
            report["custom_code"].append({"desc": row["desc"], "inputs": inputs,
                                          "code": code})
    try:
        report["inputs"] = [str(n) for n in MEL.get_material_function_input_names(mf)]
    except Exception as exc:
        report["errors"].append("inputs: " + str(exc)[:120])
    try:
        report["outputs"] = [str(n) for n in MEL.get_material_function_output_names(mf)]
    except Exception as exc:
        report["errors"].append("outputs: " + str(exc)[:120])

(OUT / "stencil_function.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"loaded": report["loaded"],
                  "inputs": report.get("inputs"),
                  "outputs": report.get("outputs"),
                  "expressions": report["expressions"],
                  "custom": [(c["desc"], c["inputs"]) for c in report["custom_code"]],
                  "errors": report["errors"]}, indent=2))
for c in report["custom_code"]:
    print("----", c["desc"])
    print(c["code"])
