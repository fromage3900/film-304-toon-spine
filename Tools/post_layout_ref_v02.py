"""Post-build cards/materials for the referenced v02 layout scene."""
from __future__ import annotations

import maya.cmds as cmds

TITLE = "G:/film-304-toon-spine/Saved/Scenes/layout_title_15mins.png"
ARROW = "G:/film-304-toon-spine/Saved/Scenes/layout_arrow_right.png"


def surface_file_mat(name: str, png: str):
    shader = cmds.shadingNode("surfaceShader", asShader=True, name=name + "_S")
    f = cmds.shadingNode("file", asTexture=True, name=name + "_F")
    cmds.setAttr(f + ".fileTextureName", png, type="string")
    cmds.connectAttr(f + ".outColor", shader + ".outColor")
    sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=name + "_SG")
    cmds.connectAttr(shader + ".outColor", sg + ".surfaceShader")
    return sg


def assign_sg(node: str, sg: str) -> None:
    try:
        cmds.sets(node, edit=True, forceElement=sg)
    except Exception as e:
        print("ASSIGN_ERR", node, e)


def main() -> None:
    if cmds.objExists("Layout_TitleCard"):
        cmds.xform("Layout_TitleCard", ws=True, ro=(90, 0, 0))
        cmds.xform("Layout_TitleCard", ws=True, t=(0, 150, -100))
        assign_sg("Layout_TitleCard", surface_file_mat("Layout_TitleCardMat", TITLE))
    if cmds.objExists("Layout_Arrow"):
        cmds.xform("Layout_Arrow", ws=True, ro=(90, 0, 0))
        assign_sg("Layout_Arrow", surface_file_mat("Layout_ArrowCardMat", ARROW))
    if cmds.objExists("Layout_DoorPanel"):
        m = cmds.shadingNode("lambert", asShader=True, name="Layout_DoorMat")
        cmds.setAttr(m + ".color", 0.22, 0.28, 0.38, type="double3")
        sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="Layout_DoorMat_SG")
        cmds.connectAttr(m + ".outColor", sg + ".surfaceShader")
        assign_sg("Layout_DoorPanel", sg)
    if cmds.objExists("Layout_DoorWall"):
        m2 = cmds.shadingNode("lambert", asShader=True, name="Layout_DoorWallMat")
        cmds.setAttr(m2 + ".color", 0.30, 0.30, 0.32, type="double3")
        sg2 = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="Layout_DoorWallMat_SG")
        cmds.connectAttr(m2 + ".outColor", sg2 + ".surfaceShader")
        assign_sg("Layout_DoorWall", sg2)
    cmds.currentTime(1)
    cmds.file(save=True, type="mayaBinary", force=True)
    print("V02_POST_SAVED")


if __name__ == "__main__":
    main()
