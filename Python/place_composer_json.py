"""Place a Brutalist-composer cook (see Tools/houdini/brutalist_composer/cook_to_json.py) in the open level.

Run inside the editor:
    import place_composer_json as p
    p.place("G:/film-304-toon-spine/Saved/GoalEst/e1_points.json", origin=(0, 20000, 0), tag="EstablishingE1", yaw_sign=-1)

Houdini (x, y-up, z) metres -> UE (x, z, y) centimetres plus `origin`. Spawns one StaticMeshActor per point,
tagged and labelled `EST_<tag>_<n>_<asset>`; re-running with the same tag first removes only its own actors.
Only spawns/removes actors it created (matching the tag). Saves nothing.
"""
import json
import unreal

EL = unreal.EditorLevelLibrary


def _load(path):
    if not path:
        return None
    return unreal.load_asset(path.split(".")[0]) or unreal.load_asset(path)


def clear(tag):
    n = 0
    for a in EL.get_all_level_actors():
        if tag in [str(t) for t in a.tags] and a.get_actor_label().startswith("EST_"):
            a.destroy_actor()
            n += 1
    return n


def place(json_path, origin=(0, 20000, 0), tag="Establishing", yaw_sign=-1, yaw_offset=0.0):
    data = json.load(open(json_path))
    clear(tag)
    placed, missing = [], []
    for i, pt in enumerate(data["points"]):
        mesh = _load(pt.get("unreal_instance"))
        if mesh is None:
            missing.append(pt.get("unreal_instance"))
            continue
        x, y_up, z = pt["p"]
        loc = unreal.Vector(origin[0] + x * 100.0, origin[1] + z * 100.0, origin[2] + y_up * 100.0)
        rot_y = (pt.get("rot") or [0, 0, 0])[1]
        rot = unreal.Rotator(roll=0, pitch=0, yaw=yaw_sign * rot_y + yaw_offset)
        sc = pt.get("scale") or [1, 1, 1]
        name = pt.get("asset_name") or mesh.get_name()
        a = EL.spawn_actor_from_class(unreal.StaticMeshActor, loc, rot)
        a.set_actor_label(f"EST_{tag}_{i:02d}_{name}")
        a.static_mesh_component.set_static_mesh(mesh)
        a.set_actor_scale3d(unreal.Vector(sc[0], sc[2], sc[1]))
        a.tags = [tag]
        # materials: multi-slot meshes carry _0/_1, single-slot carry unreal_material_instance
        mats = []
        for slot in range(len(a.static_mesh_component.get_materials())):
            key = f"unreal_material_instance_{slot}" if slot < 2 else None
            path = pt.get(key) or pt.get(f"unreal_material_{slot}") or pt.get("unreal_material_instance") or pt.get("unreal_material")
            mi = _load(path)
            if mi:
                a.static_mesh_component.set_material(slot, mi)
                mats.append(mi.get_name())
        placed.append((a.get_actor_label(), [round(v) for v in (loc.x, loc.y, loc.z)], mats))
    return placed, missing
