"""Build MF_DF_ContactBlend - distance-field ground-contact blend mask.

CONVERGED FROM MELODIA. Source: BS_GodFile Content/Python/
build_distance_field_material_spike.py `_build_function()`, recovered
read-only and rebuilt node-for-node in itself (this package already carried
a non-resolving intake drop binary of the same name; it is wiped and
regenerated in place, so the trackable package name is the same the
convergence doc lists).

READ
----
pos = WorldPos + (0,0,-WorldPositionOffset)
df  = |DistanceToNearestSurface(pos)|          (engine node, world scale)
m0  = saturate(1 - df / BlendDistance) ^ BlendSharpness
m1  = lerp(m0, m0 * sat(noise(pos * NoiseScale)), NoiseBreakup)
h   = saturate(1 - |WorldPos.z - GroundHeight| / HeightFalloff)
out = m1 * h * DistanceFieldBlendActive * BlendStrength

The height term stops the blend climbing a whole prop; the DF term stops a
horizontal band on geometry that is not actually near another surface -
same two-source logic as the source builder's comment.

Mask output only. The master decides where the mask lands (colour tint /
roughness), gated by its own BlendStrength knob = 0 default.

Input defaults are the source's function-input previews so an unwired call
behaves exactly as the source asset did.
"""
from __future__ import annotations

import unreal

import spine_lib as lib

NAME = "MF_DF_ContactBlend"

SCALAR = unreal.FunctionInputType.FUNCTION_INPUT_SCALAR

# (input_name, default) - type + preview per add_function_input
FUNCTION_INPUTS = [
    ("WorldPositionOffset", 0.0),
    ("BlendDistance", 18.0),
    ("BlendSharpness", 3.0),
    ("NoiseScale", 0.015),
    ("NoiseBreakup", 0.0),
    ("GroundHeight", 0.0),
    ("HeightFalloff", 28.0),
    ("DistanceFieldBlendActive", 1.0),
    ("BlendStrength", 1.0),
]


def build(rebuild=True):
    lib.log(f"=== {NAME} ===")
    fn = lib.get_or_create_function(NAME, rebuild=rebuild)

    ins = {}
    y = -900
    for iname, default in FUNCTION_INPUTS:
        ins[iname] = lib.add_function_input(
            fn, iname, SCALAR, preview=(default, 0, 0, 0), x=-1500, y=y)
        y += 150

    wp = lib.expr(fn, unreal.MaterialExpressionWorldPosition, -1500, 1400)

    # pos = WorldPos + (0,0,-WorldPositionOffset)
    down = lib.constant(fn, (0.0, 0.0, -1.0), -1300, 1600)
    off_vec = lib.expr(fn, unreal.MaterialExpressionMultiply, -1140, 1550)
    lib.binary(down, ins["WorldPositionOffset"], off_vec)
    pos = lib.expr(fn, unreal.MaterialExpressionAdd, -980, 1400)
    lib.binary(wp, off_vec, pos)

    # df = |DistanceToNearestSurface(pos)|
    dtn = lib.expr(fn, unreal.MaterialExpressionDistanceToNearestSurface,
                   -820, 1400)
    lib.connect(pos, "", dtn, "Position")
    dabs = lib.expr(fn, unreal.MaterialExpressionAbs, -660, 1400)
    lib.unary(dtn, dabs)

    # m0 = saturate(1 - df/BlendDistance) ^ BlendSharpness
    prox = lib.expr(fn, unreal.MaterialExpressionDivide, -500, 1400)
    lib.binary(dabs, ins["BlendDistance"], prox)
    inv = lib.expr(fn, unreal.MaterialExpressionOneMinus, -340, 1400)
    lib.unary(prox, inv)
    sat1 = lib.expr(fn, unreal.MaterialExpressionSaturate, -180, 1400)
    lib.unary(inv, sat1)
    pw = lib.expr(fn, unreal.MaterialExpressionPower, -20, 1400)
    lib.binary(sat1, ins["BlendSharpness"], pw)

    # noise breakup branch: lerp(m0, m0 * sat(noise), NoiseBreakup)
    n_pos = lib.expr(fn, unreal.MaterialExpressionMultiply, -340, 1700)
    lib.binary(pos, ins["NoiseScale"], n_pos)
    noise = lib.expr(fn, unreal.MaterialExpressionNoise, -180, 1700)
    lib.connect(n_pos, "", noise, "Position")
    noise_sat = lib.expr(fn, unreal.MaterialExpressionSaturate, -20, 1700)
    lib.unary(noise, noise_sat)
    n_mask = lib.expr(fn, unreal.MaterialExpressionMultiply, 140, 1400)
    lib.binary(pw, noise_sat, n_mask)
    broken = lib.expr(fn, unreal.MaterialExpressionLinearInterpolate, 300, 1400)
    lib.binary(pw, n_mask, broken)
    lib.connect(ins["NoiseBreakup"], "", broken, "Alpha")

    # height envelope: saturate(1 - |z - GroundHeight| / HeightFalloff)
    h_z = lib.expr(fn, unreal.MaterialExpressionComponentMask, -660, 1900)
    h_z.set_editor_property("r", False)
    h_z.set_editor_property("g", False)
    h_z.set_editor_property("b", True)
    h_z.set_editor_property("a", False)
    lib.connect(wp, "", h_z, ["Input", ""])
    h_delta = lib.expr(fn, unreal.MaterialExpressionSubtract, -500, 1900)
    lib.binary(h_z, ins["GroundHeight"], h_delta)
    h_abs = lib.expr(fn, unreal.MaterialExpressionAbs, -340, 1900)
    lib.unary(h_delta, h_abs)
    h_div = lib.expr(fn, unreal.MaterialExpressionDivide, -180, 1900)
    lib.binary(h_abs, ins["HeightFalloff"], h_div)
    h_inv = lib.expr(fn, unreal.MaterialExpressionOneMinus, -20, 1900)
    lib.unary(h_div, h_inv)
    h_sat = lib.expr(fn, unreal.MaterialExpressionSaturate, 140, 1900)
    lib.unary(h_inv, h_sat)

    # out = broken * h * active * strength
    combined = lib.expr(fn, unreal.MaterialExpressionMultiply, 460, 1500)
    lib.binary(broken, h_sat, combined)
    active_m = lib.expr(fn, unreal.MaterialExpressionMultiply, 620, 1400)
    lib.binary(combined, ins["DistanceFieldBlendActive"], active_m)
    result = lib.expr(fn, unreal.MaterialExpressionMultiply, 780, 1400)
    lib.binary(active_m, ins["BlendStrength"], result)

    out = lib.add_function_output(fn, "Result", x=1100, y=1400)
    lib.connect(result, "", out, "")

    lib.save(fn)
    lib.log(f"{NAME} built with {lib.function_expression_count(fn)} expressions")
    return fn


def verify():
    """Structural check + the recovered contract's key facts: world/DF nodes
    present and every one of the nine function inputs reaches the Custom
    chain (an unwired BlendDistance would otherwise read its preview and
    compile clean)."""
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

    if "MaterialExpressionDistanceToNearestSurface" not in kinds:
        result["error"] = "DistanceToNearestSurface node is gone"
    elif "Result" not in outputs:
        result["error"] = f"missing function output 'Result' (have {outputs})"
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
