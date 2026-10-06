"""Build M_Master_Toon_Character - the character spine master.

WHY A SECOND MASTER
-------------------
Two reasons, and only the first is load-bearing.

1. THE SHADING CONTRACT. A material instance cannot carry its own Toon Profile
   on this engine build - measured, not assumed (TOON_EXPANSION_2026-10-02.md,
   "Open decision: per-family Toon Profiles"; toon_profile_binding_probe_v3.json).
   Every instance therefore inherits whatever profile its MASTER binds. The
   result was that the whole profile library was inert: all 26 MI_Toon_* looked
   at TP_Default, while TP_Melusina, TP_Hero and TP_Character sat authored and
   never reached a pixel. Binding TP_Melusina here is what makes the film's
   declared character contract real.

   That contract is not a taste call. Three independent authorities name it:
     * the shot manifest - framing_standard.shading_pipeline.toon_profile =
       "TP_Melusina", shadow_tint_hex = "#352D40";
     * Humber_FinalYear_Prep/GROUP_STAGING_GUIDE.md section 3 - character
       shading must use TP_Melusina's warm-violet ramp;
     * Tools/dogfood_toon_spine.py step 4 asserts both of those.

   `M_Master_Toon_Universal` binds TP_Default by design - it is the fallback
   master ("anything with no better answer") and cannot be retargeted without
   moving every environment surface at once.

2. THE OFFSET RIM. Characters in a toon film separate from the background by an
   edge of light, not by being lit differently - the Spice Frontier route
   described in Docs/FILM_PIPELINE.md, whose whole takeaway we already own as
   MF_RimOffset. Universal does not call that function, so no instance of
   Universal can reach a rim; it is a wiring absence, not a value. The rim is
   the domain behaviour that makes this a master rather than a profile swap.

WHAT IT REUSES (the spine contract)
-----------------------------------
Identical to M_Master_Toon_Universal: MF_ColorRamp3 + MF_RampLUT behind
bUsePaintedRamp, Mask driven by RampStrength (default 0 = ramp inert, which is
the fix from 2026-10-03), oil blend, world-space band, gilding, ink toward
InkColor, temporal wobble, the full MF_ProceduralPatterns block with its
shadow-driven hatch density, dry/wet roughness, parallax WPO, contact shadow,
and the Substrate Toon BSDF on MP_FRONT_MATERIAL.

The parameter LISTS are imported from build_master_toon rather than retyped.
Parameter names and groups are a public contract - they are what every instance
override keys on - so a rename or a group change must land in both masters or
the instances silently fall back to defaults. Graph topology is re-declared
here (that is the established pattern: build_master_toon_water.py and
build_master_toon_foliage.py are each self-contained files), but the parameter
surface has exactly one source of truth.

THE RIM
-------
Seven parameters, default OFF (RimStrength = 0.0), so the master is inert for
rim until an artist opts in. The call feeds RimEmissive into the Toon BSDF's
EmissiveColor pin alongside EmissiveColor*EmissiveIntensity - additive, never
into BaseColor, exactly as MF_RimOffset's own contract demands (its docstring
forbids a BaseColor input so nobody can wire it wrong). RimMask is left
unconnected on purpose: it exists for debug/visualisation at the function level.

RimStrength is deliberately NOT gated by EmissiveIntensity. EmissiveIntensity
is the troffer/screen knob and defaults to 0; folding the rim into it would
mean every character was unlit-edge by default with no way to see it.

PROFILES
--------
Binds TP_Melusina at the master level. The profile a master binds IS its
shading contract - instances cannot switch it (measured 2026-10-02).

NOT YET (deliberate)
--------------------
Face/role tint needs face-vs-body masks that no texture in this project ships
yet; inventing them would be architecture ahead of content. Warm terminator
wrap cannot be built at all: SubstrateToonBSDF owns lighting and exposes only
BaseColor/Metallic/Specular/Roughness/Normal/EmissiveColor/PatternUVs/
Anisotropy/Tangent - there is no diffuse-wrap pin, so a wrap in the graph would
be a second terminator authority fighting the profile. Both belong to the
profile, not to a material graph.
"""
from __future__ import annotations

import unreal

import spine_lib as lib

# The parameter surface is Universal's, by import - see module docstring.
from build_master_toon import SURFACE_PARAMS, FLOAT_PARAMS

NAME = "M_Master_Toon_Character"

# The film's canonical character profile (manifest + GROUP_STAGING_GUIDE.md +3
# dogfood_toon_spine.py all name it). See module docstring.
MASTER_PROFILE = "TP_Melusina"

TEX_DIR = "/Game/Materials/Textures"

# (param_name, group, default, description, function_input)
# The five rim knobs that map 1:1 onto MF_RimOffset; RimColor and RimOffsetDir
# are vectors and live in RIM_VECTOR below.
RIM_SCALAR_PARAMS = [
    ("RimOffsetStrength", 0.60,
     "How far the normal is biased - this is what puts the edge on ONE side "
     "and makes it an offset rim rather than a Fresnel"),
    ("RimStart", 0.55, "Where the edge of light begins on the silhouette"),
    ("RimEnd", 0.92, "Where it ends; RimStart..RimEnd is the edge width"),
    ("RimSharpness", 2.20, "Edge tightness (Power exponent)"),
    # Default OFF. The master ships inert for rim; MI_Toon_Melusina opts in.
    ("RimStrength", 0.0, "Rim amount; 0 = no rim, >0 = additive edge of light"),
]

RIM_VECTOR_PARAMS = [
    ("RimColor", (1.0, 0.96, 0.90, 1.0), "Edge-of-light colour"),
    # VIEW space, fixed. (0,0,1) is centred on camera; x pushes the light to
    # one side. This is the control that makes the term an *offset* rim - and
    # because it is view-space it never moves with the scene lights.
    ("RimOffsetDir", (0.35, 0.0, 0.94, 0.0),
     "View-space direction the rim is biased toward"),
]


def build(rebuild=True):
    lib.log(f"=== {NAME} ===")
    mat = lib.get_or_create_material(NAME, rebuild=rebuild)

    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_SURFACE)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    lib.try_set(mat, "bUsesSubstrate", True)

    # ---------------- parameters ----------------
    # Painted-ramp texture: TextureObjectParameter, not a sample parameter -
    # the function input is texture2D and a sample would pass the sampled
    # float3 ("Cannot cast from float3 to texture2D"). See build_master_toon.
    ramp_lut_tex = lib.expr(mat, unreal.MaterialExpressionTextureObjectParameter,
                            -1400, -600)
    ramp_lut_tex.set_editor_property("parameter_name", "RampTexture")
    ramp_lut_tex.set_editor_property("group", "Ramp")
    ramp_lut_tex.set_editor_property(
        "texture",
        unreal.load_asset(lib.asset_path(TEX_DIR, "T_Ramp_Smooth")))
    lib._desc(ramp_lut_tex, "Painted 1D band ramp (horizontal strip)")

    vec = {}
    y = -400
    for pname, group, default, desc in SURFACE_PARAMS:
        vec[pname] = lib.vector(mat, pname, group, default, -2000, y, desc=desc)
        y += 120

    flt = {}
    for pname, group, default, desc in FLOAT_PARAMS:
        flt[pname] = lib.scalar(mat, pname, group, default, -2000, y)
        y += 70

    # ---------------- rim parameters ----------------
    rim_vec = {}
    for pname, default, desc in RIM_VECTOR_PARAMS:
        rim_vec[pname] = lib.vector(mat, pname, "Rim", default, -2000, y,
                                    desc=desc)
        y += 120

    rim_flt = {}
    for pname, default, desc in RIM_SCALAR_PARAMS:
        rim_flt[pname] = lib.scalar(mat, pname, "Rim", default, -2000, y,
                                    desc=desc)
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
    # (artist-painted 1D ramp). RampStrength is the Mask on BOTH, so the ramp
    # is genuinely reachable - at 0 it returns BaseColor unchanged, which is
    # the fix from 2026-10-03 that stopped the ramp being structurally valid
    # and semantically empty.
    #
    # Created explicitly, not via FLOAT_PARAMS: Universal declares it inline
    # for the same reason (it only makes sense alongside the ramp call), and
    # every MI_Toon_* override keys on the NAME. Missing it here would not
    # raise - it would leave the profile's ramp permanently inert on every
    # character, because lerp(base, ramp, 0) is base.
    ramp_strength = lib.scalar(mat, "RampStrength", "Ramp", 0.0, -1000, 740,
                               desc="0 bypasses the ramp (legacy look); >0 "
                                    "applies MF_ColorRamp3/MF_RampLUT shaping")
    mask_default = ramp_strength

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

    # ---------------- surface pattern (MF_ProceduralPatterns) ----------------
    pat_uv = lib.expr(mat, unreal.MaterialExpressionTextureCoordinate, -1200, 1600)
    pat_call = lib.expr(mat, unreal.MaterialExpressionMaterialFunctionCall,
                        -820, 1600)
    pat_call.set_editor_property("material_function",
        unreal.load_asset(lib.asset_path(lib.FUNCTION_DIR, "MF_ProceduralPatterns")))

    pat_scale = lib.scalar(mat, "PatternScale", "Pattern", 12.0, -1240, 1720,
                           desc="Pattern frequency (cells per UV unit)")
    pat_angle = lib.scalar(mat, "PatternAngle", "Pattern", 0.0, -1240, 1800,
                           desc="Pattern rotation in degrees")
    pat_index = lib.scalar(mat, "PatternIndex", "Pattern", 0.0, -1240, 1880,
                           desc="0 halftone 1 checker 2 stripes 3 crackle 4 ink "
                                "5 crosshatch 6 stipple 7 rings 8 voronoi 9 grid "
                                "10 perforation 11 weave 12 sdfmap")
    pat_density = lib.scalar(mat, "PatternDensity", "Pattern", 0.5, -1240, 1960,
                             desc="Ink coverage 0..1 - raise in shadow")
    pat_strength = lib.scalar(mat, "PatternStrength", "Pattern", 0.0, -1240, 2040,
                              desc="Pattern ink strength; 0 = off")
    # Softness MUST be connected - an unwired function input is a hard compile
    # error ("Missing function input 'Softness'") that falls back to the
    # default material and renders every surface black.
    pat_softness = lib.scalar(mat, "PatternSoftness", "Pattern", 0.10,
                              -1240, 2100,
                              desc="Pattern edge softness; 0 = razor sharp")
    # CellIndex 12 samples this texture2D; TextureObjectParameter for the same
    # reason RampTexture is one. T_SDF_Strokes is generated by build_textures.py
    # (project content, not a banned /Engine placeholder).
    pat_sdf_tex = lib.expr(mat, unreal.MaterialExpressionTextureObjectParameter,
                           -1240, 2360)
    pat_sdf_tex.set_editor_property("parameter_name", "PatternSDFMap")
    pat_sdf_tex.set_editor_property("group", "Pattern")
    pat_sdf_tex.set_editor_property(
        "texture",
        unreal.load_asset(lib.asset_path(TEX_DIR, "T_SDF_Strokes")))
    lib._desc(pat_sdf_tex, "Baked SDF stroke field for CellIndex 12")

    lib.connect(pat_uv, "", pat_call, "UV")
    lib.connect(pat_scale, "", pat_call, "Scale")
    lib.connect(pat_angle, "", pat_call, "Angle")
    lib.connect(pat_index, "", pat_call, "CellIndex")
    lib.connect(pat_softness, "", pat_call, "Softness")
    lib.connect(pat_sdf_tex, "", pat_call, "SDFMap")

    # ---- shadow-driven hatch density (hatch coverage ONLY) ----
    # Not a second terminator authority: the Toon Profile still owns the band
    # structure. This only decides how densely the surface hatches in shadow.
    key_dir = lib.vector(mat, "KeyLightDir", "Pattern", (0.0, 0.0, 1.0),
                         -1240, 2120,
                         desc="Key light direction used to densify hatch in shadow")
    key_n = lib.expr(mat, unreal.MaterialExpressionNormalize, -1040, 2120)
    lib.unary(key_dir, key_n)

    ndotl = lib.expr(mat, unreal.MaterialExpressionDotProduct, -880, 2120)
    shade_n = lib.expr(mat, unreal.MaterialExpressionPixelNormalWS, -1040, 2240)
    lib.connect(shade_n, "", ndotl, ["A", "a"])
    lib.connect(key_n, "", ndotl, ["B", "b"])

    ndotl_s = lib.expr(mat, unreal.MaterialExpressionSaturate, -720, 2120)
    lib.unary(ndotl, ndotl_s)

    shadow_m = lib.expr(mat, unreal.MaterialExpressionOneMinus, -580, 2120)
    lib.unary(ndotl_s, shadow_m)

    hatch_drive = lib.scalar(mat, "PatternHatchShadowDrive", "Pattern", 1.0,
                             -1240, 2200,
                             desc="How much the shadow mask drives hatch density "
                                  "(0 = manual only)")
    drive_m = lib.expr(mat, unreal.MaterialExpressionMultiply, -420, 2140)
    lib.binary(shadow_m, hatch_drive, drive_m)

    drive_s = lib.expr(mat, unreal.MaterialExpressionSaturate, -280, 2140)
    lib.unary(drive_m, drive_s)

    shadow_dens = lib.scalar(mat, "PatternHatchShadowDensity", "Pattern", 0.85,
                             -1240, 2280,
                             desc="Hatch coverage in shadow; PatternDensity is the "
                                  "coverage in light")
    dens_final = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate,
                          -100, 2140)
    lib.ternary(pat_density, shadow_dens, drive_s, dens_final)

    lib.connect(dens_final, "", pat_call, "Density")

    pat_amt = lib.expr(mat, unreal.MaterialExpressionMultiply, -460, 1600)
    lib.connect(pat_call, "Mask", pat_amt, ["A", "a"])
    lib.connect(pat_strength, "", pat_amt, ["B", "b"])

    patterned = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate,
                         -220, 1600)
    lib.connect(final_color, "", patterned, "A")
    lib.connect(vec["InkColor"], "", patterned, "B")
    lib.connect(pat_amt, "", patterned, "Alpha")
    final_color = patterned

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

    # ---------------- contact shadow (distance field) ----------------
    bContactShadow = lib.expr(mat, unreal.MaterialExpressionStaticSwitchParameter,
                              -900, 1150)
    bContactShadow.set_editor_property("parameter_name", "bContactShadow")
    bContactShadow.set_editor_property("group", "Contact")
    bContactShadow.set_editor_property("default_value", False)

    ao = lib.expr(mat, unreal.MaterialExpressionDistanceFieldApproxAO, -1100, 1150)
    # BaseDistance / Radius are INPUT PINS on this build, not properties.
    ao_base = lib.scalar(mat, "ContactShadowDistance", "Contact", 12.0,
                         -1100, 1280,
                         desc="Distance-field sample distance for the contact shadow")
    ao_radius = lib.scalar(mat, "ContactShadowRadius", "Contact", 40.0,
                           -1100, 1360,
                           desc="Search radius of the distance-field query")
    lib.connect(ao_base, "", ao, "BaseDistance")
    lib.connect(ao_radius, "", ao, "Radius")
    ao_scale = lib.scalar(mat, "ContactShadowStrength", "Contact", 0.45,
                          -1100, 1440,
                          desc="How hard the distance-field contact shadow reads")

    ao_tinted = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate,
                         -740, 1150)
    lib.ternary(final_color, vec["InkColor"], ao_scale, ao_tinted)

    # The StaticSwitchParameter IS the mixer. (The 2026-10-03 defect was
    # wiring a Lerp with "True"/"False" pins and handing the Toon BSDF an
    # unconnected node - every surface rendered black while verification
    # passed, because graph_reachability seeded at nodes with no consumers.)
    lib.connect(final_color, "", bContactShadow, ["False"])
    lib.connect(ao_tinted, "", bContactShadow, ["True"])
    final_color = bContactShadow

    # ---------------- Substrate Toon BSDF ----------------
    toon = lib.expr(mat, unreal.MaterialExpressionSubstrateToonBSDF, 700, 240)
    lib.connect(final_color, "", toon, ["BaseColor", "DiffuseColor"])
    lib.connect(rough, "", toon, ["Roughness"])
    lib.connect(normal, "", toon, ["Normal", "TangentNormal", "NormalMap"])

    # ---------------- rim (THE CHARACTER DOMAIN BEHAVIOUR) ----------------
    # MF_RimOffset: normal biased by RimOffsetDir, then a view-facing term
    # remapped across RimStart..RimEnd. Output is additive emissive by
    # contract - wired to the closure's EmissiveColor pin, never to BaseColor.
    rim_call = lib.expr(mat, unreal.MaterialExpressionMaterialFunctionCall, 200, 900)
    rim_call.set_editor_property("material_function",
        unreal.load_asset(lib.asset_path(lib.FUNCTION_DIR, "MF_RimOffset")))

    # Its own normal read: cheap, and keeps the rim chain independent of the
    # ordering of the earlier `normal` node.
    rim_n = lib.expr(mat, unreal.MaterialExpressionPixelNormalWS, 60, 900)
    lib.connect(rim_n, "", rim_call, "Normal")
    lib.connect(rim_vec["RimColor"], "", rim_call, "RimColor")
    lib.connect(rim_vec["RimOffsetDir"], "", rim_call, "OffsetDir")
    lib.connect(rim_flt["RimOffsetStrength"], "", rim_call, "OffsetStrength")
    lib.connect(rim_flt["RimStart"], "", rim_call, "RimStart")
    lib.connect(rim_flt["RimEnd"], "", rim_call, "RimEnd")
    lib.connect(rim_flt["RimSharpness"], "", rim_call, "Sharpness")
    lib.connect(rim_flt["RimStrength"], "", rim_call, "RimStrength")

    # ---------------- emissive ----------------
    # Base emission (troffers, screens) is EmissiveColor * EmissiveIntensity.
    # Rim is added AFTER that multiply so the two stay independent: the rim must
    # not be gated by EmissiveIntensity, which defaults to 0 for characters.
    emissive_mul = lib.expr(mat, unreal.MaterialExpressionMultiply, 440, 60)
    lib.connect(vec["EmissiveColor"], "", emissive_mul, ["A", "a"])
    lib.connect(flt["EmissiveIntensity"], "", emissive_mul, ["B", "b"])

    emissive_total = lib.expr(mat, unreal.MaterialExpressionAdd, 570, 60)
    lib.connect(emissive_mul, "", emissive_total, ["A", "a"])
    lib.connect(rim_call, "RimEmissive", emissive_total, ["B", "b"])

    lib.connect(emissive_total, "", toon, ["EmissiveColor"])
    lib.connect_property(toon, unreal.MaterialProperty.MP_FRONT_MATERIAL)

    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
    except Exception as exc:
        lib.log(f"recompile warning: {exc}")

    # ---------------- the Toon Profile itself ----------------
    # Bound LAST, on a re-fetched node, then proven by read-back. Binding a
    # freshly created material before recompile reports success and reads None
    # a second later; binding after save + modify() is the only ordering that
    # measured as persisting. (Full history: build_master_toon.py, and
    # toon_profile_recompile_probe.json.)
    toon_node = None
    for _n in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
        if type(_n).__name__ == "MaterialExpressionSubstrateToonBSDF":
            toon_node = _n
            break
    master_profile = unreal.load_asset(
        lib.asset_path(lib.PROFILE_DIR, MASTER_PROFILE))

    def _profile_bound():
        for handle in (toon_node, toon):
            if handle is None:
                continue
            try:
                p = handle.get_editor_property("toon_profile")
                if p is not None:
                    return p.get_name()
            except Exception:
                continue
        return None

    if toon_node is None:
        lib.log(f"WARN {NAME}: no SubstrateToonBSDF node - cannot bind profile")
    elif master_profile is None:
        lib.log(f"WARN master profile {MASTER_PROFILE} not found - spine will "
                f"render on a default Toon Profile")
    else:
        for handle in (toon, toon_node):
            lib.try_set(handle, "toon_profile", master_profile)
        bound = _profile_bound()
        if bound is None:
            live = unreal.load_asset(lib.asset_path(lib.MASTER_DIR, NAME))
            if live is not None:
                for _n in unreal.MaterialEditingLibrary \
                        .get_material_expressions(live) or []:
                    if type(_n).__name__ == "MaterialExpressionSubstrateToonBSDF":
                        lib.try_set(_n, "toon_profile", master_profile)
                        toon_node = _n
                        break
            bound = _profile_bound()
        lib.log(f"{NAME} Toon Profile -> {bound or 'UNBOUND'} "
                f"(wanted {MASTER_PROFILE})")

    lib.save(mat)

    # ---------------- post-save fixup ----------------
    # set_editor_property alone does not always flag the package dirty, so a
    # save can write the pre-change bytes: the value reads back in memory and
    # never appears in the file. modify() + save() + read-back closes that.
    try:
        fresh = unreal.load_asset(lib.asset_path(lib.MASTER_DIR, NAME))
        fresh_node = None
        for _n in unreal.MaterialEditingLibrary \
                .get_material_expressions(fresh) or []:
            if type(_n).__name__ == "MaterialExpressionSubstrateToonBSDF":
                fresh_node = _n
                break
        if fresh_node is not None and master_profile is not None:
            have = fresh_node.get_editor_property("toon_profile")
            if have is None:
                for target in (fresh_node, fresh):
                    try:
                        target.modify()
                    except Exception:
                        pass
                lib.try_set(fresh_node, "toon_profile", master_profile)
                lib.save(fresh)
                after = fresh_node.get_editor_property("toon_profile")
                lib.log(f"{NAME}: re-asserted Toon Profile -> "
                        f"{after.get_name() if after else 'STILL UNBOUND'}")
            else:
                lib.log(f"{NAME}: Toon Profile persisted -> {have.get_name()}")
        elif fresh_node is None:
            lib.log(f"WARN {NAME}: re-fetch found no SubstrateToonBSDF node")
    except Exception as exc:
        lib.log(f"WARN {NAME} post-save fixup failed: {str(exc)[:140]}")

    lib.log(f"{NAME} built with {lib.expression_count(mat)} expressions")
    return mat


def verify():
    """Two things verify_material cannot see for this master.

    1. THE PROFILE. lib.verify_material only reads toon_profile for
       M_Master_Toon_Universal (hard-coded branch), so every other master can
       ship with an unbound profile and still pass. For THIS master the profile
       is the whole point - it is the reason the asset exists - so it gets its
       own read-back here and it can fail the run.

    2. THE RIM. expected_calls in build_spine covers MF_RimOffset, but a call
       node with its RimEmissive pin unwired would satisfy the call-count check
       while contributing nothing. Read the pin instead.
    """
    path = lib.asset_path(lib.MASTER_DIR, NAME)
    mat = unreal.load_asset(path)
    result = {"name": NAME, "ok": False, "error": None}

    if mat is None:
        result["error"] = "does not load"
        lib.log(f"VERIFY {NAME}: FAIL {result['error']}")
        return result

    # -- profile --
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

    if profile != MASTER_PROFILE:
        result["error"] = (f"bound profile is {profile!r}, want "
                           f"{MASTER_PROFILE!r} - the character contract would "
                           f"not be in effect")

    # -- rim present, rim parameters present (deterministic) --
    if result["error"] is None:
        rim_path = lib.asset_path(lib.FUNCTION_DIR, "MF_RimOffset")
        calls = [e for e in
                 unreal.MaterialEditingLibrary.get_material_expressions(mat) or []
                 if e is not None
                 and type(e).__name__ == "MaterialExpressionMaterialFunctionCall"]
        rim = None
        for c in calls:
            try:
                mf = c.get_editor_property("material_function")
                if mf is not None and mf.get_path_name().endswith(
                        "MF_RimOffset.MF_RimOffset"):
                    rim = c
                    break
            except Exception:
                continue
        if rim is None:
            result["error"] = f"MF_RimOffset is not called (want {rim_path})"
        else:
            want = {n for n, _d, _x in RIM_SCALAR_PARAMS} | \
                   {n for n, _d, _x in RIM_VECTOR_PARAMS}
            have = set()
            for e in unreal.MaterialEditingLibrary \
                    .get_material_expressions(mat) or []:
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
                result["error"] = f"rim parameters missing from graph: {missing}"

    # -- rim OUTPUT wiring: best-effort, reported as unknown rather than
    #    silently passing when the introspection API is absent on this build --
    if result["error"] is None:
        try:
            outs = unreal.MaterialEditingLibrary \
                .get_material_expression_outputs(rim) or []
            wired = []
            for o in outs:
                conns = unreal.MaterialEditingLibrary \
                    .get_material_expression_output_connections(o)
                wired.append(bool(conns))
            # RimEmissive (index 0) must be consumed; RimMask may be unused.
            result["rim_output_wired"] = bool(wired and wired[0])
            if wired and not wired[0]:
                result["error"] = ("MF_RimOffset's RimEmissive output is "
                                   "unwired - the rim would be inert")
        except AttributeError as exc:
            result["rim_output_wired"] = None
            result["rim_output_note"] = (
                f"introspection unavailable ({str(exc)[:60]}); rim wiring NOT "
                f"proven here")
            lib.log(f"WARN {NAME}: {result['rim_output_note']}")

    if result["error"] is None:
        result["ok"] = True

    lib.log(f"VERIFY {NAME}: ok={result['ok']} profile={profile} "
            f"rim_wired={result.get('rim_output_wired')} "
            f"{result['error'] or ''}")
    return result
