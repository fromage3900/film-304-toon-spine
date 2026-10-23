# Trim, take 2 (2026-10-17). One clean sequence from a fresh duplicate of the
# original master.
#
# Order is the fix for the dangling-input errors seen in take 1: the Melodia
# features live in shared material functions (MF_Madoka 280 exprs, MF_Itto 206,
# MF_MeshBlend 7). Deleting those CALL NODES first removes the whole feature
# subgraph intact, so the feature parameters then become ordinary orphans that
# the sweep can remove -- nothing is ever left referencing a deleted input.

import json
import os
import unreal

SOURCE = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
MAT = "/Game/Materials/Masters/Film/M_Film_Toon_Universal_Trimmed"
AUDIT = unreal.Paths.project_dir() + "Saved/Audit/MasterConvergence_20261017/"
DROP_FUNCTIONS = ("MF_Madoka", "MF_Itto", "MF_MeshBlend_Activator")

# Melodia CONTENT features only. Everything reusable (AutoBlend, Stack2/3,
# LayerB/C, Parallax, Triplanar, fabric/sheen, cloth wind, boil/smear/temporal,
# distance fade, dither dissolve, wetness, iridescence, grazing rim) is kept.
DROP_PARAMS = set("""SparkleScale SparkleIntensity SparkleThreshold SparkleContrast
SparkleDriftSpeed SparkleTwinkleSpeed SparkleColorLerp ConstellationStrength ConstellationScale
CelestialStarIntensity CelestialNebulaStrength CelestialNebulaScale CelestialGalaxyStrength
CelestialGalaxyScale CelestialToonSteps GildingStrength GildingAmount GoldRoughness
ShadowFlowerStrength ShadowFlowerScale FairyMotifStyle FairyDustIntensity FairyDustScale
FairyHighlightThreshold MagicalTransform MotifScale TransformGlow WipeSoftness ElementType
ElementStrength ElementEmissiveBoost TimeOfDayWarmth TimeOfDayMPCStrength SnowDustStrength
SnowUpBias MossConcavityStrength MossCurvatureSens ContactRimStrength ContactRimPower
MadokaBlendAmount IttoBlendAmount WitchBarrierWallpaperScale MadokaGlowAmount MadokaVeinEmissive
MadokaCuteBias MadokaEmissiveBrightness MadokaRadialBands MadokaAudioReactiveAmount
MadokaRealityWarp IttoPatternScale IttoCrackDepth IttoWearAmount IttoBreakupAmount
IttoInkStrength IttoSpiralIntensity DreamBloomThreshold DreamBloomStrength DreamFlowStrength
DreamFlowSpeed DreamFlowScale DreamFlowCycles DreamPulseAmp DreamPulseSpeed SigilStrength
SigilSides SigilRings SigilSpeed SigilSharp SigilCycles DawnStrength DawnHeightScale DawnBias
MistStrength MistScale MistSpeed MistSharp GlintStrength GlintScale GlintSize GlintSharp
GlintSpeed DFContactBlendDistance DFContactBlendSharpness DFContactBlendStrength
DFContactNoiseBreakup DFContactNoiseScale DFContactWorldPositionOffset DFContactGroundHeight
DFContactHeightFalloff DFContactRoughness SDF_SeamBlendDistance SDF_SeamBlendSharpness
SDF_SeamBlendNoiseScale SDF_SeamBlendNoiseBreakup SDF_SeamBlendStrength IOR Dispersion
GemstoneRoughness GlintIntensity DreamComposition DreamThreshold ChladniScale SparkleColor
SparkleColorLow SparkleColorHigh GoldTint GoldEmissive ShadowFlowerColor FairyDustColor
MotifColor SnowDustColor MossColor ContactRimColor MadokaRampLow MadokaRampMid MadokaRampHigh
IttoRampLow IttoRampHigh DreamBloomColor DawnLowColor DawnHighColor MistColor GlintColor
DFContactTint GemstoneTint ChladniColor SparkleMask StarMap FairyGlyphMask MotifMask ChladniMask
UseUDSTimeOfDay bWeather_Active bElemental_Active bCelestial_Active bCelestialUsesDreamPalette
bFairyDust_Active bSparkleAdvanced bGemstone_Active bGemstone_Active_LEGACY
bDFContactBlend_Active bMeshBlendActivator_Active""".split())


def log(m):
    unreal.log("[TrimTake2] " + str(m))


def prop(o, n):
    try:
        return o.get_editor_property(n)
    except Exception:                                        # noqa: BLE001
        return None


def main():
    lib = unreal.MaterialEditingLibrary

    if unreal.EditorAssetLibrary.does_asset_exist(MAT):
        unreal.EditorAssetLibrary.delete_asset(MAT)
    if not unreal.EditorAssetLibrary.duplicate_asset(SOURCE, MAT):
        raise RuntimeError("duplicate failed")
    mat = unreal.load_asset(MAT)
    if mat is None:
        raise RuntimeError("cannot load " + MAT)
    n0 = lib.get_num_material_expressions(mat)
    log("duplicate ok, %d expressions" % n0)

    # --- step 1: remove the Melodia content function calls (whole subgraphs)
    calls_deleted = []
    for e in list(lib.get_material_expressions(mat)):
        if "FunctionCall" not in e.get_class().get_name():
            continue
        fn = prop(e, "material_function")
        path = str(fn.get_path_name()) if fn else ""
        if any(d in path for d in DROP_FUNCTIONS):
            try:
                lib.delete_material_expression(mat, e)
                calls_deleted.append(path.split("/")[-1])
            except Exception as exc:                         # noqa: BLE001
                log("function call delete failed %s: %s" % (path, exc))
    log("function calls deleted: %s" % calls_deleted)

    # --- step 2: remove the Melodia content parameters (now orphans)
    params_deleted, failed = [], []
    for e in list(lib.get_material_expressions(mat)):
        nm = prop(e, "parameter_name")
        if nm and str(nm) in DROP_PARAMS:
            try:
                lib.delete_material_expression(mat, e)
                params_deleted.append(str(nm))
            except Exception as exc:                         # noqa: BLE001
                failed.append("%s: %s" % (nm, exc))
    log("parameters deleted: %d (failures %d)" % (len(params_deleted), len(failed)))

    # --- step 3: sweep, recompile, and repeat the sweep while it makes progress
    for i in range(6):
        before = lib.get_num_material_expressions(mat)
        try:
            lib.delete_unused_expressions(mat)
        except Exception as exc:                             # noqa: BLE001
            log("sweep failed: %s" % exc)
            break
        after = lib.get_num_material_expressions(mat)
        log("sweep %d: %d -> %d" % (i, before, after))
        if after == before:
            break
    try:
        lib.recompile_material(mat)
    except Exception as exc:                                 # noqa: BLE001
        log("recompile failed: %s" % exc)

    n1 = lib.get_num_material_expressions(mat)
    record = {"take": 2, "asset": MAT, "expressions_before": n0,
              "expressions_after": n1, "function_calls_deleted": calls_deleted,
              "parameters_deleted": len(params_deleted), "failures": failed,
              "deleted_param_names": sorted(set(params_deleted))}
    with open(AUDIT + "trim_take2.json", "w") as f:
        json.dump(record, f, indent=1)
    log("wrote trim_take2.json; final=%d expressions" % n1)


main()
