"""Build M_Master_Toon_Sky - the banded sky dome (unlit, no Toon Profile).

WHY ITS OWN MASTER
------------------
SH010 opens on a silhouette against sky and SH020 is atmospheric depth - the
film's first image is this surface (TOON_MASTERS_PLAN_2026-10-04.md tier C).
A sky is not an environment surface: it must NOT inherit the key-light ramp an
environment master gets, because there is no light to ramp. The sky's bands are
AUTHORED, not lit.

WHAT IT DELIBERATELY IS NOT
---------------------------
- **No Substrate Toon BSDF, and no Toon Profile.** Same contract as
  M_Toon_Unlit_Character: a profile shapes a light response, a sky dome has
  none. Binding TP_* here would be a control that cannot do anything - the F6
  defect class. verify() asserts no profile and no Toon BSDF, so the day
  someone wires one the build says so.
- **Not a time-of-day system.** Three colour knobs, a posterised vertical
  gradient, noise clouds and an opt-in star field. Scripted time-of-day would
  be architecture ahead of content; the shot deck grades each shot instead.

THE GRADIENT
------------
V is masked out of the texture coordinate, posterised with Floor(uv.V * bands)
/ bands - the same node family build_mf_patterns already uses (Floor is proven
on this build), so the horizon-to-zenith lerp steps in bands rather than
ramping smoothly. That step IS the stylisation: a smooth sky gradient reads as
"lit", banded reads as "drawn".

Stars sit UNDER the clouds (stars are added to the gradient first, then the
cloud lerp runs over the top), so cloud cover occludes them instead of
shining through.
"""
from __future__ import annotations

import unreal

import spine_lib as lib

NAME = "M_Master_Toon_Sky"
TEX_DIR = "/Game/Materials/Textures"

VECTOR_PARAMS = [
    ("ZenithColor", (0.22, 0.40, 0.68, 1.0), "Top-of-sky colour (gradient B)"),
    ("HorizonColor", (0.74, 0.83, 0.88, 1.0), "Horizon colour (gradient A)"),
    ("CloudColor", (0.88, 0.91, 0.94, 1.0), "Cloud band colour"),
    ("StarColor", (0.95, 0.97, 1.00, 1.0), "Star point colour"),
]

FLOAT_PARAMS = [
    ("PosterizationBands", 5.0, "Steps in the vertical gradient; 0-ish = smooth"),
    ("CloudScale", 3.0, "Cloud noise frequency (UV multiplier)"),
    ("CloudStrength", 0.35, "How hard clouds blend over the gradient (0 = clear)"),
    ("StarScale", 90.0, "Star noise frequency - high = sparse points"),
    ("StarIntensity", 1.60, "Star brightness before the on/off switch"),
]


def build(rebuild=True):
    lib.log(f"=== {NAME} ===")
    mat = lib.get_or_create_material(NAME, folder=lib.MASTER_DIR, rebuild=rebuild)

    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_SURFACE)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)

    # ---------------- parameters ----------------
    vec = {}
    y = -600
    for pname, default, desc in VECTOR_PARAMS:
        vec[pname] = lib.vector(mat, pname, "Sky", default, -2000, y, desc=desc)
        y += 140
    flt = {}
    for pname, default, desc in FLOAT_PARAMS:
        flt[pname] = lib.scalar(mat, pname, "Sky", default, -2000, y, desc=desc)
        y += 80

    uv = lib.expr(mat, unreal.MaterialExpressionTextureCoordinate, -2000, 700)

    # ---------------- posterised vertical gradient ----------------
    uvy = lib.expr(mat, unreal.MaterialExpressionComponentMask, -1840, 700)
    uvy.set_editor_property("r", False)
    uvy.set_editor_property("g", True)
    uvy.set_editor_property("b", False)
    uvy.set_editor_property("a", False)
    lib.connect(uv, "", uvy, ["", "None"])

    poster_src = lib.expr(mat, unreal.MaterialExpressionMultiply, -1680, 700)
    lib.binary(uvy, flt["PosterizationBands"], poster_src)

    floored = lib.expr(mat, unreal.MaterialExpressionFloor, -1520, 700)
    lib.unary(poster_src, floored)

    poster = lib.expr(mat, unreal.MaterialExpressionDivide, -1360, 700)
    lib.binary(floored, flt["PosterizationBands"], poster)

    grad = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, -1200, 700)
    lib.ternary(vec["HorizonColor"], vec["ZenithColor"], poster, grad)

    # ---------------- stars (under the clouds) ----------------
    star_zero = lib.scalar_const(mat, 0.0, -1680, 1180)
    star_uv = lib.expr(mat, unreal.MaterialExpressionMultiply, -1680, 1100)
    lib.binary(uv, flt["StarScale"], star_uv)

    star_sample = lib.expr(mat, unreal.MaterialExpressionTextureSample, -1520, 1100)
    star_sample.set_editor_property("texture",
        unreal.load_asset(lib.asset_path(TEX_DIR, "T_Noise_White")))
    if star_sample.get_editor_property("texture") is None:
        raise RuntimeError("T_Noise_White missing - run build_textures first")
    lib.connect(star_uv, "", star_sample, ["UVs", ""])

    star_r = lib.expr(mat, unreal.MaterialExpressionComponentMask, -1360, 1100)
    star_r.set_editor_property("r", True)
    star_r.set_editor_property("g", False)
    star_r.set_editor_property("b", False)
    star_r.set_editor_property("a", False)
    lib.connect(star_sample, "", star_r, ["", "None"])

    # power keeps only the rare bright texels - a point field, not a grey wash
    star_pow = lib.expr(mat, unreal.MaterialExpressionPower, -1200, 1100)
    lib.binary(star_r, lib.scalar_const(mat, 40.0, -1200, 1180), star_pow)

    star_bright = lib.expr(mat, unreal.MaterialExpressionMultiply, -1040, 1100)
    lib.binary(star_pow, flt["StarIntensity"], star_bright)

    star_gate = lib.expr(mat, unreal.MaterialExpressionStaticSwitchParameter,
                         -880, 1100)
    star_gate.set_editor_property("parameter_name", "bStarsOn")
    star_gate.set_editor_property("group", "Sky")
    star_gate.set_editor_property("default_value", False)
    lib.connect(star_bright, "", star_gate, ["True"])
    lib.connect(star_zero, "", star_gate, ["False"])

    with_stars = lib.expr(mat, unreal.MaterialExpressionAdd, -720, 800)
    lib.binary(grad, star_gate, with_stars)

    # ---------------- clouds over the top ----------------
    cloud_uv = lib.expr(mat, unreal.MaterialExpressionMultiply, -1680, 1440)
    lib.binary(uv, flt["CloudScale"], cloud_uv)

    cloud_sample = lib.expr(mat, unreal.MaterialExpressionTextureSample, -1520, 1440)
    cloud_sample.set_editor_property("texture",
        unreal.load_asset(lib.asset_path(TEX_DIR, "T_Noise_White")))
    lib.connect(cloud_uv, "", cloud_sample, ["UVs", ""])

    cloud_r = lib.expr(mat, unreal.MaterialExpressionComponentMask, -1360, 1440)
    cloud_r.set_editor_property("r", True)
    cloud_r.set_editor_property("g", False)
    cloud_r.set_editor_property("b", False)
    cloud_r.set_editor_property("a", False)
    lib.connect(cloud_sample, "", cloud_r, ["", "None"])

    cloud_amt = lib.expr(mat, unreal.MaterialExpressionMultiply, -1200, 1440)
    lib.binary(cloud_r, flt["CloudStrength"], cloud_amt)

    clouded = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, -400, 800)
    lib.ternary(with_stars, vec["CloudColor"], cloud_amt, clouded)

    # ---------------- unlit surface ----------------
    unlit = lib.expr(mat, unreal.MaterialExpressionSubstrateUnlitBSDF, 200, 700)
    lib.connect(clouded, "", unlit, "BaseColor")
    lib.connect_property(unlit, unreal.MaterialProperty.MP_FRONT_MATERIAL)

    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
    except Exception as exc:
        lib.log(f"recompile warning: {exc}")

    lib.save(mat)
    lib.log(f"{NAME} built with {lib.expression_count(mat)} expressions")
    return mat


def verify():
    """No Toon Profile, no Toon BSDF, unlit BSDF present.

    The whole contract of this master: a sky must not inherit a light response.
    A profile bound here would imply a control surface over shading the dome
    never receives (same F6 defect class as M_Toon_Unlit_Character).
    """
    path = lib.asset_path(lib.MASTER_DIR, NAME)
    mat = unreal.load_asset(path)
    result = {"name": NAME, "ok": False, "error": None}

    if mat is None:
        result["error"] = "does not load"
        lib.log(f"VERIFY {NAME}: FAIL {result['error']}")
        return result

    exprs = [e for e in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []
             if e is not None]
    kinds = [type(e).__name__ for e in exprs]

    if "MaterialExpressionSubstrateUnlitBSDF" not in kinds:
        result["error"] = "no Substrate Unlit BSDF in the graph"
    else:
        toon = [e for e in exprs
                if type(e).__name__ == "MaterialExpressionSubstrateToonBSDF"]
        result["toon_bsdf_count"] = len(toon)
        if toon:
            prof = getattr(toon[0], "toon_profile", None)
            result["error"] = (
                f"a Toon BSDF is present on the sky master"
                + (f" with profile {prof.get_path_name()}" if prof else "")
                + " - a sky receives no light to ramp")
        else:
            result["ok"] = True

    result["expression_count"] = len(exprs)
    lib.log(f"VERIFY {NAME}: ok={result['ok']} exprs={len(exprs)} "
            f"{result['error'] or ''}")
    return result


def main() -> int:
    mat = build()
    res = lib.verify_material(NAME, expected_calls=[], min_expressions=15)
    graph = verify()
    ok = mat is not None and res.get("ok") and graph.get("ok")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
