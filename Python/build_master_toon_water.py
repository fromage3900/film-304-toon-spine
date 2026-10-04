"""Build M_Master_Toon_Water - stylized opaque water on the toon spine.

WHY A SECOND MASTER
--------------------
Water's motion is a DOMAIN behaviour, not a look: two scrolling noise fields
perturb the normal and drive the band mask, so the terminator itself flows.
That cannot ride an instance of M_Master_Toon_Universal without duplicating
the ripple graph per look - which is exactly what masters are for.

WHAT IT REUSES (the spine contract)
------------------------------------
MF_ColorRamp3 + MF_RampLUT behind bUsePaintedRamp, ink toward InkColor, and
the full pattern block with a PatternSDFMap TextureObjectParameter (default
off: PatternStrength 0 - a surface that hatches on demand, not by default).

RIPPLES
--------
Two T_Noise_White samples (the generated band-breakup noise, wrap-addressed)
pan at different scales and speeds; their channels build a tangent-space
normal: N = normalize((n1.r - 0.5, n2.r - 0.5, RippleFlatten)). The same
fields make the band mask (sine of the ripple luminance), so the cel bands
flow with the water instead of sitting still on it.

PROFILES
--------
Binds TP_Default at the master level (the profile a master binds is its
shading contract; per-instance profile switching is not a thing instances
can do on this build - measured 2026-10-02,
toon_profile_binding_probe_v3.json).
"""
from __future__ import annotations

import unreal

import spine_lib as lib

NAME = "M_Master_Toon_Water"
MASTER_PROFILE = "TP_Water"
TEX_DIR = "/Game/Materials/Textures"


def build(rebuild=True):
    lib.log(f"=== {NAME} ===")
    mat = lib.get_or_create_material(NAME, rebuild=rebuild)

    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_SURFACE)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    lib.try_set(mat, "bUsedWithWaterMesh", False)

    # ---------------- parameters ----------------
    vec = {
        "BaseTint": lib.vector(mat, "BaseTint", "Surface", (0.16, 0.35, 0.38, 1.0),
                               -2000, -400, desc="Deep water colour"),
        "AccentTint": lib.vector(mat, "AccentTint", "Surface", (0.45, 0.72, 0.75, 1.0),
                                 -2000, -280, desc="Ripple crest colour"),
        "InkColor": lib.vector(mat, "InkColor", "Ink", (0.02, 0.04, 0.06, 1.0),
                               -2000, -160, desc="Edge / shadow ink"),
        "EmissiveColor": lib.vector(mat, "EmissiveColor", "Surface",
                                    (0.0, 0.0, 0.0, 1.0), -2000, -40,
                                    desc="Emission (glow plankton)"),
        "KeyLightDir": lib.vector(mat, "KeyLightDir", "Pattern", (0.0, 0.0, 1.0, 1.0),
                                  -2000, 80, desc="Key light direction for hatch shadow"),
    }
    flt = {
        "RampStrength": lib.scalar(mat, "RampStrength", "Ramp", 0.70, -1400, 200),
        "InkIntensity": lib.scalar(mat, "InkIntensity", "Ink", 0.20, -1400, 270),
        "DryRoughness": lib.scalar(mat, "DryRoughness", "Surface", 0.08, -1400, 340),
        "BandScale": lib.scalar(mat, "BandScale", "Ripple", 0.030, -1400, 410),
        "BandStrength": lib.scalar(mat, "BandStrength", "Ripple", 0.22, -1400, 480),
        "RippleScale1": lib.scalar(mat, "RippleScale1", "Ripple", 14.0, -1400, 550),
        "RippleSpeed1": lib.scalar(mat, "RippleSpeed1", "Ripple", 0.90, -1400, 620),
        "RippleScale2": lib.scalar(mat, "RippleScale2", "Ripple", 23.0, -1400, 690),
        "RippleSpeed2": lib.scalar(mat, "RippleSpeed2", "Ripple", 1.30, -1400, 760),
        "RippleStrength": lib.scalar(mat, "RippleStrength", "Ripple", 0.45, -1400, 830),
        "EmissiveIntensity": lib.scalar(mat, "EmissiveIntensity", "Surface",
                                        0.0, -1400, 900),
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

    # ---------------- ripple fields (two scrolling noise reads) --------------
    noise_tex = unreal.load_asset(lib.asset_path(TEX_DIR, "T_Noise_White"))
    if noise_tex is None:
        raise RuntimeError("T_Noise_White missing - run build_textures first")

    time_n = lib.expr(mat, unreal.MaterialExpressionTime, -2000, 1200)

    uv0 = lib.expr(mat, unreal.MaterialExpressionTextureCoordinate, -2000, 1300)

    uv1_scaled = lib.expr(mat, unreal.MaterialExpressionMultiply, -1840, 1300)
    lib.binary(uv0, flt["RippleScale1"], uv1_scaled)
    t1_scaled = lib.expr(mat, unreal.MaterialExpressionMultiply, -1840, 1440)
    lib.binary(time_n, flt["RippleSpeed1"], t1_scaled)
    # pan vector = (t, t*0.7) so the scroll is diagonal, not axis-locked
    pan1_y = lib.expr(mat, unreal.MaterialExpressionMultiply, -1680, 1440)
    lib.binary(t1_scaled, lib.scalar_const(mat, 0.7, -1680, 1520), pan1_y)
    pan1 = lib.expr(mat, unreal.MaterialExpressionAppendVector, -1520, 1440)
    lib.connect(t1_scaled, "", pan1, ["A", "a"])
    lib.connect(pan1_y, "", pan1, ["B", "b"])
    uv1 = lib.expr(mat, unreal.MaterialExpressionAdd, -1360, 1370)
    lib.binary(uv1_scaled, pan1, uv1)

    sample1 = lib.expr(mat, unreal.MaterialExpressionTextureSample, -1200, 1300)
    sample1.set_editor_property("texture", noise_tex)
    # NOTE: no sampler_type override - the shared-wrap member name tried here
    # does not exist on this build (SSM_SHARED_WRAP absent, caught by the
    # 2026-10-03 spine run), and the texture asset's own wrap addressing
    # (set at import) is what the sample uses by default anyway.
    lib.connect(uv1, "", sample1, ["UVs", ""])

    uv2_scaled = lib.expr(mat, unreal.MaterialExpressionMultiply, -1840, 1700)
    lib.binary(uv0, flt["RippleScale2"], uv2_scaled)
    t2_scaled = lib.expr(mat, unreal.MaterialExpressionMultiply, -1840, 1840)
    lib.binary(time_n, flt["RippleSpeed2"], t2_scaled)
    pan2_y = lib.expr(mat, unreal.MaterialExpressionMultiply, -1680, 1840)
    lib.binary(t2_scaled, lib.scalar_const(mat, -0.6, -1680, 1920), pan2_y)
    pan2 = lib.expr(mat, unreal.MaterialExpressionAppendVector, -1520, 1840)
    lib.connect(t2_scaled, "", pan2, ["A", "a"])
    lib.connect(pan2_y, "", pan2, ["B", "b"])
    uv2 = lib.expr(mat, unreal.MaterialExpressionAdd, -1360, 1770)
    lib.binary(uv2_scaled, pan2, uv2)

    sample2 = lib.expr(mat, unreal.MaterialExpressionTextureSample, -1200, 1700)
    sample2.set_editor_property("texture", noise_tex)
    lib.connect(uv2, "", sample2, ["UVs", ""])

    # tangent-space normal from the two fields' first channels
    r1 = lib.expr(mat, unreal.MaterialExpressionComponentMask, -1040, 1300)
    r1.set_editor_property("r", True)
    r1.set_editor_property("g", False)
    r1.set_editor_property("b", False)
    r1.set_editor_property("a", False)
    lib.connect(sample1, "", r1, ["", "None"])
    r2 = lib.expr(mat, unreal.MaterialExpressionComponentMask, -1040, 1700)
    r2.set_editor_property("r", True)
    r2.set_editor_property("g", False)
    r2.set_editor_property("b", False)
    r2.set_editor_property("a", False)
    lib.connect(sample2, "", r2, ["", "None"])

    n1 = lib.expr(mat, unreal.MaterialExpressionSubtract, -880, 1300)
    lib.binary(r1, lib.scalar_const(mat, 0.5, -880, 1380), n1)
    n2 = lib.expr(mat, unreal.MaterialExpressionSubtract, -880, 1700)
    lib.binary(r2, lib.scalar_const(mat, 0.5, -880, 1780), n2)

    ripple_normal = lib.expr(mat, unreal.MaterialExpressionAppendVector, -720, 1500)
    lib.connect(n1, "", ripple_normal, ["A", "a"])
    lib.connect(n2, "", ripple_normal, ["B", "b"])
    ripple_normal3 = lib.expr(mat, unreal.MaterialExpressionAppendVector, -560, 1500)
    lib.connect(ripple_normal, "", ripple_normal3, ["A", "a"])
    lib.connect(lib.scalar_const(mat, 1.0, -560, 1580), "", ripple_normal3, ["B", "b"])
    ripple_norm = lib.expr(mat, unreal.MaterialExpressionNormalize, -400, 1500)
    lib.unary(ripple_normal3, ripple_norm)

    # ripple field for the band mask: mean of the two channels
    ripple_mean = lib.expr(mat, unreal.MaterialExpressionAdd, -720, 1820)
    lib.binary(n1, n2, ripple_mean)
    ripple_half = lib.expr(mat, unreal.MaterialExpressionMultiply, -560, 1820)
    lib.binary(ripple_mean, lib.scalar_const(mat, 0.5, -560, 1900), ripple_half)

    band_source = lib.expr(mat, unreal.MaterialExpressionSine, -400, 1820)
    band_source.set_editor_property("period", 1.0)
    band_scaled = lib.expr(mat, unreal.MaterialExpressionMultiply, -560, 1740)
    lib.binary(ripple_half, flt["BandScale"], band_scaled)
    # feed BandScale-scaled ripple into the sine: bands ride the flow
    lib.connect(band_scaled, "", band_source, ["", "None"])

    band_abs = lib.expr(mat, unreal.MaterialExpressionAbs, -240, 1820)
    lib.unary(band_source, band_abs)
    band_mask = lib.expr(mat, unreal.MaterialExpressionMultiply, -80, 1820)
    lib.binary(band_abs, flt["BandStrength"], band_mask)

    # ---------------- ramp family (spine contract) ----------------
    ramp_slider = lib.expr(mat, unreal.MaterialExpressionMaterialFunctionCall,
                           -900, 200)
    ramp_slider.set_editor_property("material_function",
        unreal.load_asset(lib.asset_path(lib.FUNCTION_DIR, "MF_ColorRamp3")))
    lib.connect(vec["BaseTint"], "", ramp_slider, "BaseColor")
    lib.connect(vec["AccentTint"], "", ramp_slider, "ColorRamp")
    lib.connect(flt["RampStrength"], "", ramp_slider, "Mask")

    ramp_lut = lib.expr(mat, unreal.MaterialExpressionMaterialFunctionCall,
                        -900, 420)
    ramp_lut.set_editor_property("material_function",
        unreal.load_asset(lib.asset_path(lib.FUNCTION_DIR, "MF_RampLUT")))
    lib.connect(vec["BaseTint"], "", ramp_lut, "BaseColor")
    lib.connect(ramp_lut_tex, "", ramp_lut, "RampTexture")
    lib.connect(flt["RampStrength"], "", ramp_lut, "Mask")

    ramp_switch = lib.expr(mat, unreal.MaterialExpressionStaticSwitchParameter,
                           -660, 320)
    ramp_switch.set_editor_property("parameter_name", "bUsePaintedRamp")
    ramp_switch.set_editor_property("group", "Ramp")
    ramp_switch.set_editor_property("default_value", False)
    lib.connect(ramp_lut, "Color", ramp_switch, ["True"])
    lib.connect(ramp_slider, "Color", ramp_switch, ["False"])

    band_lerp = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, -440, 320)
    lib.ternary(ramp_switch, vec["AccentTint"], band_mask, band_lerp)

    # edge ink: fresnel of the ripple normal pulls InkColor at grazing angles
    # (node defaults: exponent 5, base reflectivity 0.04 - the property names
    # are not python-exposed on this build; defaults are fine for edge ink)
    fresnel = lib.expr(mat, unreal.MaterialExpressionFresnel, -440, 560)
    ink_fres = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, -260, 480)
    lib.ternary(flt["InkIntensity"], lib.scalar_const(mat, 1.0, -260, 640),
                fresnel, ink_fres)

    with_ink = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, -100, 320)
    lib.ternary(band_lerp, vec["InkColor"], ink_fres, with_ink)
    final_color = with_ink

    # ---------------- surface pattern (off by default on water) --------------
    pat_uv = lib.expr(mat, unreal.MaterialExpressionTextureCoordinate, -1400, 2200)
    pat_call = lib.expr(mat, unreal.MaterialExpressionMaterialFunctionCall,
                        -660, 2200)
    pat_call.set_editor_property("material_function",
        unreal.load_asset(lib.asset_path(lib.FUNCTION_DIR, "MF_ProceduralPatterns")))

    pat_scale = lib.scalar(mat, "PatternScale", "Pattern", 12.0, -1400, 2300)
    pat_angle = lib.scalar(mat, "PatternAngle", "Pattern", 0.0, -1400, 2360)
    pat_index = lib.scalar(mat, "PatternIndex", "Pattern", 12.0, -1400, 2420)
    pat_density = lib.scalar(mat, "PatternDensity", "Pattern", 0.50, -1400, 2480)
    pat_strength = lib.scalar(mat, "PatternStrength", "Pattern", 0.0, -1400, 2540)
    pat_softness = lib.scalar(mat, "PatternSoftness", "Pattern", 0.10, -1400, 2600)
    hatch_drive = lib.scalar(mat, "PatternHatchShadowDrive", "Pattern",
                             0.0, -1400, 2660)
    hatch_shadow = lib.scalar(mat, "PatternHatchShadowDensity", "Pattern",
                              0.85, -1400, 2720)

    lib.connect(pat_uv, "", pat_call, "UV")
    lib.connect(pat_scale, "", pat_call, "Scale")
    lib.connect(pat_angle, "", pat_call, "Angle")
    lib.connect(pat_index, "", pat_call, "CellIndex")
    lib.connect(pat_softness, "", pat_call, "Softness")
    lib.connect(pat_sdf_tex, "", pat_call, "SDFMap")
    lib.connect(pat_density, "", pat_call, "Density")

    pat_amt = lib.expr(mat, unreal.MaterialExpressionMultiply, -440, 2260)
    lib.connect(pat_call, "Mask", pat_amt, ["A", "a"])
    lib.connect(pat_strength, "", pat_amt, ["B", "b"])

    patterned = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate,
                         60, 320)
    lib.connect(final_color, "", patterned, "A")
    lib.connect(vec["InkColor"], "", patterned, "B")
    lib.connect(pat_amt, "", patterned, "Alpha")
    final_color = patterned

    # ---------------- Substrate Toon BSDF ----------------
    toon = lib.expr(mat, unreal.MaterialExpressionSubstrateToonBSDF, 700, 240)
    lib.connect(final_color, "", toon, ["BaseColor", "DiffuseColor"])
    lib.connect(flt["DryRoughness"], "", toon, ["Roughness"])
    # tangent-space ripple normal (the closure's Normal pin expects it)
    lib.connect(ripple_norm, "", toon, ["Normal", "TangentNormal", "NormalMap"])

    emissive_mul = lib.expr(mat, unreal.MaterialExpressionMultiply, 700, 60)
    lib.connect(vec["EmissiveColor"], "", emissive_mul, ["A", "a"])
    lib.connect(flt["EmissiveIntensity"], "", emissive_mul, ["B", "b"])
    lib.connect(emissive_mul, "", toon, ["EmissiveColor"])

    lib.connect_property(toon, unreal.MaterialProperty.MP_FRONT_MATERIAL)

    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
    except Exception as exc:
        lib.log(f"recompile warning: {exc}")

    # ---------------- the Toon Profile (spine contract: bind LAST) ----------
    toon_node = None
    for _n in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
        if type(_n).__name__ == "MaterialExpressionSubstrateToonBSDF":
            toon_node = _n
            break
    master_profile = unreal.load_asset(
        lib.asset_path(lib.PROFILE_DIR, MASTER_PROFILE))
    if toon_node is not None and master_profile is not None:
        for handle in (toon, toon_node):
            lib.try_set(handle, "toon_profile", master_profile)
    lib.log(f"{NAME} Toon Profile -> "
            f"{(toon_node.get_editor_property('toon_profile').get_name() if toon_node and toon_node.get_editor_property('toon_profile') else 'UNBOUND')}")

    lib.save(mat)
    lib.log(f"{NAME} built with {lib.expression_count(mat)} expressions")
    return mat


def main() -> int:
    mat = build()
    ok = lib.verify_material(NAME,
                             expected_calls=["MF_ColorRamp3", "MF_RampLUT",
                                             "MF_ProceduralPatterns"],
                             min_expressions=30)
    return 0 if (mat is not None and ok.get("ok")) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
