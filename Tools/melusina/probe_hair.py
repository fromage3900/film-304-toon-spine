# Tools/melusina/probe_hair.py
import sys, json, os
sys.path.insert(0, r"G:\film-304-toon-spine\Tools\melusina")
import maya.standalone
maya.standalone.initialize(name="python")
from maya import cmds
from melusina_common import write_json

WITH_HAIR = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\ma\Brennan_Shepherd_Assignment1.ma"
PORT = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\ma\Brennan_Shepherd_Assignment1_portfolio_pose.ma"
OUT = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\report\hair_verify.json"
HAIR = ["HairFBXASC032StrandFBXASC046002Shape", "HairFBXASC032StrandFBXASC046004Shape", "HairFBXASC032StrandFBXASC046007Shape"]

def flatten(w):
    out = []
    for item in w:
        if isinstance(item, (list, tuple)):
            out.extend(float(x) for x in item)
        else:
            out.append(float(item))
    return out

def weight_stats(sc, verts):
    rows = []
    for v in verts:
        raw = cmds.getAttr("%s.weightList[%d].weights" % (sc, v))
        w = flatten(raw)
        rows.append({"vertex": v, "count": len(w), "sum": sum(w), "nonzero": len([x for x in w if x > 1e-4])})
    return rows

def main():
    cmds.file(WITH_HAIR, open=True, force=True)
    rows = []
    for shape in HAIR:
        transforms = cmds.listRelatives(shape, parent=True, fullPath=True)
        t = transforms[0] if transforms else shape
        scs = cmds.ls(cmds.listHistory(shape) or [], type="skinCluster")
        sc = scs[0] if scs else None
        vcount = cmds.polyEvaluate(shape, vertex=True)
        sample = [0, 1, vcount // 2, vcount - 1]
        rows.append({
            "shape": shape,
            "transform": t,
            "vertices": vcount,
            "skinCluster": sc,
            "bbox_bind": cmds.exactWorldBoundingBox(shape),
            "weight_stats": weight_stats(sc, sample) if sc else [],
        })
    body_bind = cmds.exactWorldBoundingBox("MelusinaShape")
    cmds.file(PORT, open=True, force=True)
    for r in rows:
        r["bbox_portfolio"] = cmds.exactWorldBoundingBox(r["shape"])
    body_port = cmds.exactWorldBoundingBox("MelusinaShape")
    write_json(OUT, {"hair": rows, "body_bbox_bind": body_bind, "body_bbox_portfolio": body_port})

main()

