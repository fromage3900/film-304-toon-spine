"""Pure planning for Houdini cook JSON -> HISM batches. No `unreal` import.

place_composer_json.py spawns one StaticMeshActor per point. That is why the
office level carried 154 StaticMeshActors and 113 un-foldered actors. The same
transforms can be carried by one HISM per (mesh, material-set) group.

Grouping is by MATERIAL SET as well as mesh, not optional: the toon master does
not read per-instance custom data, so two points that need different material
instances cannot share a component.

Units/axes follow the proven converter: Houdini is metres, Y-up; Unreal is
centimetres, Z-up; (x, y, z)_houdini -> (x, z, y)_unreal * 100 + origin, and the
yaw sign is flipped for the handedness change.
"""
from __future__ import annotations


def normalize_mesh_path(path):
    if not path:
        return None
    # Object paths arrive as /Game/Pkg/Asset.Asset; the package is what loads.
    return path.split(".")[0]


def material_slots(point):
    """Resolve the material set the same way place_composer_json.py does."""
    out = []
    for slot in range(2):
        path = (point.get("unreal_material_instance_%d" % slot)
                or point.get("unreal_material_%d" % slot)
                or point.get("unreal_material_instance")
                or point.get("unreal_material"))
        out.append(normalize_mesh_path(path))
    return tuple(out)


def to_unreal(point, origin=(0.0, 20000.0, 0.0), yaw_sign=-1.0, yaw_offset=0.0):
    x, y_up, z = point["p"]
    rot = point.get("rot") or [0.0, 0.0, 0.0]
    sc = point.get("scale") or [1.0, 1.0, 1.0]
    return {
        "loc": [origin[0] + x * 100.0,
                origin[1] + z * 100.0,
                origin[2] + y_up * 100.0],
        "yaw": yaw_sign * float(rot[1]) + yaw_offset,
        "scale": [sc[0], sc[2], sc[1]],
    }


def plan(data, origin=(0.0, 20000.0, 0.0), yaw_sign=-1.0, yaw_offset=0.0):
    groups = {}
    missing = []
    for i, point in enumerate(data.get("points", [])):
        mesh = normalize_mesh_path(point.get("unreal_instance"))
        if not mesh:
            missing.append({"index": i, "reason": "no unreal_instance"})
            continue
        key = (mesh, material_slots(point))
        groups.setdefault(key, []).append(
            dict(index=i, **to_unreal(point, origin, yaw_sign, yaw_offset)))

    out = []
    for (mesh, mats), items in groups.items():
        out.append({"mesh": mesh, "materials": list(mats),
                    "count": len(items), "instances": items})
    out.sort(key=lambda g: -g["count"])
    return {"groups": out, "missing": missing,
            "points": sum(g["count"] for g in out)}


def summarise(result):
    rows = [{"mesh": g["mesh"].split("/")[-1], "materials": g["materials"],
             "count": g["count"]} for g in result["groups"]]
    return {"groups": len(rows), "points": result["points"],
            "missing": len(result["missing"]), "largest": rows[:12]}
