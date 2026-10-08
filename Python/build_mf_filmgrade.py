"""Build MF_FilmGrade - the neutral film colour grade (one shared writer).

OWNER-SCOPED LANE CHANGE 2026-10-07. The convergence doc tracked this lane
as `MF_NikkiDreamGrade` (dreamy pastel grade). The owner's brief for the
film core re-scopes it: the film wants a NEUTRAL photographic grade - the
pastel/dream grade (and its iridescence + sparkle siblings) stay out of
Humber. So the lane is rebuilt here as a neutral grade; the Nikki lane's
look lives in Melodia, not this spine.

This package name already exists as a non-resolving intake drop binary
(tracked); the get_or_create_function in-place rebuild wipes that dead
graph and regenerates it from code, keeping object identity for any
future reference.

READ (one Custom HLSL node)
---------------------------
c   = (Color - pivot) * Contrast + pivot        pivot = 0.18 (film gamma
                                                midpoint, not 0.5 - wood
                                                gamma 2.2 of 0.5 approx 0.18)
c  += Warmth * float3(0.08, 0.03, -0.08)       luma-neutral blue..amber shift
l   = dot(c, rec709)                            Rec.709 luma
c   = lerp(luma, c, Saturation)
c  += Lift                                      pedestal, e.g. (-0.01,0.0,0.02)
out = saturate(c)                               frame-domain clamp

IDENTITY CONTRACT (the strong kind - same default->pixel-invariant law
the space/cloth lanes landed with):
    Contrast 1.0, Warmth 0.0, Saturation 1.0, Lift (0,0,0)
    -> the algebra reduces to Color exactly (saturate is a no-op on the
    LDR frame the post chain hands over).

Controls - the "simple film controls" the brief asks for:
    Color       vec3    scene colour input
    Contrast    scalar  default 1.0; useful 0.8..1.4
    Warmth      scalar  default 0.0; useful -0.5 (cool)..0.5 (amber)
    Saturation  scalar  default 1.0; useful 0.0 (mono)..1.6
    Lift        vec3    default (0,0,0); useful +-0.05

Output: Color (vec3)
"""
from __future__ import annotations

import unreal

import spine_lib as lib

NAME = "MF_FilmGrade"

SCALAR = unreal.FunctionInputType.FUNCTION_INPUT_SCALAR
VECTOR3 = unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3

FLOAT3 = unreal.CustomMaterialOutputType.CMOT_FLOAT3

CODE = """float3 c = (Color - 0.18) * max(Contrast, 0.0) + 0.18;
c += Warmth * float3(0.08, 0.03, -0.08);
float l = dot(c, float3(0.2126, 0.7152, 0.0722));
c = lerp(float3(l, l, l), c, max(Saturation, 0.0));
c += Lift;
return saturate(c);"""

CUSTOM_INPUTS = ["Color", "Contrast", "Warmth", "Saturation", "Lift"]

FUNCTION_INPUTS = [
    ("Color", VECTOR3, (0.5, 0.5, 0.5, 1.0)),
    ("Contrast", SCALAR, 1.0),
    ("Warmth", SCALAR, 0.0),
    ("Saturation", SCALAR, 1.0),
    ("Lift", VECTOR3, (0.0, 0.0, 0.0, 1.0)),
]


def build(rebuild=True):
    lib.log(f"=== {NAME} ===")
    fn = lib.get_or_create_function(NAME, rebuild=rebuild)

    ins = {}
    y = -400
    for iname, itype, preview in FUNCTION_INPUTS:
        if itype == SCALAR:
            ins[iname] = lib.add_function_input(
                fn, iname, itype, preview=(preview, 0, 0, 0), x=-1200, y=y)
        else:
            ins[iname] = lib.add_function_input(
                fn, iname, itype, preview=preview, x=-1200, y=y)
        y += 150

    c = lib.custom_node(
        fn, CODE, FLOAT3,
        inputs=CUSTOM_INPUTS, x=-200, y=-150,
        description="Neutral film grade (contrast/warmth/sat/lift)")
    lib._desc(c, "NikkiDreamGrade lane re-scoped to a neutral film grade")

    for iname in CUSTOM_INPUTS:
        lib.connect(ins[iname], "", c, iname)

    out = lib.add_function_output(fn, "Color", x=700, y=-150)
    lib.connect(c, "", out, "")

    lib.save(fn)
    lib.log(f"{NAME} built with {lib.function_expression_count(fn)} expressions")
    return fn


def verify():
    path = lib.asset_path(lib.FUNCTION_DIR, NAME)
    fn = unreal.load_asset(path)
    result = {"name": NAME, "ok": False, "error": None}

    if fn is None:
        result["error"] = "does not load"
        lib.log(f"VERIFY {NAME}: FAIL {result['error']}")
        return result

    exprs = list(
        unreal.MaterialEditingLibrary.get_material_function_expressions(fn) or [])
    kinds = [type(e).__name__ for e in exprs if e is not None]
    outputs = [str(e.get_editor_property("output_name")) for e in exprs
               if e is not None
               and type(e).__name__ == "MaterialExpressionFunctionOutput"]

    if "MaterialExpressionCustom" not in kinds:
        result["error"] = "Custom (HLSL) node is gone"
    elif "Color" not in outputs:
        result["error"] = f"missing function output 'Color' (have {outputs})"
    else:
        graph = lib.verify_function_graph(NAME, max_dead=0)
        result["graph"] = graph
        if not graph.get("ok"):
            result["error"] = graph.get("error", "graph verify failed")
        else:
            result["ok"] = True

    lib.log(f"VERIFY {NAME}: ok={result['ok']} {result['error'] or ''}")
    return result


def main() -> int:
    build()
    res = verify()
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
