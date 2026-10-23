# Tools/melusina/render_hair_test.py
import os
import maya.standalone
maya.standalone.initialize(name="python")
from maya import cmds

WITH_HAIR = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\ma\Brennan_Shepherd_Assignment1_with_hair.ma"
PREVIEW = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\preview"

def main():
    cmds.file(WITH_HAIR, open=True, force=True)
    body_shader = cmds.shadingNode("lambert", asShader=True, name="BodyGray")
    cmds.setAttr(body_shader + ".color", 0.62, 0.60, 0.57)
    hair_shader = cmds.shadingNode("lambert", asShader=True, name="HairDark")
    cmds.setAttr(hair_shader + ".color", 0.16, 0.14, 0.12)
    body_sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="BodySG")
    hair_sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="HairSG")
    cmds.connectAttr(body_shader + ".outColor", body_sg + ".surfaceShader")
    cmds.connectAttr(hair_shader + ".outColor", hair_sg + ".surfaceShader")
    for m in cmds.ls(type="mesh") or []:
        t = cmds.listRelatives(m, parent=True, fullPath=True)[0]
        if "HairFBXASC032Strand" in t:
            cmds.sets(m, edit=True, forceElement=hair_sg)
        else:
            cmds.sets(m, edit=True, forceElement=body_sg)
    key_shape = cmds.directionalLight(name="KeyLight", intensity=1.1)
    key = cmds.listRelatives(key_shape, parent=True)[0]
    cmds.setAttr(key + ".rotateX", -45)
    cmds.setAttr(key + ".rotateY", 35)
    cmds.ambientLight(name="FillLight", intensity=0.35)
    views = [
        ("hair_test_three_quarter", 304, 95, 304, 45, -1.2, 55),
        ("hair_test_back", 0, 95, -430, 180, -1.2, 55),
        ("hair_test_head", 0, 162, 130, 0, -2.0, 85),
    ]
    for name, x, y, z, ry, rx, focal in views:
        cmds.setAttr("persp.translateX", x)
        cmds.setAttr("persp.translateY", y)
        cmds.setAttr("persp.translateZ", z)
        cmds.setAttr("persp.rotateX", rx)
        cmds.setAttr("persp.rotateY", ry)
        cmds.setAttr("persp.rotateZ", 0)
        cmds.setAttr("perspShape.focalLength", focal)
        out = os.path.join(PREVIEW, name)
        cmds.playblast(frame=1, format="image", compression="png", filename=out,
                       widthHeight=(600, 800), percent=100, quality=100,
                       viewer=False, offScreen=True, showOrnaments=False,
                       clearCache=True, forceOverwrite=True)
        src = out + ".0000.png"
        dst = out + ".png"
        if os.path.exists(src):
            if os.path.exists(dst):
                os.remove(dst)
            os.rename(src, dst)

main()
