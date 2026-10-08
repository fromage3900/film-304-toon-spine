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

# Film-core lane parameter names (film material core 2026-10-07). Module
# level because verify() runs OUTSIDE build() scope - referencing the
# build() local dicts there raised NameError and failed the spine run.
WEAR_PARAM_NAMES = ("WearScale", "CrackWidth", "WearThreshold",
                    "WearStrength", "CrackStrength", "WearRoughness")
CONTACTDF_PARAM_NAMES = ("DFContactStrength", "DFContactDistance",
                         "DFContactSharpness", "DFContactNoiseScale",
                         "DFContactNoiseBreakup", "DFContactGroundHeight",
                         "DFContactHeightFalloff", "DFContactRoughness",
                         "DFContactOffset", "DFContactTint")


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
    # film material core (2026-10-07): surface wear + distance-field contact.
    # The same parameter surface as Universal, so one instance vocabulary
    # covers walls and ground. Both gates default 0 = identity.
    wear = {
        "WearScale": lib.scalar(mat, "WearScale", "Wear", 0.02, -1400, 3200,
                                desc="Wear tile frequency (cells per cm; 0.02 = ~50 cm)"),
        "CrackWidth": lib.scalar(mat, "CrackWidth", "Wear", 0.04, -1400, 3270,
                                 desc="Crack width in tile units"),
        "WearThreshold": lib.scalar(mat, "WearThreshold", "Wear", 0.55, -1400, 3340,
                                    desc="Wear patch onset"),
        "WearStrength": lib.scalar(mat, "WearStrength", "Wear", 0.0, -1400, 3410,
                                   desc="Colour wear amount; 0 = off (default)"),
        "CrackStrength": lib.scalar(mat, "CrackStrength", "Wear", 0.0, -1400, 3480,
                                    desc="Crack ink amount; 0 = off (default)"),
        "WearRoughness": lib.scalar(mat, "WearRoughness", "Wear", 0.95, -1400, 3550,
                                    desc="Roughness target under the wear mask"),
    }
    contact = {
        "DFContactStrength": lib.scalar(mat, "DFContactStrength", "ContactDF",
                                        0.0, -1400, 3620,
                                        desc="Distance-field contact tint; 0 = off (default)"),
        "DFContactDistance": lib.scalar(mat, "DFContactDistance", "ContactDF",
                                        18.0, -1400, 3690,
                                        desc="Contact falloff distance (cm)"),
        "DFContactSharpness": lib.scalar(mat, "DFContactSharpness", "ContactDF",
                                         3.0, -1400, 3760,
                                         desc="Contact transition steepness"),
        "DFContactNoiseScale": lib.scalar(mat, "DFContactNoiseScale", "ContactDF",
                                          0.015, -1400, 3830,
                                          desc="Contact breakup noise frequency (1/cm)"),
        "DFContactNoiseBreakup": lib.scalar(mat, "DFContactNoiseBreakup",
                                            "ContactDF", 0.0, -1400, 3900,
                                            desc="Noise breakup in the contact mask"),
        "DFContactGroundHeight": lib.scalar(mat, "DFContactGroundHeight",
                                            "ContactDF", 0.0, -1400, 3970,
                                            desc="Ground height envelope reference (cm)"),
        "DFContactHeightFalloff": lib.scalar(mat, "DFContactHeightFalloff",
                                             "ContactDF", 28.0, -1400, 4040,
                                             desc="Height envelope falloff (cm)"),
        "DFContactRoughness": lib.scalar(mat, "DFContactRoughness", "ContactDF",
                                         0.82, -1400, 4110,
                                         desc="Roughness target inside the contact mask"),
        "DFContactOffset": lib.scalar(mat, "DFContactOffset", "ContactDF",
                                      12.0, -1400, 4180,
                                      desc="Sample offset below the surface (cm)"),
    }
    contact_vec = {
        "DFContactTint": lib.vector(mat, "DFContactTint", "ContactDF",
                                    (0.24, 0.30, 0.34, 1.0), -2000, 1400,
                                    desc="Contact grime colour"),
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

    # ---------------- surface wear + DF contact (film core 2026-10-07) ---
    # The same two lanes Universal carries. Guides are the worn courtyard
    # marks (SH010 ground) near walls; both gates default 0 = identity.
    wear_n = lib.expr(mat, unreal.MaterialExpressionPixelNormalWS,
                      -1400, 4600)
    wear_call = lib.expr(mat, unreal.MaterialExpressionMaterialFunctionCall,
                         -1200, 4540)
    wear_call.set_editor_property("material_function",
        unreal.load_asset(lib.asset_path(lib.FUNCTION_DIR,
                                         "MF_SurfaceWear")))
    lib.connect(wear_n, "", wear_call, "Normal")
    lib.connect(wear["WearScale"], "", wear_call, "WearScale")
    lib.connect(wear["CrackWidth"], "", wear_call, "CrackWidth")
    lib.connect(wear["WearThreshold"], "", wear_call, "WearThreshold")

    crack_amt = lib.expr(mat, unreal.MaterialExpressionMultiply, -700, 4380)
    lib.connect(wear_call, "CrackMask", crack_amt, ["A", "a"])
    lib.connect(wear["CrackStrength"], "", crack_amt, ["B", "b"])
    crack_sat = lib.expr(mat, unreal.MaterialExpressionSaturate, -540, 4380)
    lib.unary(crack_amt, crack_sat)

    wear_amt = lib.expr(mat, unreal.MaterialExpressionMultiply, -700, 4520)
    lib.connect(wear_call, "WearMask", wear_amt, ["A", "a"])
    lib.connect(wear["WearStrength"], "", wear_amt, ["B", "b"])
    wear_sat = lib.expr(mat, unreal.MaterialExpressionSaturate, -540, 4520)
    lib.unary(wear_amt, wear_sat)

    wear_sum = lib.expr(mat, unreal.MaterialExpressionAdd, -380, 4450)
    lib.binary(crack_sat, wear_sat, wear_sum)
    wear_gate = lib.expr(mat, unreal.MaterialExpressionSaturate, -220, 4450)
    lib.unary(wear_sum, wear_gate)

    df_call = lib.expr(mat, unreal.MaterialExpressionMaterialFunctionCall,
                       -1200, 4960)
    df_call.set_editor_property("material_function",
        unreal.load_asset(lib.asset_path(lib.FUNCTION_DIR,
                                         "MF_DF_ContactBlend")))
    lib.connect(contact["DFContactOffset"], "", df_call, "WorldPositionOffset")
    lib.connect(contact["DFContactDistance"], "", df_call, "BlendDistance")
    lib.connect(contact["DFContactSharpness"], "", df_call, "BlendSharpness")
    lib.connect(contact["DFContactNoiseScale"], "", df_call, "NoiseScale")
    lib.connect(contact["DFContactNoiseBreakup"], "", df_call, "NoiseBreakup")
    lib.connect(contact["DFContactGroundHeight"], "", df_call, "GroundHeight")
    lib.connect(contact["DFContactHeightFalloff"], "", df_call,
                "HeightFalloff")
    df_active_1 = lib.scalar_const(mat, 1.0, -970, 5440)
    lib.connect(df_active_1, "", df_call, "DistanceFieldBlendActive")
    df_blend_1 = lib.scalar_const(mat, 1.0, -970, 5510)
    lib.connect(df_blend_1, "", df_call, "BlendStrength")

    df_raw = lib.expr(mat, unreal.MaterialExpressionMultiply, -700, 4870)
    lib.connect(df_call, "Result", df_raw, ["A", "a"])
    lib.connect(contact["DFContactStrength"], "", df_raw, ["B", "b"])
    df_gate = lib.expr(mat, unreal.MaterialExpressionSaturate, -540, 4870)
    lib.unary(df_raw, df_gate)

    worn_color = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate,
                          340, 240)
    lib.ternary(final_color, vec["InkColor"], wear_gate, worn_color)
    df_color = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate,
                        500, 240)
    lib.ternary(worn_color, contact_vec["DFContactTint"], df_gate, df_color)
    final_color = df_color

    # ---------------- Substrate Toon BSDF ----------------
    # Roughness chain: DryRoughness -> wear lerp -> DF contact lerp. Both
    # lerps are identity at their gates' 0 defaults.
    rough_wear = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate,
                          500, 480)
    lib.ternary(flt["DryRoughness"], wear["WearRoughness"], wear_gate,
                rough_wear)
    rough_df = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate,
                        660, 480)
    lib.ternary(rough_wear, contact["DFContactRoughness"], df_gate, rough_df)

    toon = lib.expr(mat, unreal.MaterialExpressionSubstrateToonBSDF, 500, 200)
    lib.connect(final_color, "", toon, ["BaseColor", "DiffuseColor"])
    lib.connect(rough_df, "", toon, ["Roughness"])
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
    (its toon_profile branch is hard-coded to M_Master_Toon_Universal), plus
    the film-core lane calls + their parameter surface (2026-10-07)."""
    path = lib.asset_path(lib.MASTER_DIR, NAME)
    mat = unreal.load_asset(path)
    result = {"name": NAME, "ok": False, "error": None}

    if mat is None:
        result["error"] = "does not load"
        lib.log(f"VERIFY {NAME}: FAIL {result['error']}")
        return result

    exprs = [e for e in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []
             if e is not None]

    profile = None
    for n in exprs:
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

    # -- film core lanes (film material core 2026-10-07): call + params --
    if result["error"] is None:
        want_lanes = {"MF_SurfaceWear", "MF_DF_ContactBlend"}
        called = set()
        for c in exprs:
            if type(c).__name__ == "MaterialExpressionMaterialFunctionCall":
                try:
                    mf = c.get_editor_property("material_function")
                    if mf is not None:
                        called.add(mf.get_name())
                except Exception:
                    continue
        missing = sorted(want_lanes - called)
        if missing:
            result["error"] = f"film core lanes not called: {missing}"
        else:
            params = set()
            for e in exprs:
                try:
                    params.add(str(e.get_editor_property("parameter_name")))
                except Exception:
                    continue
            want_params = set(WEAR_PARAM_NAMES) | set(CONTACTDF_PARAM_NAMES)
            miss_params = sorted(want_params - params)
            if miss_params:
                result["error"] = f"film core params missing: {miss_params}"

    if result["error"] is None:
        result["ok"] = True

    lib.log(f"VERIFY {NAME}: ok={result['ok']} profile={profile} "
            f"{result['error'] or ''}")
    return result


def main() -> int:
    mat = build()
    res = lib.verify_material(NAME,
                              expected_calls=["MF_ColorRamp3", "MF_RampLUT",
                                              "MF_ProceduralPatterns",
                                              "MF_SurfaceWear",
                                              "MF_DF_ContactBlend"],
                              min_expressions=30)
    graph = verify()
    ok = mat is not None and res.get("ok") and graph.get("ok")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
