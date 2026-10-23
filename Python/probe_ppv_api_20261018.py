"""Read-only capability + default probe for the PPV preset builder."""
import json
from pathlib import Path
import unreal

MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
OUT = Path(unreal.Paths.project_dir()) / "Saved/Audit/PPV"
OUT.mkdir(parents=True, exist_ok=True)

OUTLINE = "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Render2026/M_PP_StorybookOutline_Render2026"
POST = "/Game/Materials/Masters/M_Material_Toon_PostComposite_placeholder"
POST = "/Game/Materials/Masters/M_Master_Toon_PostComposite"

outline_scalars = [
    "OutlineWidth", "MinWidthPx", "MaxWidthPx", "AAWidth", "RefDistance",
    "TaperStrength", "DistanceFadeStart", "DistanceFadeEnd", "DistanceFadeStrength",
    "DepthWeight", "DepthRelativeThreshold", "NormalWeight", "InkBlurRadius",
    "InkBlurStrength", "EdgeStrength", "CreaseThreshold", "SceneExposureEV",
    "JitterCompensation", "StenciRangeMin", "StenciRangeMax", "Stencilndex",
    "StencilCharacterWeight", "StencilPropWeight", "StencilFoliageWeight",
    "HalftoneAmount", "HalftoneAngle", "HalftoneScale",
]
post_scalars = ["FilmContrast", "FilmWarmth", "FilmSaturation", "GrainStrength",
                "GrainScale", "VignetteStrength", "HalftoneStrength", "HalftoneScale"]
post_vectors = ["GradeTint", "FilmLift"]

report = {"api": {}, "defaults": {}, "references": {}, "errors": []}


def safe(fn, default=None):
    try:
        return fn()
    except Exception as exc:
        report["errors"].append(str(exc)[:160])
        return default


for name in ("clear_all_material_instance_parameters",
             "set_material_instance_scalar_parameter_value",
             "set_material_instance_vector_parameter_value",
             "set_material_instance_static_switch_parameter_value",
             "get_material_default_scalar_parameter_value",
             "get_material_default_vector_parameter_value"):
    report["api"][name] = hasattr(MEL, name)

om = safe(lambda: unreal.load_asset(OUTLINE), None)
pm = safe(lambda: unreal.load_asset(POST), None)
report["defaults"]["outline_loaded"] = om is not None
report["defaults"]["post_loaded"] = pm is not None
if om is not None:
    report["defaults"]["outline"] = {
        s: safe(lambda s=s: float(MEL.get_material_default_scalar_parameter_value(om, s)), None)
        for s in outline_scalars}
    report["defaults"]["outline_switch"] = {
        "IncludeStencilInRange": safe(lambda: bool(
            MEL.get_material_default_static_switch_parameter_value(om, "IncludeStencilInRange")), None)}
if pm is not None:
    report["defaults"]["post"] = {
        s: safe(lambda s=s: float(MEL.get_material_default_scalar_parameter_value(pm, s)), None)
        for s in post_scalars}
    report["defaults"]["post_vectors"] = {}
    for s in post_vectors:
        v = safe(lambda s=s: MEL.get_material_default_vector_parameter_value(pm, s), None)
        report["defaults"]["post_vectors"][s] = [v.r, v.g, v.b, v.a] if v else None

stub = "/Game/SK_David_Film304_v01_CtrlRig_Take1"
report["references"]["stub_exists"] = safe(
    lambda: EAL.does_asset_exist(stub), None)
report["references"]["stub_referencers"] = safe(
    lambda: [str(r) for r in EAL.find_package_referencers_for_asset(stub)], None)

(OUT / "capability.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
