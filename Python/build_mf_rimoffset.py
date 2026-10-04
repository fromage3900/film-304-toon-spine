"""Build MF_RimOffset - the offset rim-light tool, as a reusable material function.

WHY THIS EXISTS
---------------
`Docs/FILM_PIPELINE.md` §7 recommends testing the Spice Frontier route on one
shot: characters that are UNLIT and shadowless, separated from a painterly
backdrop by an adjustable edge of light. Epic's own spotlight on that show
describes the characters as *"forgoing lighting and removing shadow and detail
to maintain a 2D style"*, and names the mechanism: *"A custom-built offset
rimlight tool enabled the artists to produce an edge of light around the
character's silhouette."*

That tool is the one piece of that pipeline worth owning, and it is a function,
not a material - which is why it lives here rather than inside a single master.
Every character, prop and architecture asset calls the same term with its own
width and colour, and an artist adjusts it live in the viewport, which was the
show's own stated advantage: *"You can look in the viewport and go, 'oh, could we
tweak this a little bit?'"*

WHAT "OFFSET" ACTUALLY MEANS, AND WHAT THIS IS
---------------------------------------------
The production tool offsets a shell of geometry and lights it independently, so
the edge of light sits on ONE side and does not move when the scene lights move.
That is a screen/silhouette-space effect.

A material function cannot sample a shifted silhouette. So this reproduces the
READ rather than the mechanism: the normal is biased by `OffsetDir` before the
view dot product, which pushes the rim onto one side of the form. Same look, no
extra geometry, no second draw call.

Stated here rather than left for an artist to discover: if a shot ever needs the
real thing, that is `UE_CelLit`-class work and it wants a post pass, not a
function - see `Docs/FILM_PIPELINE.md` §6.

DELIBERATELY NO BaseColor INPUT
-------------------------------
The rim is ADDITIVE. A caller feeds the result to EmissiveColor, never to
Surface, or it erases the shading underneath. Accepting a BaseColor input here
would invite exactly that wiring, so it is not offered.

Inputs : Normal, RimColor, OffsetDir, OffsetStrength,
         RimStart, RimEnd, Sharpness, RimStrength
Outputs: RimEmissive (vec3, additive -> EmissiveColor)
         RimMask    (scalar 0-1, for masking or debug visualisation)
"""
from __future__ import annotations

import unreal

import spine_lib as lib

NAME = "MF_RimOffset"

SCALAR = unreal.FunctionInputType.FUNCTION_INPUT_SCALAR
VECTOR = unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3


def build(rebuild=True):
    lib.log(f"=== {NAME} ===")
    fn = lib.get_or_create_function(NAME, rebuild=rebuild)

    ins = {}
    y = -400
    for iname, itype, default in [
        ("Normal", VECTOR, (0.0, 0.0, 1.0, 0.0)),
        ("RimColor", VECTOR, (1.0, 0.96, 0.90, 1.0)),
        # Fixed in VIEW space: where the edge of light comes from.
        # (0,0,1) faces the camera - a centred rim. (1,0,0) pushes it to the
        # character's right. This is the control that makes it an "offset" rim
        # rather than a Fresnel, and it never moves with the scene lights.
        ("OffsetDir", VECTOR, (0.35, 0.0, 0.94, 0.0)),
        ("OffsetStrength", SCALAR, 0.60),
        ("RimStart", SCALAR, 0.55),
        ("RimEnd", SCALAR, 0.92),
        ("Sharpness", SCALAR, 2.20),
        ("RimStrength", SCALAR, 1.00),
    ]:
        ins[iname] = lib.add_function_input(fn, iname, itype,
                                            preview=default, x=-1100, y=y)
        y += 170

    # --- bias the normal so the rim lands on ONE side (the "offset") ---
    offset_scaled = lib.expr(fn, unreal.MaterialExpressionMultiply, -800, 250)
    lib.binary(ins["OffsetDir"], ins["OffsetStrength"], offset_scaled)

    biased = lib.expr(fn, unreal.MaterialExpressionAdd, -640, 180)
    lib.binary(ins["Normal"], offset_scaled, biased)

    normalised = lib.expr(fn, unreal.MaterialExpressionNormalize, -500, 180)
    lib.unary(biased, normalised)

    # --- facing term: 1 - saturate(dot(N, V)) ---
    view = lib.expr(fn, unreal.MaterialExpressionCameraVectorWS, -800, 480)
    dot = lib.expr(fn, unreal.MaterialExpressionDotProduct, -340, 300)
    lib.binary(normalised, view, dot)

    sat = lib.expr(fn, unreal.MaterialExpressionSaturate, -200, 300)
    lib.unary(dot, sat)

    facing = lib.expr(fn, unreal.MaterialExpressionOneMinus, -60, 300)
    lib.unary(sat, facing)

    # --- shape the edge: remap RimStart..RimEnd onto 0..1 ---
    minus_start = lib.expr(fn, unreal.MaterialExpressionSubtract, 90, 300)
    lib.binary(facing, ins["RimStart"], minus_start)

    span = lib.expr(fn, unreal.MaterialExpressionSubtract, -60, 500)
    lib.binary(ins["RimEnd"], ins["RimStart"], span)

    # Guard the divide. RimEnd == RimStart is a one-click accident and would put
    # inf/NaN through Power and then through the surface colour.
    span_floor = lib.scalar_const(fn, 0.0001, -220, 560)
    span_safe = lib.expr(fn, unreal.MaterialExpressionMax, 90, 500)
    lib.binary(span, span_floor, span_safe)

    remapped = lib.expr(fn, unreal.MaterialExpressionDivide, 240, 400)
    lib.binary(minus_start, span_safe, remapped)

    remap_sat = lib.expr(fn, unreal.MaterialExpressionSaturate, 380, 400)
    lib.unary(remapped, remap_sat)

    # --- tighten ---
    sharp = lib.expr(fn, unreal.MaterialExpressionPower, 520, 400)
    lib.binary(remap_sat, ins["Sharpness"], sharp)

    # --- strength, then colour ---
    scaled = lib.expr(fn, unreal.MaterialExpressionMultiply, 660, 400)
    lib.binary(sharp, ins["RimStrength"], scaled)

    coloured = lib.expr(fn, unreal.MaterialExpressionMultiply, 800, 300)
    lib.binary(scaled, ins["RimColor"], coloured)

    out_emissive = lib.add_function_output(fn, "RimEmissive", x=980, y=300)
    lib.connect(coloured, "", out_emissive, "")
    out_mask = lib.add_function_output(fn, "RimMask", x=980, y=480)
    lib.connect(scaled, "", out_mask, "")

    lib.save(fn)
    lib.log(f"{NAME} built with {lib.function_expression_count(fn)} expressions")
    return fn


def verify():
    """Structural check PLUS the two things it cannot see.

    `lib.verify_function_graph` already runs in build_spine and catches dead
    nodes, unwired outputs and unused inputs. What it cannot catch is a
    RENAMED output: that is a breaking change for every material that calls it,
    and it surfaces as an empty slot in a master rather than as an error.

    The span guard gets the same treatment - `Max` present, because losing it
    reintroduces a divide-by-zero that looks like nothing until a shot NaNs.
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

    missing = [o for o in ("RimEmissive", "RimMask") if o not in outputs]
    if missing:
        result["error"] = f"missing function outputs: {missing}"
    elif "MaterialExpressionMax" not in kinds:
        result["error"] = ("span guard (Max) is gone - RimEnd == RimStart would "
                           "divide by zero and NaN the surface")
    else:
        graph = lib.verify_function_graph(NAME, max_dead=0)
        result["graph"] = graph
        if not graph.get("ok"):
            result["error"] = graph.get("error", "graph verify failed")
        else:
            result["ok"] = True

    lib.log(f"VERIFY {NAME}: ok={result['ok']} {result['error'] or ''}")
    return result