"""Build M_Master_Toon_Glass - toon interior + fresnel-only edge.

WHY ITS OWN MASTER
------------------
SH020/SH040 (window light, bottle close-up): glass wants the cel bands
INSIDE the pane and an edge that brightens toward the silhouette while the
BODY stays see-through. Adding Opacity to M_Master_Toon_Character would
change BLEND_OPAQUE on every character instance - a cross-domain edit the
plan forbids (TOON_MASTERS_PLAN_2026-10-04.md tier C, "an instance cannot
change domain behaviour").

WHAT IT REUSES (the spine contract)
-----------------------------------
MF_ColorRamp3 + MF_RampLUT behind bUsePaintedRamp, fresnel edge ink, the full
MF_ProceduralPatterns block (default off) - NO rim (MF_RimOffset is a
character-family behaviour; glass edges are fresnel, not normal-biased), and
TP_Glass bound at the end. RampStrength defaults 0.70 here (water precedent -
new masters start IN their regime); the 0-default on the five shipped masters
was legacy-look preservation and does not apply to a master created today.

THE DOMAIN BEHAVIOUR: OPACITY
-----------------------------
fres_pow  = Power(fresnel, FresnelPower)
opacity   = lerp(OpacityBase, 1.0, fres_pow)   -> transparent core, solid edge
edge glow = FresnelColor * fres_pow             -> additive on EmissiveColor
The opacity path is attempted as a SUBSTRATE OPACITY PIN, in this order:
  1. connect to the Toon BSDF's "Opacity" input;
  2. if that pin does not exist (API/substrate version), FAIL LOUD: log a
     WARN naming the master, set BLEND_TRANSLUCENT anyway, and FALL BACK TO
     THE WATER LERP: BaseColor lerps toward FresnelColor by fres_pow, so the
     edge still reads as glass without an alpha term. This is a defined
     fallback, not a silent success - verify() records which path took and
     asserts blend_mode == BLEND_TRANSLUCENT either way.
Per the owner's rule (2026-10-05): prefer loud failure; defined fallback for
glass opacity only.
"""
from __future__ import annotations

import unreal

import spine_lib as lib

NAME = "M_Master_Toon_Glass"
MASTER_PROFILE = "TP_Glass"
TEX_DIR = "/Game/Materials/Textures"

# Set by build() so verify() can report which path took.
_opacity_path = "unresolved"


def build(rebuild=True):
    global _opacity_path
    _opacity_path = "unresolved"
    lib.log(f"=== {NAME} ===")
    mat = lib.get_or_create_material(NAME, rebuild=rebuild)

    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_SURFACE)
    # Set BEFORE wiring: if the opacity pin is missing we stay translucent
    # and let the water-lerp fallback carry the edge (see module docstring).
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("two_sided", True)

    # ---------------- parameters ----------------
    vec = {
        "BaseTint": lib.vector(mat, "BaseTint", "Surface", (0.55, 0.72, 0.78, 1.0),
                               -2000, -400, desc="Glass body colour (interior)"),
        "AccentTint": lib.vector(mat, "AccentTint", "Surface", (0.75, 0.88, 0.92, 1.0),
                                 -2000, -280, desc="Ramp lit colour"),
        "InkColor": lib.vector(mat, "InkColor", "Ink", (0.10, 0.14, 0.16, 1.0),
                               -2000, -160, desc="Edge / mullion ink"),
        "FresnelColor": lib.vector(mat, "FresnelColor", "Surface",
                                   (0.75, 0.90, 1.00, 1.0), -2000, -40,
                                   desc="Edge-of-silhouette glow colour"),
    }
    flt = {
        "FresnelPower": lib.scalar(mat, "FresnelPower", "Surface", 4.0, -1400, 100,
                                   desc="Edge tightness (Power exponent)"),
        "OpacityBase": lib.scalar(mat, "OpacityBase", "Surface", 0.30, -1400, 170,
                                  desc="Body opacity at the centre (0 = fully clear)"),
        "RampStrength": lib.scalar(mat, "RampStrength", "Ramp", 0.70, -1400, 240,
                                   desc="0 bypasses the ramp; >0 applies the profile"),
        "InkIntensity": lib.scalar(mat, "InkIntensity", "Ink", 0.10, -1400, 310),
        "DryRoughness": lib.scalar(mat, "DryRoughness", "Surface", 0.08, -1400, 380),
    }
    pat = {}
    for pname, pdef, py in (("PatternScale", 14.0, 1300),
                            ("PatternAngle", 45.0, 1370),
                            ("PatternIndex", 0.0, 1440),
                            ("PatternDensity", 0.60, 1510),
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

    # ---------------- edge ink ----------------
    fresnel = lib.expr(mat, unreal.MaterialExpressionFresnel, -440, 480)
    ink_fres = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, -240, 560)
    lib.ternary(flt["InkIntensity"], lib.scalar_const(mat, 1.0, -240, 640),
                fresnel, ink_fres)

    with_ink = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, -60, 240)
    lib.ternary(ramp_switch, vec["InkColor"], ink_fres, with_ink)
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
                         80, 240)
    lib.connect(final_color, "", patterned, "A")
    lib.connect(vec["InkColor"], "", patterned, "B")
    lib.connect(pat_amt, "", patterned, "Alpha")
    final_color = patterned

    # ---------------- fresnel opacity (the domain behaviour) ----------------
    fres_pow = lib.expr(mat, unreal.MaterialExpressionPower, -240, 760)
    lib.binary(fresnel, flt["FresnelPower"], fres_pow)

    opacity = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, -60, 760)
    lib.connect(flt["OpacityBase"], "", opacity, "A")
    lib.connect(lib.scalar_const(mat, 1.0, -60, 840), "", opacity, "B")
    lib.connect(fres_pow, "", opacity, "Alpha")

    edge_glow = lib.expr(mat, unreal.MaterialExpressionMultiply, -60, 640)
    lib.connect(vec["FresnelColor"], "", edge_glow, ["A", "a"])
    lib.connect(fres_pow, "", edge_glow, ["B", "b"])

    # ---------------- Substrate Toon BSDF ----------------
    toon = lib.expr(mat, unreal.MaterialExpressionSubstrateToonBSDF, 500, 200)
    lib.connect(final_color, "", toon, ["BaseColor", "DiffuseColor"])
    lib.connect(flt["DryRoughness"], "", toon, ["Roughness"])
    normal = lib.expr(mat, unreal.MaterialExpressionPixelNormalWS, 300, 420)
    lib.connect(normal, "", toon, ["Normal", "TangentNormal", "NormalMap"])
    lib.connect(edge_glow, "", toon, ["EmissiveColor"])

    # --- opacity pin attempt (strict first, defined fallback second) --------
    wired = False
    try:
        wired = lib.connect(opacity, "", toon, ["Opacity"])
    except Exception as exc:
        lib.log(f"WARN {NAME}: Opacity pin attempt raised {str(exc)[:120]}")
        wired = False
    if wired:
        _opacity_path = "toon_opacity_pin"
    else:
        _opacity_path = "water_lerp_fallback"
        lib.log(f"WARN {NAME}: SubstrateToonBSDF exposes no Opacity pin in "
                f"this engine build - falling back to the water-lerp edge "
                f"(BaseColor lerps toward FresnelColor by fres_pow); alpha "
                f"term NOT wired. blend_mode stays BLEND_TRANSLUCENT.")
        edge_lerp = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate,
                             240, 380)
        lib.connect(final_color, "", edge_lerp, "A")
        lib.connect(vec["FresnelColor"], "", edge_lerp, "B")
        lib.connect(fres_pow, "", edge_lerp, "Alpha")
        # reconnect BaseColor to the fallback lerp
        for pin in ("BaseColor", "DiffuseColor"):
            try:
                if lib.connect(edge_lerp, "", toon, [pin]):
                    break
            except Exception:
                continue

    lib.connect_property(toon, unreal.MaterialProperty.MP_FRONT_MATERIAL)

    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
    except Exception as exc:
        lib.log(f"recompile warning: {exc}")

    # ---------------- the Toon Profile (spine contract: bind LAST) ----------
    lib.bind_toon_profile(mat, MASTER_PROFILE)

    lib.save(mat)
    lib.log(f"{NAME} built ({lib.expression_count(mat)} expressions) "
            f"opacity_path={_opacity_path}")
    return mat


def verify():
    """Profile read-back, blend_mode read-back, and which opacity path took."""
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
                           f"{MASTER_PROFILE!r} - the glass contract would "
                           f"not be in effect")

    if result["error"] is None:
        try:
            blend = mat.get_editor_property("blend_mode")
            result["blend_mode"] = str(blend)
            if blend != unreal.BlendMode.BLEND_TRANSLUCENT:
                result["error"] = (f"blend_mode is {blend}, want "
                                   f"BLEND_TRANSLUCENT - glass would render opaque")
        except Exception as exc:
            result["error"] = f"blend_mode read: {str(exc)[:80]}"

    result["opacity_path"] = _opacity_path
    result["expression_count"] = lib.expression_count(mat)
    if result["error"] is None:
        result["ok"] = True

    lib.log(f"VERIFY {NAME}: ok={result['ok']} profile={profile} "
            f"blend={result.get('blend_mode')} path={_opacity_path} "
            f"{result['error'] or ''}")
    return result


def main() -> int:
    mat = build()
    res = lib.verify_material(NAME,
                              expected_calls=["MF_ColorRamp3", "MF_RampLUT",
                                              "MF_ProceduralPatterns"],
                              min_expressions=20)
    graph = verify()
    ok = mat is not None and res.get("ok") and graph.get("ok")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
