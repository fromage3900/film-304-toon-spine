# Tools/melusina/render_bones_v2.py
import os, math
import maya.standalone
maya.standalone.initialize(name="python")
from maya import cmds

BIND = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\ma\Brennan_Shepherd_Assignment1.ma"
PREVIEW = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\preview"

def build_bones():
    joints = cmds.ls(type="joint") or []
    shader = cmds.shadingNode("lambert", asShader=True, name="V2Bone")
    cmds.setAttr(shader + ".color", 0.05, 0.09, 0.13)
    sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="V2BoneSG")
    cmds.connectAttr(shader + ".outColor", sg + ".surfaceShader")
    for j in joints:
        p = cmds.xform(j, q=True, ws=True, t=True)
        sph = cmds.polySphere(radius=2.8, sx=8, sy=8, name="V2Bone_%s" % j)[0]
        cmds.xform(sph, ws=True, t=p)
        cmds.sets(sph, edit=True, forceElement=sg)
        for c in cmds.listRelatives(j, children=True, type="joint") or []:
            pc = cmds.xform(c, q=True, ws=True, t=True)
            dx, dy, dz = pc[0]-p[0], pc[1]-p[1], pc[2]-p[2]
            length = math.sqrt(dx*dx + dy*dy + dz*dz)
            if length < 1e-6:
                continue
            mid = ((p[0]+pc[0])/2.0, (p[1]+pc[1])/2.0, (p[2]+pc[2])/2.0)
            cyl = cmds.polyCylinder(radius=2.2, height=length, axis=(dx, dy, dz),
                                    sx=8, sy=1, name="V2Bone_%s_%s" % (j, c))[0]
            cmds.xform(cyl, ws=True, t=mid)
            cmds.sets(cyl, edit=True, forceElement=sg)
    for m in cmds.ls(type="mesh") or []:
        t = cmds.listRelatives(m, parent=True, fullPath=True)[0]
        if not t.startswith("|V2Bone_"):
            cmds.setAttr(t + ".visibility", 0)

def set_camera(x, y, z, rx, ry, focal):
    cmds.setAttr("persp.translateX", x)
    cmds.setAttr("persp.translateY", y)
    cmds.setAttr("persp.translateZ", z)
    cmds.setAttr("persp.rotateX", rx)
    cmds.setAttr("persp.rotateY", ry)
    cmds.setAttr("persp.rotateZ", 0)
    cmds.setAttr("perspShape.focalLength", focal)

def render(name):
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

def main():
    cmds.file(BIND, open=True, force=True)
    build_bones()
    key_shape = cmds.directionalLight(name="V2Key", intensity=1.1)
    key = cmds.listRelatives(key_shape, parent=True)[0]
    cmds.setAttr(key + ".rotateX", -45)
    cmds.setAttr(key + ".rotateY", 35)
    cmds.ambientLight(name="V2Ambient", intensity=0.45)
    set_camera(0, 95, 430, -1.2, 0, 55)
    render("v2_bones_front")
    set_camera(304, 95, 304, -1.2, 45, 55)
    render("v2_bones_three_quarter")

main()

