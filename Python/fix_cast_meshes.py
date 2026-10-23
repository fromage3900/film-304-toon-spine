# Assign meshes to any Film_Cast_* actor whose mesh is missing (a previous
# run could spawn and label the actor before failing on the property name).

import unreal

CAST = {
    "Film_Cast_David":  "/Game/Staging/CastRigs_20261016/David/David_v151_Deform_v3",
    "Film_Cast_Sam":    "/Game/Staging/CastRigs_20261016/Sam/Sam_Deform_v3",
    "Film_Cast_Spider": "/Game/Staging/CastRigs_20261016/Spider/Spider_Deform_v2",
}


def log(m):
    unreal.log("[CastFix] " + str(m))


def prop(o, n):
    try:
        return o.get_editor_property(n)
    except Exception:                                        # noqa: BLE001
        return None


for a in unreal.EditorLevelLibrary.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl not in CAST:
        continue
    comp = a.get_component_by_class(unreal.SkeletalMeshComponent)
    if comp is None:
        log(lbl + " has no skeletal component")
        continue
    if prop(comp, "skeletal_mesh_asset") is not None:
        log(lbl + " already has a mesh")
        continue
    mesh = unreal.load_asset(CAST[lbl])
    if mesh is None:
        log("MISSING " + CAST[lbl])
        continue
    comp.set_editor_property("skeletal_mesh_asset", mesh)
    a.set_folder_path("FilmCast")
    m = prop(mesh, "materials") or []
    log("%s -> %s (%d slots, slot0=%s)" % (
        lbl, CAST[lbl].split("/")[-1], len(m),
        str(prop(m[0], "material_interface")).split(".")[-2] if m else "NONE"))
