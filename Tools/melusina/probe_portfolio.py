# Tools/melusina/probe_portfolio.py
import sys, json
sys.path.insert(0, r"G:\film-304-toon-spine\Tools\melusina")
import maya.standalone
maya.standalone.initialize(name="python")
from maya import cmds

BIND = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\ma\Brennan_Shepherd_Assignment1.ma"
PORT = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\ma\Brennan_Shepherd_Assignment1_portfolio_pose.ma"
OUT = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\report\probe_portfolio.json"

def main():
    shape = "MelusinaShape"
    cmds.file(BIND, open=True, force=True)
    vcount = cmds.polyEvaluate(shape, vertex=True)
    sample = [0, 1, 100, 1000, 5000, 10000, min(18000, vcount - 1)]
    bbox_bind = cmds.exactWorldBoundingBox(shape)
    pos_bind = [cmds.pointPosition("%s.vtx[%d]" % (shape, v), world=True) for v in sample]
    cmds.file(PORT, open=True, force=True)
    bbox_port = cmds.exactWorldBoundingBox(shape)
    pos_port = [cmds.pointPosition("%s.vtx[%d]" % (shape, v), world=True) for v in sample]
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({
            "vcount": vcount,
            "sample_vertices": sample,
            "bbox_bind": bbox_bind,
            "bbox_portfolio": bbox_port,
            "pos_bind": pos_bind,
            "pos_portfolio": pos_port,
        }, f, indent=2)

main()
