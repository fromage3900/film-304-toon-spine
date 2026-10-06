"""Build M_Master_Toon_Face - skin shading with an authored shadow layer.

WHY ITS OWN MASTER
------------------
SH050 grades on "eyes, warm-violet halftone shadow ramp, micro-expressions".
Skin wants the face shadow to hold while the head turns - the anime trick,
where the terminator does not pop across the cheek - while the body stays
banded. An instance cannot carry a Toon Profile (measured 2026-10-02), so
"a different profile for skin" is only expressible as its own master: that is
the plan's test (TOON_MASTERS_PLAN_2026-10-04.md tier C).

WHAT IT REUSES (the spine contract)
-----------------------------------
MF_ColorRamp3 + MF_RampLUT behind bUsePaintedRamp, fresnel edge ink, the full
MF_ProceduralPatterns block (default off), MF_RimOffset wired exactly as
M_Master_Toon_Character wires it (RimEmissive additive on the Toon BSDF's
EmissiveColor pin, never BaseColor), and TP_Face bound at the end.

THE FACE SHADOW LAYER
---------------------
FaceShadowTint + FaceShadowMask lerp the ramped colour BEFORE the BSDF:
    shadow = lerp(ramped, FaceShadowTint, FaceShadowMask)
FaceShadowMask defaults 0 (inert) - it is a value/grade knob today, not a
lighting term: the profile still owns the band structure, so the face does
not gain a second terminator authority. A face MASK texture driving this pin
is lookdev work behind the content blocker (no face mask texture ships in
this project); inventing one now would be architecture ahead of content - the
same NOT YET rule M_Master_Toon_Character documents.

NO band_lerp: water's sine band and the landscape macro band are domain
behaviours of those surfaces; on a face they would fight the authored shadow
layer. ramp_switch -> shadow -> ink -> pattern, deliberately flat between.
"""
from __future__ import annotations

import unreal

import spine_lib as lib

NAME = "M_Master_Toon_Face"
MASTER_PROFILE = "TP_Face"
TEX_DIR = "/Game/Materials/Textures"

# Rim knobs, 1:1 with MF_RimOffset - names match M_Master_Toon_Character so a
# character-family instance override keys on the same surface.
RIM_SCALAR_PARAMS = [
    ("RimOffsetStrength", 0.60, "Normal bias - puts the edge on ONE side"),
    ("RimStart", 0.55, "Where the edge of light begins on the silhouette"),
    ("RimEnd", 0.92, "Where it ends"),
    ("RimSharpness", 2.20, "Edge tightness (Power exponent)"),
    ("RimStrength", 0.0, "0 = no rim (master inert until an instance opts in)"),
]
RIM_VECTOR_PARAMS = [
    ("RimColor", (1.0, 0.96, 0.90, 1.0), "Edge-of-light colour"),
    ("RimOffsetDir", (0.35, 0.0, 0.94, 0.0),
     "View-space direction the rim is biased toward"),
]


def build(rebuild=True):
    lib.log(f"=== {NAME} ===")
    mat = lib.get_or_create_material(NAME, rebuild=rebuild)

    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_SURFACE)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)

    # ---------------- parameters ----------------
    vec = {
        "BaseTint": lib.vector(mat, "BaseTint", "Surface", (0.42, 0.34, 0.34, 1.0),
                               -2000, -400, desc="Skin base (shadow family hue)"),
        "AccentTint": lib.vector(mat, "AccentTint", "Surface", (0.80, 0.70, 0.66, 1.0),
                                 -2000, -280, desc="Skin lit colour"),
        "InkColor": lib.vector(mat, "InkColor", "Ink", (0.06, 0.04, 0.06, 1.0),
                               -2000, -160, desc="Line / lash ink"),
        "FaceShadowTint": lib.vector(mat, "FaceShadowTint", "Face",
                                     (0.44, 0.34, 0.40, 1.0), -2000, -40,
                                     desc="Warm-violet authored face shadow"),
        "EmissiveColor": lib.vector(mat, "EmissiveColor", "Surface",
                                    (0.0, 0.0, 0.0, 1.0), -2000, 80,
                                    desc="Emission (eye glow etc.)"),
    }
    y = 200
    rim_vec = {}
    for pname, default, desc in RIM_VECTOR_PARAMS:
        rim_vec[pname] = lib.vector(mat, pname, "Rim", default, -2000, y, desc=desc)
        y += 120

    flt = {
        "RampStrength": lib.scalar(mat, "RampStrength", "Ramp", 0.70, -1400, 100,
                                   desc="0 bypasses the ramp; >0 applies the profile"),
        "InkIntensity": lib.scalar(mat, "InkIntensity", "Ink", 0.10, -1400, 170),
        "DryRoughness": lib.scalar(mat, "DryRoughness", "Surface", 0.65, -1400, 240),
        "FaceShadowMask": lib.scalar(mat, "FaceShadowMask", "Face", 0.0, -1400, 310,
                                     desc="0 = off (inert); >0 lerps the ramped "
                                          "colour toward FaceShadowTint"),
        "EmissiveIntensity": lib.scalar(mat, "EmissiveIntensity", "Surface",
                                        0.0, -1400, 380),
    }
    rim_flt = {}
    for pname, default, desc in RIM_SCALAR_PARAMS:
        rim_flt[pname] = lib.scalar(mat, pname, "Rim", default, -1400, 450 + 70 *
                                    [p for p, _, _ in RIM_SCALAR_PARAMS].index(pname),
                                    desc=desc)
    pat = {}
    for pname, pdef, py in (("PatternScale", 12.0, 1300),
                            ("PatternAngle", 0.0, 1370),
                            ("PatternIndex", 0.0, 1440),
                            ("PatternDensity", 0.50, 1510),
                            ("PatternStrength", 0.0, 1580),
                            ("PatternSoftness", 0.10, 1650)):
        pat[pname] = lib.scalar(mat, pname, "Pattern", pdef, -1400, py)

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

    # ---------------- ramp family (spine contract) ----------------
    ramp_slider = lib.expr(mat, unreal.MaterialExpressionMaterialFunctionCall,
                           -700, 120)
    ramp_slider.set_editor_property("material_function",
        unreal.load_asset(lib.asset_path(lib.FUNCTION_DIR, "MF_ColorRamp3")))
    lib.connect(vec["BaseTint"], "", ramp_slider, "BaseColor")
    lib.connect(vec["AccentTint"], "", ramp_slider, "ColorRamp")
    lib.connect(flt["RampStrength"], "", ramp_slider, "Mask")

    ramp_lut = lib.expr(mat, unreal.MaterialExpressionMaterialFunctionCall,
                        -700, 340)
    ramp_lut.set_editor_property("material_function",
        unreal.load_asset(lib.asset_path(lib.FUNCTION_DIR, "MF_RampLUT")))
    lib.connect(vec["BaseTint"], "", ramp_lut, "BaseColor")
    lib.connect(ramp_lut_tex, "", ramp_lut, "RampTexture")
    lib.connect(flt["RampStrength"], "", ramp_lut, "Mask")

    ramp_switch = lib.expr(mat, unreal.MaterialExpressionStaticSwitchParameter,
                           -460, 240)
    ramp_switch.set_editor_property("parameter_name", "bUsePaintedRamp")
    ramp_switch.set_editor_property("group", "Ramp")
    ramp_switch.set_editor_property("default_value", False)
    lib.connect(ramp_lut, "Color", ramp_switch, ["True"])
    lib.connect(ramp_slider, "Color", ramp_switch, ["False"])

    # ---------------- authored face shadow (BEFORE the BSDF) ----------------
    face_shadow = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate,
                           -240, 240)
    lib.ternary(ramp_switch, vec["FaceShadowTint"], flt["FaceShadowMask"],
                face_shadow)

    # ---------------- edge ink ----------------
    fresnel = lib.expr(mat, unreal.MaterialExpressionFresnel, -440, 480)
    ink_fres = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, -240, 480)
    lib.ternary(flt["InkIntensity"], lib.scalar_const(mat, 1.0, -240, 560),
                fresnel, ink_fres)

    with_ink = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, -60, 240)
    lib.ternary(face_shadow, vec["InkColor"], ink_fres, with_ink)
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

    # ---------------- rim (character-family domain behaviour) ----------------
    rim_call = lib.expr(mat, unreal.MaterialExpressionMaterialFunctionCall, 100, 700)
    rim_call.set_editor_property("material_function",
        unreal.load_asset(lib.asset_path(lib.FUNCTION_DIR, "MF_RimOffset")))
    rim_n = lib.expr(mat, unreal.MaterialExpressionPixelNormalWS, -60, 700)
    lib.connect(rim_n, "", rim_call, "Normal")
    lib.connect(rim_vec["RimColor"], "", rim_call, "RimColor")
    lib.connect(rim_vec["RimOffsetDir"], "", rim_call, "OffsetDir")
    lib.connect(rim_flt["RimOffsetStrength"], "", rim_call, "OffsetStrength")
    lib.connect(rim_flt["RimStart"], "", rim_call, "RimStart")
    lib.connect(rim_flt["RimEnd"], "", rim_call, "RimEnd")
    lib.connect(rim_flt["RimSharpness"], "", rim_call, "Sharpness")
    lib.connect(rim_flt["RimStrength"], "", rim_call, "RimStrength")

    # ---------------- emissive: base + rim additive ----------------
    emissive_mul = lib.expr(mat, unreal.MaterialExpressionMultiply, 300, 60)
    lib.connect(vec["EmissiveColor"], "", emissive_mul, ["A", "a"])
    lib.connect(flt["EmissiveIntensity"], "", emissive_mul, ["B", "b"])

    emissive_total = lib.expr(mat, unreal.MaterialExpressionAdd, 420, 60)
    lib.connect(emissive_mul, "", emissive_total, ["A", "a"])
    lib.connect(rim_call, "RimEmissive", emissive_total, ["B", "b"])
    lib.connect(emissive_total, "", toon, ["EmissiveColor"])

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
    """Profile read-back (lib.verify_material only reads it for Universal) and
    rim parameter presence - a rim call with its knobs missing from the graph
    would satisfy expected_calls while the edge of light is unreachable."""
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

    if result["error"] is None and profile != MASTER_PROFILE:
        result["error"] = (f"bound profile is {profile!r}, want "
                           f"{MASTER_PROFILE!r} - the face contract would "
                           f"not be in effect")

    if result["error"] is None:
        want = {n for n, _d, _x in RIM_SCALAR_PARAMS} | \
               {n for n, _d, _x in RIM_VECTOR_PARAMS} | {"FaceShadowMask"}
        have = set()
        for e in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
            if e is None:
                continue
            if type(e).__name__ in ("MaterialExpressionScalarParameter",
                                    "MaterialExpressionVectorParameter"):
                try:
                    have.add(str(e.get_editor_property("parameter_name")))
                except Exception:
                    pass
        missing = sorted(want - have)
        if missing:
            result["error"] = f"parameters missing from graph: {missing}"

    result["expression_count"] = lib.expression_count(mat)
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
                                              "MF_RimOffset"],
                              min_expressions=30)
    graph = verify()
    ok = mat is not None and res.get("ok") and graph.get("ok")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
