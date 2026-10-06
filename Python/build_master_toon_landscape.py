"""Build M_Master_Toon_Landscape - ground planes with macro variation.

WHY ITS OWN MASTER
------------------
Ground is not a wall. SH010 and SH030 (ground contact) need a surface whose
read comes from LARGE low-frequency variation - dirt patches, worn paths,
terrain mottling - breaking the cel bands, while a wall master bands cleanly
over one tint. That is a different response to the same light, which is the
plan's own test for a new master (TOON_MASTERS_PLAN_2026-10-04.md section 3).
Live Melodia references to regenerate against later:
M_Master_Toon_Landscape_HeightBlend, M_Master_Nikki_Landscape (not copied -
they are content references, not architectures).

WHAT IT REUSES (the spine contract)
-----------------------------------
Identical to M_Master_Toon_Water: MF_ColorRamp3 + MF_RampLUT behind
bUsePaintedRamp (Mask = RampStrength), fresnel edge ink toward InkColor, and
the full MF_ProceduralPatterns block with its TextureObjectParameter SDF map,
default OFF (PatternStrength 0). No hatch-shadow scalars: those inputs are
dead on water (nothing consumes them) and are not replicated here - a dead
parameter is a lie in the graph.

MACRO VARIATION (the domain behaviour)
--------------------------------------
Two STATIC T_Noise_White reads (no time pan - terrain does not scroll) at
MacroScale1/MacroScale2 average into one field. That field does two jobs:
  * macro_amt  = mean * MacroStrength lerps BaseTint -> AccentTint BEFORE the
    ramp, so the band thresholds ride the variation instead of painting over
    it;
  * band_mask  = abs(mean - 0.5) * BandStrength drives a small accent band at
    the variation extremes - the ground's own breakup, no sine stripes.
Hue lives in the instance (ToonProfile ramps are scalar-valued - the rule
every block in this repo follows).

PROFILES
--------
Binds TP_Landscape at the master level (instances cannot carry a profile,
measured 2026-10-02). Read back and asserted by this module's verify().
"""
from __future__ import annotations

import unreal

import spine_lib as lib

NAME = "M_Master_Toon_Landscape"
MASTER_PROFILE = "TP_Landscape"
TEX_DIR = "/Game/Materials/Textures"


def build(rebuild=True):
    lib.log(f"=== {NAME} ===")
    mat = lib.get_or_create_material(NAME, rebuild=rebuild)

    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_SURFACE)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)

    # ---------------- parameters ----------------
    vec = {
        "BaseTint": lib.vector(mat, "BaseTint", "Surface", (0.34, 0.33, 0.30, 1.0),
                               -2000, -400, desc="Ground base colour (macro low)"),
        "AccentTint": lib.vector(mat, "AccentTint", "Surface", (0.56, 0.55, 0.48, 1.0),
                                 -2000, -280, desc="Ground accent (macro high / bands)"),
        "InkColor": lib.vector(mat, "InkColor", "Ink", (0.05, 0.05, 0.05, 1.0),
                               -2000, -160, desc="Edge / shadow ink"),
        "EmissiveColor": lib.vector(mat, "EmissiveColor", "Surface",
                                    (0.0, 0.0, 0.0, 1.0), -2000, -40,
                                    desc="Emission (path glow etc.)"),
    }
    flt = {
        "RampStrength": lib.scalar(mat, "RampStrength", "Ramp", 0.70, -1400, 100,
                                   desc="0 bypasses the ramp; >0 applies the profile"),
        "InkIntensity": lib.scalar(mat, "InkIntensity", "Ink", 0.15, -1400, 170),
        "DryRoughness": lib.scalar(mat, "DryRoughness", "Surface", 0.90, -1400, 240),
        "EmissiveIntensity": lib.scalar(mat, "EmissiveIntensity", "Surface",
                                        0.0, -1400, 310),
        "MacroScale1": lib.scalar(mat, "MacroScale1", "Macro", 0.008, -1400, 380,
                                  desc="Large terrain patch frequency (UV multiplier)"),
        "MacroScale2": lib.scalar(mat, "MacroScale2", "Macro", 0.023, -1400, 450,
                                  desc="Smaller mottling frequency"),
        "MacroStrength": lib.scalar(mat, "MacroStrength", "Macro", 0.35, -1400, 520,
                                    desc="How far BaseTint lerps to AccentTint"),
        "BandStrength": lib.scalar(mat, "BandStrength", "Macro", 0.12, -1400, 590,
                                   desc="Accent band at the variation extremes"),
    }
    # pattern block (6 scalars - no hatch-shadow drive: dead on water, not replicated)
    pat = {
        "PatternScale": lib.scalar(mat, "PatternScale", "Pattern", 12.0, -1400, 1300),
        "PatternAngle": lib.scalar(mat, "PatternAngle", "Pattern", 0.0, -1400, 1370),
        "PatternIndex": lib.scalar(mat, "PatternIndex", "Pattern", 0.0, -1400, 1440,
                                   desc="0 halftone 1 checker 2 stripes 4 ink 5 crosshatch "
                                        "6 stipple 12 sdfmap 13 subway 14 blinds "
                                        "15 paperfiber 16 brushed 17 chevron "
                                        "18 frostbands"),
        "PatternDensity": lib.scalar(mat, "PatternDensity", "Pattern", 0.50, -1400, 1510),
        "PatternStrength": lib.scalar(mat, "PatternStrength", "Pattern", 0.0, -1400, 1580,
                                      desc="0 = off (default); surface hatches on demand"),
        "PatternSoftness": lib.scalar(mat, "PatternSoftness", "Pattern", 0.10, -1400, 1650),
    }

    ramp_lut_tex = lib.expr(mat, unreal.MaterialExpressionTextureObjectParameter,
                            -1400, -700)
    ramp_lut_tex.set_editor_property("parameter_name", "RampTexture")
    ramp_lut_tex.set_editor_property("group", "Ramp")
    ramp_lut_tex.set_editor_property(
        "texture", unreal.load_asset(lib.asset_path(TEX_DIR, "T_Ramp_Smooth")))
    lib._desc(ramp_lut_tex, "Painted 1D band ramp (horizontal strip)")

    pat_sdf_tex = lib.expr(mat, unreal.MaterialExpressionTextureObjectParameter,
                           -1400, -630)
    pat_sdf_tex.set_editor_property("parameter_name", "PatternSDFMap")
    pat_sdf_tex.set_editor_property("group", "Pattern")
    pat_sdf_tex.set_editor_property(
        "texture", unreal.load_asset(lib.asset_path(TEX_DIR, "T_SDF_Strokes")))
    lib._desc(pat_sdf_tex, "Baked SDF stroke field for CellIndex 12")

    # ---------------- macro field (two static noise reads) ----------------
    noise_tex = unreal.load_asset(lib.asset_path(TEX_DIR, "T_Noise_White"))
    if noise_tex is None:
        raise RuntimeError("T_Noise_White missing - run build_textures first")

    muv = lib.expr(mat, unreal.MaterialExpressionTextureCoordinate, -2000, 300)

    m1_uv = lib.expr(mat, unreal.MaterialExpressionMultiply, -1840, 260)
    lib.binary(muv, flt["MacroScale1"], m1_uv)
    m1 = lib.expr(mat, unreal.MaterialExpressionTextureSample, -1680, 260)
    m1.set_editor_property("texture", noise_tex)
    lib.connect(m1_uv, "", m1, ["UVs", ""])
    m1_r = lib.expr(mat, unreal.MaterialExpressionComponentMask, -1520, 260)
    m1_r.set_editor_property("r", True)
    m1_r.set_editor_property("g", False)
    m1_r.set_editor_property("b", False)
    m1_r.set_editor_property("a", False)
    lib.connect(m1, "", m1_r, ["", "None"])

    m2_uv = lib.expr(mat, unreal.MaterialExpressionMultiply, -1840, 480)
    lib.binary(muv, flt["MacroScale2"], m2_uv)
    m2 = lib.expr(mat, unreal.MaterialExpressionTextureSample, -1680, 480)
    m2.set_editor_property("texture", noise_tex)
    lib.connect(m2_uv, "", m2, ["UVs", ""])
    m2_r = lib.expr(mat, unreal.MaterialExpressionComponentMask, -1520, 480)
    m2_r.set_editor_property("r", True)
    m2_r.set_editor_property("g", False)
    m2_r.set_editor_property("b", False)
    m2_r.set_editor_property("a", False)
    lib.connect(m2, "", m2_r, ["", "None"])

    m_sum = lib.expr(mat, unreal.MaterialExpressionAdd, -1360, 370)
    lib.binary(m1_r, m2_r, m_sum)
    macro_mean = lib.expr(mat, unreal.MaterialExpressionMultiply, -1200, 370)
    lib.binary(m_sum, lib.scalar_const(mat, 0.5, -1200, 450), macro_mean)

    macro_amt = lib.expr(mat, unreal.MaterialExpressionMultiply, -1040, 300)
    lib.binary(macro_mean, flt["MacroStrength"], macro_amt)

    base_src = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, -880, 300)
    lib.ternary(vec["BaseTint"], vec["AccentTint"], macro_amt, base_src)

    # ---------------- ramp family (spine contract) ----------------
    ramp_slider = lib.expr(mat, unreal.MaterialExpressionMaterialFunctionCall,
                           -700, 120)
    ramp_slider.set_editor_property("material_function",
        unreal.load_asset(lib.asset_path(lib.FUNCTION_DIR, "MF_ColorRamp3")))
    lib.connect(base_src, "", ramp_slider, "BaseColor")
    lib.connect(vec["AccentTint"], "", ramp_slider, "ColorRamp")
    lib.connect(flt["RampStrength"], "", ramp_slider, "Mask")

    ramp_lut = lib.expr(mat, unreal.MaterialExpressionMaterialFunctionCall,
                        -700, 340)
    ramp_lut.set_editor_property("material_function",
        unreal.load_asset(lib.asset_path(lib.FUNCTION_DIR, "MF_RampLUT")))
    lib.connect(base_src, "", ramp_lut, "BaseColor")
    lib.connect(ramp_lut_tex, "", ramp_lut, "RampTexture")
    lib.connect(flt["RampStrength"], "", ramp_lut, "Mask")

    ramp_switch = lib.expr(mat, unreal.MaterialExpressionStaticSwitchParameter,
                           -460, 240)
    ramp_switch.set_editor_property("parameter_name", "bUsePaintedRamp")
    ramp_switch.set_editor_property("group", "Ramp")
    ramp_switch.set_editor_property("default_value", False)
    lib.connect(ramp_lut, "Color", ramp_switch, ["True"])
    lib.connect(ramp_slider, "Color", ramp_switch, ["False"])

    # ---------------- macro band at the variation extremes ----------------
    band_dev = lib.expr(mat, unreal.MaterialExpressionSubtract, -1040, 640)
    lib.binary(macro_mean, lib.scalar_const(mat, 0.5, -1040, 720), band_dev)
    band_abs = lib.expr(mat, unreal.MaterialExpressionAbs, -880, 640)
    lib.unary(band_dev, band_abs)
    band_mask = lib.expr(mat, unreal.MaterialExpressionMultiply, -720, 640)
    lib.binary(band_abs, flt["BandStrength"], band_mask)

    band_lerp = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, -240, 240)
    lib.ternary(ramp_switch, vec["AccentTint"], band_mask, band_lerp)

    # ---------------- edge ink (water pattern) ----------------
    fresnel = lib.expr(mat, unreal.MaterialExpressionFresnel, -440, 480)
    ink_fres = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, -240, 480)
    lib.ternary(flt["InkIntensity"], lib.scalar_const(mat, 1.0, -240, 560),
                fresnel, ink_fres)

    with_ink = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, -60, 240)
    lib.ternary(band_lerp, vec["InkColor"], ink_fres, with_ink)
    final_color = with_ink

    # ---------------- surface pattern (off by default) ----------------
    pat_uv = lib.expr(mat, unreal.MaterialExpressionTextureCoordinate, -1400, 900)
    pat_call = lib.expr(mat, unreal.MaterialExpressionMaterialFunctionCall,
                        -700, 900)
    pat_call.set_editor_property("material_function",
        unreal.load_asset(lib.asset_path(lib.FUNCTION_DIR, "MF_ProceduralPatterns")))
    lib.connect(pat_uv, "", pat_call, "UV")
    lib.connect(pat["PatternScale"], "", pat_call, "Scale")
    lib.connect(pat["PatternAngle"], "", pat_call, "Angle")
    lib.connect(pat["PatternIndex"], "", pat_call, "CellIndex")
    lib.connect(pat["PatternSoftness"], "", pat_call, "Softness")
    lib.connect(pat_sdf_tex, "", pat_call, "SDFMap")
    lib.connect(pat["PatternDensity"], "", pat_call, "Density")

    pat_amt = lib.expr(mat, unreal.MaterialExpressionMultiply, -440, 940)
    lib.connect(pat_call, "Mask", pat_amt, ["A", "a"])
    lib.connect(pat["PatternStrength"], "", pat_amt, ["B", "b"])

    patterned = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate,
                         140, 240)
    lib.connect(final_color, "", patterned, "A")
    lib.connect(vec["InkColor"], "", patterned, "B")
    lib.connect(pat_amt, "", patterned, "Alpha")
    final_color = patterned

    # ---------------- Substrate Toon BSDF ----------------
    toon = lib.expr(mat, unreal.MaterialExpressionSubstrateToonBSDF, 500, 200)
    lib.connect(final_color, "", toon, ["BaseColor", "DiffuseColor"])
    lib.connect(flt["DryRoughness"], "", toon, ["Roughness"])
    normal = lib.expr(mat, unreal.MaterialExpressionPixelNormalWS, 300, 420)
    lib.connect(normal, "", toon, ["Normal", "TangentNormal", "NormalMap"])

    emissive_mul = lib.expr(mat, unreal.MaterialExpressionMultiply, 300, 60)
    lib.connect(vec["EmissiveColor"], "", emissive_mul, ["A", "a"])
    lib.connect(flt["EmissiveIntensity"], "", emissive_mul, ["B", "b"])
    lib.connect(emissive_mul, "", toon, ["EmissiveColor"])

    lib.connect_property(toon, unreal.MaterialProperty.MP_FRONT_MATERIAL)

    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
    except Exception as exc:
        lib.log(f"recompile warning: {exc}")

    # ---------------- the Toon Profile (spine contract: bind LAST) ----------
    lib.bind_toon_profile(mat, MASTER_PROFILE)

    lib.save(mat)
    lib.log(f"{NAME} built with {lib.expression_count(mat)} expressions")
    return mat


def verify():
    """The profile read-back lib.verify_material cannot do for this master
    (its toon_profile branch is hard-coded to M_Master_Toon_Universal)."""
    path = lib.asset_path(lib.MASTER_DIR, NAME)
    mat = unreal.load_asset(path)
    result = {"name": NAME, "ok": False, "error": None}

    if mat is None:
        result["error"] = "does not load"
        lib.log(f"VERIFY {NAME}: FAIL {result['error']}")
        return result

    profile = None
    for n in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
        if type(n).__name__ == "MaterialExpressionSubstrateToonBSDF":
            try:
                p = n.get_editor_property("toon_profile")
                profile = p.get_name() if p else None
            except Exception as exc:
                result["error"] = f"profile read: {str(exc)[:80]}"
            break
    result["toon_profile"] = profile
    result["expression_count"] = lib.expression_count(mat)

    if result["error"] is None and profile != MASTER_PROFILE:
        result["error"] = (f"bound profile is {profile!r}, want "
                           f"{MASTER_PROFILE!r} - the landscape contract would "
                           f"not be in effect")
    if result["error"] is None:
        result["ok"] = True

    lib.log(f"VERIFY {NAME}: ok={result['ok']} profile={profile} "
            f"{result['error'] or ''}")
    return result


def main() -> int:
    mat = build()
    res = lib.verify_material(NAME,
                              expected_calls=["MF_ColorRamp3", "MF_RampLUT",
                                              "MF_ProceduralPatterns"],
                              min_expressions=30)
    graph = verify()
    ok = mat is not None and res.get("ok") and graph.get("ok")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
