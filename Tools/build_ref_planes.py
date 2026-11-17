"""Add per-camera storyboard image planes to a REF copy of the handoff scene."""
from __future__ import annotations

import json
import os

import maya.cmds as cmds

ROOT = "G:/film-304-toon-spine"
SCENE = ROOT + "/Saved/Scenes/L_Scene62-66_BS.mb"
REF = ROOT + "/Saved/Scenes/L_Scene62-66_BS_REF.mb"
PNG = ROOT + "/Saved/StoryboardRefs/"
REPORT = ROOT + "/Saved/Scenes/layout_62_66_refplanes_report.json"
SHOTS = [
    ("62", "Cam_Shot62", "SB_Shot_62.png"),
    ("63A", "Cam_Shot63A1", "SB_Shot_63A.png"),
    ("63B", "Cam_Shot63B1", "SB_Shot_63B.png"),
    ("64A", "Cam_Shot64A1", "SB_Shot_64A.png"),
    ("64B", "Cam_Shot64B1", "SB_Shot_64B.png"),
    ("65", "Cam_Shot65", "SB_Shot_65.png"),
    ("66A", "Cam_Shot66A1", "SB_Shot_66A.png"),
    ("66B", "Cam_Shot66B1", "SB_Shot_66B.png"),
]
report = {"planes": []}


def main():
    cmds.file(SCENE, open=True, force=True, ignoreVersion=True)
    layer = "DL_STORYBOARD_REFS"
    if not cmds.objExists(layer):
        cmds.createDisplayLayer(name=layer, empty=True)
    try:
        cmds.setAttr(layer + ".visibility", 1)
    except Exception:
        pass
    for label, cam, png in SHOTS:
        path = PNG + png
        if not cmds.objExists(cam):
            report["planes"].append({"shot": label, "status": "missing_camera"})
            continue
        if not os.path.exists(path):
            report["planes"].append({"shot": label, "status": "missing_png"})
            continue
        # remove a previous REF for this shot
        for n in cmds.ls("REF_Shot" + label + "*") or []:
            try:
                cmds.delete(n)
            except Exception:
                pass
        created = cmds.imagePlane(camera=cam, fileName=path, name="REF_Shot" + label,
                                  lookThrough=False)
        shape = None
        for n in created:
            if cmds.nodeType(n) == "imagePlane":
                shape = n
                break
        if not shape:
            report["planes"].append({"shot": label, "status": "no_shape"})
            continue
        transform = (cmds.listRelatives(shape, parent=True) or [shape])[0]
        try:
            transform = cmds.rename(transform, "REF_Shot" + label)
        except Exception:
            pass
        # renaming the transform may rename the shape too; re-resolve it
        shapes = cmds.listRelatives(transform, shapes=True, type="imagePlane") or []
        if not shapes:
            shapes = cmds.listRelatives(transform, shapes=True) or []
        if shapes:
            shape = shapes[0]
        # 25% width, top-left; image aspect preserved by the plane's width/height
        for attr, value in (("displayMode", 3), ("sizeX", 0.354), ("sizeY", 0.257),
                            ("offsetX", -0.50), ("offsetY", 0.24), ("depth", 100),
                            ("visibility", 1)):
            if cmds.attributeQuery(attr, node=shape, exists=True):
                try:
                    cmds.setAttr(shape + "." + attr, value)
                except Exception:
                    pass
        try:
            cmds.editDisplayLayerMembers(layer, [transform, shape], noRecurse=True)
        except Exception:
            pass
        report["planes"].append({"shot": label, "camera": cam, "png": path,
                                 "shape": shape, "visibility": cmds.getAttr(shape + ".visibility")})
    try:
        cmds.setAttr(layer + ".visibleInRendering", 0)
    except Exception:
        pass
    cmds.file(rename=REF)
    cmds.file(save=True, type="mayaBinary", force=True)
    report["scene"] = REF
    report["saved"] = True
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print("REFPLANES_DONE")


if __name__ == "__main__":
    main()
