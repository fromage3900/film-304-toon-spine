# Tools/melusina/render_isolate.py
import os
import maya.standalone
maya.standalone.initialize(name="python")
from maya import cmds

BIND = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\ma\Brennan_Shepherd_Assignment1.ma"
PREVIEW = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\preview"

CANDIDATES = [
    ("melusina002", "MelusinaFBXASC046002"),
    ("plane005", "Retopo_Plane005FBXASC046002"),
]

def main():
    cmds.file(BIND, open=True, force=True)
    transforms = []
    for m in cmds.ls(type="mesh") or []:
        t = cmds.listRelatives(m, parent=True, fullPath=True)[0]
        if t not in transforms:
            transforms.append(t)
    for t in transforms:
        try:
            cmds.setAttr(t + ".visibility", 0)
        except Exception:
            cmds.hide(t)
    shader = cmds.shadingNode("lambert", asShader=True, name="IsoOrange")
    cmds.setAttr(shader + ".color", 1.0, 0.42, 0.08)
    sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="IsoSG")
    cmds.connectAttr(shader + ".outColor", sg + ".surfaceShader")
    key_shape = cmds.directionalLight(name="IsoKey", intensity=1.2)
    key = cmds.listRelatives(key_shape, parent=True)[0]
    cmds.setAttr(key + ".rotateX", -40)
    cmds.setAttr(key + ".rotateY", 30)
    cmds.ambientLight(name="IsoFill", intensity=0.45)
    for key_name, tname in CANDIDATES:
        t = "|" + tname
        if not cmds.objExists(t):
            continue
        try:
            cmds.setAttr(t + ".visibility", 1)
        except Exception:
            cmds.showHidden(t)
        shapes = cmds.listRelatives(t, shapes=True) or []
        shape = None
        for s in shapes:
            try:
                if not cmds.getAttr(s + ".intermediateObject"):
                    shape = s
                    break
            except Exception:
                pass
        if not shape:
            shape = shapes[0]
        cmds.sets(shape, edit=True, forceElement=sg)
        bbox = cmds.exactWorldBoundingBox(t)
        cx = (bbox[0] + bbox[3]) / 2.0
        cy = (bbox[1] + bbox[4]) / 2.0
        cz = (bbox[2] + bbox[5]) / 2.0
        size = max(bbox[3] - bbox[0], bbox[4] - bbox[1], bbox[5] - bbox[2])
        dist = max(size * 1.8, 60.0)
        for view, zsign, ry in (("front", 1, 0), ("back", -1, 180)):
            cmds.setAttr("persp.translateX", cx)
            cmds.setAttr("persp.translateY", cy)
            cmds.setAttr("persp.translateZ", cz + zsign * dist)
            cmds.setAttr("persp.rotateX", 0)
            cmds.setAttr("persp.rotateY", ry)
            cmds.setAttr("persp.rotateZ", 0)
            cmds.setAttr("perspShape.focalLength", 50)
            out = os.path.join(PREVIEW, "isolate_%s_%s" % (key_name, view))
            cmds.playblast(frame=1, format="image", compression="png", filename=out,
                           widthHeight=(400, 500), percent=100, quality=100,
                           viewer=False, offScreen=True, showOrnaments=False,
                           clearCache=True, forceOverwrite=True)
            src = out + ".0000.png"
            dst = out + ".png"
            if os.path.exists(src):
                if os.path.exists(dst):
                    os.remove(dst)
                os.rename(src, dst)
        try:
            cmds.setAttr(t + ".visibility", 0)
        except Exception:
            cmds.hide(t)

main()
