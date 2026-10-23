"""Apply a clean film Toon Profile to an isolated duplicate of Universal Toon.

The source Universal master is never edited. This script expects the destination
to have been created with the editor's native material-duplicate action and
changes only its root Substrate Toon BSDF profile.
"""
from pathlib import Path
import json
import unreal


SOURCE_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
VARIANT_PATH = "/Game/Materials/Masters/OneDriveRigs_20261016/M_Master_UniversalToon_DanaFilmClean_20261016"
PROFILE_PATH = "/Game/Materials/ToonProfiles/TP_DanaFilm_Clean"
REPORT_PATH = Path(unreal.Paths.project_dir()) / "Saved/Audit/OneDriveRigs_20261016/universal_profile_variant.json"

EAL = unreal.EditorAssetLibrary
ME = unreal.MaterialEditingLibrary


def load_required(path: str):
    asset = EAL.load_asset(path)
    if asset is None:
        raise RuntimeError("Required material asset is missing: " + path)
    return asset


def toon_nodes(material):
    return [node for node in (ME.get_material_expressions(material) or [])
            if type(node).__name__ == "MaterialExpressionSubstrateToonBSDF"]


def profile_path(node) -> str:
    profile = node.get_editor_property("toon_profile")
    return profile.get_path_name().split(".")[0] if profile else ""


def main() -> None:
    source = load_required(SOURCE_PATH)
    variant = load_required(VARIANT_PATH)
    profile = load_required(PROFILE_PATH)

    source_expressions = ME.get_material_expressions(source) or []
    variant_expressions = ME.get_material_expressions(variant) or []
    source_calls = [n for n in source_expressions
                    if type(n).__name__ == "MaterialExpressionMaterialFunctionCall"]
    variant_calls = [n for n in variant_expressions
                     if type(n).__name__ == "MaterialExpressionMaterialFunctionCall"]
    source_toon = toon_nodes(source)
    variant_toon = toon_nodes(variant)
    if len(source_expressions) != 1303 or len(variant_expressions) != 1303:
        raise RuntimeError("Universal graph expression count changed; expected 1303 on both assets")
    if len(source_calls) != 16 or len(variant_calls) != 16:
        raise RuntimeError("Universal graph function-call count changed; expected 16 on both assets")
    if len(source_toon) != 1 or len(variant_toon) != 1:
        raise RuntimeError("Expected exactly one root Substrate Toon BSDF in each material")

    source_profile = profile_path(source_toon[0])
    before_profile = profile_path(variant_toon[0])
    if before_profile == SOURCE_PATH:
        raise RuntimeError("Variant Toon Profile unexpectedly points at a material path")
    if before_profile not in (source_profile, PROFILE_PATH):
        raise RuntimeError("Variant profile is neither the copied source profile nor the requested clean profile")

    if before_profile != PROFILE_PATH:
        variant.modify()
        variant_toon[0].modify()
        variant_toon[0].set_editor_property("toon_profile", profile)
        if profile_path(variant_toon[0]) != PROFILE_PATH:
            raise RuntimeError("Clean Toon Profile did not persist on the variant")
        ME.recompile_material(variant)
        if not EAL.save_loaded_asset(variant, only_if_is_dirty=False):
            raise RuntimeError("Could not save the isolated material variant")

    result = {
        "status": "profile_variant_created_pending_dependency_audit",
        "source_path": SOURCE_PATH,
        "variant_path": VARIANT_PATH,
        "source_profile": source_profile,
        "variant_profile_before": before_profile,
        "variant_profile_after": profile_path(variant_toon[0]),
        "profile_override_only": True,
        "source_modified": False,
        "expression_count_source": len(source_expressions),
        "expression_count_variant": len(variant_expressions),
        "function_call_count_source": len(source_calls),
        "function_call_count_variant": len(variant_calls),
        "source_only_reported_by_editor": True,
        "note": "Graph parity and compiled readback must be confirmed through Monolith; this copy retains the source graph's existing texture dependencies.",
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.log("Universal Toon clean profile variant: %s" % str(REPORT_PATH))


main()
