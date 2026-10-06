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

# The Toon Profile bound to the master's Substrate Toon BSDF. A profile is what
# turns the surface into cel shading; with it unbound the whole spine renders on
# engine defaults. TP_Default is the neutral fallback - CONTENT_CONVENTIONS.md
# designates it "anything with no better answer".
MASTER_PROFILE = "TP_Default"

# (param_name, group, default, description) - recovered from the source master
SURFACE_PARAMS = [
    ("BaseTint", "Palette", (0.55, 0.48, 0.42, 1.0), "Base surface colour"),
    ("AccentTint", "Palette", (0.72, 0.62, 0.52, 1.0), "Second colour for ramp/blend"),
    ("InkColor", "Palette", (0.05, 0.08, 0.15, 1.0), "Ink line / pooling colour"),
    ("GoldTint", "Palette", (0.85, 0.65, 0.25, 1.0), "Gilding colour"),
    # Added 2026-10-02. Feeds the Substrate Toon closure's NATIVE EmissiveColor
    # pin (probed on this build - see Saved/Audit/toon_surface_probe_v2.json),
    # not MP_EMISSIVE_COLOR, so the emission stays inside the substrate closure
    # instead of becoming a second legacy output path. Default 0 = off, so every
    # pre-existing instance is unchanged until it opts in.
    ("EmissiveColor", "Emissive", (0.0, 0.0, 0.0, 1.0),
     "Emission colour for troffers, monitor screens, signage"),
]

FLOAT_PARAMS = [
    # FIX 2026-10-03 - 19 of these 42 scalars never reached the Toon closure
    # (live forward-reachability, Saved/Audit/lookdev_census.json): the artist
    # dragged them and nothing changed. Actions taken here:
    #   * UVScale / UVRotation DELETED - redundant with the LIVE PatternScale /
    #     PatternAngle knobs (the pattern function already scales and rotates
    #     internally), so keeping them was two controls for one behaviour.
    #   * the remaining 17 unwired scalars moved to group "Parked" with an
    #     UNWIRED description. Names kept: they mark lanes the film still wants
    #     (2D-animation boil, audio-reactive banding, ornament, outline
    #     reference) and re-wiring is tracked in Docs/SDF_PATTERN_PIPELINE.md.
    #     In the MI editor they now sort into their own group instead of
    #     masquerading as working controls.
    ("ParallaxScale", "Parallax", 0.04, "Height-map parallax amount"),
    ("ParallaxSteps", "Parked", 8.0, "UNWIRED - parked parallax step count"),
    ("ParallaxHeight", "Parallax", 0.04, "Height contribution to WPO"),
    ("GildingStrength", "Gilding", 0.0, "Gold-leaf overlay amount"),
    ("GoldEmissive", "Parked", 0.0, "UNWIRED - parked gold emissive boost"),
    ("OilPaintStrength", "OilPaint", 0.0, "Impasto/oil blend amount"),
    ("StrokeStrength", "Parked", 0.55, "UNWIRED - parked brush-stroke breakup"),
    ("BrushScale", "Parked", 0.045, "UNWIRED - parked brush texture scale"),
    ("TemporalStrength", "Temporal", 0.0, "Hand-drawn temporal wobble"),
    ("NoiseScale", "Parked", 1.5, "UNWIRED - parked temporal noise scale"),
    ("SmearStrength", "Parked", 0.0, "UNWIRED - parked temporal smear"),
    ("BoilIntensity", "Parked", 0.0, "UNWIRED - parked line boil (hand-drawn shimmer)"),
    ("InkIntensity", "Surface", 0.0, "Ink line intensity"),
    ("PoolingStrength", "Parked", 0.5, "UNWIRED - parked ink pooling in creases"),
    ("Wetness", "Surface", 0.0, "Wetness: blends dry/wet roughness"),
    ("OrnamentStyle", "Parked", 0.0, "UNWIRED - parked ornament style index"),
    ("OrnamentScale", "Parked", 1.0, "UNWIRED - parked ornament scale"),
    ("CurvatureSensitivity", "Parked", 2.0, "UNWIRED - parked curvature response for ornament"),
    ("AudioReactivity", "Parked", 0.0, "UNWIRED - parked audio-reactive amount"),
    ("BassWeight", "Parked", 1.0, "UNWIRED - parked bass band weight"),
    ("MidWeight", "Parked", 0.5, "UNWIRED - parked mid band weight"),
    ("TrebleWeight", "Parked", 0.25, "UNWIRED - parked treble band weight"),
    ("DryRoughness", "Surface", 0.78, "Dry surface roughness"),
    ("WetRoughness", "Surface", 0.25, "Wet surface roughness"),
    ("EdgeStrength", "Parked", 1.0, "UNWIRED - parked outline strength reference"),
    ("BandScale", "SDF", 0.035, "World-space band frequency"),
    ("BandStrength", "SDF", 0.12, "World-space band depth"),
    # Added 2026-10-02 with the EmissiveColor parameter. Scales EmissiveColor
    # into the Toon closure; 0 disables emission entirely.
    ("EmissiveIntensity", "Emissive", 0.0,
     "Emission strength. 0 = unlit (default); raise for troffers/screens"),
]

# UTILITY PARAMS - Office Spider expansion, 2026-10-06.
# A SEPARATE list from FLOAT_PARAMS on purpose: Character imports
# FLOAT_PARAMS by reference (build_master_toon_character.py), so anything
# appended there would appear on the Character master as an unwired knob -
# the placebo-control defect class (a dragged slider that changes nothing).
# These three are WIRED below, in this master only; Character/Face/Hair
# do not carry them until a real consumer asks (one line in each builder,
# plus wiring - not silence).
UTILITY_SCALARS = [
    ("ShadowLift", "Utility", 0.0,
     "Uniform lift added to the shaded colour before the Toon closure. "
     "0 = today's look (default); raise to keep dark-corner surfaces "
     "(spider body, p12-2) off black without forking a profile"),
    ("FlickerRate", "Utility", 0.0,
     "Emissive flicker speed (sine cycles/sec); 0 = steady"),
    ("FlickerDepth", "Utility", 0.0,
     "Emissive flicker amount 0..1; 0 = off, so every existing instance "
     "is pixel-identical until it opts in (monitor throb, troffer buzz, "
     "spider-eye throb)"),
]

# RIM - ported from M_Master_Toon_Character 2026-10-06 (Office Spider:
# the p12-2 spider sits in a dark corner and melts into black without an
# edge of light). Same seven knobs, same MF_RimOffset contract (additive
# emissive, never BaseColor), same default-OFF. The two lists are
# deliberately duplicated rather than imported: each master file is
# self-contained (established pattern), and parameter names/groups are
# the public contract instances key on.
RIM_SCALAR_PARAMS = [
    ("RimOffsetStrength", 0.60,
     "How far the normal is biased - puts the edge on ONE side"),
    ("RimStart", 0.55, "Where the edge of light begins on the silhouette"),
    ("RimEnd", 0.92, "Where it ends; RimStart..RimEnd is the edge width"),
    ("RimSharpness", 2.20, "Edge tightness (Power exponent)"),
    ("RimStrength", 0.0, "Rim amount; 0 = no rim (default)"),
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
    lib.try_set(mat, "bUsesSubstrate", True)

    # ---------------- parameters ----------------
    # FIX 2026-10-03: this used to be a TextureSampleParameter2D feeding
    # MF_RampLUT's texture input - but a sample parameter's output is the
    # SAMPLED COLOR (float3), and the function input is texture2D, so the
    # painted-ramp branch failed to compile with "Cannot cast from float3 to
    # texture2D". TextureObjectParameter passes the texture REFERENCE, keeps
    # RampTexture overridable per-instance, and defaults to the project-built
    # strip LUT (the grey-default policy here only bans /Engine placeholder
    # content; T_Ramp_Smooth is generated by build_textures.py).
    ramp_lut_tex = lib.expr(mat, unreal.MaterialExpressionTextureObjectParameter,
                            -1400, -600)
    ramp_lut_tex.set_editor_property("parameter_name", "RampTexture")
    ramp_lut_tex.set_editor_property("group", "Ramp")
    ramp_lut_tex.set_editor_property(
        "texture",
        unreal.load_asset(lib.asset_path("/Game/Materials/Textures",
                                         "T_Ramp_Smooth")))
    lib._desc(ramp_lut_tex, "Painted 1D band ramp (horizontal strip)")

    vec = {}
    y = -400
    for pname, group, default, desc in SURFACE_PARAMS:
        vec[pname] = lib.vector(mat, pname, group, default, -2000, y, desc=desc)
        y += 120

    flt = {}
    for i, (pname, group, default, desc) in enumerate(FLOAT_PARAMS):
        flt[pname] = lib.scalar(mat, pname, group, default, -2000, y)
        y += 70

    # Utility knobs (Office Spider 2026-10-06) - WIRED below, not parked.
    for pname, group, default, desc in UTILITY_SCALARS:
        flt[pname] = lib.scalar(mat, pname, group, default, -2000, y,
                                desc=desc)
        y += 70

    # Rim parameters (ported from Character 2026-10-06) - WIRED below.
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
    # (artist-painted 1D ramp). Both share the BaseColor/ColorRamp/Mask
    # signature, so the switch is a pure substitution.
    #
    # FIX 2026-10-02 - the ramp subsystem used to be INERT. Mask was wired to a
    # hard constant 0.0, and both functions end in lerp(base_color, ramp_rgb,
    # mask): at mask=0 that returns BaseColor unchanged, so bUsePaintedRamp
    # toggled between two identical outputs and all six Ramp* parameters plus
    # RampTexture were unreachable. verify_material still passed because it
    # counts function CALLS, not their influence on the result - the exact
    # "structurally valid, semantically empty" defect class the repo docs warn
    # about. Promoting the constant to a parameter with default 0.0 keeps every
    # existing instance pixel-identical while making the ramp reachable: an
    # artist sets RampStrength > 0 to opt in.
    ramp_strength = lib.scalar(mat, "RampStrength", "Ramp", 0.0, -1000, 740,
                               desc="0 bypasses the ramp (legacy look); >0 "
                                    "applies MF_ColorRamp3/MF_RampLUT shaping")
    mask_default = ramp_strength
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

    # ---------------- surface pattern (MF_ProceduralPatterns) ----------------
    # Hatching / screentone overlay. PatternMask * PatternStrength inks the
    # surface toward InkColor, so one material instance can carry painted
    # shadow hatching instead of needing a bespoke master. PatternDensity is
    # the coverage knob - drive it from a shadow mask and the hatch densifies
    # automatically. PatternStrength defaults to 0, so every existing MI is
    # unaffected until an artist turns it on.
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
                                  "10 perforation 11 weave 12 sdfmap 13 subway "
                                  "14 blinds 15 paperfiber 16 brushed 17 chevron "
                                  "18 frostbands")
    pat_density = lib.scalar(mat, "PatternDensity", "Pattern", 0.5, -1240, 1960,
                             desc="Ink coverage 0..1 - raise in shadow")
    pat_strength = lib.scalar(mat, "PatternStrength", "Pattern", 0.0, -1240, 2040,
                              desc="Pattern ink strength; 0 = off")
    # FIX 2026-10-03: the function's Softness input was never connected at the
    # call site, and a function input with no caller connection compiles as a
    # hard error ("Missing function input 'Softness'") - the master fell back
    # to the default material and every surface rendered black. Promoted to an
    # artist knob: 0 = razor-sharp cel edge, higher = softer screen-tone edge.
    pat_softness = lib.scalar(mat, "PatternSoftness", "Pattern", 0.10,
                              -1240, 2100,
                              desc="Pattern edge softness; 0 = razor sharp")
    # EXPANSION 2026-10-03: CellIndex 12 (SDFMap) needs a texture2D source.
    # TextureObjectParameter for the same reason RampTexture is one: the
    # function input is texture2D, and a sample parameter would pass the
    # sampled float3 ("Cannot cast from float3 to texture2D"). Default
    # T_SDF_Strokes is generated by build_textures.py - project-built
    # content, not /Engine placeholder, so the grey-default policy is kept.
    pat_sdf_tex = lib.expr(mat, unreal.MaterialExpressionTextureObjectParameter,
                           -1240, 2360)
    pat_sdf_tex.set_editor_property("parameter_name", "PatternSDFMap")
    pat_sdf_tex.set_editor_property("group", "Pattern")
    pat_sdf_tex.set_editor_property(
        "texture",
        unreal.load_asset(lib.asset_path("/Game/Materials/Textures",
                                         "T_SDF_Strokes")))
    lib._desc(pat_sdf_tex, "Baked SDF stroke field for CellIndex 12")

    lib.connect(pat_uv, "", pat_call, "UV")
    lib.connect(pat_scale, "", pat_call, "Scale")
    lib.connect(pat_angle, "", pat_call, "Angle")
    lib.connect(pat_index, "", pat_call, "CellIndex")
    lib.connect(pat_softness, "", pat_call, "Softness")
    lib.connect(pat_sdf_tex, "", pat_call, "SDFMap")

    # ---------------- shadow-driven hatch density ----------------
    # The hatch should densify into shadow the way a painter hatches into the
    # terminator, so density is driven by a KeyLightDir . Normal mask.
    #
    # This is deliberately NOT a second terminator authority: it exists only to
    # modulate hatch COVERAGE, and the Toon Profile still owns the band
    # structure. PatternHatchShadowDrive = 0 leaves density purely manual.
    key_dir = lib.vector(mat, "KeyLightDir", "Pattern", (0.0, 0.0, 1.0),
                         -1240, 2120,
                         desc="Key light direction used to densify hatch in shadow")
    key_n = lib.expr(mat, unreal.MaterialExpressionNormalize, -1040, 2120)
    lib.unary(key_dir, key_n)

    ndotl = lib.expr(mat, unreal.MaterialExpressionDotProduct, -880, 2120)
    # Its own normal read rather than reusing the later `normal` node: this
    # block runs before that one is defined, and a shadow-mask read costs
    # nothing. (Caught by the build: NameError on `normal`.)
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

    # ---------------- matte finish (Office Spider 2026-10-06) --------------
    # One-click matte for papers/poster/calendar: True forces roughness 1.0,
    # False keeps the dry/wet blend above. The StaticSwitchParameter IS the
    # mixer (True/False pins, not a Lerp - see the 2026-10-03 defect note at
    # the contact-shadow block). Default False = today's look.
    bMatteFinish = lib.expr(mat, unreal.MaterialExpressionStaticSwitchParameter,
                            760, 520)
    bMatteFinish.set_editor_property("parameter_name", "bMatteFinish")
    bMatteFinish.set_editor_property("group", "Surface")
    bMatteFinish.set_editor_property("default_value", False)
    lib._desc(bMatteFinish, "True = dead-matte roughness 1.0 (paper/poster)")
    lib.connect(rough, "", bMatteFinish, ["False"])
    lib.connect(lib.scalar_const(mat, 1.0, 760, 620), "", bMatteFinish,
                ["True"])
    rough = bMatteFinish

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
    # The only distance-field nodes UE 5.8 ships are ApproxAO and Gradient,
    # which read a mesh's BAKED field - they cannot author procedural shapes,
    # but they do give a grounded contact shadow that stops a toon surface
    # floating. Gated so it costs nothing when unused.
    bContactShadow = lib.expr(mat, unreal.MaterialExpressionStaticSwitchParameter,
                              -900, 1150)
    bContactShadow.set_editor_property("parameter_name", "bContactShadow")
    bContactShadow.set_editor_property("group", "Contact")
    bContactShadow.set_editor_property("default_value", False)

    ao = lib.expr(mat, unreal.MaterialExpressionDistanceFieldApproxAO, -1100, 1150)
    # UE 5.8 exposes BaseDistance / Radius as INPUT PINS, not properties.
    # Probed 2026-09-30: props list is empty, input_names are
    #   ["World Position", "Normal", "BaseDistance", "Radius"].
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

    contact = lib.expr(mat, unreal.MaterialExpressionMultiply, -580, 1150)
    lib.connect(ao, "", contact, ["A"])
    lib.connect(ao_scale, "", contact, ["B"])

    # FIX 2026-10-03: the StaticSwitchParameter IS the mixer. The previous
    # version built a LinearInterpolate and connected the switch INTO it using
    # True/False pin names - a Lerp exposes A/B/Alpha, so all three connects
    # failed, connect() swallowed the pin errors, and `final_color = shaded`
    # handed the Toon BSDF an UNCONNECTED Lerp (constant 0 = black). Live
    # evidence: Saved/Audit/master_chain_dump.json node 88, in=[], used_by=89.
    # Every surface in the film rendered black with the graph "passing"
    # verification, because graph_reachability seeds its walk at nodes with no
    # consumers and ao_tinted/contact/bContactShadow qualified as sinks.
    lib.connect(final_color, "", bContactShadow, ["False"])
    lib.connect(ao_tinted, "", bContactShadow, ["True"])
    final_color = bContactShadow

    # ---------------- shadow lift (Office Spider 2026-10-06) ----------------
    # Uniform lift AFTER the contact mixer so it raises the whole surface
    # floor (contact shadow included) by one DP knob. ShadowLift = 0
    # multiplies to zero and adds zero: every existing instance is
    # pixel-identical until it opts in.
    lift_white = lib.expr(mat, unreal.MaterialExpressionConstant3Vector,
                          700, 420)
    lift_white.set_editor_property(
        "constant", unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
    lift_amt = lib.expr(mat, unreal.MaterialExpressionMultiply, 860, 420)
    lib.connect(lift_white, "", lift_amt, ["A", "a"])
    lib.connect(flt["ShadowLift"], "", lift_amt, ["B", "b"])
    lifted = lib.expr(mat, unreal.MaterialExpressionAdd, 1020, 300)
    lib.connect(final_color, "", lifted, ["A", "a"])
    lib.connect(lift_amt, "", lifted, ["B", "b"])
    final_color = lifted

    # ---------------- Substrate Toon BSDF ----------------
    toon = lib.expr(mat, unreal.MaterialExpressionSubstrateToonBSDF, 700, 240)
    lib.connect(final_color, "", toon, ["BaseColor", "DiffuseColor"])
    lib.connect(rough, "", toon, ["Roughness"])
    lib.connect(normal, "", toon, ["Normal", "TangentNormal", "NormalMap"])

    # ---------------- rim (ported from Character 2026-10-06) ----------------
    # MF_RimOffset: normal biased by RimOffsetDir, view-facing term remapped
    # across RimStart..RimEnd. Output is additive emissive by contract -
    # wired to the closure's EmissiveColor pin, never to BaseColor.
    # RimStrength defaults to 0.0: the master is inert for rim until an
    # instance opts in (spider body in the p12-2 dark corner).
    rim_call = lib.expr(mat, unreal.MaterialExpressionMaterialFunctionCall,
                        200, 900)
    rim_call.set_editor_property("material_function",
        unreal.load_asset(lib.asset_path(lib.FUNCTION_DIR, "MF_RimOffset")))
    rim_n = lib.expr(mat, unreal.MaterialExpressionPixelNormalWS, 60, 900)
    lib.connect(rim_n, "", rim_call, "Normal")
    lib.connect(rim_vec["RimColor"], "", rim_call, "RimColor")
    lib.connect(rim_vec["RimOffsetDir"], "", rim_call, "OffsetDir")
    lib.connect(rim_flt["RimOffsetStrength"], "", rim_call, "OffsetStrength")
    lib.connect(rim_flt["RimStart"], "", rim_call, "RimStart")
    lib.connect(rim_flt["RimEnd"], "", rim_call, "RimEnd")
    lib.connect(rim_flt["RimSharpness"], "", rim_call, "Sharpness")
    lib.connect(rim_flt["RimStrength"], "", rim_call, "RimStrength")

    # ---------------- emissive + flicker (Office Spider 2026-10-06) ---------
    # Routed into the closure's own EmissiveColor pin. PROBED 2026-10-02
    # (Saved/Audit/toon_surface_probe_v2.json): MaterialExpressionSubstrate
    # ToonBSDF exposes BaseColor, Metallic, Specular, Roughness, Normal,
    # EmissiveColor, PatternUVs, Anisotropy, Tangent on this build, and a
    # FrontMaterial + MP_EMISSIVE_COLOR pair also recompiles. The pin is
    # preferred: it keeps emission inside the substrate closure rather than
    # adding a second legacy output path alongside FrontMaterial.
    #
    # Flicker factor is 1 + sin(2*pi*rate*t) * depth, so depth = 0 gives
    # exactly 1 and the path reduces to today's EmissiveColor*Intensity.
    # The Time/Sine pulse is the M_Master_Toon_EmissiveFX pattern in this
    # repo (build_m_toon_emissivefx.py) - second use, not a new idiom.
    # Rim is added AFTER the flicker multiply so the edge of light never
    # throbs with the screen buzz (same independence rule as Character).
    emissive_mul = lib.expr(mat, unreal.MaterialExpressionMultiply, 440, 60)
    lib.connect(vec["EmissiveColor"], "", emissive_mul, ["A", "a"])
    lib.connect(flt["EmissiveIntensity"], "", emissive_mul, ["B", "b"])

    flick_time = lib.expr(mat, unreal.MaterialExpressionTime, 60, 60)
    flick_rate = lib.expr(mat, unreal.MaterialExpressionMultiply, 200, 60)
    lib.connect(flick_time, "", flick_rate, ["A", "a"])
    lib.connect(flt["FlickerRate"], "", flick_rate, ["B", "b"])
    flick_wave = lib.expr(mat, unreal.MaterialExpressionSine, 340, 60)
    flick_wave.set_editor_property("period", 1.0)
    lib.connect(flick_rate, "", flick_wave, ["Input", ""])
    flick_scaled = lib.expr(mat, unreal.MaterialExpressionMultiply, 480, 60)
    lib.connect(flick_wave, "", flick_scaled, ["A", "a"])
    lib.connect(flt["FlickerDepth"], "", flick_scaled, ["B", "b"])
    flick_factor = lib.expr(mat, unreal.MaterialExpressionAdd, 620, 60)
    lib.connect(flick_scaled, "", flick_factor, ["A", "a"])
    lib.connect(lib.scalar_const(mat, 1.0, 620, 140), "", flick_factor,
                ["B", "b"])

    emissive_flick = lib.expr(mat, unreal.MaterialExpressionMultiply,
                              760, 60)
    lib.connect(emissive_mul, "", emissive_flick, ["A", "a"])
    lib.connect(flick_factor, "", emissive_flick, ["B", "b"])

    emissive_total = lib.expr(mat, unreal.MaterialExpressionAdd, 900, 60)
    lib.connect(emissive_flick, "", emissive_total, ["A", "a"])
    lib.connect(rim_call, "RimEmissive", emissive_total, ["B", "b"])

    lib.connect(emissive_total, "", toon, ["EmissiveColor"])

    lib.connect_property(toon, unreal.MaterialProperty.MP_FRONT_MATERIAL)

    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
    except Exception as exc:
        lib.log(f"recompile warning: {exc}")

    # ---------------- the Toon Profile itself ----------------
    # FIX 2026-10-02 - the spine was running with NO profile bound.
    # `toon_profile` is a property of the SubstrateToonBSDF NODE, not of the
    # material and not of the material instance. Nothing in this builder ever
    # set it and nothing verified it, so every surface in the film was shading
    # on engine defaults while 19 TP_* assets sat unused.
    #
    # It is bound HERE, after recompile and immediately before save, and the
    # node is RE-FETCHED rather than reusing the handle from graph build time.
    # Measured behaviour on this build:
    #   * binding an EXISTING material: survives recompile and save (probe
    #     toon_profile_recompile_probe.json, steps 1-5 all TP_Default)
    #   * binding a FRESHLY CREATED material before recompile: the log printed
    #     success and verify_material read None one second later - the value was
    #     gone. Doing it last removes that ordering dependency entirely.
    # verify_material now fails the build if this does not stick, so a
    # regression here cannot pass silently again.
    toon_node = None
    for _n in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
        if type(_n).__name__ == "MaterialExpressionSubstrateToonBSDF":
            toon_node = _n
            break
    master_profile = unreal.load_asset(
        lib.asset_path(lib.PROFILE_DIR, MASTER_PROFILE))

    def _profile_bound():
        """Read the bound profile back off whichever handle answers."""
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
        # Set on the construction handle AND the re-fetched one, then prove it
        # by reading back. Setting reported success while verify_material read
        # None, so the return value of set_editor_property is not evidence here
        # and neither is a try_set() that does not raise - only a read-back is.
        for handle in (toon, toon_node):
            lib.try_set(handle, "toon_profile", master_profile)
        bound = _profile_bound()
        if bound is None:
            # A material created in THIS session can hand out a detached
            # expression object; retry against the live package expression.
            live = unreal.load_asset(
                lib.asset_path(lib.MASTER_DIR, NAME))
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
    # The handle that build() wrote the profile to is not reliably the handle
    # that verify_material reads from a second later: build() read back
    # "TP_Default" and verify_material read None one second later, on the same
    # path, in the same process. Re-fetching the material and re-asserting the
    # binding on the node that comes back makes the saved asset the thing that
    # was written, rather than the object build() happened to hold.
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
                # modify() marks the object dirty so the change is actually
                # serialised. set_editor_property alone updates the object but
                # does not always flag the package, and a save then writes the
                # pre-change bytes - which is consistent with everything measured:
                # the value reads back in memory yet never appears in the file.
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
    """What lib.verify_material cannot see for this master.

    1. THE RIM (ported from Character 2026-10-06). expected_calls in
       build_spine covers MF_RimOffset, but a call node with RimEmissive
       unwired would satisfy the count while contributing nothing - the
       exact "structurally valid, semantically empty" class. Read the pin.
    2. THE UTILITY KNOBS. ShadowLift / FlickerRate / FlickerDepth must be
       present as scalar parameters and consumed (a created-but-unwired
       knob is the placebo defect); bMatteFinish must be present as a
       static switch. Mirrors the rim-param presence check.
    """
    path = lib.asset_path(lib.MASTER_DIR, NAME)
    mat = unreal.load_asset(path)
    result = {"name": NAME, "ok": False, "error": None}

    if mat is None:
        result["error"] = "does not load"
        lib.log(f"VERIFY {NAME}: FAIL {result['error']}")
        return result

    exprs = unreal.MaterialEditingLibrary.get_material_expressions(mat) or []

    # -- profile: Universal binds the neutral fallback by design --
    for n in exprs:
        if type(n).__name__ == "MaterialExpressionSubstrateToonBSDF":
            try:
                p = n.get_editor_property("toon_profile")
                result["toon_profile"] = p.get_name() if p else None
            except Exception as exc:
                result["error"] = f"profile read: {str(exc)[:80]}"
            break
    if result["error"] is None and result.get("toon_profile") != MASTER_PROFILE:
        result["error"] = (f"bound profile is {result.get('toon_profile')!r}, "
                           f"want {MASTER_PROFILE!r}")

    # -- rim call present, rim parameters present --
    if result["error"] is None:
        rim = None
        for c in exprs:
            if c is not None and type(c).__name__ == \
                    "MaterialExpressionMaterialFunctionCall":
                try:
                    mf = c.get_editor_property("material_function")
                    if mf is not None and mf.get_path_name().endswith(
                            "MF_RimOffset.MF_RimOffset"):
                        rim = c
                        break
                except Exception:
                    continue
        if rim is None:
            result["error"] = "MF_RimOffset is not called"
        else:
            want = {n for n, _d, _x in RIM_SCALAR_PARAMS} | \
                   {n for n, _d, _x in RIM_VECTOR_PARAMS}
            scalars, switches = set(), set()
            for e in exprs:
                if e is None:
                    continue
                t = type(e).__name__
                try:
                    pname = str(e.get_editor_property("parameter_name"))
                except Exception:
                    continue
                if t == "MaterialExpressionScalarParameter":
                    scalars.add(pname)
                elif t == "MaterialExpressionVectorParameter":
                    scalars.add(pname)
                elif t == "MaterialExpressionStaticSwitchParameter":
                    switches.add(pname)
            want_all = (want
                        | {n for n, _g, _d, _x in UTILITY_SCALARS}
                        | {"bMatteFinish"})
            missing = sorted(want_all - scalars - switches)
            if missing:
                result["error"] = (f"rim/utility parameters missing: "
                                   f"{missing}")
            else:
                # -- RimEmissive consumed (best-effort introspection) --
                try:
                    outs = unreal.MaterialEditingLibrary \
                        .get_material_expression_outputs(rim) or []
                    wired = []
                    for o in outs:
                        conns = unreal.MaterialEditingLibrary \
                            .get_material_expression_output_connections(o)
                        wired.append(bool(conns))
                    result["rim_output_wired"] = bool(wired and wired[0])
                    if wired and not wired[0]:
                        result["error"] = ("MF_RimOffset's RimEmissive "
                                           "output is unwired")
                except AttributeError as exc:
                    result["rim_output_wired"] = None
                    result["rim_output_note"] = (
                        f"introspection unavailable ({str(exc)[:60]}); "
                        f"rim wiring NOT proven here")
                    lib.log(f"WARN {NAME}: {result['rim_output_note']}")

    if result["error"] is None:
        result["ok"] = True

    lib.log(f"VERIFY {NAME}: ok={result['ok']} "
            f"profile={result.get('toon_profile')} "
            f"rim_wired={result.get('rim_output_wired')} "
            f"{result['error'] or ''}")
    return result
