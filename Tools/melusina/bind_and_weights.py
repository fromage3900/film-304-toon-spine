# Tools/melusina/bind_and_weights.py
# Bind the full character mesh set to the clean HIK skeleton and refine weights.
import sys, os, json, datetime
sys.path.insert(0, r"G:\film-304-toon-spine\Tools\melusina")
import maya.standalone
maya.standalone.initialize(name="python")
from maya import cmds
import weight_refine_api2 as wr
from melusina_common import write_json

IN_MA = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\scratch\skeleton_test.ma"
OUT_MA = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\ma\Brennan_Shepherd_Assignment1.ma"
OUT_JSON = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\report\bind_report.json"
MAX_INFLUENCES = 4
SMOOTH_ITERATIONS = 2

def bind_mesh(mesh_transform, joints):
    cmds.select(clear=True)
    cmds.select(joints, add=True)
    cmds.select(mesh_transform, add=True)
    name = "%s_skinCluster" % mesh_transform.replace("|", "_")
    try:
        sc = cmds.skinCluster(name=name, toSelectedBones=True, bindMethod=0, skinMethod=0,
                              normalizeWeights=1, obeyMaxInfluences=True,
                              maximumInfluences=MAX_INFLUENCES,
                              dropoffRate=4.0, heatMap=True)
        sc_name = sc[0] if isinstance(sc, list) else sc
        return sc_name, "heatMap"
    except Exception:
        try:
            sc = cmds.skinCluster(name=name, toSelectedBones=True, bindMethod=0, skinMethod=0,
                                  normalizeWeights=1, obeyMaxInfluences=True,
                                  maximumInfluences=MAX_INFLUENCES,
                                  dropoffRate=4.0)
            sc_name = sc[0] if isinstance(sc, list) else sc
            return sc_name, "closestDistance"
        except Exception as exc:
            return None, "failed: %s" % exc

def refine_mesh(mesh_transform, skin_cluster):
    shapes = cmds.listRelatives(mesh_transform, shapes=True, fullPath=True) or []
    if not shapes:
        return {"error": "no shape"}
    shape = shapes[0]
    dag_path = wr.get_mesh_dag_path(shape)
    adjacency = wr.get_adjacency(dag_path)
    influence_names = cmds.skinCluster(skin_cluster, q=True, influence=True)
    influence_paths = wr.get_influence_paths(skin_cluster)
    num_verts = cmds.polyEvaluate(shape, vertex=True)
    weights = wr.get_all_weights(skin_cluster, influence_names, shape, num_verts)
    weights, repaired = wr.repair_zero_weights(weights, adjacency)
    weights = wr.smooth_weights(weights, adjacency, iterations=SMOOTH_ITERATIONS)
    weights = wr.prune_small_weights(weights, threshold=0.001)
    weights = wr.clamp_influences(weights, MAX_INFLUENCES)
    weights = wr.normalize_weights(weights)
    skin_fn = wr.get_skin_cluster_fn(skin_cluster)
    wr.set_all_weights(skin_fn, influence_paths, weights, dag_path)
    return {"vertices": num_verts, "repaired_zero": repaired, "influences": len(influence_paths)}

def main():
    cmds.file(IN_MA, open=True, force=True)
    cmds.currentUnit(linear="cm", time="film", angle="deg")
    joints = cmds.ls(type="joint") or []
    mesh_transforms = []
    for m in cmds.ls(type="mesh") or []:
        transforms = cmds.listRelatives(m, parent=True, fullPath=True)
        if transforms:
            mesh_transforms.append(transforms[0])
    report_rows = []
    for t in mesh_transforms:
        sc, method = bind_mesh(t, joints)
        if not sc:
            report_rows.append({"mesh": t, "method": method, "status": "bind_failed"})
            continue
        report_rows.append({"mesh": t, "method": method, "skinCluster": sc, "status": "bound"})
    cmds.file(rename=OUT_MA)
    cmds.file(save=True, type="mayaAscii")
    report = {
        "tool": "bind_and_weights",
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "max_influences": MAX_INFLUENCES,
        "smooth_iterations": SMOOTH_ITERATIONS,
        "joint_count": len(joints),
        "mesh_count": len(mesh_transforms),
        "rows": report_rows,
        "saved_ma": OUT_MA,
    }
    write_json(OUT_JSON, report)

main()
