"""Build the Office Spider layout for storyboard shots 62-66.

Base: opened David rig source (its rig setup runs on open; importing collapses
the head). Spider is referenced from C_Spider.ma. Set, props, cameras and
animation are generated here. The source .mb is never saved over.

Output:
  G:/film-304-toon-spine/Saved/Scenes/Shepherd_Brennan_LayoutScene(62-66)_BS_v01.mb
  G:/film-304-toon-spine/Saved/Scenes/layout_62_66_v2_report.json
"""
from __future__ import annotations

import json
import math
import traceback

import maya.cmds as cmds

ROOT = "G:/film-304-toon-spine"
DAVID_SRC = ROOT + "/Saved/OfflineIntake/Source/David_Rig_v1.51.mb"
SPIDER_SRC = ROOT + "/Saved/OfflineIntake/Source/C_Spider.ma"
TITLE_PNG = ROOT + "/Saved/Scenes/layout_title_15mins.png"
ARROW_PNG = ROOT + "/Saved/Scenes/layout_arrow_right.png"
OUT_SCENE = ROOT + "/Saved/Scenes/Shepherd_Brennan_LayoutScene(62-66)_BS_v02.mb"
OUT_JSON = ROOT + "/Saved/Scenes/layout_62_66_v2_report.json"

FPS = 24
DAVID_TARGET_HEIGHT = 180.0
SPIDER_SCALE = 3.6

# Timeline (frames inclusive)
SHOTS = {
    "62":   (1, 48),
    "63A":  (49, 72),
    "63B":  (73, 120),
    "64A":  (121, 144),
    "64B":  (145, 192),
    "65":   (193, 216),
    "66A":  (217, 240),
    "66B":  (241, 288),
}


def ensure_visible(node: str, visible: bool = True) -> None:
    if not cmds.objExists(node):
        return
    conns = cmds.listConnections(node + ".visibility", source=True, destination=False) or []
    for c in conns:
        for plug in ("outValue", "output", "visibility"):
            try:
                cmds.disconnectAttr(c + "." + plug, node + ".visibility")
                break
            except Exception:
                continue
    try:
        cmds.setAttr(node + ".visibility", lock=False)
    except Exception:
        pass
    try:
        cmds.setAttr(node + ".visibility", visible)
    except Exception:
        pass


def visible_bbox(prefix: str | None = None):
    meshes = []
    for m in cmds.ls(type="mesh", long=True) or []:
        name = m.split("|")[-1]
        if "Orig" in name or "Base" in name:
            continue
        tr = (cmds.listRelatives(m, parent=True) or [m])[0]
        if prefix and not (tr.startswith(prefix) or name.startswith(prefix)):
            continue
        try:
            if cmds.getAttr(tr + ".visibility"):
                meshes.append(m)
        except Exception:
            pass
    if not meshes:
        return None
    return [round(v, 2) for v in cmds.exactWorldBoundingBox(meshes)]


def make_material(name: str, color):
    mat = cmds.shadingNode("lambert", asShader=True, name=name)
    cmds.setAttr(mat + ".color", color[0], color[1], color[2], type="double3")
    return mat


def assign_material(mat: str, nodes) -> None:
    sgs = cmds.listConnections(mat, type="shadingEngine") or []
    sg = sgs[0] if sgs else None
    if not sg:
        sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=mat + "_SG")
        cmds.connectAttr(mat + ".outColor", sg + ".surfaceShader")
    for n in nodes:
        try:
            cmds.sets(n, edit=True, forceElement=sg)
        except Exception:
            pass


def create_camera(name: str, eye, target, focal: float):
    cam = cmds.camera(name=name)[0]
    cmds.setAttr(cam + ".focalLength", focal)
    cmds.setAttr(cam + ".filmFit", 1)  # horizontal
    cmds.setAttr(cam + ".horizontalFilmAperture", 1.417)  # inches = 36 mm
    cmds.setAttr(cam + ".verticalFilmAperture", 0.797)
    cmds.xform(cam, ws=True, t=eye)
    loc = cmds.spaceLocator(name=name + "_Target")[0]
    cmds.xform(loc, ws=True, t=target)
    cmds.aimConstraint(loc, cam, aimVector=(0, 0, -1), upVector=(0, 1, 0),
                       worldUpType="vector", worldUpVector=(0, 1, 0))
    return cam


def reset_fk() -> None:
    for c in cmds.ls("*:FK*", type="transform") or []:
        for attr in ("translateX", "translateY", "translateZ",
                     "rotateX", "rotateY", "rotateZ"):
            if not cmds.attributeQuery(attr, node=c, exists=True):
                continue
            try:
                if not cmds.getAttr(c + "." + attr, lock=True):
                    cmds.setAttr(c + "." + attr, 0)
            except Exception:
                pass


def set_rot(ctrl: str, rx=0.0, ry=0.0, rz=0.0) -> None:
    if not cmds.objExists(ctrl):
        return
    for attr, val in (("rotateX", rx), ("rotateY", ry), ("rotateZ", rz)):
        if cmds.attributeQuery(attr, node=ctrl, exists=True):
            try:
                if not cmds.getAttr(ctrl + "." + attr, lock=True):
                    cmds.setAttr(ctrl + "." + attr, val)
            except Exception:
                pass


def key_rot(ctrl: str, frame: int, rx=0.0, ry=0.0, rz=0.0) -> None:
    if not cmds.objExists(ctrl):
        return
    for attr, val in (("rotateX", rx), ("rotateY", ry), ("rotateZ", rz)):
        if cmds.attributeQuery(attr, node=ctrl, exists=True):
            try:
                cmds.setAttr(ctrl + "." + attr, val)
                cmds.setKeyframe(ctrl, attribute=attr, time=frame)
            except Exception:
                pass


def base_pose():
    set_rot("David:FKSpine1_M", 0, 0, 0)
    set_rot("David:FKSpine2_M", 0, 0, 0)
    set_rot("David:FKChest_M", 0, 0, 0)
    set_rot("David:FKNeck_M", 0, 0, 0)
    set_rot("David:FKHead_M", 0, 0, 0)
    set_rot("David:FKShoulder_L", 0, 70, 8)
    set_rot("David:FKShoulder_R", 0, 70, -8)
    set_rot("David:FKElbow_L", 0, 25, 0)
    set_rot("David:FKElbow_R", 0, 25, 0)
    set_rot("David:FKWrist_L", 0, 0, 0)
    set_rot("David:FKWrist_R", 0, 0, 0)
    set_rot("David:FKJaw_M", 0, 0, 0)


def pose_angry():
    base_pose()
    set_rot("David:FKSpine1_M", 4, 0, 0)
    set_rot("David:FKChest_M", 3, 0, 0)
    set_rot("David:FKNeck_M", 4, 0, 0)
    set_rot("David:FKHead_M", 6, -8, 0)
    set_rot("David:FKShoulder_L", 0, 55, 12)
    set_rot("David:FKShoulder_R", 0, 55, -12)
    set_rot("David:FKElbow_L", 0, 40, 0)
    set_rot("David:FKElbow_R", 0, 40, 0)


def pose_rage():
    base_pose()
    set_rot("David:FKSpine1_M", 2, 0, 0)
    set_rot("David:FKChest_M", -4, 0, 0)
    set_rot("David:FKNeck_M", -2, 0, 0)
    set_rot("David:FKHead_M", -4, -6, 0)
    set_rot("David:FKShoulder_L", 0, 45, 18)
    set_rot("David:FKShoulder_R", 0, 45, -18)
    set_rot("David:FKElbow_L", 0, 55, 0)
    set_rot("David:FKElbow_R", 0, 55, 0)
    if cmds.objExists("David:FKJaw_M"):
        set_rot("David:FKJaw_M", 22, 0, 0)
    if cmds.objExists("BM_Regions"):
        try:
            cmds.setAttr("BM_Regions.David_BMH_JawOpen", 0.65)
        except Exception:
            pass


def pose_ready():
    base_pose()
    set_rot("David:FKSpine1_M", 12, 0, 0)
    set_rot("David:FKChest_M", 6, 0, 0)
    set_rot("David:FKNeck_M", -6, 0, 0)
    set_rot("David:FKHead_M", -8, 0, 0)
    set_rot("David:FKShoulder_L", 0, 10, 25)
    set_rot("David:FKShoulder_R", 0, 10, -25)
    set_rot("David:FKElbow_L", 0, 15, 0)
    set_rot("David:FKElbow_R", 0, 15, 0)


def pose_run():
    base_pose()
    set_rot("David:FKSpine1_M", 18, 0, 0)
    set_rot("David:FKChest_M", 8, 0, 0)
    set_rot("David:FKNeck_M", -10, 0, 0)
    set_rot("David:FKHead_M", -10, 0, 0)
    set_rot("David:FKShoulder_L", 0, 55, 35)
    set_rot("David:FKShoulder_R", 0, 55, -35)
    set_rot("David:FKElbow_L", 0, 75, 0)
    set_rot("David:FKElbow_R", 0, 75, 0)


def pose_startled():
    base_pose()
    set_rot("David:FKSpine1_M", -10, 0, 0)
    set_rot("David:FKChest_M", -8, 0, 0)
    set_rot("David:FKNeck_M", 8, 0, 0)
    set_rot("David:FKHead_M", 12, 0, 0)
    set_rot("David:FKShoulder_L", 0, 40, 30)
    set_rot("David:FKShoulder_R", 0, 40, -30)
    set_rot("David:FKElbow_L", 0, 60, 0)
    set_rot("David:FKElbow_R", 0, 60, 0)


def key_visibility(node: str, frame: int, value: int) -> None:
    if not cmds.objExists(node):
        return
    try:
        cmds.setAttr(node + ".visibility", value)
        cmds.setKeyframe(node, attribute="visibility", time=frame)
    except Exception:
        pass


def main() -> None:
    report = {"shots": SHOTS, "steps": []}
    try:
        # --- Base scene: reference both characters ---
        cmds.file(new=True, force=True)
        cmds.currentUnit(linear="centimeter")
        cmds.currentUnit(time="film")
        cmds.playbackOptions(minTime=1, maxTime=288, animationStartTime=1, animationEndTime=288)

        try:
            cmds.file(DAVID_SRC, reference=True, namespace="David", ignoreVersion=True,
                      mergeNamespacesOnClash=False)
            report["david_reference"] = True
        except Exception:
            report["david_reference_error"] = traceback.format_exc()

        try:
            cmds.file(SPIDER_SRC, reference=True, namespace="Spider", ignoreVersion=True,
                      mergeNamespacesOnClash=False, type="mayaAscii")
            report["spider_reference"] = True
        except Exception:
            report["spider_reference_error"] = traceback.format_exc()

        for rn in cmds.ls(type="reference") or []:
            try:
                cmds.setAttr(rn + ".relativePath", True)
            except Exception:
                pass

        # --- David root / scale / position ---
        # Do NOT reset FK controls here: the referenced source opens in its
        # correct default pose; zeroing FKHead/Neck collapses the head.
        for n in cmds.ls("*:David_Body_breathe", type="transform") or []:
            ensure_visible(n, False)
        for n in cmds.ls("*:David_Body_GEOBase*", type="transform") or []:
            ensure_visible(n, False)

        david_root = cmds.createNode("transform", name="Layout_David_Root")
        cmds.parent("David:Group", david_root, absolute=True)
        b0 = visible_bbox()
        height0 = b0[4] - b0[1]
        dscale = DAVID_TARGET_HEIGHT / height0
        cmds.setAttr(david_root + ".scale", dscale, dscale, dscale)
        cmds.refresh(force=True)
        b1 = visible_bbox()
        cmds.setAttr(david_root + ".translateY", -b1[1])
        cmds.setAttr(david_root + ".translateX", -(b1[0] + b1[3]) / 2.0)
        cmds.setAttr(david_root + ".translateZ", -(b1[2] + b1[5]) / 2.0)
        cmds.refresh(force=True)
        report["david_scale"] = round(dscale, 4)
        report["david_bbox_positioned"] = visible_bbox()

        # --- Spider root / scale / position ---
        spider_top = None
        for n in cmds.ls("Spider:*", type="transform") or []:
            if n.endswith("wolfSpiderRig"):
                spider_top = n
                break
        if not spider_top:
            spider_top = "Spider:wolfSpiderRig" if cmds.objExists("Spider:wolfSpiderRig") else None
        report["spider_top"] = spider_top
        spider_root = None
        if spider_top:
            spider_root = cmds.createNode("transform", name="Layout_Spider_Root")
            cmds.parent(spider_top, spider_root, absolute=True)
            cmds.setAttr(spider_root + ".scale", SPIDER_SCALE, SPIDER_SCALE, SPIDER_SCALE)
            cmds.setAttr(spider_root + ".translateX", -25)
            cmds.setAttr(spider_root + ".translateY", 250)
            cmds.setAttr(spider_root + ".translateZ", 0)
            cmds.refresh(force=True)
            report["spider_bbox"] = visible_bbox("Spider")

        # --- Set ---
        set_grp = cmds.createNode("transform", name="Layout_Office_Set")
        gray = make_material("Layout_Gray", (0.62, 0.62, 0.62))
        mid = make_material("Layout_Mid", (0.36, 0.36, 0.38))
        dark = make_material("Layout_Dark", (0.18, 0.18, 0.2))
        red = make_material("Layout_Red", (0.72, 0.08, 0.06))
        white = make_material("Layout_White", (0.92, 0.92, 0.9))
        black = make_material("Layout_Black", (0.02, 0.02, 0.02))

        floor = cmds.polyPlane(name="Layout_Floor", width=900, height=900)[0]
        cmds.parent(floor, set_grp)
        assign_material(gray, [floor])

        wall = cmds.polyPlane(name="Layout_BackWall", width=900, height=420)[0]
        cmds.xform(wall, ws=True, t=(0, 210, -190), ro=(90, 0, 0))
        cmds.parent(wall, set_grp)
        assign_material(gray, [wall])

        desk = cmds.polyCube(name="Layout_Desk", width=160, height=6, depth=70)[0]
        cmds.xform(desk, ws=True, t=(0, 75, 0))
        cmds.parent(desk, set_grp)
        assign_material(gray, [desk])
        for i, (x, z) in enumerate([(70, 28), (70, -28), (-70, 28), (-70, -28)]):
            leg = cmds.polyCylinder(name=f"Layout_DeskLeg_{i}", radius=3, height=75)[0]
            cmds.xform(leg, ws=True, t=(x, 37.5, z))
            cmds.parent(leg, set_grp)
            assign_material(dark, [leg])

        # Side shelf for the spray can
        shelf = cmds.polyCube(name="Layout_Shelf", width=60, height=6, depth=50)[0]
        cmds.xform(shelf, ws=True, t=(-110, 90, 15))
        cmds.parent(shelf, set_grp)
        assign_material(gray, [shelf])
        shelf_leg = cmds.polyCylinder(name="Layout_ShelfLeg", radius=3, height=90)[0]
        cmds.xform(shelf_leg, ws=True, t=(-110, 45, 15))
        cmds.parent(shelf_leg, set_grp)
        assign_material(dark, [shelf_leg])

        # Swatter flat on the desk: handle along +X, white grid head.
        swatter = cmds.createNode("transform", name="Layout_Swatter")
        handle = cmds.polyCylinder(name="Layout_SwatterHandle", radius=0.8, height=28)[0]
        cmds.xform(handle, ws=True, t=(0, 0, 0), ro=(0, 0, 90))
        head = cmds.polyCube(name="Layout_SwatterHead", width=16, height=1, depth=10)[0]
        cmds.xform(head, ws=True, t=(20, 0, 0))
        cmds.parent(handle, swatter)
        cmds.parent(head, swatter)
        assign_material(white, [head])
        assign_material(dark, [handle])
        for i in range(3):
            bar = cmds.polyCube(name=f"Layout_SwatterBar_{i}", width=16, height=0.2, depth=0.6)[0]
            cmds.xform(bar, ws=True, t=(20, 0.7, -3 + i * 3))
            cmds.parent(bar, swatter)
            assign_material(dark, [bar])
        cmds.xform(swatter, ws=True, t=(20, 78.8, 5))
        cmds.parent(swatter, set_grp)

        # Spray can on the shelf
        can = cmds.createNode("transform", name="Layout_SprayCan")
        can_body = cmds.polyCylinder(name="Layout_CanBody", radius=6, height=20)[0]
        can_cap = cmds.polyCylinder(name="Layout_CanCap", radius=4, height=5)[0]
        cmds.xform(can_cap, ws=True, t=(0, 12, 0))
        cmds.parent(can_body, can)
        cmds.parent(can_cap, can)
        cmds.xform(can, ws=True, t=(-110, 103, 15))
        cmds.parent(can, set_grp)
        assign_material(red, [can_body])
        assign_material(black, [can_cap])

        # --- Door set ---
        door_grp = cmds.createNode("transform", name="Layout_Door_Set")
        for side, x in (("L", -67.5), ("R", 67.5)):
            post = cmds.polyCube(name=f"Layout_DoorPost_{side}", width=15, height=250, depth=12)[0]
            cmds.xform(post, ws=True, t=(x, 125, -400))
            cmds.parent(post, door_grp)
            assign_material(dark, [post])
        lintel = cmds.polyCube(name="Layout_DoorLintel", width=150, height=15, depth=12)[0]
        cmds.xform(lintel, ws=True, t=(0, 257.5, -400))
        cmds.parent(lintel, door_grp)
        assign_material(dark, [lintel])
        # Door panel, hinged on its left edge.
        hinge = cmds.createNode("transform", name="Layout_DoorHinge")
        cmds.xform(hinge, ws=True, t=(-55, 0, -395))
        door = cmds.polyCube(name="Layout_DoorPanel", width=110, height=220, depth=5)[0]
        cmds.parent(door, hinge)
        cmds.xform(door, ws=True, t=(0, 110, -395))
        cmds.parent(hinge, door_grp)
        assign_material(mid, [door])
        door_floor = cmds.polyPlane(name="Layout_DoorFloor", width=260, height=300)[0]
        cmds.xform(door_floor, ws=True, t=(0, 0, -400))
        cmds.parent(door_floor, door_grp)
        assign_material(mid, [door_floor])
        door_wall = cmds.polyPlane(name="Layout_DoorWall", width=500, height=300)[0]
        cmds.xform(door_wall, ws=True, t=(0, 150, -430), ro=(90, 0, 0))
        cmds.parent(door_wall, door_grp)
        assign_material(mid, [door_wall])

        # Arrow card on the wall for 66A
        arrow_plane = cmds.polyPlane(name="Layout_Arrow", width=45, height=45)[0]
        cmds.xform(arrow_plane, ws=True, t=(45, 160, -394))
        cmds.parent(arrow_plane, door_grp)
        arrow_mat = cmds.shadingNode("surfaceShader", asShader=True, name="Layout_ArrowMat")
        arrow_file = cmds.shadingNode("file", asTexture=True, name="Layout_ArrowFile")
        cmds.setAttr(arrow_file + ".fileTextureName", ARROW_PNG, type="string")
        cmds.connectAttr(arrow_file + ".outColor", arrow_mat + ".outColor")
        assign_material(arrow_mat, [arrow_plane])

        # --- Title card ---
        title_plane = cmds.polyPlane(name="Layout_TitleCard", width=300, height=168)[0]
        cmds.xform(title_plane, ws=True, t=(0, 150, -120))
        title_mat = cmds.shadingNode("surfaceShader", asShader=True, name="Layout_TitleMat")
        title_file = cmds.shadingNode("file", asTexture=True, name="Layout_TitleFile")
        cmds.setAttr(title_file + ".fileTextureName", TITLE_PNG, type="string")
        cmds.connectAttr(title_file + ".outColor", title_mat + ".outColor")
        assign_material(title_mat, [title_plane])

        # --- Exterminator proxy ---
        ex_grp = cmds.createNode("transform", name="Layout_Exterminator")
        parts = []
        torso = cmds.polyCylinder(name="Layout_ExTorso", radius=26, height=100)[0]
        cmds.xform(torso, ws=True, t=(0, 105, 0))
        parts.append(torso)
        shoulders = cmds.polyCube(name="Layout_ExShoulders", width=95, height=25, depth=35)[0]
        cmds.xform(shoulders, ws=True, t=(0, 150, 0))
        parts.append(shoulders)
        head = cmds.polySphere(name="Layout_ExHead", radius=22)[0]
        cmds.xform(head, ws=True, t=(0, 177, 0))
        parts.append(head)
        cap = cmds.polyCylinder(name="Layout_ExCap", radius=24, height=7)[0]
        cmds.xform(cap, ws=True, t=(0, 196, 0))
        parts.append(cap)
        brim = cmds.polyCylinder(name="Layout_ExBrim", radius=33, height=2)[0]
        cmds.xform(brim, ws=True, t=(0, 192, 5))
        parts.append(brim)
        for side, x in (("L", 38), ("R", -38)):
            arm = cmds.polyCylinder(name=f"Layout_ExArm_{side}", radius=8, height=70)[0]
            cmds.xform(arm, ws=True, t=(x, 120, 0), ro=(0, 0, 35 if side == "L" else -35))
            parts.append(arm)
        for side, x in (("L", 18), ("R", -18)):
            leg = cmds.polyCylinder(name=f"Layout_ExLeg_{side}", radius=12, height=70)[0]
            cmds.xform(leg, ws=True, t=(x, 35, 0))
            parts.append(leg)
            boot = cmds.polyCube(name=f"Layout_ExBoot_{side}", width=22, height=10, depth=32)[0]
            cmds.xform(boot, ws=True, t=(x, 5, 8))
            parts.append(boot)
        for p in parts:
            cmds.parent(p, ex_grp)
        cmds.xform(ex_grp, ws=True, t=(-10, 0, -430))
        assign_material(dark, parts)

        # --- Cameras ---
        cams = {
            "62": create_camera("Cam_Shot62", (0, 95, 170), (0, 88, 5), 50),
            "63A": create_camera("Cam_Shot63A", (50, 168, 260), (0, 158, 0), 65),
            "63B": create_camera("Cam_Shot63B", (60, 162, 280), (0, 155, 0), 55),
            "64A": create_camera("Cam_Shot64A", (0, 120, 320), (0, 100, 0), 35),
            "64B": create_camera("Cam_Shot64B", (0, 125, 340), (40, 120, 0), 40),
            "65": create_camera("Cam_Shot65", (0, 150, 300), (0, 150, -120), 50),
            "66A": create_camera("Cam_Shot66A", (0, 140, -200), (0, 140, -400), 35),
            "66B": create_camera("Cam_Shot66B", (0, 90, -80), (0, 120, -400), 30),
        }
        report["cameras"] = {k: v for k, v in cams.items()}

        # --- Visibility cuts ---
        key_visibility(set_grp, 1, 1)
        key_visibility(set_grp, 193, 0)
        key_visibility(set_grp, 217, 0)
        key_visibility(door_grp, 1, 0)
        key_visibility(door_grp, 217, 1)
        key_visibility(door_grp, 241, 1)
        key_visibility(title_plane, 1, 0)
        key_visibility(title_plane, 193, 1)
        key_visibility(title_plane, 217, 0)
        key_visibility(arrow_plane, 1, 0)
        key_visibility(arrow_plane, 217, 1)
        key_visibility(arrow_plane, 241, 0)
        key_visibility(david_root, 1, 0)
        key_visibility(david_root, 49, 1)
        key_visibility(david_root, 193, 0)
        key_visibility(david_root, 241, 1)
        key_visibility(spider_root, 1, 1)
        key_visibility(spider_root, 49, 0)
        key_visibility(ex_grp, 1, 0)
        key_visibility(ex_grp, 241, 1)

        # --- Spider descent (shot 62) ---
        if spider_root:
            for f, y, x in ((1, 260, -60), (48, 105, -25)):
                cmds.setAttr(spider_root + ".translateY", y)
                cmds.setAttr(spider_root + ".translateX", x)
                cmds.setKeyframe(spider_root, attribute="translateY", time=f)
                cmds.setKeyframe(spider_root, attribute="translateX", time=f)

        # Silk thread from the ceiling down to the spider.
        thread = cmds.polyCylinder(name="Layout_SilkThread", radius=0.35, height=290)[0]
        cmds.xform(thread, ws=True, t=(-25, 250, 0))
        silk_mat = make_material("Layout_SilkMat", (0.86, 0.86, 0.82))
        assign_material(silk_mat, [thread])
        key_visibility(thread, 1, 1)
        key_visibility(thread, 49, 0)

        # --- David position per shot ---
        # 63/64: behind the desk, facing camera.
        for f in (49, 120):
            cmds.setAttr(david_root + ".translateX", 0)
            cmds.setAttr(david_root + ".translateY", 0)
            cmds.setAttr(david_root + ".translateZ", -70)
            cmds.setAttr(david_root + ".rotateY", 0)
            cmds.setKeyframe(david_root, attribute="translateX", time=f)
            cmds.setKeyframe(david_root, attribute="translateY", time=f)
            cmds.setKeyframe(david_root, attribute="translateZ", time=f)
            cmds.setKeyframe(david_root, attribute="rotateY", time=f)
        # 64A: ready stance facing the can.
        for f in (121, 144):
            cmds.setAttr(david_root + ".translateX", 55)
            cmds.setAttr(david_root + ".translateZ", 0)
            cmds.setAttr(david_root + ".rotateY", -90)
            cmds.setKeyframe(david_root, attribute="translateX", time=f)
            cmds.setKeyframe(david_root, attribute="translateZ", time=f)
            cmds.setKeyframe(david_root, attribute="rotateY", time=f)
        # 64B: run to screen right.
        for f, x in ((145, 55), (192, 145)):
            cmds.setAttr(david_root + ".translateX", x)
            cmds.setAttr(david_root + ".translateZ", 0)
            cmds.setAttr(david_root + ".rotateY", -90)
            cmds.setKeyframe(david_root, attribute="translateX", time=f)
            cmds.setKeyframe(david_root, attribute="translateZ", time=f)
            cmds.setKeyframe(david_root, attribute="rotateY", time=f)
        # 66B: by the door, facing left toward the exterminator.
        for f in (241, 288):
            cmds.setAttr(david_root + ".translateX", 70)
            cmds.setAttr(david_root + ".translateY", 0)
            cmds.setAttr(david_root + ".translateZ", -360)
            cmds.setAttr(david_root + ".rotateY", -90)
            cmds.setKeyframe(david_root, attribute="translateX", time=f)
            cmds.setKeyframe(david_root, attribute="translateY", time=f)
            cmds.setKeyframe(david_root, attribute="translateZ", time=f)
            cmds.setKeyframe(david_root, attribute="rotateY", time=f)

        # --- David poses per shot (keyed at shot starts/ends) ---
        pose_frames = {
            "63A": (49, 72, pose_angry),
            "63B": (73, 120, pose_rage),
            "64A": (121, 144, pose_ready),
            "64B": (145, 192, pose_run),
            "66B": (241, 288, pose_startled),
        }
        for label, (f0, f1, fn) in pose_frames.items():
            fn()
            for c in cmds.ls("*:FK*", type="transform") or []:
                for attr in ("rotateX", "rotateY", "rotateZ"):
                    if cmds.attributeQuery(attr, node=c, exists=True):
                        try:
                            cmds.setKeyframe(c, attribute=attr, time=f0)
                            cmds.setKeyframe(c, attribute=attr, time=f1)
                        except Exception:
                            pass
        # Rage jaw beat
        if cmds.objExists("David:FKJaw_M"):
            for f, v in ((73, 0), (84, 22), (112, 22), (120, 0)):
                cmds.setAttr("David:FKJaw_M.rotateX", v)
                cmds.setKeyframe("David:FKJaw_M", attribute="rotateX", time=f)

        # --- Door slam (66B) ---
        hinge_name = "Layout_DoorHinge"
        for f, ang in ((240, 0), (252, -105), (288, -105)):
            cmds.setAttr(hinge_name + ".rotateY", ang)
            cmds.setKeyframe(hinge_name, attribute="rotateY", time=f)

        # --- Exterminator step-in (66B) ---
        for f, z in ((240, -430), (252, -390), (288, -390)):
            cmds.setAttr(ex_grp + ".translateZ", z)
            cmds.setKeyframe(ex_grp, attribute="translateZ", time=f)

        # --- Render settings ---
        try:
            cmds.setAttr("defaultRenderGlobals.currentRenderer", "mayaSoftware", type="string")
        except Exception:
            pass
        try:
            cmds.setAttr("defaultResolution.width", 1920)
            cmds.setAttr("defaultResolution.height", 1080)
            cmds.setAttr("defaultResolution.deviceAspectRatio", 16.0 / 9.0)
        except Exception:
            pass

        # Add a key light and fill for the set.
        key_shape = cmds.directionalLight(name="Layout_Key_Light", intensity=2.4)
        if isinstance(key_shape, (list, tuple)):
            key_shape = key_shape[0]
        key_tr = cmds.listRelatives(key_shape, parent=True)[0]
        cmds.setAttr(key_tr + ".rotateX", -35)
        cmds.setAttr(key_tr + ".rotateY", -25)
        fill_shape = cmds.directionalLight(name="Layout_Fill_Light", intensity=0.7)
        if isinstance(fill_shape, (list, tuple)):
            fill_shape = fill_shape[0]
        fill_tr = cmds.listRelatives(fill_shape, parent=True)[0]
        cmds.setAttr(fill_tr + ".rotateX", -15)
        cmds.setAttr(fill_tr + ".rotateY", 150)

        # Save
        cmds.file(rename=OUT_SCENE)
        cmds.file(save=True, type="mayaBinary", force=True)
        report["scene"] = OUT_SCENE
        report["ok"] = True
    except Exception:
        report["fatal"] = traceback.format_exc()
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print("LAYOUT_BUILD_DONE", json.dumps({k: report.get(k) for k in
          ("ok", "david_scale", "david_bbox_positioned", "fatal")}))


if __name__ == "__main__":
    main()
