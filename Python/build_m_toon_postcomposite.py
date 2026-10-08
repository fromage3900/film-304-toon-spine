"""Build M_Master_Toon_PostComposite - the film-wide grade, one shared writer.

WHY ITS OWN MASTER (and why it is the ONLY post-process material)
----------------------------------------------------------------
Every Humber shot shares one finishing pass: grade tint, animated grain,
vignette, and the halftone that makes the frame read as print. The spine
rules say ONE writer per surface - a post-process volume with eight
per-shot materials would be eight writers on one screen. This master is
that single writer; instances change the numbers, never the graph.

Domain evidence (proven in-repo, not assumed):
  * material_domain = MD_POST_PROCESS (build_dreamprint_material.py:198)
  * output = MP_EMISSIVE_COLOR (dreamprint:212, setup_storybook_outline.py:249,
    setup_audio_outline.py:123)
  * scene input = MaterialExpressionSceneTexture with scene_texture_id, proven
    fallback PPI_POST_PROCESS_INPUT0 (dreamprint `_pp_input_id()`); output
    pin "Color". ScreenPosition (default mode, 0..1) proven for PP UV
    (dreamprint:298).

NO BSDF, NO Toon Profile - verify() asserts both (post-process materials have
no front material). The pattern call is the surface spine's
MF_ProceduralPatterns reused as a FRAME halftone (UV = screen * HalftoneScale).

THE DOMAIN BEHAVIOUR: GRADE * GRAIN * VIGNETTE * HALFTONE
---------------------------------------------------------
scene  = SceneTexture PPI_POST_PROCESS_INPUT0 (dreamprint `_pp_input_id()`)
graded = MF_FilmGrade(scene, FilmContrast/FilmWarmth/FilmSaturation/
                      FilmLift). Neutral photographic grade re-scoped from
                      the Melodia NikkiDreamGrade lane (2026-10-07); every
                      control defaults to identity, so the frame is
                      unchanged until a shot opts in. then multiplied by
                      GradeTint (per-shot tint).
grain  = (noise_r - 0.5) * GrainStrength           -- signed, so it dithers both ways
vign   = 1 - saturate(length2(uv - 0.5) * VignetteStrength)
half   = lerp(graded * vign * (1+grain), 0.75 * ..., mask * HalftoneStrength)
out    -> MP_EMISSIVE_COLOR
HalftoneStrength 0 = pass-through grade (inert-until-instance); GrainScale
drives the noise sample frequency.

Scene-colour source: SceneTexture with candidate ids [PPI_POST_PROCESS_INPUT0
first, PPI_SCENE_COLOR second], candidate output pins ["Color", ""]. Loud
WARN on total failure - the run reports which path took via verify().
MaterialExpressionSceneColor is REMOVED (2026-10-06): it instantiates from
Python but the shader compiler rejects it in MD_POST_PROCESS ("Only 'surface'
material domain can use the scene color node", build log 2026-10-06) - both
the master and MI_Toon_PostComposite failed to compile and fell back to
Default Material. Instantiation success is not engine truth.
"""
from __future__ import annotations

import unreal

import spine_lib as lib

NAME = "M_Master_Toon_PostComposite"
TEX_DIR = "/Game/Materials/Textures"

# Set by build() so verify() can report which path took.
_state = {"scene_input": None, "scene_output_pin": None}


def _scene_color_source(mat, x, y):
    """Return (node, description) for the current-frame colour.

    Mirrors build_dreamprint_material.py `_pp_input_id()`:
      1. MaterialExpressionSceneTexture + scene_texture_id candidates, with
         PPI_POST_PROCESS_INPUT0 first (the proven dreamprint path);
      2. None - caller logs loud and continues (grade would run on black).

    MaterialExpressionSceneColor is deliberately NOT attempted: it
    instantiates fine from Python but is shader-illegal in MD_POST_PROCESS
    (build log 2026-10-06), which is exactly the "instantiation success is
    not engine truth" failure mode this repo guards against.
    """
    ids = ["PPI_POST_PROCESS_INPUT0", "PPI_SCENE_COLOR"]
    for id_name in ids:
        try:
            node = lib.expr(mat, unreal.MaterialExpressionSceneTexture, x, y)
            if node is None:
                continue
            enum_val = None
            try:
                enum_val = getattr(unreal.SceneTextureId, id_name)
            except Exception:
                enum_val = None
            if enum_val is None:
                continue
            node.set_editor_property("scene_texture_id", enum_val)
            return node, f"SceneTexture:{id_name}"
        except Exception:
            continue
    return None, None


def build(rebuild=True):
    global _state
    _state = {"scene_input": None, "scene_output_pin": None}
    lib.log(f"=== {NAME} ===")
    mat = lib.get_or_create_material(NAME, rebuild=rebuild)

    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_POST_PROCESS)
    # two_sided/bloom etc. are not meaningful here; no blend_mode on PP.

    # ---------------- parameters ----------------
    vec = {
        "GradeTint": lib.vector(mat, "GradeTint", "Grade", (1.0, 1.0, 1.0, 1.0),
                                -1600, -400,
                                desc="Per-shot colour grade multiplier"),
        "FilmLift": lib.vector(mat, "FilmLift", "Film", (0.0, 0.0, 0.0, 1.0),
                               -1600, -280,
                               desc="Shadow pedestal (neutral film grade; "
                                    "0,0,0 = off)"),
    }
    flt = {
        "GrainStrength": lib.scalar(mat, "GrainStrength", "Grade", 0.06, -1000, -400,
                                    desc="Signed film grain amplitude"),
        "GrainScale": lib.scalar(mat, "GrainScale", "Grade", 320.0, -1000, -330,
                                 desc="Grain sample frequency (UV multiplier)"),
        "VignetteStrength": lib.scalar(mat, "VignetteStrength", "Grade", 0.35,
                                       -1000, -260,
                                       desc="Edge darkening (0 = off)"),
        "HalftoneStrength": lib.scalar(mat, "HalftoneStrength", "Grade", 0.0,
                                       -1000, -190,
                                       desc="0 = pass-through (inert default); "
                                            ">0 = print-dot blend"),
        "HalftoneScale": lib.scalar(mat, "HalftoneScale", "Grade", 240.0, -1000, -120,
                                    desc="Dots per frame scale (UV multiplier)"),
        # Neutral film grade 2026-10-07 (MF_FilmGrade). Identity at the
        # defaults below: Contrast 1 / Warmth 0 / Saturation 1 / Lift 0
        # reduce the call to its input, so the existing frame is unchanged.
        "FilmContrast": lib.scalar(mat, "FilmContrast", "Film", 1.0, -1000, -50,
                                   desc="Film contrast about the 0.18 pivot "
                                        "(1.0 = unchanged; useful 0.8..1.4)"),
        "FilmWarmth": lib.scalar(mat, "FilmWarmth", "Film", 0.0, -1000, 20,
                                 desc="Blue..amber shift (0 = neutral; "
                                      "useful -0.5 cool .. 0.5 amber)"),
        "FilmSaturation": lib.scalar(mat, "FilmSaturation", "Film", 1.0,
                                     -1000, 90,
                                     desc="Colour saturation (1.0 = unchanged; "
                                          "0 = mono)"),
    }

    pat_sdf_tex = lib.expr(mat, unreal.MaterialExpressionTextureObjectParameter,
                           -1000, -50)
    pat_sdf_tex.set_editor_property("parameter_name", "PatternSDFMap")
    pat_sdf_tex.set_editor_property("group", "Grade")
    pat_sdf_tex.set_editor_property(
        "texture", unreal.load_asset(lib.asset_path(TEX_DIR, "T_SDF_Strokes")))
    lib._desc(pat_sdf_tex, "Baked SDF stroke field for CellIndex 12")

    # ---------------- UV: ScreenPosition (proven dreamprint:298) ------------
    uv = lib.expr(mat, unreal.MaterialExpressionScreenPosition, -1600, 300)
    lib._desc(uv, "Screen UV 0..1 (default mode)")

    # ---------------- scene colour input -----------------------------------
    scene, scene_desc = _scene_color_source(mat, -1600, 60)
    scene_rgb = None
    if scene is not None:
        _state["scene_input"] = scene_desc
        for pin in ("Color", ""):
            try:
                probe = lib.expr(mat, unreal.MaterialExpressionComponentMask, -1440, 60)
                probe.set_editor_property("r", True)
                probe.set_editor_property("g", True)
                probe.set_editor_property("b", True)
                probe.set_editor_property("a", False)
                if lib.connect(scene, "", probe, [pin, "None"]):
                    scene_rgb = probe
                    _state["scene_output_pin"] = pin
                    break
            except Exception:
                continue
    if scene_rgb is None:
        _state["scene_input"] = "FAILED"
        lib.log(f"WARN {NAME}: no scene-colour source resolved - grade would "
                f"run on black. Loud per the owner's rule; verify() reports "
                f"scene_input=FAILED so the run does not claim success.")

    # ---------------- grade -------------------------------------------------
    # film grade (2026-10-07): scene colour runs through the neutral
    # MF_FilmGrade (contrast/warmth/saturation/lift - all identity at the
    # defaults), then the per-shot GradeTint multiplier. GradeTint stays the
    # final multiply so shot tint semantics are unchanged.
    if scene_rgb is not None:
        grade_call = lib.expr(mat, unreal.MaterialExpressionMaterialFunctionCall,
                              -1440, 160)
        grade_call.set_editor_property("material_function",
            unreal.load_asset(lib.asset_path(lib.FUNCTION_DIR,
                                             "MF_FilmGrade")))
        lib.connect(scene_rgb, "", grade_call, "Color")
        lib.connect(flt["FilmContrast"], "", grade_call, "Contrast")
        lib.connect(flt["FilmWarmth"], "", grade_call, "Warmth")
        lib.connect(flt["FilmSaturation"], "", grade_call, "Saturation")
        lib.connect(vec["FilmLift"], "", grade_call, "Lift")

        graded = lib.expr(mat, unreal.MaterialExpressionMultiply, -1280, 60)
        lib.connect(grade_call, "Color", graded, ["A", "a"])
        lib.connect(vec["GradeTint"], "", graded, ["B", "b"])
        current = graded
    else:
        current = vec["GradeTint"]  # placeholder; loud WARN above

    # ---------------- grain: (noise_r - 0.5) * GrainStrength ----------------
    noise_tex = unreal.load_asset(lib.asset_path(TEX_DIR, "T_Noise_White"))
    if noise_tex is not None:
        g_uv = lib.expr(mat, unreal.MaterialExpressionMultiply, -1440, 460)
        lib.connect(uv, "", g_uv, ["A", "a"])
        lib.connect(flt["GrainScale"], "", g_uv, ["B", "b"])
        noise = lib.expr(mat, unreal.MaterialExpressionTextureSample, -1280, 460)
        noise.set_editor_property("texture", noise_tex)
        lib.connect(g_uv, "", noise, ["UVs", ""])
        n_r = lib.expr(mat, unreal.MaterialExpressionComponentMask, -1120, 460)
        n_r.set_editor_property("r", True)
        n_r.set_editor_property("g", False)
        n_r.set_editor_property("b", False)
        n_r.set_editor_property("a", False)
        lib.connect(noise, "", n_r, ["", "None"])
        n_off = lib.expr(mat, unreal.MaterialExpressionSubtract, -960, 460)
        lib.binary(n_r, lib.scalar_const(mat, 0.5, -960, 540), n_off)
        grain = lib.expr(mat, unreal.MaterialExpressionMultiply, -800, 460)
        lib.binary(n_off, flt["GrainStrength"], grain)

        grain_add = lib.expr(mat, unreal.MaterialExpressionMultiply, -640, 200)
        lib.connect(current, "", grain_add, ["A", "a"])
        # scale 1+grain via lerp-free multiply: current * (1+grain) approximated
        # as current + current*grain (keeps grain signed and hue-preserving).
        cg = lib.expr(mat, unreal.MaterialExpressionMultiply, -640, 380)
        lib.connect(current, "", cg, ["A", "a"])
        lib.connect(grain, "", cg, ["B", "b"])
        add_n = lib.expr(mat, unreal.MaterialExpressionAdd, -480, 240)
        lib.connect(current, "", add_n, ["A", "a"])
        lib.connect(cg, "", add_n, ["B", "b"])
        current = add_n

    # ---------------- vignette: 1 - saturate(r * VignetteStrength) ----------
    # Radial distance from frame centre via the PROVEN lib.length2 helper
    # (build_mf_patterns.py:168,344: AppendVector + Length on two scalars).
    # dx/dy are masked out of (uv - 0.5) first so the append is a plain float2
    # and Length returns sqrt(dx^2 + dy^2), not a doubled-component length.
    # Constant2Vector (float2), NOT lib.constant (float3): Subtract of the
    # float2 ScreenPosition against a float3 failed shader compile with
    # "Arithmetic between types float2 and float3 are undefined" (build log
    # 2026-10-06). Dreamprint:297 uses the same Constant2Vector pattern.
    uv_c = lib.expr(mat, unreal.MaterialExpressionSubtract, -1440, 700)
    half_uv = lib.expr(mat, unreal.MaterialExpressionConstant2Vector, -1440, 780)
    half_uv.set_editor_property("r", 0.5)
    half_uv.set_editor_property("g", 0.5)
    lib.binary(uv, half_uv, uv_c)
    dx = lib.expr(mat, unreal.MaterialExpressionComponentMask, -1280, 640)
    dx.set_editor_property("r", True)
    dx.set_editor_property("g", False)
    dx.set_editor_property("b", False)
    dx.set_editor_property("a", False)
    lib.connect(uv_c, "", dx, ["", "None"])
    dy = lib.expr(mat, unreal.MaterialExpressionComponentMask, -1280, 740)
    dy.set_editor_property("r", False)
    dy.set_editor_property("g", True)
    dy.set_editor_property("b", False)
    dy.set_editor_property("a", False)
    lib.connect(uv_c, "", dy, ["", "None"])
    dist = lib.length2(mat, dx, dy, -1120, 700)

    vig_amt = lib.expr(mat, unreal.MaterialExpressionMultiply, -880, 700)
    lib.binary(dist, flt["VignetteStrength"], vig_amt)
    vig_sat = lib.expr(mat, unreal.MaterialExpressionSaturate, -720, 700)
    lib.unary(vig_amt, vig_sat)
    vig_f = lib.expr(mat, unreal.MaterialExpressionOneMinus, -560, 700)
    lib.unary(vig_sat, vig_f)

    vigged = lib.expr(mat, unreal.MaterialExpressionMultiply, -320, 300)
    lib.connect(current, "", vigged, ["A", "a"])
    lib.connect(vig_f, "", vigged, ["B", "b"])
    current = vigged

    # ---------------- halftone: frame pattern, inert at 0 -------------------
    h_uv = lib.expr(mat, unreal.MaterialExpressionMultiply, -640, 980)
    lib.connect(uv, "", h_uv, ["A", "a"])
    lib.connect(flt["HalftoneScale"], "", h_uv, ["B", "b"])
    pat_call = lib.expr(mat, unreal.MaterialExpressionMaterialFunctionCall,
                        -320, 980)
    pat_call.set_editor_property("material_function",
        unreal.load_asset(lib.asset_path(lib.FUNCTION_DIR, "MF_ProceduralPatterns")))
    lib.connect(h_uv, "", pat_call, "UV")
    lib.connect(lib.scalar_const(mat, 1.0, -320, 1060), "", pat_call, "Scale")
    lib.connect(lib.scalar_const(mat, 0.0, -320, 1120), "", pat_call, "Angle")
    lib.connect(lib.scalar_const(mat, 6.0, -320, 1180), "", pat_call, "CellIndex")
    lib.connect(lib.scalar_const(mat, 0.15, -320, 1240), "", pat_call, "Softness")
    lib.connect(pat_sdf_tex, "", pat_call, "SDFMap")
    lib.connect(lib.scalar_const(mat, 0.5, -320, 1300), "", pat_call, "Density")

    # dark = current * 0.75; out = lerp(current, dark, mask * HalftoneStrength)
    dark = lib.expr(mat, unreal.MaterialExpressionMultiply, -160, 420)
    lib.connect(current, "", dark, ["A", "a"])
    lib.connect(lib.scalar_const(mat, 0.75, -160, 500), "", dark, ["B", "b"])

    h_amt = lib.expr(mat, unreal.MaterialExpressionMultiply, -160, 780)
    lib.connect(pat_call, "Mask", h_amt, ["A", "a"])
    lib.connect(flt["HalftoneStrength"], "", h_amt, ["B", "b"])

    out_lerp = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, 120, 300)
    lib.connect(current, "", out_lerp, "A")
    lib.connect(dark, "", out_lerp, "B")
    lib.connect(h_amt, "", out_lerp, "Alpha")

    # ---------------- output: MP_EMISSIVE_COLOR (proven) --------------------
    lib.connect_property(out_lerp, unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
    except Exception as exc:
        lib.log(f"recompile warning: {exc}")

    # NO bind_toon_profile: post-process domain, no Toon BSDF.

    lib.save(mat)
    lib.log(f"{NAME} built with {lib.expression_count(mat)} expressions "
            f"scene_input={_state['scene_input']}")
    return mat


def verify():
    """Domain read-back MUST be MD_POST_PROCESS (dreamprint precedent), no
    BSDF present, and the scene-input path reported honestly."""
    path = lib.asset_path(lib.MASTER_DIR, NAME)
    mat = unreal.load_asset(path)
    result = {"name": NAME, "ok": False, "error": None}

    if mat is None:
        result["error"] = "does not load"
        lib.log(f"VERIFY {NAME}: FAIL {result['error']}")
        return result

    try:
        domain = mat.get_editor_property("material_domain")
        result["material_domain"] = str(domain)
        if domain != unreal.MaterialDomain.MD_POST_PROCESS:
            result["error"] = (f"material_domain is {domain}, want "
                               f"MD_POST_PROCESS - the grade would shade a "
                               f"surface instead of the frame")
    except Exception as exc:
        result["error"] = f"domain read: {str(exc)[:80]}"

    have_bsdf = False
    for n in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
        if type(n).__name__ in ("MaterialExpressionSubstrateToonBSDF",
                                "MaterialExpressionSubstrateBSDF",
                                "MaterialExpressionUnlitBSDF"):
            have_bsdf = True
            break
    result["have_bsdf"] = have_bsdf
    if result["error"] is None and have_bsdf:
        result["error"] = "BSDF present on a post-process material"

    result["scene_input"] = _state["scene_input"]
    result["scene_output_pin"] = _state["scene_output_pin"]
    if result["error"] is None and _state["scene_input"] == "FAILED":
        result["error"] = "no scene-colour source resolved (grade runs on black)"

    # -- neutral film grade (2026-10-07): MF_FilmGrade called + its parameter
    # surface present. At the identity defaults the call reduces to its
    # input, so verify() checks the wiring exists, not that pixels moved.
    if result["error"] is None:
        exprs = [e for e in
                 unreal.MaterialEditingLibrary.get_material_expressions(mat)
                 or [] if e is not None]
        called = set()
        for c in exprs:
            if type(c).__name__ == "MaterialExpressionMaterialFunctionCall":
                try:
                    mf = c.get_editor_property("material_function")
                    if mf is not None:
                        called.add(mf.get_name())
                except Exception:
                    continue
        if "MF_FilmGrade" not in called:
            result["error"] = "MF_FilmGrade is not called"
        else:
            params = set()
            for e in exprs:
                try:
                    params.add(str(e.get_editor_property("parameter_name")))
                except Exception:
                    continue
            want_params = {"FilmContrast", "FilmWarmth", "FilmSaturation",
                           "FilmLift"}
            miss_params = sorted(want_params - params)
            if miss_params:
                result["error"] = f"film grade params missing: {miss_params}"

    result["expression_count"] = lib.expression_count(mat)
    if result["error"] is None:
        result["ok"] = True

    lib.log(f"VERIFY {NAME}: ok={result['ok']} domain={result.get('material_domain')} "
            f"scene={_state['scene_input']} {result['error'] or ''}")
    return result


def main() -> int:
    mat = build()
    res = lib.verify_material(NAME,
                              expected_calls=["MF_ProceduralPatterns",
                                              "MF_FilmGrade"],
                              min_expressions=15)
    graph = verify()
    ok = mat is not None and res.get("ok") and graph.get("ok")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
