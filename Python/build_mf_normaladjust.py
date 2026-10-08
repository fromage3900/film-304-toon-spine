"""Build MF_NormalAdjust - normal conditioning for the toon spine.

CONVERGED FROM MELODIA, FILM-REFINED. Source lane:
    MF_NormalAdjust (Melodia master, Docs/MELODIA_TOON_CONVERGENCE.md)
Source asset even exists on disk here only as the non-resolving intake
drop - no usable graph, so this is authored from the recovered param
contract plus the source graph's own semantic
(BS_GodFile Content/Python/setup_material_functions.py `_build_normal_adjust`).

WHY THE FILM CONTRACT DIFFERS FROM THE SOURCE CONTRACT
------------------------------------------------------
The Melodia function operated on a PACKED tangent-space normal map
(n*2-1 rescale, XY scaled, Z powered, renormalized, repacked) - it is a
normal-MAP conditioner for a master that samples one. This film master
does not sample a normal map: it feeds the Substrate Toon BSDF a
WORLD-SPACE geometric normal (PixelNormalWS). Converting the source
maths to packed-in/packed-out would produce garbage against a
world-space input, so the function is rebased on the source's actual
JOB - scale how far the surface normal strays from its base, in
world space:

    n = base + (Normal - base) * NormalStrength, renormalized

* NormalStrength 1.0 (default) is an EXACT identity - pixel-identical
  to the pre-lane graph, which is the default-off law every lane in
  this repo obeys.
* < 1.0 softens normal response (cel bands ride smoother over curved
  geometry), > 1.0 exaggerates curvature (bands snap to edges).
  Clamp at 0 so a negative strength cannot invert the normal.

Controls (all FunctionInputs so any spine master can wire them):
    Normal         vec3   caller normal (world space, unit)
    BaseNormal     vec3   reference axis (world space, usually
                          VertexNormalWS or PixelNormalWS)
    NormalStrength scalar default 1.0 - identity

Output: Normal (vec3, world space, unit length)
"""
from __future__ import annotations

import unreal

import spine_lib as lib

NAME = "MF_NormalAdjust"

SCALAR = unreal.FunctionInputType.FUNCTION_INPUT_SCALAR
VECTOR3 = unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3

FLOAT3 = unreal.CustomMaterialOutputType.CMOT_FLOAT3

CODE = """float3 base_n = normalize(BaseNormal);
float3 n = base_n + (Normal - base_n) * max(NormalStrength, 0.0);
float len = length(n);
if (len < 1e-5) {
    n = base_n;
    len = max(length(base_n), 1e-5);
}
return n / len;"""

# Function inputs, in the order the code references them.
CUSTOM_INPUTS = ["Normal", "BaseNormal", "NormalStrength"]

FUNCTION_INPUTS = [
    ("Normal", VECTOR3, (0.0, 0.0, 1.0, 1.0)),
    ("BaseNormal", VECTOR3, (0.0, 0.0, 1.0, 1.0)),
    ("NormalStrength", SCALAR, 1.0),
]


def build(rebuild=True):
    lib.log(f"=== {NAME} ===")
    fn = lib.get_or_create_function(NAME, rebuild=rebuild)

    ins = {}
    y = -300
    for iname, itype, preview in FUNCTION_INPUTS:
        ins[iname] = lib.add_function_input(fn, iname, itype, preview=preview,
                                            x=-1200, y=y)
        y += 160

    c = lib.custom_node(
        fn, CODE, FLOAT3,
        inputs=CUSTOM_INPUTS, x=-200, y=-150,
        description="Normal strength shaping (1.0 = identity)")
    lib._desc(c, "Melodia-normal-adjust lane, world-space film contract")

    for iname in CUSTOM_INPUTS:
        lib.connect(ins[iname], "", c, iname)

    out = lib.add_function_output(fn, "Normal", x=800, y=-150)
    lib.connect(c, "", out, "")

    lib.save(fn)
    lib.log(f"{NAME} built with {lib.function_expression_count(fn)} expressions")
    return fn


def verify():
    """Structural + contract check (same shape as build_mf_spaceparallax)."""
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
    elif "Normal" not in outputs:
        result["error"] = f"missing function output 'Normal' (have {outputs})"
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
