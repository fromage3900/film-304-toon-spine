# Pass 3: clear the compile errors left by passes 1-2.
#  - TextureSample nodes whose Texture was a deleted parameter -> broken, delete.
#  - Custom HLSL nodes whose inputs were deleted parameters -> identify by their
#    own code/description first, log everything, delete only dropped-feature ones.
# Then sweep orphans, recompile, and report.

import json
import os
import unreal

MAT = "/Game/Materials/Masters/Film/M_Film_Toon_Universal_Trimmed"
AUDIT = unreal.Paths.project_dir() + "Saved/Audit/MasterConvergence_20261017/"
KEYS = ("chladni", "sigil", "madoka", "itto", "celestial", "fairy", "sparkle", "motif",
        "dawn", "mist", "glint", "snow", "moss", "gemstone", "gilding", "dfcontact",
        "contactrim", "witchbarrier", "constellation")


def log(m):
    unreal.log("[MasterTrim3] " + str(m))


def prop(obj, name):
    try:
        return obj.get_editor_property(name)
    except Exception:                                        # noqa: BLE001
        return None


def main():
    lib = unreal.MaterialEditingLibrary
    mat = unreal.load_asset(MAT)
    if mat is None:
        raise RuntimeError("cannot load " + MAT)

    broken_samples, custom_info, doomed = [], [], []
    for e in lib.get_material_expressions(mat):
        cls = e.get_class().get_name()
        if cls == "MaterialExpressionTextureSample":
            if prop(e, "texture") is None:
                broken_samples.append(e)
        elif cls == "MaterialExpressionCustom":
            code = str(prop(e, "code") or "")[:200]
            desc = str(prop(e, "description") or "")[:80]
            inputs = []
            for inp in (prop(e, "inputs") or []):
                nm = str(prop(inp, "input_name") or "")
                conn = prop(inp, "input")
                connected = conn is not None and str(conn) != "()"
                inputs.append((nm, connected))
            custom_info.append({"desc": desc, "code": code, "inputs": inputs})
            blob = (desc + " " + code).lower()
            unconnected = [nm for nm, c in inputs if not c]
            if any(k in blob for k in KEYS) or any(
                    nm in ("Scale", "Sides") for nm in unconnected):
                doomed.append(e)

    log("broken TextureSamples=%d" % len(broken_samples))
    for i, c in enumerate(custom_info):
        log("Custom[%d] desc=%r inputs=%s" % (i, c["desc"], c["inputs"]))

    deleted, failed = [], []
    for e in broken_samples:
        try:
            lib.delete_material_expression(mat, e)
            deleted.append("TextureSample(null)")
        except Exception as exc:                             # noqa: BLE001
            failed.append("TextureSample: %s" % exc)
    for e in doomed:
        try:
            lib.delete_material_expression(mat, e)
            deleted.append("Custom")
        except Exception as exc:                             # noqa: BLE001
            failed.append("Custom: %s" % exc)

    try:
        lib.delete_unused_expressions(mat)
    except Exception as exc:                                 # noqa: BLE001
        log("sweep failed: %s" % exc)
    try:
        lib.recompile_material(mat)
    except Exception as exc:                                 # noqa: BLE001
        log("recompile failed: %s" % exc)

    n1 = lib.get_num_material_expressions(mat)
    record = {"pass": 3, "asset": MAT, "expressions_after": n1,
              "deleted": deleted, "failures": failed, "custom_nodes": custom_info}
    with open(AUDIT + "trim_pass3_broken.json", "w") as f:
        json.dump(record, f, indent=1)
    log("after=%d expressions, deleted=%d, failures=%d" % (n1, len(deleted), len(failed)))


main()
