# Check: did any pass modify the SHARED material functions? Those are used by
# other materials, so an unintended edit there is a project-wide problem.

import unreal

FUNCS = [
    "/Game/Materials/MF_MeshBlend_Activator_Index_0",
    "/Game/EnvSandbox/Materials/Functions/MF_NormalAdjust",
    "/Game/EnvSandbox/Materials/Functions/MF_Madoka",
    "/Game/EnvSandbox/Materials/Functions/MF_Itto",
    "/Game/EnvSandbox/Materials/Functions/MF_NikkiDreamGrade",
    "/Game/EnvSandbox/Materials/Functions/MF_ColorRamp3",
]


def log(m):
    unreal.log("[FuncCheck] " + str(m))


dirty = []
log("dirty check via find_package().is_dirty()")

for p in FUNCS:
    exists = unreal.EditorAssetLibrary.does_asset_exist(p)
    pkg = unreal.find_package(p)
    is_dirty = bool(pkg is not None and pkg.is_dirty())
    lib = unreal.MaterialEditingLibrary
    n = None
    if exists:
        try:
            a = unreal.load_asset(p)
            n = len(lib.get_material_function_expressions(a) or [])
        except Exception as e:                               # noqa: BLE001
            n = "ERR %s" % e
    log("%s exists=%s dirty=%s expressions=%s" % (p.split("/")[-1], exists, is_dirty, n))
