"""Build MF_Impasto - directional painterly impasto relief (film utility).

CONVERGED FROM MELODIA, FILM-REFINED. Source lane:
MF_Impressionist_Impasto ("Impasto height from stroke mask") plus the
Impressionist brush-stroke field's actual maths
(BS_GodFile setup_material_functions._build_brush_stroke:
field = |sin(worldXY * BrushScale)| * StrokeStrength). The source asset
exists here only as a non-resolving intake drop binary, so the lane is
rebuilt as a film utility under a film-clear name (the task's "impasto").
The Melodia Impressionist family siblings (BrushStroke / InkPool /
Temporal) are family content, not this lane: they stay out of the film
spine like the rest of the speculative Melodia library.

READ (one Custom HLSL node)
---------------------------
p     = rotate(WorldXY, StrokeAngle)          # projector-graded axis
field = |sin(p.x * BrushScale)|               # directional stroke stripes
mask  = saturate(field * StrokeStrength)
height= mask * ImpastoStrength * ImpastoHeight
return float3(mask, height, mask*height)      # r=StrokeMask, g=Height

Master wiring: WorldPositionOffset ADD of (Height * VertexNormal).
Defaults keep every existing instance pixel-identical, by the gate,
not by muting the dials:

  * ImpastoStrength 0 (the master's gate) -> height 0, stroke field live
    but inert until opted in.
  * StrokeStrength 0.55 / BrushScale 0.045 / StrokeAngle 0 - the source's
    useful brush defaults, actually USED here instead of parked.
  * BrushScale 0.02..0.09 is the useful range (period 2*pi/scale in cm:
    0.045 gives ~140 cm strokes, 0.09 gives ~70 cm).

Outputs:
    StrokeMask         float1  gated field for future colour use
    ImpastoHeightField float1  WPO-ready relief amount (0 by default)
"""
from __future__ import annotations

import unreal

import spine_lib as lib

NAME = "MF_Impasto"

SCALAR = unreal.FunctionInputType.FUNCTION_INPUT_SCALAR
VECTOR3 = unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3

FLOAT3 = unreal.CustomMaterialOutputType.CMOT_FLOAT3

CODE = """float rad = radians(StrokeAngle);
float cs = cos(rad);
float sn = sin(rad);
float2 p = float2(dot(WorldXY.xy, float2(cs, sn)),
                  dot(WorldXY.xy, float2(-sn, cs)));
float ridge = abs(sin(p.x * max(BrushScale, 1e-5)));
float mask = saturate(ridge * max(StrokeStrength, 0.0));
float height = mask * max(ImpastoStrength, 0.0) * ImpastoHeight;
return float3(mask, height, mask * height);"""

CUSTOM_INPUTS = ["WorldXY", "BrushScale", "StrokeStrength", "StrokeAngle",
                 "ImpastoStrength", "ImpastoHeight"]

FUNCTION_INPUTS = [
    ("BrushScale", SCALAR, 0.045),
    ("StrokeStrength", SCALAR, 0.55),
    ("StrokeAngle", SCALAR, 0.0),
    ("ImpastoStrength", SCALAR, 0.0),
    ("ImpastoHeight", SCALAR, 0.025),
]


def build(rebuild=True):
    lib.log(f"=== {NAME} ===")
    fn = lib.get_or_create_function(NAME, rebuild=rebuild)

    ins = {}
    y = -500
    for iname, itype, preview in FUNCTION_INPUTS:
        ins[iname] = lib.add_function_input(fn, iname, itype,
                                            preview=(preview, 0, 0, 0),
                                            x=-1300, y=y)
        y += 150

    wp = lib.expr(fn, unreal.MaterialExpressionWorldPosition, -1300, 1400)

    c = lib.custom_node(
        fn, CODE, FLOAT3,
        inputs=CUSTOM_INPUTS, x=-250, y=-100,
        description="Impasto: directional stroke relief (WPO-ready)")
    lib._desc(c, "Impressionist impasto lane, film-generated")

    lib.connect(wp, "", c, "WorldXY")
    for iname in ("BrushScale", "StrokeStrength", "StrokeAngle",
                  "ImpastoStrength", "ImpastoHeight"):
        lib.connect(ins[iname], "", c, iname)

    mask_m = lib.expr(fn, unreal.MaterialExpressionComponentMask, 250, -260)
    mask_m.set_editor_property("r", True)
    mask_m.set_editor_property("g", False)
    mask_m.set_editor_property("b", False)
    mask_m.set_editor_property("a", False)
    lib.connect(c, "", mask_m, ["", "None"])

    height_m = lib.expr(fn, unreal.MaterialExpressionComponentMask, 250, -60)
    height_m.set_editor_property("r", False)
    height_m.set_editor_property("g", True)
    height_m.set_editor_property("b", False)
    height_m.set_editor_property("a", False)
    lib.connect(c, "", height_m, ["", "None"])

    out_mask = lib.add_function_output(fn, "StrokeMask", x=650, y=-260)
    lib.connect(mask_m, "", out_mask, "")
    out_h = lib.add_function_output(fn, "ImpastoHeightField", x=650, y=-60)
    lib.connect(height_m, "", out_h, "")

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
    elif sorted(outputs) != ["ImpastoHeightField", "StrokeMask"]:
        result["error"] = (f"outputs are {outputs}, want "
                           f"ImpastoHeightField+StrokeMask")
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
