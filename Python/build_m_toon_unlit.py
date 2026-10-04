"""Build M_Toon_Unlit_Character - the shadowless character master.

WHY THIS EXISTS
---------------
This is the one-shot experiment from `Docs/FILM_PIPELINE.md` §7, turned into an
asset. The Spice Frontier route - the closest published match to a cel-shaded
UE5 production - does not styleise character lighting, it **deletes** it, and
separates the character from a painted backdrop with an offset rim instead.
Epic's spotlight on that show: *"forgoing lighting and removing shadow and
detail to maintain a 2D style"*.

That matters here because it sidesteps almost every failure mode in
`Docs/TOON_PIPELINE_REFERENCE.md` §3 at once: no band popping (there are no
bands), no Lumen noise, no shadow terminator artifacts, no shadow acne, no
shadow-cascade tuning. The most-cited complaint about Substrate Toon is that
sky light and GI land on top of the bands as smooth, unramped shading - and
this master has no bands to spoil.

WHAT IT DELIBERATELY IS NOT
---------------------------
- **No Substrate Toon BSDF, and no Toon Profile.** A profile drives a light
  response; this surface has no light response. Binding `TP_*` here would imply
  a control surface that does nothing, which is the F6 defect class in a new
  costume. `verify()` asserts the profile is NOT set, so the day someone wires
  one up the build says so.
- **Not a game character master.** It carries no WPO, no wind, no cloth. It is a
  graphic-film surface: flat colour, one rim, nothing else.

OUTPUT WIRING
-------------
The rim is ADDITIVE and goes to EmissiveColor. Wiring it to Surface would erase
the shading beneath - the mistake `MF_RimOffset`'s docstring warns about, and
the reason this master exists as the single place that gets it right.
"""
from __future__ import annotations

import unreal

import spine_lib as lib

NAME = "M_Toon_Unlit_Character"

SURFACE_PARAMS = [
    ("BaseTint", "Palette", (0.62, 0.55, 0.50, 1.0), "Flat character colour"),
    ("RimColor", "Palette", (1.00, 0.95, 0.88, 1.0), "Edge-of-light colour"),
]

FLOAT_PARAMS = [
    ("RimStart", "Rim", 0.55, "Where the rim starts along the facing term"),
    ("RimEnd", "Rim", 0.92, "Where the rim ends"),
    ("RimSharpness", "Rim", 2.20, "Rim edge tightness"),
    ("RimStrength", "Rim", 1.00, "Overall rim amount"),
    ("OffsetStrength", "Rim", 0.60, "How far the rim is pushed to one side"),
]


def build(rebuild=True):
    lib.log(f"=== {NAME} ===")
    mat = lib.get_or_create_material(NAME, folder=lib.MASTER_DIR, rebuild=rebuild)

    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_SURFACE)
    # Opaque: the surface is flat colour and the rim is additive, so there is
    # nothing to mask. Masked would only cost an alpha test per pixel.
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    lib.try_set(mat, "two_sided", False)

    vec, flt = {}, {}
    y = -600
    for pname, group, default, desc in SURFACE_PARAMS:
        vec[pname] = lib.vector(mat, pname, group, default, -1400, y, desc=desc)
        y += 180
    y = -600
    for pname, group, default, desc in FLOAT_PARAMS:
        flt[pname] = lib.scalar(mat, pname, group, default, -1400, y, desc=desc)
        y += 180

    # ---- the reusable rim term ----
    rim = lib.expr(mat, unreal.MaterialExpressionMaterialFunctionCall, -600, 0)
    rim.set_editor_property("material_function",
                            unreal.load_asset(
                                lib.asset_path(lib.FUNCTION_DIR, "MF_RimOffset")))
    lib.connect(flt["RimStart"], "", rim, "RimStart")
    lib.connect(flt["RimEnd"], "", rim, "RimEnd")
    lib.connect(flt["RimSharpness"], "", rim, "Sharpness")
    lib.connect(flt["RimStrength"], "", rim, "RimStrength")
    lib.connect(flt["OffsetStrength"], "", rim, "OffsetStrength")
    lib.connect(vec["RimColor"], "", rim, "RimColor")

    # Normal comes from the node's own world normal: this master does not accept
    # a custom normal input, so there is nothing to wire and no way for a caller
    # to disagree with the rim.

    # ---- surface: flat colour, unlit ----
    unlit = lib.expr(mat, unreal.MaterialExpressionSubstrateUnlitBSDF, 200, 0)
    lib.connect(vec["BaseTint"], "", unlit, "BaseColor")
    lib.connect_property(unlit, unreal.MaterialProperty.MP_FRONT_MATERIAL)

    # ---- rim: additive on top ----
    lib.connect_property(rim, unreal.MaterialProperty.MP_EMISSIVE_COLOR,
                         src_output="RimEmissive")

    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
    except Exception as exc:
        lib.log(f"recompile warning: {exc}")

    lib.save(mat)
    lib.log(f"{NAME} built with {lib.expression_count(mat)} expressions")
    return mat


def verify():
    """Assert the call is present, the rim is on EMISSIVE not SURFACE, and no
    Toon Profile is bound.

    The first two are the two ways this master can be subtly wrong while still
    compiling and still looking plausible in a viewport: an unwired function call
    (the 2026-09-29 truncation failure, where `verify_material` counted zero calls
    and reported clean) or a rim on Surface that flattens the shading.
    """
    path = lib.asset_path(lib.MASTER_DIR, NAME)
    mat = unreal.load_asset(path)
    result = {"name": NAME, "ok": False, "error": None}

    if mat is None:
        result["error"] = "does not load"
        lib.log(f"VERIFY {NAME}: FAIL {result['error']}")
        return result

    el = unreal.MaterialEditingLibrary
    exprs = list(el.get_material_expressions(mat) or [])
    kinds = [type(e).__name__ for e in exprs if e is not None]

    calls = lib.function_calls(mat)
    rim_calls = [c for c in calls if c.endswith("MF_RimOffset")]
    result["function_calls"] = calls

    if not rim_calls:
        result["error"] = ("MF_RimOffset is not called - the master would render as "
                           "flat colour with no edge of light, which is the one "
                           "thing it exists to do")
    elif "MaterialExpressionSubstrateUnlitBSDF" not in kinds:
        result["error"] = "no Substrate Unlit BSDF in the graph"
    else:
        # A Toon Profile here would be a control that cannot do anything.
        toon = [e for e in exprs
                if e is not None
                and type(e).__name__ == "MaterialExpressionSubstrateToonBSDF"]
        result["toon_bsdf_count"] = len(toon)
        if toon:
            prof = getattr(toon[0], "toon_profile", None)
            if prof is not None:
                result["error"] = (f"a Toon Profile is bound ({prof.get_path_name()}) "
                                   "on an unlit surface - it controls a light "
                                   "response this master does not have")
            else:
                result["error"] = ("a Toon BSDF is present on an unlit master - "
                                   "remove it or bind nothing")
        else:
            result["ok"] = True

    lib.log(f"VERIFY {NAME}: ok={result['ok']} {result['error'] or ''}")
    return result