# Probe: the real shape of expression inputs, so the broken-node test is correct.
import unreal

MAT = "/Game/Materials/Masters/Film/M_Film_Toon_Universal_Trimmed"
lib = unreal.MaterialEditingLibrary
mat = unreal.load_asset(MAT)


def log(m):
    unreal.log("[TrimProbe4] " + str(m))


shown = 0
for e in lib.get_material_expressions(mat):
    cls = e.get_class().get_name()
    if cls not in ("MaterialExpressionComponentMask", "MaterialExpressionStaticSwitchParameter"):
        continue
    try:
        inputs = lib.get_inputs_for_material_expression(e)
    except Exception as exc:                                 # noqa: BLE001
        log("%s inputs ERR %s" % (cls, exc))
        continue
    detail = []
    for i in (inputs or []):
        detail.append({
            "type": type(i).__name__,
            "name": str(getattr(i, "input_name", "")),
            "raw": str(i)[:150],
        })
    log("%s n_inputs=%d detail=%s" % (cls, len(inputs or []), str(detail)[:600]))
    shown += 1
    if shown >= 4:
        break
