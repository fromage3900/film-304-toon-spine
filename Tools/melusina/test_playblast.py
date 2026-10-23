# Tools/melusina/test_playblast.py
import os
import maya.standalone
maya.standalone.initialize(name="python")
from maya import cmds

BIND = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\ma\Brennan_Shepherd_Assignment1.ma"
OUT = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\preview\test_bind"

def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    cmds.file(BIND, open=True, force=True)
    cmds.setAttr("persp.translateX", 0)
    cmds.setAttr("persp.translateY", 95)
    cmds.setAttr("persp.translateZ", 520)
    cmds.setAttr("persp.rotateX", -1.0)
    cmds.setAttr("persp.rotateY", 0)
    cmds.setAttr("persp.rotateZ", 0)
    cmds.setAttr("perspShape.focalLength", 50)
    key_shape = cmds.directionalLight(name="KeyLight", intensity=1.2)
    key = cmds.listRelatives(key_shape, parent=True)[0]
    cmds.setAttr(key + ".rotateX", -45)
    cmds.setAttr(key + ".rotateY", 35)
    fill = cmds.ambientLight(name="FillLight", intensity=0.35)
    cmds.playblast(frame=1, format="image", compression="png", filename=OUT,
                   widthHeight=(600, 800), percent=100, quality=100,
                   viewer=False, offScreen=True, showOrnaments=False,
                   clearCache=True, forceOverwrite=True)

main()
