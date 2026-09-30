"""Build MF_RampLUT - painted-band ramp driven by a 1D lookup texture.

WHY
---
MF_ColorRamp3 shapes bands with sliders. This is the art-directable sibling:
the band curve lives in a texture the artist paints, so the terminator, the
shadow lift and the highlight rolloff can be reshaped without touching the
material graph. This is the classic toon ramp path.

Same signature as MF_ColorRamp3 (BaseColor / ColorRamp / Mask -> Color) so the
two are interchangeable in the master via bUsePaintedRamp.

Mask = 0 bypasses, matching MF_ColorRamp3, so an unwired instance reproduces
the plain colour blend.
"""
from __future__ import annotations

import unreal

import spine_lib as lib

NAME = "MF_RampLUT"

FI_SCALAR = unreal.FunctionInputType.FUNCTION_INPUT_SCALAR
FI_VECTOR3 = unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3
FI_TEXTURE = unreal.FunctionInputType.FUNCTION_INPUT_TEXTURE2D


def build(rebuild=True):
    lib.log(f"=== {NAME} ===")
    fn = lib.get_or_create_function(NAME, rebuild=rebuild)
    lib.try_set(fn, "description",
                "Painted 1D ramp lookup. Mask=0 bypasses. Art-directable bands.")

    # ---------------- inputs ----------------
    base_color = lib.add_function_input(
        fn, "BaseColor", FI_VECTOR3, preview=(0.5, 0.5, 0.5, 1.0), x=-1400, y=0)
    ramp_tex = lib.add_function_input(
        fn, "RampTexture", FI_TEXTURE, x=-1400, y=220)
    mask = lib.add_function_input(
        fn, "Mask", FI_SCALAR, preview=(0.0, 0.0, 0.0, 0.0), x=-1400, y=420)

    # ---------------- luminance of BaseColor ----------------
    thirds = lib.expr(fn, unreal.MaterialExpressionConstant3Vector, -1400, -220)
    thirds.set_editor_property("constant",
                               unreal.LinearColor(0.3333, 0.3333, 0.3333, 1.0))

    dot = lib.expr(fn, unreal.MaterialExpressionDotProduct, -1200, 0)
    lib.connect(base_color, "", dot, ["A", "a"])
    lib.connect(thirds, "", dot, ["B", "b"])

    lum = lib.expr(fn, unreal.MaterialExpressionSaturate, -1040, 0)
    lib.unary(dot, lum)

    # ---------------- ramp texture UV = (lum, 0.5) ----------------
    # The LUT is authored as a horizontal strip; sample its centre row.
    zero = lib.expr(fn, unreal.MaterialExpressionConstant, -1040, 200)
    zero.set_editor_property("r", 0.5)

    uv = lib.expr(fn, unreal.MaterialExpressionAppendVector, -860, 60)
    lib.connect(lum, "", uv, ["A", "a"])
    lib.connect(zero, "", uv, ["B", "b"])

    sample = lib.expr(fn, unreal.MaterialExpressionTextureSample, -660, 60)
    lib.connect(ramp_tex, "", sample, ["TextureObject", ""])
    lib.connect(uv, "", sample, ["UVs", ""])

    # ---------------- lerp original over the ramped result ----------------
    mixed = lib.expr(fn, unreal.MaterialExpressionLinearInterpolate, -200, 60)
    lib.ternary(base_color, sample, mask, mixed)

    out = lib.add_function_output(fn, "Color", x=40, y=60)
    lib.connect(mixed, "", out, "")

    lib.save(fn)
    lib.log(f"{NAME} built with {lib.function_expression_count(fn)} expressions")
    return fn
