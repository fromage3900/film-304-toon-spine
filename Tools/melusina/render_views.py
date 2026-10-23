# Tools/melusina/render_views.py
import os, sys
sys.path.insert(0, r"G:\film-304-toon-spine\Tools\melusina")
import maya.standalone
maya.standalone.initialize(name="python")
from maya import cmds

BIND = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\ma\Brennan_Shepherd_Assignment1.ma"
POSE = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\ma\Brennan_Shepherd_Assignment1_pose_test.ma"
PREVIEW = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\preview"

VIEWS = [
    ("front", 0, 430, 0),
    ("three_quarter", 304, 304, 45),
    ("side", 430, 0, 90),
    ("back", 0, -430, 180),
]

def setup_scene():
    shader = cmds.shadingNode("lambert", asShader=True, name="ContactGray")
    cmds.setAttr(shader + ".color", 0.45, 0.47, 0.52)
    sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="ContactSG")
    cmds.connectAttr(shader + ".outColor", sg + ".surfaceShader")
    for m in cmds.ls(type="mesh") or []:
        try:
            cmds.sets(m, edit=True, forceElement=sg)
        except Exception:
            pass
    key_shape = cmds.directionalLight(name="KeyLight", intensity=1.0)
    key = cmds.listRelatives(key_shape, parent=True)[0]
    cmds.setAttr(key + ".rotateX", -45)
    cmds.setAttr(key + ".rotateY", 35)
    cmds.ambientLight(name="FillLight", intensity=0.4)
    try:
        cmds.setAttr("hardwareRenderingGlobals.displayLights", 1)
    except Exception:
        pass
    cmds.setAttr("persp.translateY", 95)
    cmds.setAttr("persp.rotateX", -1.2)
    cmds.setAttr("perspShape.focalLength", 55)

def render_view(name, x, z, ry):
    cmds.setAttr("persp.translateX", x)
    cmds.setAttr("persp.translateZ", z)
    cmds.setAttr("persp.rotateY", ry)
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

def render_set(prefix, path):
    cmds.file(path, open=True, force=True)
    setup_scene()
    for name, x, z, ry in VIEWS:
        render_view("%s_%s" % (prefix, name), x, z, ry)

def main():
    os.makedirs(PREVIEW, exist_ok=True)
    render_set("bind", BIND)
    render_set("posed", POSE)

main()
