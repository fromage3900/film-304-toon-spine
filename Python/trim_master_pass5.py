# Pass 5: delete the Melodia CONTENT function calls from the trimmed master.
# MF_Madoka / MF_Itto / MF_MeshBlend_Activator are Melodia-specific. The call
# NODES are deleted here; the shared function ASSETS are not touched, because
# other materials still reference them.
# MF_NormalAdjust, MF_ColorRamp3 and MF_NikkiDreamGrade are general capability
# and stay.

import json
import os
import unreal

MAT = "/Game/Materials/Masters/Film/M_Film_Toon_Universal_Trimmed"
AUDIT = unreal.Paths.project_dir() + "Saved/Audit/MasterConvergence_20261017/"
DROP_FUNCTIONS = ("MF_Madoka", "MF_Itto", "MF_MeshBlend_Activator")


def log(m):
    unreal.log("[MasterTrim5] " + str(m))


def prop(o, n):
    try:
        return o.get_editor_property(n)
    except Exception:                                        # noqa: BLE001
        return None


def main():
    lib = unreal.MaterialEditingLibrary
    mat = unreal.load_asset(MAT)
    if mat is None:
        raise RuntimeError("cannot load " + MAT)

    n0 = lib.get_num_material_expressions(mat)
    deleted, failed = [], []
    for e in list(lib.get_material_expressions(mat)):
        if "FunctionCall" not in e.get_class().get_name():
            continue
        fn = prop(e, "material_function")
        path = str(fn.get_path_name()) if fn else ""
        if any(d in path for d in DROP_FUNCTIONS):
            try:
                lib.delete_material_expression(mat, e)
                deleted.append(path.split("/")[-1])
            except Exception as exc:                         # noqa: BLE001
                failed.append("%s: %s" % (path, exc))

    sweep = "n/a"
    try:
        lib.delete_unused_expressions(mat)
        sweep = "swept to %d" % lib.get_num_material_expressions(mat)
    except Exception as exc:                                 # noqa: BLE001
        sweep = "sweep failed: %s" % exc
    try:
        lib.recompile_material(mat)
    except Exception as exc:                                 # noqa: BLE001
        log("recompile failed: %s" % exc)

    n1 = lib.get_num_material_expressions(mat)
    record = {"pass": 5, "asset": MAT, "expressions_before": n0,
              "expressions_after": n1, "deleted_calls": deleted,
              "failures": failed, "sweep": sweep}
    with open(AUDIT + "trim_pass5_functions.json", "w") as f:
        json.dump(record, f, indent=1)
    log("before=%d after=%d deleted=%s failures=%d sweep=%s" % (
        n0, n1, deleted, failed, sweep))


main()
