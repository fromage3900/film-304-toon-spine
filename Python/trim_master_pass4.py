# Pass 4: iterate the orphan unwind until the trimmed master compiles clean.
# Only deletes nodes whose REQUIRED input is unconnected on node types that
# cannot legally have it missing (StaticSwitchParameter.A, ComponentMask.Input,
# TextureSample.Texture). Loops because each round of deletions exposes another.

import json
import os
import unreal

MAT = "/Game/Materials/Masters/Film/M_Film_Toon_Universal_Trimmed"
AUDIT = unreal.Paths.project_dir() + "Saved/Audit/MasterConvergence_20261017/"
MAX_ROUNDS = 12


def log(m):
    unreal.log("[MasterTrim4] " + str(m))


def prop(obj, name):
    try:
        return obj.get_editor_property(name)
    except Exception:                                        # noqa: BLE001
        return None


def is_broken(e, lib, mat):
    """Return a reason string when this node cannot legally compile, else None."""
    cls = e.get_class().get_name()
    try:
        inputs = lib.get_inputs_for_material_expression(mat, e) or []
    except Exception:                                        # noqa: BLE001
        inputs = []
    connected = []
    for i in inputs:
        src = getattr(i, "input", None)
        connected.append(src is not None and str(src) not in ("()", "None", ""))

    if cls == "MaterialExpressionStaticSwitchParameter" and connected and not connected[0]:
        return "StaticSwitchParameter.A unconnected"
    if cls == "MaterialExpressionComponentMask" and connected and not connected[0]:
        return "ComponentMask.Input unconnected"
    if cls.startswith("MaterialExpressionTextureSample") and "Parameter" not in cls:
        if prop(e, "texture") is None:
            return "TextureSample.Texture null"
    return None


def main():
    lib = unreal.MaterialEditingLibrary
    mat = unreal.load_asset(MAT)
    if mat is None:
        raise RuntimeError("cannot load " + MAT)

    rounds = []
    for r in range(MAX_ROUNDS):
        doomed = []
        for e in lib.get_material_expressions(mat):
            why = is_broken(e, lib, mat)
            if why:
                doomed.append((e, why))
        if not doomed:
            rounds.append({"round": r, "deleted": 0, "note": "clean"})
            break
        deleted, failed = [], []
        for e, why in doomed:
            try:
                lib.delete_material_expression(mat, e)
                deleted.append(why)
            except Exception as exc:                         # noqa: BLE001
                failed.append("%s: %s" % (why, exc))
        try:
            lib.delete_unused_expressions(mat)
        except Exception as exc:                             # noqa: BLE001
            log("sweep failed: %s" % exc)
        try:
            lib.recompile_material(mat)
        except Exception as exc:                             # noqa: BLE001
            log("recompile failed: %s" % exc)
        n = lib.get_num_material_expressions(mat)
        rounds.append({"round": r, "deleted": len(deleted), "failed": failed,
                       "expressions": n, "reasons": sorted(set(deleted))})
        log("round %d deleted=%d -> %d expressions" % (r, len(deleted), n))

    try:
        lib.recompile_material(mat)
    except Exception as exc:                                 # noqa: BLE001
        log("final recompile failed: %s" % exc)

    n = lib.get_num_material_expressions(mat)
    record = {"pass": 4, "asset": MAT, "expressions_final": n, "rounds": rounds}
    with open(AUDIT + "trim_pass4_iterate.json", "w") as f:
        json.dump(record, f, indent=1)
    log("wrote trim_pass4_iterate.json; final=%d expressions" % n)


main()
