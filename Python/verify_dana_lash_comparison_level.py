"""Read back comparison actors/materials/bounds from a fresh Unreal commandlet."""
import json
from pathlib import Path
import unreal

ROOT=Path(__file__).resolve().parents[1]
MAP="/Game/Maps/Lookdev/L_Dana_LashVisibility_Compare"
OUT=ROOT/"Saved/Audit/dana_lash_comparison_level_readback.json"
if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP):
    raise RuntimeError("comparison level load failed")
sub=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
rows=[]
for actor in sub.get_all_level_actors():
    label=actor.get_actor_label()
    if not label.startswith("DANA_LASHCMP_"): continue
    row={"label":label,"class":actor.get_class().get_name(),
         "location":[actor.get_actor_location().x,actor.get_actor_location().y,actor.get_actor_location().z],
         "rotation":[actor.get_actor_rotation().pitch,actor.get_actor_rotation().yaw,actor.get_actor_rotation().roll]}
    try:
        row["hidden_in_game"] = bool(actor.get_editor_property("hidden"))
    except Exception:
        row["hidden_in_game"] = None
    try:
        row["actor_scale"] = [actor.get_actor_scale3d().x, actor.get_actor_scale3d().y, actor.get_actor_scale3d().z]
    except Exception:
        row["actor_scale"] = None
    meshcomp=actor.get_component_by_class(unreal.SkeletalMeshComponent)
    if meshcomp:
        mesh=meshcomp.get_skeletal_mesh_asset()
        origin,extent=actor.get_actor_bounds(False)
        row.update({"mesh":mesh.get_path_name() if mesh else None,
          "bounds_origin":[origin.x,origin.y,origin.z],
          "bounds_extent":[extent.x,extent.y,extent.z],
          "materials":[meshcomp.get_material(i).get_path_name() if meshcomp.get_material(i) else None
                       for i in range(len(mesh.materials))] if mesh else []})
    rows.append(row)
report={"result":"pass" if len([x for x in rows if x["class"]=="SkeletalMeshActor"])==2 else "fail",
        "map":MAP,"actors":rows}
OUT.write_text(json.dumps(report,indent=2),encoding="utf-8")
unreal.log("[DanaLashCompareReadback] "+json.dumps(report))
