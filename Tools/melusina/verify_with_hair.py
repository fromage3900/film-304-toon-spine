# Tools/melusina/verify_with_hair.py
import json, os
import maya.standalone
maya.standalone.initialize(name="python")
from maya import cmds

MA = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\ma\Brennan_Shepherd_Assignment1.ma"
OUT = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\report\verify_with_hair.json"

def flatten(w):
    out = []
    for item in w:
        if isinstance(item, (list, tuple)):
            out.extend(float(x) for x in item)
        else:
            out.append(float(item))
    return out

def stats(sc, v):
    raw = cmds.getAttr("%s.weightList[%d].weights" % (sc, v))
    w = flatten(raw)
    return {"sum": sum(w), "nonzero": len([x for x in w if x > 1e-4]), "count": len(w)}

def main():
    cmds.file(MA, open=True, force=True)
    joints = cmds.ls(type="joint") or []
    scs = cmds.ls(type="skinCluster") or []
    result = {
        "file": MA,
        "units": {"linear": cmds.currentUnit(q=True, linear=True), "time": cmds.currentUnit(q=True, time=True), "angle": cmds.currentUnit(q=True, angle=True)},
        "up_axis": cmds.upAxis(q=True, axis=True),
        "joint_count": len(joints),
        "root_joints": [j for j in joints if not cmds.listRelatives(j, parent=True, type="joint")],
        "mesh_count": len(cmds.ls(type="mesh") or []),
        "skin_cluster_count": len(scs),
        "body_weight_sample": stats("_Melusina_skinCluster", 0),
        "hair_weight_sample": stats("_HairFBXASC032StrandFBXASC046007_skinCluster", 0),
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

main()

