"""Read-only: full scalar/vector defaults for the outline master."""
import json
from pathlib import Path
import unreal

MEL = unreal.MaterialEditingLibrary
OUT = Path(unreal.Paths.project_dir()) / "Saved/Audit/PPV"
OUT.mkdir(parents=True, exist_ok=True)
P = "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Render2026/M_PP_StorybookOutline_Render2026"

scalars = ["OutlineWidth", "MinWidthPx", "MaxWidthPx", "AAWidth", "RefDistance",
           "TaperStrength", "FalloffStart", "FalloffEnd", "SkyDepth",
           "InkBlurRadius", "InkBlurStrength", "DepthRelativeThreshold",
           "MultiplyDarken", "UseMultiplyTintAmount", "UDSTintStrength",
           "FoliageDistanceFadeStart", "FoliageDistanceFadeEnd",
           "FoliageDepthInkStrength", "FoliageNormalInkStrength",
           "CreaseThreshold", "HalftoneAmount", "HalftoneAngle", "HalftoneScale"]
vectors = ["OutlineColor", "OutlineColorNight", "CreaseColor",
           "AtmosphericFadeColor", "Style1Color", "Style2Color", "Style3Color",
           "UDSTint"]

report = {"path": P, "scalars": {}, "vectors": {}, "switch": {}, "errors": []}


def safe(fn, default=None):
    try:
        return fn()
    except Exception as exc:
        report["errors"].append(str(exc)[:140])
        return default


m = safe(lambda: unreal.load_asset(P), None)
report["loaded"] = m is not None
if m is not None:
    for s in scalars:
        report["scalars"][s] = safe(
            lambda s=s: round(float(MEL.get_material_default_scalar_parameter_value(m, s)), 4), None)
    for s in vectors:
        v = safe(lambda s=s: MEL.get_material_default_vector_parameter_value(m, s), None)
        report["vectors"][s] = [round(x, 4) for x in (v.r, v.g, v.b, v.a)] if v else None
    report["switch"]["IncludeStencilInRange"] = safe(
        lambda: bool(MEL.get_material_default_static_switch_parameter_value(
            m, "IncludeStencilInRange")), None)

(OUT / "outline_defaults.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
