"""Place a Houdini cook as HISM batches (one actor per mesh+material group).

`apply=False` only plans and reports; nothing is spawned and the level is
untouched. Set apply=True to replace the tag's previous actors.

Why this exists: place_composer_json.py spawns one StaticMeshActor per point.
The office level already carries 154 StaticMeshActors and 113 un-foldered
actors. The group->HISM pattern is the one already proven in
Tools/houdini/stage_cinematic_cables.py.

Saves nothing.
"""
import json
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir()) / "Python"))
import hism_plan  # noqa: E402

EL = unreal.EditorLevelLibrary
OUT = Path(unreal.Paths.project_dir()) / "Saved/Audit/Stage"
OUT.mkdir(parents=True, exist_ok=True)


def clear(tag):
    n = 0
    for a in EL.get_all_level_actors():
        if tag in [str(t) for t in a.tags] and a.get_actor_label().startswith("EST_"):
            a.destroy_actor()
            n += 1
    return n


def place(json_path, origin=(0.0, 20000.0, 0.0), tag="Establishing",
          yaw_sign=-1.0, yaw_offset=0.0, apply=False, folder="Film304/07_Houdini_Baked"):
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    plan = hism_plan.plan(data, origin=origin, yaw_sign=yaw_sign, yaw_offset=yaw_offset)
    report = {"json": str(json_path), "tag": tag, "apply": apply,
              "summary": hism_plan.summarise(plan), "created": [], "errors": []}
    if not apply:
        report["planned"] = True
        (OUT / ("hism_plan_" + tag + ".json")).write_text(
            json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report["summary"]))
        return report

    destroyed = clear(tag)
    report["destroyed_previous"] = destroyed
    for group in plan["groups"]:
        mesh = unreal.load_asset(group["mesh"])
        if mesh is None:
            report["errors"].append("mesh not found: " + group["mesh"])
            continue
        holder = EL.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(0.0, 0.0, 0.0),
            unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0))
        label = "EST_%s_%s" % (tag, mesh.get_name())
        holder.set_actor_label(label)
        holder.set_folder_path(folder)
        holder.tags = [tag]
        # Instance transforms are absolute because the component sits at the
        # world origin with identity rotation.
        hism = unreal.new_object(
            unreal.HierarchicalInstancedStaticMeshComponent, holder,
            name=label + "_HISM")
        hism.attach_to_component(
            holder.root_component, unreal.Name(),
            unreal.AttachmentRule.KEEP_RELATIVE,
            unreal.AttachmentRule.KEEP_RELATIVE,
            unreal.AttachmentRule.KEEP_RELATIVE, False)
        hism.set_static_mesh(mesh)
        for slot, mat_path in enumerate(group["materials"]):
            if not mat_path:
                continue
            mi = unreal.load_asset(mat_path)
            if mi is None:
                report["errors"].append("material not found: " + mat_path)
                continue
            hism.set_material(slot, mi)
        for inst in group["instances"]:
            hism.add_instance(unreal.Transform(
                location=unreal.Vector(*inst["loc"]),
                rotation=unreal.Rotator(pitch=0.0, yaw=inst["yaw"], roll=0.0),
                scale=unreal.Vector(*inst["scale"])))
        report["created"].append({"actor": label, "mesh": mesh.get_name(),
                                  "instances": group["count"],
                                  "materials": group["materials"]})
    report["ok"] = not report["errors"]
    (OUT / ("hism_place_" + tag + ".json")).write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"summary": report["summary"], "created": len(report["created"]),
                      "destroyed_previous": destroyed, "errors": report["errors"]}))
    return report


if __name__ == "__main__":
    place(str(Path(unreal.Paths.project_dir()) / "Saved/GoalEst/e1_points.json"),
          tag="EstablishingE1", apply=False)
