# Tools/melusina/probe_axes.py
import sys, json, os
sys.path.insert(0, r"G:\film-304-toon-spine\Tools\melusina")
import maya.standalone
maya.standalone.initialize(name="python")
from maya import cmds

BIND = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\ma\Brennan_Shepherd_Assignment1.ma"
OUT = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\report\joint_axes.json"

JOINTS = ["LeftArm", "LeftForeArm", "LeftHand", "RightArm", "RightForeArm", "RightHand",
          "LeftUpLeg", "LeftLeg", "LeftFoot", "RightUpLeg", "RightLeg", "RightFoot",
          "Spine", "Spine1", "Neck", "Head"]

def main():
    cmds.file(BIND, open=True, force=True)
    rows = {}
    for j in JOINTS:
        m = cmds.xform(j, q=True, ws=True, matrix=True)
        rows[j] = {
            "X": [round(v, 4) for v in m[0:3]],
            "Y": [round(v, 4) for v in m[4:7]],
            "Z": [round(v, 4) for v in m[8:11]],
            "pos": [round(v, 4) for v in m[12:15]],
        }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

main()
