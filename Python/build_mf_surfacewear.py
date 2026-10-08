"""Build MF_SurfaceWear - truchet cracks + wear-field masks (film utility).

CONVERGED FROM MELODIA, FILM-REFINED. Source lane: MF_Itto ("Truchet crack
+ wear masks / cracks", Docs/MELODIA_TOON_CONVERGENCE.md). The source asset
exists here only as a non-resolving intake drop binary and its full node
graph was never regenerable from text - a byte copy was exactly the failure
this repo's generated-not-copied rule exists for. So the lane is rebuilt as
a film utility under a film-clear name (the task's "surface wear"):

    MF_Itto (Melodia drop, unused, stays out of the spine)
      -> MF_SurfaceWear (generated, this builder, consumed by the spine)

WHAT IT DOES (all maths inside one Custom HLSL node)
----------------------------------------------------
* Dominant-axis world projection: the pattern grid follows walls (ZY / ZX
  planes) and floors (XY) so cracks never stretch across a face - the
  cheap film-grade stand-in for triplanar.
* CrackMask: classic two-variant truchet double-arc maze, hash-selected
  per cell. CrackWidth is the line thickness in cell units.
* WearMask: low-frequency bilinear value-noise patches, thresholded -
  the broad wear field the cracks sit inside.

It outputs MASKS ONLY. What happens to colour/roughness is the caller's
decision (this repo's functions stay pure; masters own material intent).

Controls (all FunctionInputs):
    Normal        vec3    caller PixelNormalWS (world space, unit)
    WearScale     scalar  tile frequency in cells/cm; 0.02 = a 50 cm cell
    CrackWidth    scalar  crack line width in cell units (0.02..0.08 useful)
    WearThreshold scalar  patch onset 0..1 (higher = rarer wear patches)

Outputs:
    CrackMask float1 0..1 truchet line field (1 on the crack)
    WearMask  float1 0..1 wear patches

Default-stable by construction: the MASTER gates both masks behind
WearStrength / CrackStrength = 0, so existing instances are
pixel-identical until they opt in.
"""
from __future__ import annotations

import unreal

import spine_lib as lib

NAME = "MF_SurfaceWear"

SCALAR = unreal.FunctionInputType.FUNCTION_INPUT_SCALAR
VECTOR3 = unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3

FLOAT3 = unreal.CustomMaterialOutputType.CMOT_FLOAT3

# r = crack mask, g = wear mask. The master masks the components.
CODE = """float3 an = abs(Normal);
float2 g;
if (an.z >= an.x && an.z >= an.y) {
    g = WorldPos.xy;
} else if (an.y >= an.x) {
    g = WorldPos.xz;
} else {
    g = WorldPos.zy;
}
float cell = max(WearScale, 1e-5);
g *= cell;

float2 idf = floor(g);
float2 f = g - idf;

// truchet double-arc maze, two variants picked per cell
float da = abs(min(length(f - float2(0.0, 0.5)),
                   length(f - float2(1.0, 0.5))) - 0.5);
float db = abs(min(length(f - float2(0.5, 0.0)),
                   length(f - float2(0.5, 1.0))) - 0.5);
float pick = frac(sin(dot(idf + 0.5, float2(127.1, 311.7))) * 43758.5453);
float d = (pick > 0.5) ? da : db;
float width = max(CrackWidth, 1e-4);
float crack = 1.0 - saturate(d / width);
crack = saturate((crack - 0.25) / 0.75);

// low-frequency wear patches: bilinear value noise on a 2.7x-larger grid
float2 wn = g * 0.37;
float2 wid = floor(wn);
float2 wf = wn - wid;
float na = frac(sin(dot(wid, float2(127.1, 311.7))) * 43758.5453);
float nb = frac(sin(dot(wid + float2(1.0, 0.0), float2(127.1, 311.7))) * 43758.5453);
float nc = frac(sin(dot(wid + float2(0.0, 1.0), float2(127.1, 311.7))) * 43758.5453);
float nd = frac(sin(dot(wid + float2(1.0, 1.0), float2(127.1, 311.7))) * 43758.5453);
float nv = lerp(lerp(na, nb, wf.x), lerp(nc, nd, wf.x), wf.y);
float wear = smoothstep(WearThreshold, min(WearThreshold + 0.35, 1.0), nv);

return float3(crack, wear, crack * wear);"""

CUSTOM_INPUTS = ["Normal", "WorldPos", "WearScale", "CrackWidth",
                 "WearThreshold"]

FUNCTION_INPUTS = [
    ("Normal", VECTOR3, (0.0, 0.0, 1.0, 1.0)),
    ("WearScale", SCALAR, 0.02),
    ("CrackWidth", SCALAR, 0.04),
    ("WearThreshold", SCALAR, 0.55),
]


def build(rebuild=True):
    lib.log(f"=== {NAME} ===")
    fn = lib.get_or_create_function(NAME, rebuild=rebuild)

    ins = {}
    y = -450
    for iname, itype, preview in FUNCTION_INPUTS:
        ins[iname] = lib.add_function_input(fn, iname, itype, preview=preview,
                                            x=-1300, y=y)
        y += 170

    # internal reads: world position + pixel normal (self-contained lane)
    wp = lib.expr(fn, unreal.MaterialExpressionWorldPosition, -1300, 220)
    pn = lib.expr(fn, unreal.MaterialExpressionPixelNormalWS, -1300, 380)

    c = lib.custom_node(
        fn, CODE, FLOAT3,
        inputs=CUSTOM_INPUTS, x=-250, y=-100,
        description="Truchet cracks + wear patches (dominant-axis world)")
    lib._desc(c, "MF_Itto lane rebuilt as film surface-wear masks")

    lib.connect(ins["Normal"], "", c, "Normal")
    lib.connect(wp, "", c, "WorldPos")
    for iname in ("WearScale", "CrackWidth", "WearThreshold"):
        lib.connect(ins[iname], "", c, iname)

    crack_m = lib.expr(fn, unreal.MaterialExpressionComponentMask, 200, -260)
    crack_m.set_editor_property("r", True)
    crack_m.set_editor_property("g", False)
    crack_m.set_editor_property("b", False)
    crack_m.set_editor_property("a", False)
    lib.connect(c, "", crack_m, ["", "None"])

    wear_m = lib.expr(fn, unreal.MaterialExpressionComponentMask, 200, -60)
    wear_m.set_editor_property("r", False)
    wear_m.set_editor_property("g", True)
    wear_m.set_editor_property("b", False)
    wear_m.set_editor_property("a", False)
    lib.connect(c, "", wear_m, ["", "None"])

    out_crack = lib.add_function_output(fn, "CrackMask", x=600, y=-260)
    lib.connect(crack_m, "", out_crack, "")
    out_wear = lib.add_function_output(fn, "WearMask", x=600, y=-60)
    lib.connect(wear_m, "", out_wear, "")

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
    elif sorted(outputs) != ["CrackMask", "WearMask"]:
        result["error"] = f"outputs are {outputs}, want CrackMask+WearMask"
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
