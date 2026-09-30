"""Build MF_ProceduralPatterns - SDF-style procedural patterns for the toon spine.

NO SDF NODE EXISTS IN UE 5.8. Probed 2029-09-30:
    unreal.MaterialExpressionSDF           -> absent
    unreal.MaterialExpressionShaderToRGB   -> absent
    unreal.MaterialExpressionSmoothMin     -> absent

Only DistanceFieldApproxAO / DistanceFieldGradient ship, and those read a mesh's
baked field - they cannot author shapes. So this module composes analytic
distance-style fields from the nodes that DO exist: Sine, Frac, Abs, Floor,
Sign, Distance, DotProduct, Normalize, SmoothStep, If.

Each pattern is a classic signed-distance-style construction evaluated on a UV
lattice, then hard-thresholded with SmoothStep. Hard edges are the point: they
stay crisp at any zoom and under camera move, which is what a cel look needs and
what a filtered texture cannot give.

Inputs
    UV          float2 - lattice coordinate, drive with TexCoord or UV scale
    Scale       scalar - pattern frequency (defaults per-pattern below)
    Softness    scalar - edge width of the hard threshold (0 = razor sharp)
    Angle       scalar - pattern rotation in degrees
    CellIndex   scalar - selects which pattern to return

Outputs
    Pattern     scalar - 0..1 field for the selected pattern
    Mask        scalar - same field, hard-thresholded

Patterns
    0  Halftone   - offset dot lattice, screen-print cell shading
    1  Checker    - hard checkerboard
    2  Stripes    - hard parallel bars
    3  Crackle    - Worley-ish cell breakup from fractional sine distance
    4  InkSplat   - radial falloff rings, high contrast
"""
from __future__ import annotations

import math

import unreal

import spine_lib as lib

NAME = "MF_ProceduralPatterns"

FI_SCALAR = unreal.FunctionInputType.FUNCTION_INPUT_SCALAR
FI_VECTOR2 = unreal.FunctionInputType.FUNCTION_INPUT_VECTOR2


def _uv_basis(fn, angle_source, x=-2000):
    """Build a rotated UV frame driven by `angle_source` (degrees).

    Returns (texcoord, u, v). Rotation is the standard 2x2 frame:
        u' = u*cos - v*sin
        v' = u*sin + v*cos
    """
    tex = lib.expr(fn, unreal.MaterialExpressionTextureCoordinate, x, 900)

    to_rad = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 160, 900)
    lib.connect(angle_source, "", to_rad, ["A", "a"])
    lib.connect(lib.scalar_const(fn, math.pi / 180.0, x + 160, 980), "", to_rad, ["B", "b"])

    ang = to_rad

    cos_n = lib.expr(fn, unreal.MaterialExpressionCosine, x + 300, 840)
    sin_n = lib.expr(fn, unreal.MaterialExpressionSine, x + 300, 960)
    lib.unary(ang, cos_n)
    lib.unary(ang, sin_n)

    # u' = u*cos - v*sin
    u_cos = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 440, 840)
    lib.connect(tex, "", u_cos, ["A", "a"])
    lib.connect(cos_n, "", u_cos, ["B", "b"])

    v_sin = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 440, 980)
    lib.connect(tex, "", v_sin, ["A", "a"])
    lib.connect(sin_n, "", v_sin, ["B", "b"])

    u = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 580, 900)
    lib.binary(u_cos, v_sin, u)

    # v' = u*sin + v*cos
    u_sin = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 440, 1120)
    lib.connect(tex, "", u_sin, ["A", "a"])
    lib.connect(sin_n, "", u_sin, ["B", "b"])

    v_cos = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 440, 1240)
    lib.connect(tex, "", v_cos, ["A", "a"])
    lib.connect(cos_n, "", v_cos, ["B", "b"])

    v = lib.expr(fn, unreal.MaterialExpressionAdd, x + 580, 1180)
    lib.binary(u_sin, v_cos, v)

    return tex, u, v


def _halftone(fn, uv, scale, x=-1100):
    """Offset dot lattice: classic screen-print cell."""
    scaled = lib.expr(fn, unreal.MaterialExpressionMultiply, x, 200)
    lib.connect(uv, "", scaled, ["A", "a"])
    lib.connect(scale, "", scaled, ["B", "b"])

    # offset every other row/column by half a cell -> triangular lattice
    row = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 150, 120)
    lib.connect(scaled, "", row, ["A", "a"])
    lib.connect(scale, "", row, ["B", "b"])

    fract_row = lib.expr(fn, unreal.MaterialExpressionFrac, x + 290, 120)
    lib.unary(row, fract_row)

    cell_x = lib.expr(fn, unreal.MaterialExpressionFloor, x + 290, 260)
    lib.unary(scaled, cell_x)

    paren = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 430, 260)
    lib.binary(cell_x, lib.scalar_const(fn, 0.5, x + 430, 340), paren)

    shifted = lib.expr(fn, unreal.MaterialExpressionAdd, x + 570, 180)
    lib.binary(fract_row, paren, shifted)

    frac_v = lib.expr(fn, unreal.MaterialExpressionFrac, x + 570, 40)
    lib.unary(scaled, frac_v)

    cell_v = lib.expr(fn, unreal.MaterialExpressionFloor, x + 570, -60)
    lib.unary(scaled, cell_v)

    # distance from cell centre in 0..1
    cx = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 710, 180)
    lib.binary(shifted, lib.scalar_const(fn, 0.5, x + 710, 260), cx)

    cy = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 710, 40)
    lib.binary(frac_v, lib.scalar_const(fn, 0.5, x + 710, -20), cy)

    len_n = lib.expr(fn, unreal.MaterialExpressionLength, x + 850, 100)
    lib.connect(cx, "", len_n, ["A", "a"])
    lib.connect(cy, "", len_n, ["B", "b"])
    return len_n


def _checker(fn, uv, scale, x=-1100, y_offset=400):
    scaled = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset)
    lib.connect(uv, "", scaled, ["A", "a"])
    lib.connect(scale, "", scaled, ["B", "b"])

    a = lib.expr(fn, unreal.MaterialExpressionFrac, x + 150, y_offset)
    lib.unary(scaled, a)
    b = lib.expr(fn, unreal.MaterialExpressionFrac, x + 150, y_offset + 120)
    lib.unary(scaled, b)

    step = lib.expr(fn, unreal.MaterialExpressionIf, x + 320, y_offset + 60)
    lib.connect(a, "", step, ["A"])
    lib.connect(lib.scalar_const(fn, 0.5, x + 320, y_offset + 160), "", step, ["B"])
    lib.connect(lib.scalar_const(fn, 0.0, x + 320, y_offset + 240), "", step, ["A > B"])
    lib.connect(lib.scalar_const(fn, 1.0, x + 320, y_offset + 320), "", step, ["A == B"])
    lib.connect(lib.scalar_const(fn, 0.0, x + 320, y_offset + 400), "", step, ["A < B"])
    return step


def _stripes(fn, uv, scale, x=-1100, y_offset=900):
    scaled = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset)
    lib.connect(uv, "", scaled, ["A", "a"])
    lib.connect(scale, "", scaled, ["B", "b"])

    f = lib.expr(fn, unreal.MaterialExpressionFrac, x + 150, y_offset)
    lib.unary(scaled, f)

    tri = lib.expr(fn, unreal.MaterialExpressionAbs, x + 290, y_offset)
    lib.unary(f, tri)

    centred = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 430, y_offset)
    lib.binary(tri, lib.scalar_const(fn, 0.25, x + 430, y_offset + 100), centred)
    return centred


def _crackle(fn, uv, scale, x=-1100, y_offset=1400):
    """Cell-edge field: fract of two rotated sines, distance to the cell wall."""
    scaled = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset)
    lib.connect(uv, "", scaled, ["A", "a"])
    lib.connect(scale, "", scaled, ["B", "b"])

    s1 = lib.expr(fn, unreal.MaterialExpressionSine, x + 150, y_offset)
    s1.set_editor_property("period", 1.0)
    lib.unary(scaled, s1)

    # second, rotated octave for irregular cells
    rot = lib.expr(fn, unreal.MaterialExpressionAdd, x + 150, y_offset + 160)
    lib.connect(scaled, "", rot, ["A"])
    lib.connect(lib.scalar_const(fn, 2.399963, x + 150, y_offset + 240), "", rot, ["B"])

    s2 = lib.expr(fn, unreal.MaterialExpressionCosine, x + 300, y_offset + 160)
    s2.set_editor_property("period", 1.0)
    lib.unary(rot, s2)

    mix = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 440, y_offset + 60)
    lib.binary(s1, s2, mix)

    f = lib.expr(fn, unreal.MaterialExpressionFrac, x + 580, y_offset + 60)
    lib.unary(mix, f)

    dist = lib.expr(fn, unreal.MaterialExpressionAbs, x + 720, y_offset + 60)
    lib.unary(f, dist)

    centred = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 860, y_offset + 60)
    lib.binary(dist, lib.scalar_const(fn, 0.5, x + 860, y_offset + 140), centred)
    return centred


def _inksplat(fn, uv, scale, x=-1100, y_offset=1900):
    """Radial rings: distance from lattice centre, ringed."""
    scaled = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset)
    lib.connect(uv, "", scaled, ["A", "a"])
    lib.connect(scale, "", scaled, ["B", "b"])

    fr = lib.expr(fn, unreal.MaterialExpressionFrac, x + 150, y_offset)
    lib.unary(scaled, fr)

    cx = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 290, y_offset)
    lib.binary(fr, lib.scalar_const(fn, 0.5, x + 290, y_offset + 80), cx)

    len_n = lib.expr(fn, unreal.MaterialExpressionLength, x + 430, y_offset)
    lib.connect(cx, "", len_n, ["A", "a"])

    ring = lib.expr(fn, unreal.MaterialExpressionSine, x + 570, y_offset)
    ring.set_editor_property("period", 1.0)
    lib.unary(len_n, ring)

    half = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 710, y_offset)
    lib.binary(ring, lib.scalar_const(fn, 0.5, x + 710, y_offset + 80), half)

    biased = lib.expr(fn, unreal.MaterialExpressionAdd, x + 850, y_offset)
    lib.binary(half, lib.scalar_const(fn, 0.5, x + 850, y_offset + 80), biased)
    return biased


def build(rebuild=True):
    lib.log(f"=== {NAME} ===")
    fn = lib.get_or_create_function(NAME, rebuild=rebuild)
    lib.try_set(fn, "description",
                "SDF-style procedural patterns (halftone/checker/stripes/crackle/ink). "
                "UE 5.8 has no SDF node; these are analytic distance constructions.")

    # ---------------- inputs ----------------
    uv_in = lib.add_function_input(fn, "UV", FI_VECTOR2, x=-2200, y=0)
    scale_in = lib.add_function_input(fn, "Scale", FI_SCALAR,
                                      preview=(12.0, 0, 0, 0), x=-2200, y=200)
    soft_in = lib.add_function_input(fn, "Softness", FI_SCALAR,
                                     preview=(0.02, 0, 0, 0), x=-2200, y=340)
    angle_in = lib.add_function_input(fn, "Angle", FI_SCALAR,
                                      preview=(0.0, 0, 0, 0), x=-2200, y=460)
    cell_in = lib.add_function_input(fn, "CellIndex", FI_SCALAR,
                                     preview=(0.0, 0, 0, 0), x=-2200, y=600)

    # per-pattern scale multipliers so one Scale knob still gives each pattern
    # its natural frequency
    scales = {}
    for i, mult in enumerate([1.0, 1.0, 1.0, 1.0, 1.0]):
        scales[i] = lib.expr(fn, unreal.MaterialExpressionMultiply, -1900, 700 + i * 60)
        lib.connect(scale_in, "", scales[i], ["A"])
        lib.connect(lib.scalar_const(fn, mult, -1900, 780 + i * 60), "", scales[i], ["B"])

    # rotated UV frame, shared by every pattern. Built at angle 0 from
    # TextureCoordinate; Angle is applied per-instance via the input.
    tex, u, v = _uv_basis(fn, angle_in)

    # ---------------- pattern fields ----------------
    fields = {
        0: _halftone(fn, u, scales[0]),
        1: _checker(fn, u, scales[1]),
        2: _stripes(fn, u, scales[2]),
        3: _crackle(fn, u, scales[3]),
        4: _inksplat(fn, u, scales[4]),
    }

    # ---------------- pattern selector (nested static-free If chain) ----------------
    # Static switches would bake per-instance; an If chain on CellIndex stays
    # dynamic so one material instance can switch pattern at runtime.
    current = None
    for idx in sorted(fields, reverse=True):
        if current is None:
            current = fields[idx]
            continue
        cond = lib.expr(fn, unreal.MaterialExpressionIf, -700 + idx * 180, 2200)
        lib.connect(cell_in, "", cond, ["A"])
        lib.connect(lib.scalar_const(fn, float(idx), -700 + idx * 180, 2300), "", cond, ["B"])
        lib.connect(fields[idx], "", cond, ["A > B"])
        lib.connect(current, "", cond, ["A == B"])
        lib.connect(current, "", cond, ["A < B"])
        current = cond

    selected = current

    # ---------------- hard threshold ----------------
    # SmoothStep(Min, Max, Value). Softness as the edge width around 0.5:
    #   Min = 0.5 - Softness/2, Max = 0.5 + Softness/2, Value = field
    # Softness 0 collapses to a razor edge, which is the cel look we want.
    half_soft = lib.expr(fn, unreal.MaterialExpressionMultiply, -100, 2400)
    lib.connect(soft_in, "", half_soft, ["A"])
    lib.connect(lib.scalar_const(fn, 0.5, -100, 2480), "", half_soft, ["B"])

    lo = lib.expr(fn, unreal.MaterialExpressionSubtract, 40, 2360)
    lib.connect(lib.scalar_const(fn, 0.5, -100, 2560), "", lo, ["A"])
    lib.connect(half_soft, "", lo, ["B"])

    hi = lib.expr(fn, unreal.MaterialExpressionAdd, 40, 2560)
    lib.connect(lib.scalar_const(fn, 0.5, -100, 2640), "", hi, ["A"])
    lib.connect(half_soft, "", hi, ["B"])

    edge = lib.expr(fn, unreal.MaterialExpressionSmoothStep, 200, 2200)
    lib.connect(lo, "", edge, ["Min"])
    lib.connect(hi, "", edge, ["Max"])
    lib.connect(selected, "", edge, ["Value"])

    out_pattern = lib.add_function_output(fn, "Pattern", x=520, y=2160)
    lib.connect(selected, "", out_pattern, "")

    out_mask = lib.add_function_output(fn, "Mask", x=520, y=2280)
    lib.connect(edge, "", out_mask, "")

    lib.save(fn)
    lib.log(f"{NAME} built with {lib.function_expression_count(fn)} expressions")
    return fn
