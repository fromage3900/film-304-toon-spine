"""Build MF_ClothWindDrape - cloth wind WPO (Melodia convergence).

CONVERGED FROM MELODIA, NOT COPIED. Source asset:
    D:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Materials/Functions/MF_ClothWindDrape.uasset
Recovered 2026-10-06 by static scan; the function is ONE MaterialExpressionCustom
(HLSL) node, so its logic is copied VERBATIM. See
Docs/MELODIA_TOON_CONVERGENCE.md.

Read: a wind sweep plus a two-frequency fold/flap wave along U, amplifying into
a World-Position-Offset vector. Feed the output to WPO on cloth/foliage.

Inputs : WindDirection (vec3), WindStrength, WindSpeed, FoldingAmount,
         DrapeMask, UV (vec2)
Output : NormalOffset (vec3 -> WorldPositionOffset)

CONTROL CONTRACT (refined 2026-10-07, film material core - descriptions
and ranges only, no maths change):
    WindStrength    scalar default 0, gate #1. cm of displacement.
                    Useful: drift 0.05..0.15, walk breeze 0.2..0.35,
                    gale 0.5..1.0.
    WindSpeed       scalar default 0.5 cycles/sec.
                    Useful: 0.2 slow drift .. 1.5 gusting.
    FoldingAmount   scalar default 0, gate #2. 0..1.
                    Useful: 0.25..0.5 for a read-from-stage cloth flap.
    DrapeMask       scalar default 1. Per-surface weight (0 calms one
                    surface entirely, e.g. a pinned sleeve).
    WindDirection   vec3   default (1,0,0). WORLD space; the offset is
                    emitted along this axis (normalize before wiring).

IDENTITY GATE: WindStrength 0 AND FoldingAmount 0 (both) -> every term
is zero and the output is exactly (0,0,0), which is what the master
ships by default. The master's own verify() and the spine expected-calls
assert this surface; nothing here changes pixels until an instance opts
in.

Note: the source wired a Constant3Vector somewhere in this graph. This
reconstruction exposes WindDirection as a function INPUT instead, so the wind
direction is artist-controllable from the master rather than baked - the
convergent, film-useful contract. Flagged in Docs/MELODIA_TOON_CONVERGENCE.md.
"""
from __future__ import annotations

import unreal

import spine_lib as lib

NAME = "MF_ClothWindDrape"

SCALAR = unreal.FunctionInputType.FUNCTION_INPUT_SCALAR
VECTOR2 = unreal.FunctionInputType.FUNCTION_INPUT_VECTOR2
VECTOR3 = unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3

FLOAT3 = unreal.CustomMaterialOutputType.CMOT_FLOAT3

# Verbatim from the source Custom node.
CODE = """float sweep = WindStrength * sin(Time * WindSpeed * 3.14159 * 2.0);
float phaseU = UV.x * 6.28318;
float fold = FoldingAmount * sin(phaseU * 2.0 + Time * WindSpeed * 6.28318 * 0.75);
float flap = FoldingAmount * 0.35 * sin(phaseU + Time * WindSpeed * 6.28318 * 1.25 + 1.7);
float amp = DrapeMask * saturate(WindStrength * 3.0 + FoldingAmount * 1.5);
float3 offset = WindDirection * (sweep + fold + flap) * amp;
offset.z += amp * 0.25 * (1.0 + sin(Time * WindSpeed * 3.14159 * 1.6 + phaseU * 0.5));
return offset;"""

CUSTOM_INPUTS = [
    "WindDirection", "WindStrength", "WindSpeed", "FoldingAmount",
    "DrapeMask", "UV", "Time",
]

FUNCTION_INPUTS = [
    ("WindDirection", VECTOR3, (1.0, 0.0, 0.0, 1.0)),
    ("WindStrength", SCALAR, 0.25),
    ("WindSpeed", SCALAR, 0.50),
    ("FoldingAmount", SCALAR, 0.35),
    ("DrapeMask", SCALAR, 1.0),
    ("UV", VECTOR2, (0, 0, 0, 0)),
]


def build(rebuild=True):
    lib.log(f"=== {NAME} ===")
    fn = lib.get_or_create_function(NAME, rebuild=rebuild)

    ins = {}
    y = -500
    for iname, itype, preview in FUNCTION_INPUTS:
        ins[iname] = lib.add_function_input(fn, iname, itype, preview=preview,
                                            x=-1400, y=y)
        y += 160

    # FIX 2026-10-07 (film material core stability gate): the source HLSL
    # references `Time`, and a Custom node has no Time identifier of its
    # own. In a WorldPositionOffset context this code compiles ONLY in
    # vertex shaders, where no Time uniform exists - the first real
    # compile of this graph failed with "use of undeclared identifier
    # 'Time'" (spine run 2, 2026-10-07) and Universal would have rendered
    # Default Material. The source graph fed the Custom a
    # MaterialExpressionTime node; reproduce that: Time is an INTERNAL
    # read, not a function input, so the master's call sites stay
    # unchanged and the function's artist-facing inputs are exactly the
    # six FUNCTION_INPUTS above.
    tm = lib.expr(fn, unreal.MaterialExpressionTime, -1400, 460)

    c = lib.custom_node(
        fn, CODE, FLOAT3,
        inputs=CUSTOM_INPUTS, x=-300, y=-200,
        description="MF_ClothWindDrape wind sweep/fold/flap")
    lib._desc(c, "Melodia MF_ClothWindDrape, verbatim HLSL (Time internal)")

    for iname, _t, _p in FUNCTION_INPUTS:
        lib.connect(ins[iname], "", c, iname)
    lib.connect(tm, "", c, "Time")

    out = lib.add_function_output(fn, "NormalOffset", x=900, y=-200)
    lib.connect(c, "", out, "")

    lib.save(fn)
    lib.log(f"{NAME} built with {lib.function_expression_count(fn)} expressions")
    return fn


def verify():
    """Structural check + Custom-node contract (see build_mf_spaceparallax)."""
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
    elif "NormalOffset" not in outputs:
        result["error"] = f"missing function output 'NormalOffset' (have {outputs})"
    else:
        graph = lib.verify_function_graph(NAME, max_dead=0)
        result["graph"] = graph
        if not graph.get("ok"):
            result["error"] = graph.get("error", "graph verify failed")
        else:
            result["ok"] = True

    lib.log(f"VERIFY {NAME}: ok={result['ok']} {result['error'] or ''}")
    return result
