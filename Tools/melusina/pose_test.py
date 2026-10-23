# Tools/melusina/pose_test.py
import maya.standalone
maya.standalone.initialize(name="python")
from maya import cmds

IN_MA = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\ma\Brennan_Shepherd_Assignment1.ma"
OUT_MA = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\ma\Brennan_Shepherd_Assignment1_pose_test.ma"

def main():
    cmds.file(IN_MA, open=True, force=True)
    cmds.setAttr("LeftArm.rotateZ", 90)
    cmds.setAttr("RightArm.rotateZ", -90)
    cmds.setAttr("LeftForeArm.rotateZ", 45)
    cmds.setAttr("RightForeArm.rotateZ", -45)
    cmds.setAttr("LeftUpLeg.rotateX", -45)
    cmds.setAttr("RightUpLeg.rotateX", -45)
    cmds.setAttr("LeftLeg.rotateX", 60)
    cmds.setAttr("RightLeg.rotateX", 60)
    cmds.setAttr("Spine.rotateZ", 10)
    cmds.setAttr("Spine1.rotateZ", 10)
    cmds.setAttr("Neck.rotateZ", -15)
    cmds.file(rename=OUT_MA)
    cmds.file(save=True, type="mayaAscii")

main()
