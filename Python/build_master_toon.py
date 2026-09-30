"""Build M_Master_Toon_Universal - the 304 film toon spine master.

RECONSTRUCTED, NOT COPIED. Parameter surface recovered from the source master on
2026-09-29 via binary name-table scan; groups preserved exactly so the same
material instances authored against the source still resolve.

Substrate Toon BSDF is UE 5.8's experimental cel-shading path. In 5.8 the node
is MaterialExpressionSubstrateToonBSDF and its output goes to
MP_FRONT_MATERIAL - the legacy lit outputs (BaseColor/Roughness/Emissive) are
deliberately NOT wired, because Substrate owns the surface response once
FrontMaterial is connected.

Outlines are NOT part of this shader. Edge lines stay a separate pass (overlay
material or post-process depth/normal edge detect); InkIntensity/InkColor here
tint the surface only.
"""
from __future__ import annotations

import unreal

import spine_lib as lib

NAME = "M_Master_Toon_Universal"

# (param_name, group, default, description) - recovered from the source master
SURFACE_PARAMS = [
    ("BaseTint", "Palette", (0.55, 0.48, 0.42, 1.0), "Base surface colour"),
    ("AccentTint", "Palette", (0.72, 0.62, 0.52, 1.0), "Second colour for ramp/blend"),
    ("InkColor", "Palette", (0.05, 0.08, 0.15, 1.0), "Ink line / pooling colour"),
    ("GoldTint", "Palette", (0.85, 0.65, 0.25, 1.0), "Gilding colour"),
]

FLOAT_PARAMS = [
    ("UVScale", "UV", 1.0, "Texture tiling"),
    ("UVRotation", "UV", 0.0, "Texture rotation in degrees"),
    ("ParallaxScale", "Parallax", 0.04, "Height-map parallax amount"),
    ("ParallaxSteps", "Parallax", 8.0, "Parallax step count"),
    ("ParallaxHeight", "Parallax", 0.04, "Height contribution to WPO"),
    ("GildingStrength", "Gilding", 0.0, "Gold-leaf overlay amount"),
    ("GoldEmissive", "Gilding", 0.0, "Gold emissive boost"),
    ("OilPaintStrength", "OilPaint", 0.0, "Impasto/oil blend amount"),
    ("StrokeStrength", "OilPaint", 0.55, "Brush-stroke breakup"),
    ("BrushScale", "OilPaint", 0.045, "Brush texture scale"),
    ("TemporalStrength", "Temporal", 0.0, "Hand-drawn temporal wobble"),
    ("WindSpeed", "Temporal", 0.15, "Wind animation speed"),
    ("NoiseScale", "Temporal", 1.5, "Temporal noise scale"),
    ("SmearStrength", "Temporal", 0.0, "Temporal smear"),
    ("BoilIntensity", "Temporal", 0.0, "Line boil (hand-drawn shimmer)"),
    ("InkIntensity", "Surface", 0.0, "Ink line intensity"),
    ("PoolingStrength", "Surface", 0.5, "Ink pooling in creases"),
    ("Wetness", "Surface", 0.0, "Wetness: blends dry/wet roughness"),
    ("OrnamentStyle", "Ornament", 0.0, "Ornament style index"),
    ("OrnamentScale", "Ornament", 1.0, "Ornament scale"),
    ("CurvatureSensitivity", "Ornament", 2.0, "Curvature response for ornament"),
    ("AudioReactivity", "Audio", 0.0, "Audio-reactive amount"),
    ("BassWeight", "Audio", 1.0, "Bass band weight"),
    ("MidWeight", "Audio", 0.5, "Mid band weight"),
    ("TrebleWeight", "Audio", 0.25, "Treble band weight"),
    ("DryRoughness", "Surface", 0.78, "Dry surface roughness"),
    ("WetRoughness", "Surface", 0.25, "Wet surface roughness"),
    ("EdgeStrength", "Outline", 1.0, "Outline strength reference"),
    ("BandScale", "SDF", 0.035, "World-space band frequency"),
    ("BandStrength", "SDF", 0.12, "World-space band depth"),
]


def build(rebuild=True):
    lib.log(f"=== {NAME} ===")
    mat = lib.get_or_create_material(NAME, rebuild=rebuild)

    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_SURFACE)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    lib.try_set(mat, "bUsesSubstrate", True)

    # ---------------- parameters ----------------
    # Artist-painted 1D ramp LUT, used when bUsePaintedRamp = 1.
    ramp_lut_tex = lib.texture_param(mat, "RampTexture", "Ramp", -1400, -600,
                                     desc="Painted 1D band ramp (horizontal strip)")

    vec = {}
    y = -400
    for pname, group, default, desc in SURFACE_PARAMS:
        vec[pname] = lib.vector(mat, pname, group, default, -2000, y, desc=desc)
        y += 120

    flt = {}
    for i, (pname, group, default, desc) in enumerate(FLOAT_PARAMS):
        flt[pname] = lib.scalar(mat, pname, group, default, -2000, y)
        y += 70

    # ---------------- world-space band mask (SDF-ish relief) ----------------
    world = lib.expr(mat, unreal.MaterialExpressionWorldPosition, -1600, 400)
    xy = lib.expr(mat, unreal.MaterialExpressionComponentMask, -1440, 400)
    xy.set_editor_property("r", True)
    xy.set_editor_property("g", True)
    xy.set_editor_property("b", False)
    xy.set_editor_property("a", False)
    lib.connect(world, "", xy, "")

    band_scale_mul = lib.expr(mat, unreal.MaterialExpressionMultiply, -1280, 400)
    lib.binary(xy, flt["BandScale"], band_scale_mul)

    sin_n = lib.expr(mat, unreal.MaterialExpressionSine, -1120, 400)
    sin_n.set_editor_property("period", 1.0)
    lib.unary(band_scale_mul, sin_n)

    abs_n = lib.expr(mat, unreal.MaterialExpressionAbs, -960, 400)
    lib.unary(sin_n, abs_n)

    band_mask = lib.expr(mat, unreal.MaterialExpressionMultiply, -800, 400)
    lib.binary(abs_n, flt["BandStrength"], band_mask)

    # ---------------- palette blend: ramp family, switchable ----------------
    # bUsePaintedRamp: 0 = MF_ColorRamp3 (slider bands), 1 = MF_RampLUT
    # (artist-painted 1D ramp). Both share the BaseColor/ColorRamp/Mask
    # signature, so the switch is a pure substitution.
    mask_default = lib.scalar_const(mat, 0.0, -1000, 740)
    # The ramp is a real MaterialFunctionCall, not inline math: that keeps one
    # authored source of truth for band shape across the whole spine, and it is
    # what the original master did.
    ramp_slider = lib.expr(mat, unreal.MaterialExpressionMaterialFunctionCall,
                           -700, 180)
    ramp_slider.set_editor_property("material_function",
        unreal.load_asset(lib.asset_path(lib.FUNCTION_DIR, "MF_ColorRamp3")))
    lib.connect(vec["BaseTint"], "", ramp_slider, "BaseColor")
    lib.connect(vec["AccentTint"], "", ramp_slider, "ColorRamp")
    lib.connect(mask_default, "", ramp_slider, "Mask")

    ramp_lut = lib.expr(mat, unreal.MaterialExpressionMaterialFunctionCall,
                        -700, 400)
    ramp_lut.set_editor_property("material_function",
        unreal.load_asset(lib.asset_path(lib.FUNCTION_DIR, "MF_RampLUT")))
    lib.connect(vec["BaseTint"], "", ramp_lut, "BaseColor")
    lib.connect(ramp_lut_tex, "", ramp_lut, "RampTexture")
    lib.connect(mask_default, "", ramp_lut, "Mask")

    ramp_switch = lib.expr(mat, unreal.MaterialExpressionStaticSwitchParameter,
                           -460, 300)
    ramp_switch.set_editor_property("parameter_name", "bUsePaintedRamp")
    ramp_switch.set_editor_property("group", "Ramp")
    ramp_switch.set_editor_property("default_value", False)
    lib.connect(ramp_lut, "Color", ramp_switch, ["True"])
    lib.connect(ramp_slider, "Color", ramp_switch, ["False"])

    oil_blend = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, -240, 300)
    lib.connect(ramp_switch, "", oil_blend, "A")

    oil_mod = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, -120, 300)
    lib.ternary(vec["BaseTint"], oil_blend, flt["OilPaintStrength"], oil_mod)

    # ---------------- band lerp into colour ----------------
    band_lerp = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, 60, 300)
    lib.ternary(oil_mod, vec["AccentTint"], band_mask, band_lerp)

    # ---------------- gilding ----------------
    gild_col = lib.expr(mat, unreal.MaterialExpressionMultiply, -600, 640)
    lib.binary(flt["GildingStrength"], vec["GoldTint"], gild_col)

    with_gild = lib.expr(mat, unreal.MaterialExpressionAdd, 240, 300)
    lib.binary(band_lerp, gild_col, with_gild)

    # ---------------- ink ----------------
    with_ink = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, 420, 300)
    lib.ternary(with_gild, vec["InkColor"], flt["InkIntensity"], with_ink)

    # ---------------- temporal wobble ----------------
    const_t = lib.expr(mat, unreal.MaterialExpressionConstant3Vector, 120, 520)
    const_t.set_editor_property("constant",
                               unreal.LinearColor(0.02, 0.02, 0.03, 1.0))
    temporal_vec = lib.expr(mat, unreal.MaterialExpressionMultiply, 280, 520)
    lib.binary(flt["TemporalStrength"], const_t, temporal_vec)

    final_color = lib.expr(mat, unreal.MaterialExpressionAdd, 600, 300)
    lib.binary(with_ink, temporal_vec, final_color)

    # ---------------- roughness: dry <-> wet ----------------
    rough = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, 600, 520)
    lib.ternary(flt["DryRoughness"], flt["WetRoughness"], flt["Wetness"], rough)

    # ---------------- normal ----------------
    normal = lib.expr(mat, unreal.MaterialExpressionPixelNormalWS, 600, 640)

    # ---------------- parallax WPO ----------------
    height_mul = lib.expr(mat, unreal.MaterialExpressionMultiply, -600, 880)
    lib.binary(flt["ParallaxHeight"], flt["ParallaxScale"], height_mul)

    vertex_n = lib.expr(mat, unreal.MaterialExpressionVertexNormalWS, -600, 980)
    wpo = lib.expr(mat, unreal.MaterialExpressionMultiply, -300, 900)
    lib.binary(height_mul, vertex_n, wpo)
    lib.connect_property(wpo, unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)

    # ---------------- Substrate Toon BSDF ----------------
    toon = lib.expr(mat, unreal.MaterialExpressionSubstrateToonBSDF, 700, 240)
    lib.connect(final_color, "", toon, ["BaseColor", "DiffuseColor"])
    lib.connect(rough, "", toon, ["Roughness"])
    lib.connect(normal, "", toon, ["Normal", "TangentNormal", "NormalMap"])
    lib.connect_property(toon, unreal.MaterialProperty.MP_FRONT_MATERIAL)

    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
    except Exception as exc:
        lib.log(f"recompile warning: {exc}")

    lib.save(mat)
    lib.log(f"{NAME} built with {lib.expression_count(mat)} expressions")
    return mat
