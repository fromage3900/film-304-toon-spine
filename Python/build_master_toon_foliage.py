"""Build M_Master_Toon_Foliage - masked two-sided foliage on the toon spine.

WHY A SECOND MASTER (and not an instance of M_Master_Toon_Universal)
--------------------------------------------------------------------
Two domain-level facts the universal master cannot carry:
  * BLEND_MASKED + two-sided rendering - leaf cards cut silhouettes and shade
    from both faces.
  * wind sway in WPO, driven by its own parameter group.
The rule "a look is an instance, not a master copy" still holds: this master
exists for the DOMAIN, and every surface look on it stays an instance.

WHAT IT REUSES (the spine contract)
------------------------------------
The band/ramp machinery is the same code-generated source of truth as the
universal master: MF_ColorRamp3 + MF_RampLUT behind bUsePaintedRamp, ink
toward InkColor, and the full pattern block including CellIndex 12 via a
PatternSDFMap TextureObjectParameter - shadow-driven hatch density applies
here exactly as it does on the universal master.

OPACITY
--------
The cover mask is a GENERATED SDF texture (T_SDF_Leaf, unioned capsule
leaves with soft silhouette edges): opacity = saturate((R - Cutoff) *
Sharpness). Generated content only - the grey-default policy bans /Engine
placeholder textures. Masked + Substrate: the closure carries no opacity pin
on this build (probed pin list: BaseColor/Metallic/Specular/Roughness/
Normal/EmissiveColor/PatternUVs/Anisotropy/Tangent), so opacity rides the
legacy MP_OPACITY property; recompile failure would surface in the spine
report, and an opaque fallback is the visible failure mode, not silence.

SWAY
----
WPO = SwayAmount * sin(Time * SwaySpeed + worldphase) * VertexNormalWS.
The worldphase term varies over the surface so a card bends rather than
bobs rigidly. No heightmask: cards are small and uniform here - add one
when a pivot-driven system lands.
"""
from __future__ import annotations

import unreal

import spine_lib as lib

NAME = "M_Master_Toon_Foliage"
MASTER_PROFILE = "TP_Foliage"
TEX_DIR = "/Game/Materials/Textures"


def build(rebuild=True):
    lib.log(f"=== {NAME} ===")
    mat = lib.get_or_create_material(NAME, rebuild=rebuild)

    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_SURFACE)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    lib.try_set(mat, "two_sided", True)
    lib.try_set(mat, "bUsedWithSkeletalMesh", False)

    # ---------------- parameters ----------------
    vec = {
        "BaseTint": lib.vector(mat, "BaseTint", "Surface", (0.24, 0.42, 0.22, 1.0),
                               -2000, -400, desc="Leaf base colour"),
        "AccentTint": lib.vector(mat, "AccentTint", "Surface", (0.46, 0.66, 0.34, 1.0),
                                 -2000, -280, desc="Lit-side colour"),
        "InkColor": lib.vector(mat, "InkColor", "Ink", (0.02, 0.05, 0.03, 1.0),
                               -2000, -160, desc="Ink line / shadow colour"),
        "EmissiveColor": lib.vector(mat, "EmissiveColor", "Surface",
                                    (0.0, 0.0, 0.0, 1.0), -2000, -40,
                                    desc="Emission (fireflies, glow spores)"),
        "KeyLightDir": lib.vector(mat, "KeyLightDir", "Pattern", (0.0, 0.0, 1.0, 1.0),
                                  -2000, 80, desc="Key light direction for hatch shadow"),
    }
    flt = {
        "RampStrength": lib.scalar(mat, "RampStrength", "Ramp", 1.0, -1400, 200),
        "InkIntensity": lib.scalar(mat, "InkIntensity", "Ink", 0.10, -1400, 270),
        "DryRoughness": lib.scalar(mat, "DryRoughness", "Surface", 0.88, -1400, 340),
        "BandScale": lib.scalar(mat, "BandScale", "Surface", 0.05, -1400, 410),
        "BandStrength": lib.scalar(mat, "BandStrength", "Surface", 0.15, -1400, 480),
        "EmissiveIntensity": lib.scalar(mat, "EmissiveIntensity", "Surface",
                                        0.0, -1400, 550),
        "MaskCutoff": lib.scalar(mat, "MaskCutoff", "Mask", 0.35, -1400, 620),
        "MaskSharpness": lib.scalar(mat, "MaskSharpness", "Mask", 8.0, -1400, 690),
        "SwayAmount": lib.scalar(mat, "SwayAmount", "Sway", 0.06, -1400, 760),
        "SwaySpeed": lib.scalar(mat, "SwaySpeed", "Sway", 1.2, -1400, 830),
        "SwayPhase": lib.scalar(mat, "SwayPhase", "Sway", 0.35, -1400, 900),
    }

    # ---------------- mask + ramp texture params ----------------
    cover_tex = lib.expr(mat, unreal.MaterialExpressionTextureObjectParameter,
                         -1400, -700)
    cover_tex.set_editor_property("parameter_name", "CoverMask")
    cover_tex.set_editor_property("group", "Mask")
    cover_tex.set_editor_property(
        "texture", unreal.load_asset(lib.asset_path(TEX_DIR, "T_SDF_Leaf")))
    lib._desc(cover_tex, "Leaf-cluster cover SDF - opacity source")

    ramp_lut_tex = lib.expr(mat, unreal.MaterialExpressionTextureObjectParameter,
                            -1400, -630)
    ramp_lut_tex.set_editor_property("parameter_name", "RampTexture")
    ramp_lut_tex.set_editor_property("group", "Ramp")
    ramp_lut_tex.set_editor_property(
        "texture", unreal.load_asset(lib.asset_path(TEX_DIR, "T_Ramp_Smooth")))
    lib._desc(ramp_lut_tex, "Painted 1D band ramp (horizontal strip)")

    pat_sdf_tex = lib.expr(mat, unreal.MaterialExpressionTextureObjectParameter,
                           -1400, -560)
    pat_sdf_tex.set_editor_property("parameter_name", "PatternSDFMap")
    pat_sdf_tex.set_editor_property("group", "Pattern")
    pat_sdf_tex.set_editor_property(
        "texture", unreal.load_asset(lib.asset_path(TEX_DIR, "T_SDF_Strokes")))
    lib._desc(pat_sdf_tex, "Baked SDF stroke field for CellIndex 12")

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

    # ---------------- world-space band mask ----------------
    world = lib.expr(mat, unreal.MaterialExpressionWorldPosition, -1400, 1000)
    xy = lib.expr(mat, unreal.MaterialExpressionComponentMask, -1240, 1000)
    xy.set_editor_property("r", True)
    xy.set_editor_property("g", True)
    xy.set_editor_property("b", False)
    xy.set_editor_property("a", False)
    lib.connect(world, "", xy, "")

    band_scale_mul = lib.expr(mat, unreal.MaterialExpressionMultiply, -1080, 1000)
    lib.binary(xy, flt["BandScale"], band_scale_mul)

    sin_n = lib.expr(mat, unreal.MaterialExpressionSine, -920, 1000)
    sin_n.set_editor_property("period", 1.0)
    lib.unary(band_scale_mul, sin_n)

    abs_n = lib.expr(mat, unreal.MaterialExpressionAbs, -760, 1000)
    lib.unary(sin_n, abs_n)

    band_mask = lib.expr(mat, unreal.MaterialExpressionMultiply, -600, 1000)
    lib.binary(abs_n, flt["BandStrength"], band_mask)

    band_lerp = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, -440, 320)
    lib.ternary(ramp_switch, vec["AccentTint"], band_mask, band_lerp)

    # ---------------- ink ----------------
    with_ink = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, -260, 320)
    lib.ternary(band_lerp, vec["InkColor"], flt["InkIntensity"], with_ink)
    final_color = with_ink

    # ---------------- surface pattern (MF_ProceduralPatterns) ----------------
    # Same contract as the universal master: Mask * PatternStrength inks toward
    # InkColor; PatternDensity is shadow-driven via KeyLightDir . Normal so the
    # veining densifies into shadow. PatternIndex defaults to 12 (SDFMap).
    pat_uv = lib.expr(mat, unreal.MaterialExpressionTextureCoordinate, -1400, 1200)
    pat_call = lib.expr(mat, unreal.MaterialExpressionMaterialFunctionCall,
                        -660, 1200)
    pat_call.set_editor_property("material_function",
        unreal.load_asset(lib.asset_path(lib.FUNCTION_DIR, "MF_ProceduralPatterns")))

    pat_scale = lib.scalar(mat, "PatternScale", "Pattern", 8.0, -1400, 1300)
    pat_angle = lib.scalar(mat, "PatternAngle", "Pattern", 0.0, -1400, 1360)
    pat_index = lib.scalar(mat, "PatternIndex", "Pattern", 12.0, -1400, 1420)
    pat_density = lib.scalar(mat, "PatternDensity", "Pattern", 0.45, -1400, 1480)
    pat_strength = lib.scalar(mat, "PatternStrength", "Pattern", 0.30, -1400, 1540)
    pat_softness = lib.scalar(mat, "PatternSoftness", "Pattern", 0.06, -1400, 1600)
    hatch_drive = lib.scalar(mat, "PatternHatchShadowDrive", "Pattern",
                             1.0, -1400, 1660)
    hatch_shadow = lib.scalar(mat, "PatternHatchShadowDensity", "Pattern",
                              0.75, -1400, 1720)

    lib.connect(pat_uv, "", pat_call, "UV")
    lib.connect(pat_scale, "", pat_call, "Scale")
    lib.connect(pat_angle, "", pat_call, "Angle")
    lib.connect(pat_index, "", pat_call, "CellIndex")
    lib.connect(pat_softness, "", pat_call, "Softness")
    lib.connect(pat_sdf_tex, "", pat_call, "SDFMap")

    # shadow-driven density: KeyLightDir . PixelNormalWS -> shadow mask
    key_n = lib.expr(mat, unreal.MaterialExpressionNormalize, -1240, 80)
    lib.unary(vec["KeyLightDir"], key_n)

    shade_n = lib.expr(mat, unreal.MaterialExpressionPixelNormalWS, -1240, 180)
    ndotl = lib.expr(mat, unreal.MaterialExpressionDotProduct, -1080, 180)
    lib.connect(shade_n, "", ndotl, ["A", "a"])
    lib.connect(key_n, "", ndotl, ["B", "b"])

    ndotl_s = lib.expr(mat, unreal.MaterialExpressionSaturate, -920, 180)
    lib.unary(ndotl, ndotl_s)
    shadow_m = lib.expr(mat, unreal.MaterialExpressionOneMinus, -760, 180)
    lib.unary(ndotl_s, shadow_m)

    drive_m = lib.expr(mat, unreal.MaterialExpressionMultiply, -600, 180)
    lib.binary(shadow_m, hatch_drive, drive_m)
    drive_s = lib.expr(mat, unreal.MaterialExpressionSaturate, -440, 180)
    lib.unary(drive_m, drive_s)

    dens_final = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate,
                          -280, 160)
    lib.ternary(pat_density, hatch_shadow, drive_s, dens_final)
    lib.connect(dens_final, "", pat_call, "Density")

    pat_amt = lib.expr(mat, unreal.MaterialExpressionMultiply, -440, 1260)
    lib.connect(pat_call, "Mask", pat_amt, ["A", "a"])
    lib.connect(pat_strength, "", pat_amt, ["B", "b"])

    patterned = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate,
                         -100, 320)
    lib.connect(final_color, "", patterned, "A")
    lib.connect(vec["InkColor"], "", patterned, "B")
    lib.connect(pat_amt, "", patterned, "Alpha")
    final_color = patterned

    # ---------------- roughness / normal ----------------
    rough = flt["DryRoughness"]
    normal = lib.expr(mat, unreal.MaterialExpressionPixelNormalWS, 300, 640)

    # ---------------- sway WPO ----------------
    time_n = lib.expr(mat, unreal.MaterialExpressionTime, -1400, 1900)
    time_scaled = lib.expr(mat, unreal.MaterialExpressionMultiply, -1240, 1900)
    lib.binary(time_n, flt["SwaySpeed"], time_scaled)

    world_phase = lib.expr(mat, unreal.MaterialExpressionDotProduct, -1240, 2040)
    phase_axis = lib.expr(mat, unreal.MaterialExpressionConstant3Vector, -1400, 2040)
    phase_axis.set_editor_property(
        "constant", unreal.LinearColor(0.61, 0.39, 0.13, 1.0))
    lib.connect(xy, "", world_phase, ["A", "a"])
    lib.connect(phase_axis, "", world_phase, ["B", "b"])
    phase_scaled = lib.expr(mat, unreal.MaterialExpressionMultiply, -1080, 2040)
    lib.binary(world_phase, flt["SwayPhase"], phase_scaled)

    phase = lib.expr(mat, unreal.MaterialExpressionAdd, -920, 1960)
    lib.binary(time_scaled, phase_scaled, phase)

    sway_sin = lib.expr(mat, unreal.MaterialExpressionSine, -760, 1960)
    sway_sin.set_editor_property("period", 1.0)
    lib.unary(phase, sway_sin)

    sway_amp = lib.expr(mat, unreal.MaterialExpressionMultiply, -600, 1960)
    lib.binary(sway_sin, flt["SwayAmount"], sway_amp)

    vertex_n = lib.expr(mat, unreal.MaterialExpressionVertexNormalWS, -600, 2100)
    wpo = lib.expr(mat, unreal.MaterialExpressionMultiply, -440, 2020)
    lib.binary(sway_amp, vertex_n, wpo)
    lib.connect_property(wpo, unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)

    # ---------------- opacity from the cover SDF ----------------
    # opacity = saturate((cover - Cutoff) * Sharpness): a soft silhouette cut
    # against the generated leaf field, tunable without touching the texture.
    cover_sample = lib.expr(mat, unreal.MaterialExpressionTextureSample,
                            -1400, 2340)
    lib.connect(cover_tex, "", cover_sample, ["Tex", "TextureObject", ""])

    cover_r = lib.expr(mat, unreal.MaterialExpressionComponentMask, -1240, 2340)
    cover_r.set_editor_property("r", True)
    cover_r.set_editor_property("g", False)
    cover_r.set_editor_property("b", False)
    cover_r.set_editor_property("a", False)
    lib.connect(cover_sample, "", cover_r, ["", "None"])

    cutoff_sub = lib.expr(mat, unreal.MaterialExpressionSubtract, -1080, 2340)
    lib.binary(cover_r, flt["MaskCutoff"], cutoff_sub)

    opacity = lib.expr(mat, unreal.MaterialExpressionMultiply, -920, 2340)
    lib.binary(cutoff_sub, flt["MaskSharpness"], opacity)
    opacity_s = lib.expr(mat, unreal.MaterialExpressionSaturate, -760, 2340)
    lib.unary(opacity, opacity_s)
    lib.connect_property(opacity_s, unreal.MaterialProperty.MP_OPACITY)

    # ---------------- Substrate Toon BSDF ----------------
    toon = lib.expr(mat, unreal.MaterialExpressionSubstrateToonBSDF, 700, 240)
    lib.connect(final_color, "", toon, ["BaseColor", "DiffuseColor"])
    lib.connect(rough, "", toon, ["Roughness"])
    lib.connect(normal, "", toon, ["Normal", "TangentNormal", "NormalMap"])

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
        live = unreal.load_asset(lib.asset_path(lib.MASTER_DIR, NAME))
        if live is not None:
            for _n in unreal.MaterialEditingLibrary.get_material_expressions(live) or []:
                if type(_n).__name__ == "MaterialExpressionSubstrateToonBSDF":
                    p = None
                    try:
                        p = _n.get_editor_property("toon_profile")
                    except Exception:
                        pass
                    if p is None:
                        lib.try_set(_n, "toon_profile", master_profile)
                    break
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
