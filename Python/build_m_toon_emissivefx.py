"""Build M_Master_Toon_EmissiveFX - unlit pattern glow with an optional pulse.

WHY ITS OWN MASTER
------------------
Sigil glyphs, cymbal rings, beat markers (SH060/SH070): these glow, they do
not receive light. Routing them through a Toon BSDF would shade them by the
scene - wrong by definition. M_Toon_Unlit_Character is the plain unlit base;
this master ADDS the two things FX asks for that the plain unlit does not
have: a pattern mask (halftone / strokes / SDF via MF_ProceduralPatterns,
shared with the surface masters so the FX reads in the same ink family) and
a time pulse (sine over Time, the same node proven by M_Master_Toon_Water).

WHAT IT REUSES
--------------
unlit BSDF (MaterialExpressionSubstrateUnlitBSDF, BaseColor in) +
MP_FRONT_MATERIAL (M_Toon_Unlit_Character / M_Master_Toon_Sky pattern), Time
node + Sine proven on water, MF_ProceduralPatterns proven across the surface
spine.
NO Toon BSDF, NO Toon Profile - bind_toon_profile is deliberately not called;
verify() asserts the absence. NO ramp family: ramp needs lit/unlit structure
that does not exist on an unlit surface (and RampStrength would then be a
dead knob).

THE DOMAIN BEHAVIOUR: PULSE * PATTERN
--------------------------------------
pulse  = 1 + sin(Time * PulseRate * 2*pi?)  -- via MaterialExpressionSine with
         period 1.0 (water precedent), so PulseRate reads in Hz.
gate   = lerp(1.0, pattern_mask, PatternStrength)   -- PatternStrength 0 = no
         pattern contribution at all, matching the surface masters' inert
         default; unlike them this master's PATTERN DEFAULTS ON at 0.6 in the
         MI because FX is pattern by nature (the master itself keeps 0.6 as
         its authored value - see parameters).
final  = EmissiveColor * EmissiveIntensity * pulse * gate  -> unlit BaseColor
PulseDepth defaults 0.0: a pulse-free constant glow until an instance opts
in (inert-until-instance, the repo pattern).
"""
from __future__ import annotations

import math

import unreal

import spine_lib as lib

NAME = "M_Master_Toon_EmissiveFX"
TEX_DIR = "/Game/Materials/Textures"


def build(rebuild=True):
    lib.log(f"=== {NAME} ===")
    mat = lib.get_or_create_material(NAME, rebuild=rebuild)

    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_SURFACE)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)

    # ---------------- parameters ----------------
    vec = {
        "EmissiveColor": lib.vector(mat, "EmissiveColor", "FX",
                                    (1.0, 0.7, 0.9, 1.0), -1600, -400,
                                    desc="Glow colour"),
    }
    flt = {
        "EmissiveIntensity": lib.scalar(mat, "EmissiveIntensity", "FX",
                                        2.0, -1000, -400,
                                        desc="Overall glow multiplier"),
        "PulseRate": lib.scalar(mat, "PulseRate", "FX", 1.0, -1000, -330,
                                desc="Pulse frequency in Hz (Sine period 1.0)"),
        "PulseDepth": lib.scalar(mat, "PulseDepth", "FX", 0.0, -1000, -260,
                                 desc="0 = constant glow; >0 = sine amplitude"),
    }
    pat = {}
    for pname, pdef, py in (("PatternScale", 8.0, -1000),
                            ("PatternAngle", 0.0, -930),
                            ("PatternIndex", 0.0, -860),
                            ("PatternDensity", 0.55, -790),
                            ("PatternStrength", 0.6, -720),
                            ("PatternSoftness", 0.12, -650)):
        pat[pname] = lib.scalar(mat, pname, "Pattern", pdef, -1000, py)

    pat_sdf_tex = lib.expr(mat, unreal.MaterialExpressionTextureObjectParameter,
                           -1000, -580)
    pat_sdf_tex.set_editor_property("parameter_name", "PatternSDFMap")
    pat_sdf_tex.set_editor_property("group", "Pattern")
    pat_sdf_tex.set_editor_property(
        "texture", unreal.load_asset(lib.asset_path(TEX_DIR, "T_SDF_Strokes")))
    lib._desc(pat_sdf_tex, "Baked SDF stroke field for CellIndex 12")

    # ---------------- pulse: 1 + sin(2*pi * PulseRate * t) * PulseDepth ------
    time_n = lib.expr(mat, unreal.MaterialExpressionTime, -1000, 100)
    rate_t = lib.expr(mat, unreal.MaterialExpressionMultiply, -840, 100)
    lib.connect(time_n, "", rate_t, ["A", "a"])
    lib.connect(flt["PulseRate"], "", rate_t, ["B", "b"])
    wave = lib.expr(mat, unreal.MaterialExpressionSine, -680, 100)
    wave.set_editor_property("period", 1.0)
    lib.connect(rate_t, "", wave, ["Input", ""])
    wave_scaled = lib.expr(mat, unreal.MaterialExpressionMultiply, -520, 100)
    lib.connect(wave, "", wave_scaled, ["A", "a"])
    lib.connect(flt["PulseDepth"], "", wave_scaled, ["B", "b"])
    pulse = lib.expr(mat, unreal.MaterialExpressionAdd, -360, 100)
    lib.connect(wave_scaled, "", pulse, ["A", "a"])
    lib.connect(lib.scalar_const(mat, 1.0, -360, 180), "", pulse, ["B", "b"])

    # ---------------- pattern gate: lerp(1, mask, strength) -----------------
    pat_uv = lib.expr(mat, unreal.MaterialExpressionTextureCoordinate, -1000, 400)
    pat_call = lib.expr(mat, unreal.MaterialExpressionMaterialFunctionCall,
                        -680, 400)
    pat_call.set_editor_property("material_function",
        unreal.load_asset(lib.asset_path(lib.FUNCTION_DIR, "MF_ProceduralPatterns")))
    lib.connect(pat_uv, "", pat_call, "UV")
    lib.connect(pat["PatternScale"], "", pat_call, "Scale")
    lib.connect(pat["PatternAngle"], "", pat_call, "Angle")
    lib.connect(pat["PatternIndex"], "", pat_call, "CellIndex")
    lib.connect(pat["PatternSoftness"], "", pat_call, "Softness")
    lib.connect(pat_sdf_tex, "", pat_call, "SDFMap")
    lib.connect(pat["PatternDensity"], "", pat_call, "Density")

    gate = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, -360, 400)
    lib.connect(lib.scalar_const(mat, 1.0, -520, 460), "", gate, "A")
    lib.connect(pat_call, "Mask", gate, "B")
    lib.connect(pat["PatternStrength"], "", gate, "Alpha")

    # ---------------- final = EmissiveColor * Intensity * pulse * gate -------
    c_i = lib.expr(mat, unreal.MaterialExpressionMultiply, -200, -300)
    lib.connect(vec["EmissiveColor"], "", c_i, ["A", "a"])
    lib.connect(flt["EmissiveIntensity"], "", c_i, ["B", "b"])

    p_g = lib.expr(mat, unreal.MaterialExpressionMultiply, -200, 200)
    lib.connect(pulse, "", p_g, ["A", "a"])
    lib.connect(gate, "", p_g, ["B", "b"])

    final = lib.expr(mat, unreal.MaterialExpressionMultiply, -40, 0)
    lib.connect(c_i, "", final, ["A", "a"])
    lib.connect(p_g, "", final, ["B", "b"])

    # ---------------- unlit BSDF (M_Toon_Unlit_Character / Sky pattern) ------
    # SubstrateUnlitBSDF directly, BaseColor in - the pattern build_m_toon_sky
    # and build_m_toon_unlit already prove. The earlier MaterialFunctionCall to
    # /Engine/Functions/Engine_MaterialFunctions02/Shading/BasicShading/Unlit
    # was wrong: no such function exists in UE 5.8 ("Failed to find object",
    # build log 2026-10-06), the call saved with a null function, and verify()
    # correctly failed "glow unreachable". Instantiation success is not
    # engine truth; this node is.
    unlit = lib.expr(mat, unreal.MaterialExpressionSubstrateUnlitBSDF, 300, 0)
    lib.connect(final, "", unlit, "BaseColor")
    lib.connect_property(unlit, unreal.MaterialProperty.MP_FRONT_MATERIAL)

    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
    except Exception as exc:
        lib.log(f"recompile warning: {exc}")

    # NO bind_toon_profile: unlit surface, no Toon BSDF - verify() asserts this.

    lib.save(mat)
    lib.log(f"{NAME} built with {lib.expression_count(mat)} expressions")
    return mat


def verify():
    """Unlit BSDF present, NO Toon BSDF / profile - the mirror of the TP
    masters' profile assertion."""
    path = lib.asset_path(lib.MASTER_DIR, NAME)
    mat = unreal.load_asset(path)
    result = {"name": NAME, "ok": False, "error": None}

    if mat is None:
        result["error"] = "does not load"
        lib.log(f"VERIFY {NAME}: FAIL {result['error']}")
        return result

    have_toon = False
    have_unlit = False
    for n in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
        t = type(n).__name__
        if t == "MaterialExpressionSubstrateToonBSDF":
            have_toon = True
        if t == "MaterialExpressionSubstrateUnlitBSDF":
            have_unlit = True
    result["expression_count"] = lib.expression_count(mat)

    if have_toon:
        result["error"] = "Toon BSDF present on an unlit FX master - it would "\
                          "receive light it must not"
    elif not have_unlit:
        result["error"] = "no Substrate Unlit BSDF in the graph - glow unreachable"

    if result["error"] is None:
        result["ok"] = True
    lib.log(f"VERIFY {NAME}: ok={result['ok']} {result['error'] or ''}")
    return result


def main() -> int:
    mat = build()
    res = lib.verify_material(NAME,
                              expected_calls=["MF_ProceduralPatterns"],
                              min_expressions=12)
    graph = verify()
    ok = mat is not None and res.get("ok") and graph.get("ok")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
