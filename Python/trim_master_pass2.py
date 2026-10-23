# Pass 2 of the Universal-master trim (2026-10-17).
# Deletes the Melodia feature STATIC SWITCHES (whose branches now dangle after
# pass 1 removed their parameters) and retries any parameters whose deletion
# failed in pass 1 (deleting a dependent node often unblocks them).
# Then sweeps orphans and recompiles.

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
ConstellationRampLow ConstellationRampMid ConstellationRampHigh
bWeather_Active bElemental_Active bCelestial_Active bCelestialUsesDreamPalette
bFairyDust_Active bSparkleAdvanced bGemstone_Active bGemstone_Active_LEGACY
bDFContactBlend_Active bMeshBlendActivator_Active""".split())


def log(m):
    unreal.log("[MasterTrim2] " + str(m))


def main():
    os.makedirs(AUDIT, exist_ok=True)
    mat = unreal.load_asset(MAT)
    if mat is None:
        raise RuntimeError("cannot load " + MAT)
    lib = unreal.MaterialEditingLibrary

    n0 = lib.get_num_material_expressions(mat)
    doomed = []
    for e in lib.get_material_expressions(mat):
        if e is None:
            continue
        try:
            nm = e.get_editor_property("parameter_name")
        except Exception:                                    # noqa: BLE001
            nm = None
        if nm and str(nm) in DROP:
            doomed.append((e, str(nm)))
    log("before=%d expressions, %d DROP nodes matched" % (n0, len(doomed)))

    deleted, failed = [], []
    for e, nm in doomed:
        try:
            lib.delete_material_expression(mat, e)
            deleted.append(nm)
        except Exception as exc:                             # noqa: BLE001
            failed.append("%s: %s" % (nm, exc))

    # second attempt on the failures: an earlier failure is often only ordering
    if failed:
        retry_failed = []
        for nm in [f.split(":")[0] for f in failed]:
            for e in lib.get_material_expressions(mat):
                if e is None:
                    continue
                try:
                    if str(e.get_editor_property("parameter_name")) == nm:
                        try:
                            lib.delete_material_expression(mat, e)
                            deleted.append(nm)
                        except Exception as exc:             # noqa: BLE001
                            retry_failed.append("%s: %s" % (nm, exc))
                        break
                except Exception:                            # noqa: BLE001
                    pass
        failed = retry_failed

    swept_note = "n/a"
    try:
        lib.delete_unused_expressions(mat)
        swept_note = "swept to %d expressions" % lib.get_num_material_expressions(mat)
    except Exception as exc:                                 # noqa: BLE001
        swept_note = "sweep failed: %s" % exc

    try:
        lib.recompile_material(mat)
    except Exception as exc:                                 # noqa: BLE001
        log("recompile failed: %s" % exc)
    n1 = lib.get_num_material_expressions(mat)

    record = {
        "pass": 2, "asset": MAT,
        "expressions_before": n0, "expressions_after": n1,
        "nodes_deleted": len(deleted),
        "delete_failures": failed,
        "orphan_sweep": swept_note,
        "deleted_names": sorted(set(deleted)),
    }
    out = os.path.join(AUDIT, "trim_pass2_switches.json")
    with open(out, "w") as f:
        json.dump(record, f, indent=1)
    log("wrote " + out)
    log("after=%d expressions, failures=%d" % (n1, len(failed)))


main()
