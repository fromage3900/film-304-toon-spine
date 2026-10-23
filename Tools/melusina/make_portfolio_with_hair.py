# Tools/melusina/make_portfolio_with_hair.py
import maya.standalone
maya.standalone.initialize(name="python")
from maya import cmds

BIND = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\ma\Brennan_Shepherd_Assignment1.ma"
OUT = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\ma\Brennan_Shepherd_Assignment1_portfolio_pose.ma"

ROT = {
    "LeftArm": (0, 0, -50),
    "RightArm": (0, 0, -50),
    "LeftForeArm": (0, 0, -35),
    "RightForeArm": (0, 0, -35),
    "LeftHand": (0, 0, -8),
    "RightHand": (0, 0, -8),
    "LeftUpLeg": (0, 25, 0),
    "LeftLeg": (0, -35, 0),
    "LeftFoot": (0, 10, 0),
    "RightUpLeg": (0, -20, 0),
    "RightLeg": (0, -15, 0),
    "RightFoot": (0, 5, 0),
    "Spine": (8, 0, 0),
    "Spine1": (8, 0, 0),
    "Neck": (-10, 0, 0),
    "Head": (-5, 0, 0),
}

def main():
    cmds.file(BIND, open=True, force=True)
    for j, (rx, ry, rz) in ROT.items():
        cmds.setAttr(j + ".rotateX", rx)
        cmds.setAttr(j + ".rotateY", ry)
        cmds.setAttr(j + ".rotateZ", rz)
    cmds.file(rename=OUT)
    cmds.file(save=True, type="mayaAscii")

main()

