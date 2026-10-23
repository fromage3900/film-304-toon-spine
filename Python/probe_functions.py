# Probe: which Material Functions does the trimmed master call, and do those
# functions own the broken ComponentMask / StaticSwitchParameter nodes?
import unreal

MAT = "/Game/Materials/Masters/Film/M_Film_Toon_Universal_Trimmed"
lib = unreal.MaterialEditingLibrary
mat = unreal.load_asset(MAT)


def log(m):
    unreal.log("[TrimProbe5] " + str(m))


def prop(o, n):
    try:
        return o.get_editor_property(n)
    except Exception:                                        # noqa: BLE001
        return None


calls = {}
for e in lib.get_material_expressions(mat):
    cls = e.get_class().get_name()
    if "FunctionCall" in cls:
        fn = prop(e, "material_function")
        try:
            path = str(fn.get_path_name()) if fn else "None"
        except Exception:                                    # noqa: BLE001
            path = "unreadable"
        calls[path] = calls.get(path, 0) + 1
log("function calls: %s" % calls)

# inspect each referenced function for broken nodes
for path in calls:
    if path in ("None", "unreadable"):
        continue
    fn = unreal.load_asset(path)
    if fn is None:
        log("cannot load function " + path)
        continue
    broken = {"StaticSwitchParameter": 0, "ComponentMask": 0}
    try:
        fexprs = lib.get_material_function_expressions(fn)
    except Exception as exc:                                 # noqa: BLE001
        log("%s expressions ERR %s" % (path, exc))
        continue
    for fe in (fexprs or []):
        c = fe.get_class().get_name()
        if c in broken:
            try:
                inputs = lib.get_inputs_for_material_expression(fe) or []
                if not inputs:
                    broken[c] += 1
            except Exception:                                # noqa: BLE001
                broken[c] += 1
    log("%s -> %d expressions, broken-by-empty-inputs %s" % (
        path.split("/")[-1], len(fexprs or []), broken))
