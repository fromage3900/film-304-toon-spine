"""v04 storyboard-match pass: film-project props + board cameras/poses."""
from __future__ import annotations

import json
import os
import traceback

import maya.cmds as cmds

ROOT = "G:/film-304-toon-spine"
V03 = ROOT + "/Saved/Scenes/Shepherd_Brennan_LayoutScene(62-66)_BS_v03.mb"
V04 = ROOT + "/Saved/Scenes/Shepherd_Brennan_LayoutScene(62-66)_BS_v04_match.mb"
REPORT = ROOT + "/Saved/Scenes/layout_62_66_v04_match_report.json"
PROPS = ROOT + "/Content/Meshes/Office/Props/"
BREAK = ROOT + "/Content/Meshes/BreakRoom/Props/"

report = {"items": []}


def log(name, status, detail=""):
    report["items"].append({"name": name, "status": status, "detail": str(detail)[:1200]})


def hide(node, state=True):
    if cmds.objExists(node):
        try:
            cmds.setAttr(node + ".visibility", 0 if state else 1)
        except Exception:
            pass


def key(node, attr, frame, value):
    if not cmds.objExists(node) or not cmds.attributeQuery(attr, node=node, exists=True):
        return
    try:
        cmds.setAttr(node + "." + attr, value)
        cmds.setKeyframe(node, attribute=attr, time=frame)
    except Exception:
        pass


def set_cam(cam, target, eye, aim, focal, frames):
    if cmds.objExists(cam):
        cmds.setAttr(cam + ".focalLength", focal)
        cmds.xform(cam, ws=True, t=eye)
        if cmds.objExists(target):
            cmds.xform(target, ws=True, t=aim)
        for f in frames:
            for a, v in (("translateX", eye[0]), ("translateY", eye[1]), ("translateZ", eye[2])):
                key(cam, a, f, v)
            for a, v in (("translateX", aim[0]), ("translateY", aim[1]), ("translateZ", aim[2])):
                key(target, a, f, v)


def import_fbx(src, group):
    if not os.path.exists(src):
        raise RuntimeError("missing " + src)
    before = set(cmds.ls(assemblies=True) or [])
    cmds.file(src, i=True, type="FBX", ignoreVersion=True)
    after = set(cmds.ls(assemblies=True) or [])
    new = [n for n in (after - before) if n not in ("persp", "top", "front", "side", "left")]
    for n in new:
        try:
            cmds.parent(n, group, absolute=True)
        except Exception:
            pass
    return new


def main():
    cmds.file(V03, open=True, force=True, ignoreVersion=True)
    try:
        cmds.loadPlugin("fbxmaya", quiet=True)
    except Exception:
        pass
    cmds.currentTime(1)

    # --- Film props: desk + box ---
    props_grp = "Layout_Props_Film"
    if not cmds.objExists(props_grp):
        cmds.createNode("transform", name=props_grp)
    try:
        new = import_fbx(PROPS + "P_OfficeDesk_AC.fbx", props_grp)
        log("film desk", "pass", new)
    except Exception:
        log("film desk", "fail", traceback.format_exc()[-800:])
    # real desk is already 0..76 cm; hide the proxy desk
    for n in ["Layout_Desk"] + (cmds.ls("Layout_DeskLeg_*") or []):
        hide(n, True)
    try:
        new = import_fbx(PROPS + "P_Box_EF.fbx", props_grp)
        box = new[0] if new else None
        if box:
            cmds.xform(box, ws=True, t=(-110, 60, 15))
        log("film box", "pass", new)
    except Exception:
        log("film box", "fail", traceback.format_exc()[-800:])
    # stand under the box + can on top
    if not cmds.objExists("Layout_BoxStand"):
        stand = cmds.polyCube(name="Layout_BoxStand", width=10, height=60, depth=10)[0]
        cmds.xform(stand, ws=True, t=(-110, 30, 15))
        try: cmds.parent(stand, props_grp, absolute=True)
        except Exception: pass
    if cmds.objExists("Layout_SprayCan"):
        cmds.xform("Layout_SprayCan", ws=True, t=(-110, 89.5, 15))
    for n in ("Layout_Shelf", "Layout_ShelfLeg"):
        hide(n, True)
    # swatter on the real desk edge, left of center like the board
    if cmds.objExists("Layout_Swatter"):
        cmds.xform("Layout_Swatter", ws=True, t=(-10, 76.5, 5))

    # --- Hidden library of real office props (not in the Board 62-66 panels) ---
    lib = "Layout_Props_Film_Library"
    if not cmds.objExists(lib):
        cmds.createNode("transform", name=lib)
    for src in ("P_ComputerMonitor_AC.fbx", "P_Chair_KS.fbx", "P_ComputerTower_AC.fbx",
                "P_File_EF.fbx", "P_Lamp_EF.fbx", "P_StickyNotes_PMB.fbx", "P_Book_PMB.fbx"):
        try:
            new = import_fbx(PROPS + src, lib)
            log("library " + src, "pass", new)
        except Exception:
            log("library " + src, "fail", traceback.format_exc()[-500:])
    hide(lib, True)

    # --- Remove/hide the 20-item dressing that fights the board ---
    for n in ("Layout_MonitorBase", "Layout_MonitorStand", "Layout_MonitorScreen",
              "Layout_Keyboard", "Layout_DeskMug", "Layout_Chair", "Layout_ChairBack"):
        hide(n, True)
    for n in cmds.ls("Layout_Paper_*") or []:
        hide(n, True)

    # --- Camera match ---
    set_cam("Cam_Shot62", "Cam_Shot62_Target", (0, 95, 120), (0, 85, 10), 65, (1, 48))
    set_cam("Cam_Shot63A1", "Cam_Shot63A_Target", (50, 168, 150), (0, 160, 0), 85, (49, 72))
    set_cam("Cam_Shot63B1", "Cam_Shot63B_Target", (55, 165, 160), (0, 158, 0), 75, (73, 120))
    set_cam("Cam_Shot64A1", "Cam_Shot64A_Target", (0, 95, 330), (0, 95, 0), 35, (121, 144))
    set_cam("Cam_Shot64B1", "Cam_Shot64B_Target", (0, 105, 340), (40, 100, 0), 40, (145, 192))
    set_cam("Cam_Shot66A1", "Cam_Shot66A_Target", (0, 120, -200), (0, 140, -400), 35, (217, 240))
    set_cam("Cam_Shot66B1", "Cam_Shot66B_Target", (0, 30, -160), (0, 130, -400), 28, (241, 288))

    # --- 62: spider/thread at the swatter axis ---
    if cmds.objExists("Layout_Spider_Root"):
        for f, x, y in ((1, 0, 260), (24, 0, 185), (40, 0, 108), (44, 0, 112), (48, 0, 105)):
            key("Layout_Spider_Root", "translateX", f, x)
            key("Layout_Spider_Root", "translateY", f, y)
    if cmds.objExists("Layout_SilkThread"):
        cmds.xform("Layout_SilkThread", ws=True, t=(0, 250, 0))

    # --- 64A ready stance: arms out, feet wide ---
    for f in (121, 144):
        for c, a, v in (("David:FKShoulder_L", "rotateY", 0), ("David:FKShoulder_R", "rotateY", 0),
                        ("David:FKElbow_L", "rotateY", 20), ("David:FKElbow_R", "rotateY", 20),
                        ("David:FKSpine1_M", "rotateX", 10), ("David:FKChest_M", "rotateX", 5),
                        ("David:FKHead_M", "rotateX", -8)):
            key(c, a, f, v)
    for side, z in (("L", 12), ("R", -12)):
        node = "David:IKLegHandle_" + side
        for f in (121, 144):
            key(node, "translateZ", f, z)
            key(node, "translateY", f, 0)
    # --- 64B arm swing (legs already keyed in v03) ---
    for f in (145, 192):
        for c, a, v in (("David:FKShoulder_L", "rotateY", 55), ("David:FKShoulder_R", "rotateY", 55),
                        ("David:FKShoulder_L", "rotateZ", 45), ("David:FKShoulder_R", "rotateZ", -45),
                        ("David:FKElbow_L", "rotateY", 75), ("David:FKElbow_R", "rotateY", 75)):
            key(c, a, f, v)

    # --- 66A: open/hide the door panel, use a simple black arrow ---
    if cmds.objExists("Layout_DoorPanel"):
        for f, v in ((217, 0), (239, 0), (240, 1), (288, 1)):
            key("Layout_DoorPanel", "visibility", f, v)
    hide("Layout_Arrow", True)
    if not cmds.objExists("Layout_ArrowMesh"):
        grp = cmds.createNode("transform", name="Layout_ArrowMesh")
        shaft = cmds.polyCube(name="Layout_ArrowShaft", width=24, height=2, depth=0.6)[0]
        cmds.parent(shaft, grp)
        for i, rot in enumerate((45, -45)):
            head = cmds.polyCube(name="Layout_ArrowHead_%d" % i, width=10, height=2, depth=0.6)[0]
            cmds.xform(head, ws=True, t=(10, 3 if i == 0 else -3, 0), ro=(0, 0, rot))
            cmds.parent(head, grp)
        cmds.xform(grp, ws=True, t=(20, 190, -394))
        if cmds.objExists("Layout_Door_Set"):
            try: cmds.parent(grp, "Layout_Door_Set", absolute=True)
            except Exception: pass
        m = cmds.shadingNode("lambert", asShader=True, name="Layout_ArrowBlack")
        cmds.setAttr(m + ".color", 0.02, 0.02, 0.02, type="double3")
        sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="Layout_ArrowBlack_SG")
        cmds.connectAttr(m + ".outColor", sg + ".surfaceShader")
        for n in (grp, shaft) + tuple(cmds.listRelatives(grp, children=True, type="transform") or []):
            try: cmds.sets(n, edit=True, forceElement=sg)
            except Exception: pass

    # Save
    cmds.currentTime(1)
    cmds.file(rename=V04)
    cmds.file(save=True, type="mayaBinary", force=True)
    report["scene"] = V04
    report["saved"] = True
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print("V04_MATCH_DONE")


if __name__ == "__main__":
    main()
