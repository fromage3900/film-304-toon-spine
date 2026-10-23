# Tools/melusina/verify_assignment1.py
import json, os, datetime
import maya.standalone
maya.standalone.initialize(name="python")
from maya import cmds

MA = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\ma\Brennan_Shepherd_Assignment1.ma"
OUT = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\report\verify_report.json"

def main():
    cmds.file(MA, open=True, force=True)
    units = {
        "linear": cmds.currentUnit(q=True, linear=True),
        "time": cmds.currentUnit(q=True, time=True),
        "angle": cmds.currentUnit(q=True, angle=True),
    }
    up_axis = cmds.upAxis(q=True, axis=True)
    joints = cmds.ls(type="joint") or []
    meshes = cmds.ls(type="mesh") or []
    skin_clusters = cmds.ls(type="skinCluster") or []
    roots = [j for j in joints if not cmds.listRelatives(j, parent=True, type="joint")]
    weight_rows = []
    for sc in skin_clusters:
        geo = cmds.skinCluster(sc, q=True, geometry=True)
        if not geo:
            continue
        shape = geo[0]
        influences = cmds.skinCluster(sc, q=True, influence=True)
        num_verts = cmds.polyEvaluate(shape, vertex=True)
        sample_count = min(num_verts, 50)
        sums = []
        max_nonzero = []
        for v in range(sample_count):
            cmds.select("%s.vtx[%d]" % (shape, v))
            weights = cmds.skinCluster(sc, q=True, weight=True)
            if weights is None:
                continue
            total = sum(weights)
            nonzero = len([w for w in weights if w > 1e-4])
            sums.append(total)
            max_nonzero.append(nonzero)
        weight_rows.append({
            "skinCluster": sc,
            "shape": shape,
            "influences": len(influences),
            "vertices": num_verts,
            "sampled": sample_count,
            "min_sum": min(sums) if sums else None,
            "max_sum": max(sums) if sums else None,
            "max_nonzero": max(max_nonzero) if max_nonzero else None,
        })
    report = {
        "tool": "verify_assignment1",
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "file": MA,
        "units": units,
        "up_axis": up_axis,
        "joint_count": len(joints),
        "root_joints": roots,
        "mesh_count": len(meshes),
        "skin_cluster_count": len(skin_clusters),
        "weight_rows": weight_rows,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

main()
