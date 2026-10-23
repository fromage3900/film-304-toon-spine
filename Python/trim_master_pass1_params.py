# Pass 1 of the Universal-master trim (2026-10-17).
# Deletes the Melodia CONTENT feature parameter expressions from
# M_Film_Toon_Universal_Trimmed. General material capability is kept.
# Driven by an explicit parameter-name list computed from the live asset,
# so nothing reusable is caught by a loose prefix rule.

import json
import os
import unreal

MAT = "/Game/Materials/Masters/Film/M_Film_Toon_Universal_Trimmed"
PROJECT = unreal.Paths.project_dir()
AUDIT = os.path.join(PROJECT, "Saved", "Audit", "MasterConvergence_20261017")

DROP = set("""SparkleScale SparkleIntensity SparkleThreshold SparkleContrast SparkleDriftSpeed
SparkleTwinkleSpeed SparkleColorLerp ConstellationStrength ConstellationScale
CelestialStarIntensity CelestialNebulaStrength CelestialNebulaScale CelestialGalaxyStrength
CelestialGalaxyScale CelestialToonSteps GildingStrength GoldRoughness ShadowFlowerStrength
ShadowFlowerScale FairyMotifStyle FairyDustIntensity FairyDustScale FairyHighlightThreshold
MagicalTransform MotifScale TransformGlow WipeSoftness ElementType ElementStrength
ElementEmissiveBoost TimeOfDayWarmth TimeOfDayMPCStrength SnowDustStrength SnowUpBias
MossConcavityStrength MossCurvatureSens ContactRimStrength ContactRimPower MadokaBlendAmount
IttoBlendAmount WitchBarrierWallpaperScale MadokaGlowAmount MadokaVeinEmissive MadokaCuteBias
MadokaEmissiveBrightness MadokaRadialBands MadokaAudioReactiveAmount MadokaRealityWarp
IttoPatternScale IttoCrackDepth IttoWearAmount IttoBreakupAmount IttoInkStrength
IttoSpiralIntensity DreamBloomThreshold DreamBloomStrength DreamFlowStrength DreamFlowSpeed
DreamFlowScale DreamFlowCycles DreamPulseAmp DreamPulseSpeed SigilStrength SigilSides
SigilRings SigilSpeed SigilSharp SigilCycles DawnStrength DawnHeightScale DawnBias MistStrength
MistScale MistSpeed MistSharp GlintStrength GlintScale GlintSize GlintSharp GlintSpeed
DFContactBlendDistance DFContactBlendSharpness DFContactBlendStrength DFContactNoiseBreakup
DFContactNoiseScale DFContactWorldPositionOffset DFContactGroundHeight DFContactHeightFalloff
DFContactRoughness SDF_SeamBlendDistance SDF_SeamBlendSharpness SDF_SeamBlendNoiseScale
SDF_SeamBlendNoiseBreakup SDF_SeamBlendStrength IOR Dispersion GemstoneRoughness GlintIntensity
DreamComposition DreamThreshold GildingAmount ChladniScale SparkleColor SparkleColorLow
SparkleColorHigh GoldTint GoldEmissive ShadowFlowerColor FairyDustColor MotifColor SnowDustColor
MossColor ContactRimColor MadokaRampLow MadokaRampMid MadokaRampHigh IttoRampLow IttoRampHigh
DreamBloomColor DawnLowColor DawnHighColor MistColor GlintColor DFContactTint GemstoneTint
ChladniColor SparkleMask StarMap FairyGlyphMask MotifMask ChladniMask UseUDSTimeOfDay
ConstellationRampLow ConstellationRampMid ConstellationRampHigh""".split())


def log(m):
    unreal.log("[MasterTrim] " + str(m))


def main():
    os.makedirs(AUDIT, exist_ok=True)
    mat = unreal.load_asset(MAT)
    if mat is None:
        raise RuntimeError("cannot load " + MAT)
    lib = unreal.MaterialEditingLibrary
    exprs = lib.get_material_expressions(mat)
    n0 = len(exprs)
    doomed = []
    for e in exprs:
        if e is None:
            continue
        try:
            nm = e.get_editor_property("parameter_name")
        except Exception:                                    # noqa: BLE001
            nm = None
        if nm and str(nm) in DROP:
            doomed.append((e, str(nm)))
    log("before=%d expressions, %d DROP parameters matched" % (n0, len(doomed)))

    deleted, failed = [], []
    for e, nm in doomed:
        try:
            lib.delete_material_expression(mat, e)
            deleted.append(nm)
        except Exception as exc:                             # noqa: BLE001
            failed.append("%s: %s" % (nm, exc))

    # sweep expressions orphaned by the deletions above
    swept = []
    try:
        lib.delete_unused_expressions(mat)
        swept = lib.get_material_expressions(mat)
        swept = ["swept_to=%d" % len(swept)]
    except Exception as exc:                                 # noqa: BLE001
        swept = ["sweep failed: %s" % exc]

    try:
        lib.recompile_material(mat)
    except Exception as exc:                                 # noqa: BLE001
        log("recompile failed: %s" % exc)
    n1 = lib.get_num_material_expressions(mat)

    record = {
        "pass": 1, "asset": MAT,
        "expressions_before": n0, "expressions_after": n1,
        "parameters_deleted": len(deleted), "delete_failures": failed,
        "orphan_sweep": swept,
        "deleted_parameter_names": sorted(set(deleted)),
    }
    out = os.path.join(AUDIT, "trim_pass1_params.json")
    with open(out, "w") as f:
        json.dump(record, f, indent=1)
    log("wrote " + out)
    log("after=%d expressions" % n1)


main()
