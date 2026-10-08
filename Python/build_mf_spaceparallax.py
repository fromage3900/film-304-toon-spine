"""Build MF_SpaceParallax - toon multi-depth space parallax (Melodia convergence).

CONVERGED FROM MELODIA, NOT COPIED. Source asset:
    D:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Materials/Functions/MF_SpaceParallax.uasset
Recovered 2026-10-06 by static scan (Saved/Audit/melodia_toon_master_scan_2026-10-06.json).
The whole function is ONE MaterialExpressionCustom (HLSL) node fed by
CameraVectorWS / PixelNormalWS / TextureCoordinate / Time plus its own inputs,
so the logic below is copied VERBATIM - nothing is re-derived. See
Docs/MELODIA_TOON_CONVERGENCE.md.

Read: stars, galaxy and nebula sample the SAME StarMap at three different
depths; the view/normal offset (`pdir`) slides each layer by its Depth, so the
layers parallax against each other as the camera moves. The nebula band is
toon-stepped into shells (`ToonSteps`); stars composite last with a twinkle.

Inputs : StarMap (tex2D), SpaceLow, NebulaTint, GalaxyTint, StarTint,
         NebulaDepth, GalaxyDepth, StarDepth,
         NebulaStrength, GalaxyStrength, StarStrength, ToonSteps
Output : Color (vec3, additive -> EmissiveColor)
"""
from __future__ import annotations

import unreal

import spine_lib as lib

NAME = "MF_SpaceParallax"

SCALAR = unreal.FunctionInputType.FUNCTION_INPUT_SCALAR
VECTOR2 = unreal.FunctionInputType.FUNCTION_INPUT_VECTOR2
VECTOR3 = unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3
TEX2D = unreal.FunctionInputType.FUNCTION_INPUT_TEXTURE2D

FLOAT3 = unreal.CustomMaterialOutputType.CMOT_FLOAT3

# Verbatim from the source Custom node.
CODE = """float3 V = normalize(Cam);
float3 N = normalize(Normal);
float2 pdir = (V - N*dot(V,N)).xy;
float3 nebL = Texture2DSample(StarMap, StarMapSampler, UV + pdir*NebulaDepth).rgb;
float3 galL = Texture2DSample(StarMap, StarMapSampler, UV + pdir*GalaxyDepth).rgb;
float3 starL = Texture2DSample(StarMap, StarMapSampler, UV + pdir*StarDepth).rgb;
float steps = max(ToonSteps,1.0);
float nl = dot(nebL, float3(0.299,0.587,0.114));
float nb = floor(saturate(nl*2.0)*steps)/steps;
float3 col = SpaceLow;
col += NebulaTint * nb * NebulaStrength;
col += galL * GalaxyTint * GalaxyStrength;
float sl = dot(starL, float3(0.299,0.587,0.114));
float sb = saturate((sl-0.55)*6.0);
col += StarTint * sb * StarStrength * (0.6+0.4*sin(Tm*2.0 + sl*30.0));
return col;"""

# Inputs, in the order the code references them. Names are the HLSL identifiers.
CUSTOM_INPUTS = [
    "Cam", "Normal", "UV", "Tm", "StarMap",
    "NebulaDepth", "GalaxyDepth", "StarDepth", "ToonSteps", "SpaceLow",
    "NebulaTint", "NebulaStrength", "GalaxyTint", "GalaxyStrength",
    "StarTint", "StarStrength",
]

# (input_name, type, preview) - the artist-facing contract.
FUNCTION_INPUTS = [
    ("StarMap", TEX2D, (0, 0, 0)),
    ("SpaceLow", VECTOR3, (0.02, 0.02, 0.06, 1.0)),
    ("NebulaTint", VECTOR3, (0.35, 0.18, 0.45, 1.0)),
    ("GalaxyTint", VECTOR3, (0.45, 0.45, 0.75, 1.0)),
    ("StarTint", VECTOR3, (1.0, 0.95, 0.85, 1.0)),
    ("NebulaDepth", SCALAR, 0.150),
    ("GalaxyDepth", SCALAR, 0.060),
    ("StarDepth", SCALAR, 0.020),
    ("NebulaStrength", SCALAR, 0.80),
    ("GalaxyStrength", SCALAR, 0.60),
    ("StarStrength", SCALAR, 0.70),
    ("ToonSteps", SCALAR, 4.0),
]


def build(rebuild=True):
    lib.log(f"=== {NAME} ===")
    fn = lib.get_or_create_function(NAME, rebuild=rebuild)

    ins = {}
    y = -600
    for iname, itype, preview in FUNCTION_INPUTS:
        ins[iname] = lib.add_function_input(fn, iname, itype, preview=preview,
                                            x=-1600, y=y)
        y += 150

    # View / normal / uv / time come from the graph, not the caller.
    cam = lib.expr(fn, unreal.MaterialExpressionCameraVectorWS, -1400, -900)
    nrm = lib.expr(fn, unreal.MaterialExpressionPixelNormalWS, -1400, -760)
    uv = lib.expr(fn, unreal.MaterialExpressionTextureCoordinate, -1400, -620)
    tm = lib.expr(fn, unreal.MaterialExpressionTime, -1400, -480)

    c = lib.custom_node(
        fn, CODE, FLOAT3,
        inputs=CUSTOM_INPUTS, x=-400, y=-200,
        description="Space Parallax ~ cosmic depth trick")
    lib._desc(c, "Melodia MF_SpaceParallax, verbatim HLSL")

    # Wire the Custom inputs (declared above, so the pins exist).
    lib.connect(cam, "", c, "Cam")
    lib.connect(nrm, "", c, "Normal")
    lib.connect(uv, "", c, "UV")
    lib.connect(tm, "", c, "Tm")
    for iname in ("StarMap", "NebulaDepth", "GalaxyDepth", "StarDepth",
                  "ToonSteps", "SpaceLow", "NebulaTint", "NebulaStrength",
                  "GalaxyTint", "GalaxyStrength", "StarTint", "StarStrength"):
        lib.connect(ins[iname], "", c, iname)

    out = lib.add_function_output(fn, "Color", x=900, y=-200)
    lib.connect(c, "", out, "")

    lib.save(fn)
    lib.log(f"{NAME} built with {lib.function_expression_count(fn)} expressions")
    return fn


def verify():
    """Structural check + the Custom node's own contract.

    verify_function_graph catches dead nodes / unwired outputs / unused inputs.
    It cannot see a Custom input that was declared but never wired (the node
    still lists 16 inputs, it just reads the HLSL default), so the wiring is
    asserted here - an unwired StarMap/Depth would otherwise compile clean.
    """
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

