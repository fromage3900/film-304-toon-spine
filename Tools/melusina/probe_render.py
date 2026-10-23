# Tools/melusina/probe_render.py
import sys
sys.path.insert(0, r"G:\film-304-toon-spine\Tools\melusina")
import maya.standalone
maya.standalone.initialize(name="python")
from maya import cmds
from melusina_common import write_json

BIND = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\ma\Brennan_Shepherd_Assignment1.ma"
POSE = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\ma\Brennan_Shepherd_Assignment1_pose_test.ma"
OUT = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\report\probe_render.json"

def flatten_weights(w):
    if w is None:
        return None
    out = []
    for item in w:
        if isinstance(item, (list, tuple)):
            out.extend([float(x) for x in item])
        else:
            out.append(float(item))
    return out

def weight_stats(sc, verts):
    rows = []
    for v in verts:
        try:
            raw = cmds.getAttr("%s.weightList[%d].weights" % (sc, v))
        except Exception as exc:
            rows.append({"vertex": v, "error": str(exc)})
            continue
        w = flatten_weights(raw)
        if w is None:
            rows.append({"vertex": v, "weights": None})
            continue
        rows.append({
            "vertex": v,
            "count": len(w),
            "sum": sum(w),
            "nonzero": len([x for x in w if x > 1e-4]),
            "max": max(w) if w else None,
            "first": w[:6],
        })
    return rows

def main():
    cmds.file(BIND, open=True, force=True)
    sc = "_Melusina_skinCluster"
    shape = "MelusinaShape"
    vcount = cmds.polyEvaluate(shape, vertex=True)
    sample = [0, 1, 100, 1000, 5000, 10000, min(18000, vcount - 1)]
    stats = weight_stats(sc, sample)
    bbox_bind = cmds.exactWorldBoundingBox(shape)
    pos_bind = [cmds.pointPosition("%s.vtx[%d]" % (shape, v), world=True) for v in sample]
    cmds.file(POSE, open=True, force=True)
    bbox_pose = cmds.exactWorldBoundingBox(shape)
    pos_pose = [cmds.pointPosition("%s.vtx[%d]" % (shape, v), world=True) for v in sample]
    result = {
        "renderers": [],
        "has_playblast": hasattr(cmds, "playblast"),
        "vcount": vcount,
        "weight_stats": stats,
        "bbox_bind": bbox_bind,
        "bbox_pose": bbox_pose,
        "pos_bind": pos_bind,
        "pos_pose": pos_pose,
        "sample_vertices": sample,
    }
    write_json(OUT, result)

main()
