"""Build MF_ColorRamp3 - the unified toon ramp every other spine MF depends on.

RECONSTRUCTED, NOT COPIED. The API below was recovered from the source asset's
name table on 2026-09-29:

    inputs   BaseColor, ColorRamp, Mask
    params   RampLow, RampMid, RampHigh, RampPosMid, RampContrast, RampSharpness
    groups   Color, Mask
    nodes    ScalarParameter, Constant, Add, Subtract, Multiply, Divide,
             Power, LinearInterpolate, Saturate, FunctionInput, FunctionOutput
    outputs  (one colour output)

Shape: remap BaseColor through a three-stop luminance ramp, then lerp toward the
caller's Mask. RampStrength = 0 bypasses (the source master documents
"RampStrength=0 bypasses"); this build exposes that as the Mask input defaulting
to 0, so an unwired Mask reproduces the original colour untouched.

Both MF_Itto and MF_Madoka call this function, so it must exist before they can
be built.
"""
from __future__ import annotations

import unreal

import spine_lib as lib

NAME = "MF_ColorRamp3"

FI_SCALAR = unreal.FunctionInputType.FUNCTION_INPUT_SCALAR
FI_VECTOR3 = unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3


def build(rebuild=True):
    lib.log(f"=== {NAME} ===")
    fn = lib.get_or_create_function(NAME, rebuild=rebuild)
    fn.set_editor_property("description",
                           "Three-stop toon luminance ramp. Mask=0 bypasses.")

    # ---------------- inputs ----------------
    base_color = lib.add_function_input(
        fn, "BaseColor", FI_VECTOR3, preview=(0.5, 0.5, 0.5, 1.0), x=-1600, y=0)
    color_ramp = lib.add_function_input(
        fn, "ColorRamp", FI_VECTOR3, preview=(1.0, 1.0, 1.0, 1.0), x=-1600, y=200)
    mask = lib.add_function_input(
        fn, "Mask", FI_SCALAR, preview=(0.0, 0.0, 0.0, 0.0), x=-1600, y=400)

    # ---------------- parameters ----------------
    ramp_low = lib.scalar(fn, "RampLow", "Color", 0.0, -1600, -300,
                          desc="Ramp value at the darkest band (shadow)")
    ramp_mid = lib.scalar(fn, "RampMid", "Color", 0.5, -1600, -180,
                          desc="Ramp value at the terminator")
    ramp_high = lib.scalar(fn, "RampHigh", "Color", 1.0, -1600, -60,
                           desc="Ramp value at the brightest band (light)")
    ramp_pos_mid = lib.scalar(fn, "RampPosMid", "Color", 0.5, -1600, 60,
                              desc="Where the mid stop sits along the ramp (0-1)")
    ramp_contrast = lib.scalar(fn, "RampContrast", "Color", 1.0, -1600, 180,
                               desc="Contrast around the mid stop")
    ramp_sharpness = lib.scalar(fn, "RampSharpness", "Color", 1.0, -1600, 300,
                                desc="Edge hardness of each band transition")

    # ---------------- luminance ----------------
    # BaseColor -> dot(RGB, 1/3) = perceived value driving the ramp lookup.
    dot = lib.expr(fn, unreal.MaterialExpressionDotProduct, -1200, 0)
    thirds = lib.expr(fn, unreal.MaterialExpressionConstant3Vector, -1360, 120)
    thirds.set_editor_property("constant",
                               unreal.LinearColor(0.3333, 0.3333, 0.3333, 1.0))
    lib.connect(base_color, "", dot, ["A", "a"])
    lib.connect(thirds, "", dot, ["B", "b"])

    lum = lib.expr(fn, unreal.MaterialExpressionSaturate, -1040, 0)
    lib.unary(dot, lum)

    # ---------------- contrast around the mid stop ----------------
    # (lum - 0.5) * contrast + 0.5
    half = lib.scalar_const(fn, 0.5, -1200, 240)
    centred = lib.expr(fn, unreal.MaterialExpressionSubtract, -880, 40)
    lib.binary(lum, half, centred)

    contrast_mul = lib.expr(fn, unreal.MaterialExpressionMultiply, -720, 40)
    lib.binary(centred, ramp_contrast, contrast_mul)

    half_again = lib.scalar_const(fn, 0.5, -880, 200)
    contrasted = lib.expr(fn, unreal.MaterialExpressionAdd, -560, 40)
    lib.binary(contrast_mul, half_again, contrasted)

    # ---------------- three-stop ramp lookup ----------------
    # low -> mid, positioned by RampPosMid
    pos_scaled = lib.expr(fn, unreal.MaterialExpressionMultiply, -1040, 320)
    lib.binary(contrasted, ramp_pos_mid, pos_scaled)

    lerp_low = lib.expr(fn, unreal.MaterialExpressionLinearInterpolate, -400, 60)
    lib.ternary(ramp_low, ramp_mid, pos_scaled, lerp_low)

    # mid -> high across the remaining range
    inv_pos = lib.expr(fn, unreal.MaterialExpressionSubtract, -560, 360)
    one = lib.scalar_const(fn, 1.0, -720, 420)
    lib.binary(one, ramp_pos_mid, inv_pos)

    inv_scaled = lib.expr(fn, unreal.MaterialExpressionMultiply, -400, 360)
    lib.binary(contrasted, inv_scaled, inv_scaled)

    hi_scale = lib.expr(fn, unreal.MaterialExpressionSaturate, -240, 360)
    lib.unary(inv_scaled, hi_scale)

    lerp_hi = lib.expr(fn, unreal.MaterialExpressionLinearInterpolate, -80, 200)
    lib.ternary(ramp_mid, ramp_high, hi_scale, lerp_hi)

    # lower half -> upper half
    is_upper = lib.expr(fn, unreal.MaterialExpressionSaturate, 80, 360)
    lib.unary(pos_scaled, is_upper)

    ramp_value = lib.expr(fn, unreal.MaterialExpressionLinearInterpolate, 260, 140)
    lib.ternary(lerp_low, lerp_hi, is_upper, ramp_value)

    # sharpness: push the value through pow to harden the transitions
    sharp = lib.expr(fn, unreal.MaterialExpressionPower, 420, 140)
    lib.binary(ramp_value, ramp_sharpness, sharp)

    # ---------------- apply as a colour ----------------
    # The ramp drives the caller's ColorRamp through a multiply, then the
    # result is lerped over BaseColor by Mask (Mask=0 -> original colour).
    ramp_rgb = lib.expr(fn, unreal.MaterialExpressionMultiply, 420, -180)
    lib.connect(color_ramp, "", ramp_rgb, ["A", "a"])
    lib.unary(sharp, ramp_rgb)

    mixed = lib.expr(fn, unreal.MaterialExpressionLinearInterpolate, 620, 0)
    lib.ternary(base_color, ramp_rgb, mask, mixed)

    out = lib.add_function_output(fn, "Color", x=860, y=0)
    lib.connect(mixed, "", out, "")

    lib.save(fn)
    lib.log(f"{NAME} built with {lib.function_expression_count(fn)} expressions")
    return fn
