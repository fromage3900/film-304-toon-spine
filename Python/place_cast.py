# Place the cast in L_Film_Office, spaced in a line beside Dana.
# Each mesh asset already carries its own material slots (the intake lane's
# MI_OneDriveRigs_<Rig>_* set), so placement is: spawn, aim, floor-snap, verify.

import unreal

CAST = [
    ("Film_Cast_David",  "/Game/Staging/CastRigs_20261016/David/David_v151_Deform_v3",  110.0),
    ("Film_Cast_Sam",    "/Game/Staging/CastRigs_20261016/Sam/Sam_Deform_v3",           -110.0),
    ("Film_Cast_Spider", "/Game/Staging/CastRigs_20261016/Spider/Spider_Deform_v2",     -240.0),
]
DANA = "Film_Subject_Dana"
YAW = 90.0
Y = -63.10


def log(m):
    unreal.log("[CastPlace] " + str(m))


def prop(o, n):
    try:
        return o.get_editor_property(n)
    except Exception:                                        # noqa: BLE001
        return None


def find_by_label(prefix):
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if a.get_actor_label().startswith(prefix):
            return a
    return None


def main():
    danaref = find_by_label(DANA)
    dana_loc = danaref.get_actor_location() if danaref else unreal.Vector(5.44, -63.10, -0.66)
    log("dana at %s" % [round(dana_loc.x, 1), round(dana_loc.y, 1), round(dana_loc.z, 1)])

    made = []
    for label, mesh_path, x in CAST:
        if find_by_label(label):
            log("%s already present, skipping" % label)
            made.append(label)
            continue
        mesh = unreal.load_asset(mesh_path)
        if mesh is None:
            log("MISSING MESH " + mesh_path)
            continue
        loc = unreal.Vector(dana_loc.x + x, Y, dana_loc.z)
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.SkeletalMeshActor, loc, unreal.Rotator(0, YAW, 0))
        if actor is None:
            log("spawn failed for " + label)
            continue
        actor.set_actor_label(label)
        comp = actor.get_component_by_class(unreal.SkeletalMeshComponent)
        if comp is None:
            log("no skeletal component on " + label)
            continue
        comp.set_editor_property("skeletal_mesh_asset", mesh)
        # keep Dana's authored scale so nobody renders at the wrong size
        if danaref:
            actor.set_actor_scale3d(danaref.get_actor_scale3d())
        actor.set_folder_path("FilmCast")
        made.append(label)
        log("placed %s at %s" % (label, [round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)]))

    # verify: read back what is actually in the level
    report = []
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        lbl = a.get_actor_label()
        if lbl.startswith("Film_Cast_") or lbl.startswith(DANA):
            comp = a.get_component_by_class(unreal.SkeletalMeshComponent)
            mesh = prop(comp, "skeletal_mesh_asset") if comp else None
            m = prop(mesh, "materials") or []
            report.append({
                "label": lbl,
                "loc": [round(v, 1) for v in (a.get_actor_location().x,
                                              a.get_actor_location().y,
                                              a.get_actor_location().z)],
                "mesh": str(mesh).split(".")[-1] if mesh else "NONE",
                "slots": len(m),
                "slot0": (str(prop(m[0], "material_interface")).split(".")[-2]
                          if m else "NONE"),
            })
    log("verified: %s" % report)

    import json
    import os
    out = unreal.Paths.project_dir() + "Saved/Audit/MasterConvergence_20261017/cast_placement.json"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(report, f, indent=1)


main()
