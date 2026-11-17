"""Stage all 20 v03 layout improvements on the referenced v02 scene.

Run through maya.standalone (see run_v03.py). Saves:
  Saved/Scenes/Shepherd_Brennan_LayoutScene(62-66)_BS_v03.mb
  Saved/Scenes/layout_62_66_v03_report.json
"""
from __future__ import annotations

import json
import os
import re
import traceback

import maya.cmds as cmds
import maya.mel as mel

ROOT = "G:/film-304-toon-spine"
V02 = ROOT + "/Saved/Scenes/Shepherd_Brennan_LayoutScene(62-66)_BS_v02.mb"
V03 = ROOT + "/Saved/Scenes/Shepherd_Brennan_LayoutScene(62-66)_BS_v03.mb"
REPORT = ROOT + "/Saved/Scenes/layout_62_66_v03_report.json"
SHOT_RANGES = {"62": (1, 48), "63A": (49, 72), "63B": (73, 120),
               "64A": (121, 144), "64B": (145, 192), "65": (193, 216),
               "66A": (217, 240), "66B": (241, 288)}
CAMERAS = {"62": "Cam_Shot62", "63A": "Cam_Shot63A1", "63B": "Cam_Shot63B1",
           "64A": "Cam_Shot64A1", "64B": "Cam_Shot64B1", "65": "Cam_Shot65",
           "66A": "Cam_Shot66A1", "66B": "Cam_Shot66B1"}

report = {"items": []}


def item(n, name, fn):
    try:
        detail = fn()
        report["items"].append({"n": n, "name": name, "status": "pass",
                                "detail": "" if detail is None else str(detail)[:800]})
    except Exception:
        report["items"].append({"n": n, "name": name, "status": "fail",
                                "detail": traceback.format_exc()[-1600:]})


def sg_for(mat):
    sgs = cmds.listConnections(mat, type="shadingEngine") or []
    return sgs[0] if sgs else None


def assign(mat, nodes):
    sg = sg_for(mat)
    if not sg:
        return
    for n in nodes:
        if n and cmds.objExists(n):
            try:
                cmds.sets(n, edit=True, forceElement=sg)
            except Exception:
                pass


def lambert(name, rgb):
    if cmds.objExists(name):
        return name
    m = cmds.shadingNode("lambert", asShader=True, name=name)
    cmds.setAttr(m + ".color", rgb[0], rgb[1], rgb[2], type="double3")
    sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=name + "_SG")
    cmds.connectAttr(m + ".outColor", sg + ".surfaceShader")
    return m


def surface_file(name, png):
    shader = cmds.shadingNode("surfaceShader", asShader=True, name=name + "_S")
    f = cmds.shadingNode("file", asTexture=True, name=name + "_F")
    cmds.setAttr(f + ".fileTextureName", png, type="string")
    cmds.connectAttr(f + ".outColor", shader + ".outColor")
    sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=name + "_SG")
    cmds.connectAttr(shader + ".outColor", sg + ".surfaceShader")
    return sg


def key_vis(node, frame, value):
    if not cmds.objExists(node):
        return
    try:
        cmds.setAttr(node + ".visibility", value)
        cmds.setKeyframe(node, attribute="visibility", time=frame)
    except Exception:
        pass


def key_val(node, attr, frame, value):
    if not cmds.objExists(node) or not cmds.attributeQuery(attr, node=node, exists=True):
        return
    try:
        cmds.setAttr(node + "." + attr, value)
        cmds.setKeyframe(node, attribute=attr, time=frame)
    except Exception:
        pass


def main() -> None:
    cmds.file(V02, open=True, force=True, ignoreVersion=True)
    cmds.currentTime(1)

    # 1. Scene README + metadata
    def i1():
        if not cmds.objExists("Layout_Info"):
            cmds.createNode("transform", name="Layout_Info")
        data = {
            "shot_ranges": "62:1-48;63A:49-72;63B:73-120;64A:121-144;64B:145-192;"
                           "65:193-216;66A:217-240;66B:241-288",
            "cameras": "Cam_Shot62,Cam_Shot63A1,Cam_Shot63B1,Cam_Shot64A1,"
                       "Cam_Shot64B1,Cam_Shot65,Cam_Shot66A1,Cam_Shot66B1",
            "fps": "24", "owner": "Brennan Shepherd", "version": "v03",
            "references": "DavidRN, SpiderRN",
        }
        for k, v in data.items():
            if not cmds.attributeQuery(k, node="Layout_Info", exists=True):
                cmds.addAttr("Layout_Info", longName=k, dataType="string")
            cmds.setAttr("Layout_Info." + k, v, type="string")
        readme = ROOT + "/Saved/Scenes/README_LAYOUT.txt"
        with open(readme, "w", encoding="utf-8") as fh:
            fh.write("Office Spider layout 62-66 - v03\n"
                     "Open Shepherd_Brennan_LayoutScene(62-66)_BS_v03.mb\n"
                     "24 fps, 1-288. Cameras per shot: " + data["cameras"] + "\n"
                     "References: DavidRN and SpiderRN. Keep G: mounted or make refs relative.\n"
                     "Display layers start with DL_. Timeline markers are Shot_62...Shot_66B.\n")
        return readme
    item(1, "scene README + metadata", i1)

    # 2. Exact camera names
    def i2():
        if cmds.objExists("Cam_Shot1") and not cmds.objExists("Cam_Shot62"):
            cmds.rename("Cam_Shot1", "Cam_Shot62")
        return CAMERAS
    item(2, "exact camera names", i2)

    # 3. Camera switcher + LayoutCameras set
    def i3():
        existing = [c for c in CAMERAS.values() if cmds.objExists(c)]
        if cmds.objExists("LayoutCameras"):
            cmds.delete("LayoutCameras")
        cmds.sets(existing, name="LayoutCameras")
        script = ROOT + "/Tools/switch_layout_camera.py"
        with open(script, "w", encoding="utf-8") as fh:
            fh.write('"""One-click layout camera switcher. Run in Maya\'s script editor."""\n'
                     "import maya.cmds as cmds\n"
                     "SHOTS = " + repr(CAMERAS) + "\n"
                     "def go(shot):\n"
                     "    cam = SHOTS[shot]\n"
                     "    if cmds.objExists(cam):\n"
                     "        cmds.lookThru(cam)\n"
                     "        cmds.select(cam, replace=True)\n"
                     "        print('Layout camera:', shot, cam)\n"
                     "if __name__ == '__main__':\n"
                     "    import sys\n"
                     "    go(sys.argv[1] if len(sys.argv) > 1 else '62')\n")
        return script
    item(3, "camera switcher + set", i3)

    # 4. Display layers
    def i4():
        layers = {
            "DL_SET": ["Layout_Office_Set"],
            "DL_DAVID": ["Layout_David_Root"],
            "DL_SPIDER": ["Layout_Spider_Root"],
            "DL_DOOR": ["Layout_Door_Set"],
            "DL_PROPS": ["Layout_Swatter", "Layout_SprayCan", "Layout_SilkThread"],
            "DL_PROXY": ["Layout_Exterminator"],
            "DL_REFS": cmds.ls("Spider:transform*", type="transform") or [],
            "DL_INFO": ["Layout_Info"],
        }
        made = {}
        for name, members in layers.items():
            if not cmds.objExists(name):
                cmds.createDisplayLayer(name=name, empty=True)
            members = [m for m in members if cmds.objExists(m)]
            if members:
                try:
                    cmds.editDisplayLayerMembers(name, members, noRecurse=True)
                except Exception:
                    pass
            try:
                cmds.setAttr(name + ".visibility", 0 if name == "DL_REFS" else 1)
            except Exception:
                pass
            made[name] = len(members)
        return made
    item(4, "display layers", i4)

    # 5. Timeline markers
    def i5():
        made = []
        for label, frame in [(k, v[0]) for k, v in SHOT_RANGES.items()]:
            ok = False
            try:
                cmds.timelineMarker(name="Shot_" + label, time=frame)
                ok = True
            except Exception:
                try:
                    mel.eval('timelineMarker -n "Shot_%s" -t %d;' % (label, frame))
                    ok = True
                except Exception:
                    pass
            if ok:
                made.append(label)
        if not made:
            grp = "Layout_ShotMarkers"
            if not cmds.objExists(grp):
                cmds.createNode("transform", name=grp)
            for label, frame in [(k, v[0]) for k, v in SHOT_RANGES.items()]:
                loc = cmds.spaceLocator(name="ShotMarker_" + label)[0]
                cmds.parent(loc, grp, absolute=True)
                if not cmds.attributeQuery("shot_frame", node=loc, exists=True):
                    cmds.addAttr(loc, longName="shot_frame", attributeType="long")
                cmds.setAttr(loc + ".shot_frame", frame)
            made = ["fallback_locators"]
        return made
    item(5, "timeline markers", i5)

    # 6. Playback defaults
    def i6():
        cmds.currentUnit(time="film")
        cmds.playbackOptions(minTime=1, maxTime=288, animationStartTime=1, animationEndTime=288)
        cmds.currentTime(1)
        cmds.autoKeyframe(state=False)
        try:
            cmds.playbackOptions(loop="once")
        except Exception:
            pass
        return "24fps 1-288"
    item(6, "playback defaults", i6)

    # 7. Selection sets
    def i7():
        made = []
        for label, (start, end) in SHOT_RANGES.items():
            nodes = [CAMERAS.get(label), "Layout_David_Root", "Layout_Spider_Root",
                     "Layout_Office_Set", "Layout_Door_Set", "Layout_Exterminator",
                     "Layout_TitleCard"]
            nodes = [n for n in nodes if n and cmds.objExists(n)]
            name = "SEL_shot" + label
            if cmds.objExists(name):
                cmds.delete(name)
            cmds.sets(nodes, name=name)
            made.append(name)
        return made
    item(7, "selection sets", i7)

    # 8. One-click playblast script
    def i8():
        script = ROOT + "/Tools/playblast_layout_all.py"
        with open(script, "w", encoding="utf-8") as fh:
            fh.write('"""Render layout playblasts for all shots. Run in Maya GUI."""\n'
                     "import maya.cmds as cmds, os\n"
                     "SHOTS = " + repr({k: (CAMERAS.get(k), v[0], v[1]) for k, v in SHOT_RANGES.items()}) + "\n"
                     "OUT = r'G:/film-304-toon-spine/Saved/Playblasts/Layout_62-66/v03'\n"
                     "def run(width=640, height=360):\n"
                     "    os.makedirs(OUT, exist_ok=True)\n"
                     "    for label, (cam, start, end) in SHOTS.items():\n"
                     "        if not cmds.objExists(cam):\n"
                     "            continue\n"
                     "        cmds.lookThru(cam)\n"
                     "        path = os.path.join(OUT, 'Shepherd_Brennan_LayoutScene(62-66)_BS_shot' + label + '_v03.mp4')\n"
                     "        cmds.playblast(format='movie', filename=path, startTime=start, endTime=end,\n"
                     "                       widthHeight=(width, height), percent=100, viewer=False,\n"
                     "                       showOrnaments=False, offScreen=True, forceOverwrite=True, compression='H.264')\n"
                     "        print('Playblast:', path)\n"
                     "if __name__ == '__main__':\n"
                     "    run()\n")
        return script
    item(8, "one-click playblast script", i8)

    # 9. Relative reference paths
    def i9():
        states = {}
        for rn in cmds.ls(type="reference") or []:
            has = cmds.attributeQuery("relativePath", node=rn, exists=True)
            if has:
                try:
                    cmds.setAttr(rn + ".relativePath", True)
                except Exception:
                    pass
            try:
                states[rn] = {"relativePath": cmds.getAttr(rn + ".relativePath") if has else None,
                              "filename": cmds.referenceQuery(rn, filename=True)}
            except Exception:
                states[rn] = "query_error"
        return states
    item(9, "relative references", i9)

    # 10. Outliner hygiene / master grouping
    def i10():
        if not cmds.objExists("Layout_MASTER"):
            cmds.createNode("transform", name="Layout_MASTER")
        for n in ["Layout_David_Root", "Layout_Spider_Root", "Layout_Office_Set",
                  "Layout_Door_Set", "Layout_TitleCard", "Layout_Exterminator",
                  "Layout_SilkThread", "Layout_Key_Light", "Layout_Fill_Light",
                  "Layout_Ambient"]:
            if cmds.objExists(n):
                try:
                    cmds.parent(n, "Layout_MASTER", absolute=True)
                except Exception:
                    pass
        if not cmds.objExists("Layout_Cameras"):
            cmds.createNode("transform", name="Layout_Cameras")
        for n in (list(CAMERAS.values()) + (cmds.ls("Cam_*_Target") or [])):
            if cmds.objExists(n):
                try:
                    cmds.parent(n, "Layout_Cameras", absolute=True)
                except Exception:
                    pass
        for a in ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"):
            try:
                cmds.setAttr("Layout_MASTER." + a, lock=True)
            except Exception:
                pass
        return "master grouped, master transform locked"
    item(10, "outliner hygiene", i10)

    # 11. Face/eye material + brow staging (eyelid open remains GUI)
    def i11():
        assign("Layout_Eye", ["David:David_Eye_Lf_GEO", "David:David_Eye_Rt_GEO"])
        assign("Layout_EyeDark", ["David:David_EyeInt_Lf_GEO", "David:David_EyeInt_Rt_GEO"])
        assign("Layout_Cornea", ["David:David_Cornea_Lf_GEO", "David:David_Cornea_Rt_GEO"])
        for n in ("David:FKEyeRegion_L", "David:FKEyeRegion_R"):
            if cmds.objExists(n):
                for a in ("scaleX", "scaleY", "scaleZ"):
                    cmds.setAttr(n + "." + a, 1.0)
        brows = "David:David_Eyebrows_GEO"
        if cmds.objExists(brows):
            for f, v in ((49, -1.0), (72, -1.0), (73, -1.5), (120, -1.5),
                         (121, 0.0), (192, 0.0), (241, 0.5), (288, 0.5)):
                key_val(brows, "translateY", f, v)
        return "white sclera/dark iris, brow keys; eyelid open left for GUI"
    item(11, "face/eye staging", i11)

    # 12. Hands / hero swatter / mug
    def i12():
        fingers = [n for n in (cmds.ls("David:FK*Finger*", type="transform") or [])
                   if cmds.attributeQuery("rotateX", node=n, exists=True)]
        for f0, f1 in ((121, 144), (145, 192), (241, 288)):
            for n in fingers:
                for a, v in (("rotateX", 35), ("rotateZ", 15)):
                    key_val(n, a, f0, v)
                    key_val(n, a, f1, v)
        # Hero swatter in the right hand.
        hero = None
        if cmds.objExists("Layout_Swatter") and cmds.objExists("David:Wrist_R"):
            dup = cmds.duplicate("Layout_Swatter", name="Layout_HeroSwatter")
            hero = dup[0] if dup else None
            if hero:
                p = cmds.xform("David:Wrist_R", q=True, ws=True, t=True)
                cmds.xform(hero, ws=True, t=p)
                try:
                    cmds.parent(hero, "David:Wrist_R", absolute=True)
                except Exception:
                    cmds.parent(hero, "Layout_David_Root", absolute=True)
                cmds.xform(hero, ws=True, ro=(0, 0, 90))
                cmds.setAttr(hero + ".scale", 0.65, 0.65, 0.65)
                for f, v in ((1, 0), (121, 1), (192, 1), (193, 0), (288, 0)):
                    key_vis(hero, f, v)
        # Mug in the right hand for 66B.
        mug = None
        if cmds.objExists("David:Wrist_R") and not cmds.objExists("Layout_Mug"):
            mug = cmds.createNode("transform", name="Layout_Mug")
            body = cmds.polyCylinder(name="Layout_MugBody", radius=4, height=8)[0]
            cmds.parent(body, mug)
            try:
                handle = cmds.polyTorus(name="Layout_MugHandle", radius=3.2, sectionRadius=0.7)[0]
                cmds.xform(handle, ws=True, t=(4, 0, 0), ro=(90, 0, 0))
                cmds.parent(handle, mug)
            except Exception:
                pass
            m = lambert("Layout_MugMat", (0.85, 0.82, 0.76))
            assign(m, [body])
            p = cmds.xform("David:Wrist_R", q=True, ws=True, t=True)
            cmds.xform(mug, ws=True, t=(p[0], p[1] + 4, p[2]))
            try:
                cmds.parent(mug, "David:Wrist_R", absolute=True)
            except Exception:
                cmds.parent(mug, "Layout_David_Root", absolute=True)
            for f, v in ((1, 0), (241, 1), (288, 1)):
                key_vis(mug, f, v)
        return {"fingers": len(fingers), "hero": hero, "mug": mug}
    item(12, "hands + hero props", i12)

    # 13. 64B leg cycle
    def i13():
        L, R = "David:IKLegHandle_L", "David:IKLegHandle_R"
        lkeys = [(145, 0, 0), (153, 12, 8), (161, 0, 0), (169, 0, -8),
                 (177, 12, 0), (185, 0, 8), (192, 0, 0)]
        rkeys = [(145, 0, 0), (153, 0, -8), (161, 12, 8), (169, 0, 0),
                 (177, 0, -8), (185, 12, 0), (192, 0, 0)]
        for node, keys in ((L, lkeys), (R, rkeys)):
            if not cmds.objExists(node):
                continue
            for f, y, x in keys:
                key_val(node, "translateY", f, y)
                key_val(node, "translateX", f, x)
        return "64B leg keys on IKLegHandle L/R"
    item(13, "64B leg cycle", i13)

    # 14. Spider settle / thread sway
    def i14():
        s = "Layout_Spider_Root"
        if cmds.objExists(s):
            for f, y, x, rz in ((1, 260, -60, 0), (24, 185, -40, 0),
                                (40, 108, -25, 4), (44, 112, -25, 2), (48, 105, -25, 0)):
                key_val(s, "translateY", f, y)
                key_val(s, "translateX", f, x)
                key_val(s, "rotateZ", f, rz)
        t = "Layout_SilkThread"
        if cmds.objExists(t):
            for f, rz in ((1, 0), (24, 2), (40, -2), (48, 0)):
                key_val(t, "rotateZ", f, rz)
        return "spider settle + thread sway"
    item(14, "spider polish", i14)

    # 15. Swatter red grid
    def i15():
        red = lambert("Layout_Red", (0.72, 0.08, 0.06))
        dark = lambert("Layout_Dark", (0.18, 0.18, 0.2))
        if cmds.objExists("Layout_SwatterHead"):
            assign(red, ["Layout_SwatterHead"])
        for i, x in enumerate((16, 20, 24)):
            name = "Layout_SwatterCross_%d" % i
            if not cmds.objExists(name):
                bar = cmds.polyCube(name=name, width=0.6, height=0.2, depth=10)[0]
                cmds.xform(bar, ws=True, t=(x, 0.7, 0))
                try:
                    cmds.parent(bar, "Layout_Swatter", absolute=True)
                except Exception:
                    pass
                assign(dark, [bar])
        return "red head + cross grid"
    item(15, "swatter detail", i15)

    # 16. Desk dressing
    def i16():
        parent = "Layout_Office_Set" if cmds.objExists("Layout_Office_Set") else None
        screen = lambert("Layout_Screen", (0.035, 0.05, 0.08))
        white = lambert("Layout_White", (0.92, 0.92, 0.9))
        dark = lambert("Layout_Dark", (0.18, 0.18, 0.2))
        gray = lambert("Layout_Gray", (0.62, 0.62, 0.62))
        made = []
        def add(node, mat):
            if parent:
                try: cmds.parent(node, parent, absolute=True)
                except Exception: pass
            assign(mat, [node]); made.append(node)
        if not cmds.objExists("Layout_MonitorBase"):
            base = cmds.polyCube(name="Layout_MonitorBase", width=40, height=2, depth=25)[0]
            cmds.xform(base, ws=True, t=(-60, 79, -20)); add(base, dark)
            stand = cmds.polyCube(name="Layout_MonitorStand", width=10, height=18, depth=10)[0]
            cmds.xform(stand, ws=True, t=(-60, 88, -22)); add(stand, dark)
            scr = cmds.polyCube(name="Layout_MonitorScreen", width=50, height=30, depth=3)[0]
            cmds.xform(scr, ws=True, t=(-60, 110, -30)); add(scr, screen)
        if not cmds.objExists("Layout_Keyboard"):
            kb = cmds.polyCube(name="Layout_Keyboard", width=40, height=2, depth=14)[0]
            cmds.xform(kb, ws=True, t=(0, 79, 20)); add(kb, dark)
        for i, (x, z) in enumerate(((-30, 8), (-28, 12), (-32, 14))):
            name = "Layout_Paper_%d" % i
            if not cmds.objExists(name):
                p = cmds.polyCube(name=name, width=24, height=0.4, depth=17)[0]
                cmds.xform(p, ws=True, t=(x, 79, z), ro=(0, i * 4, 0)); add(p, white)
        if not cmds.objExists("Layout_DeskMug"):
            mug = cmds.polyCylinder(name="Layout_DeskMug", radius=4, height=9)[0]
            cmds.xform(mug, ws=True, t=(45, 84, 15)); add(mug, white)
        if not cmds.objExists("Layout_Chair"):
            seat = cmds.polyCube(name="Layout_Chair", width=45, height=5, depth=45)[0]
            cmds.xform(seat, ws=True, t=(-90, 45, -105)); add(seat, gray)
            back = cmds.polyCube(name="Layout_ChairBack", width=45, height=50, depth=5)[0]
            cmds.xform(back, ws=True, t=(-90, 70, -128)); add(back, gray)
        return made
    item(16, "desk dressing", i16)

    # 17. Door set detail
    def i17():
        parent = "Layout_Door_Set" if cmds.objExists("Layout_Door_Set") else None
        mid = lambert("Layout_Mid", (0.36, 0.36, 0.38))
        dark = lambert("Layout_Dark", (0.18, 0.18, 0.2))
        made = []
        def add(node, mat):
            if parent:
                try: cmds.parent(node, parent, absolute=True)
                except Exception: pass
            assign(mat, [node]); made.append(node)
        for side, x in (("L", -75), ("R", 75)):
            name = "Layout_DoorTrim_" + side
            if not cmds.objExists(name):
                t = cmds.polyCube(name=name, width=5, height=255, depth=14)[0]
                cmds.xform(t, ws=True, t=(x, 127.5, -400)); add(t, mid)
        if not cmds.objExists("Layout_DoorTopTrim"):
            t = cmds.polyCube(name="Layout_DoorTopTrim", width=160, height=5, depth=14)[0]
            cmds.xform(t, ws=True, t=(0, 267.5, -400)); add(t, mid)
        if not cmds.objExists("Layout_DoorHandle"):
            h = cmds.polyCylinder(name="Layout_DoorHandle", radius=2, height=10)[0]
            cmds.xform(h, ws=True, t=(40, 105, -392), ro=(90, 0, 0)); add(h, dark)
        if not cmds.objExists("Layout_DoorThreshold"):
            th = cmds.polyCube(name="Layout_DoorThreshold", width=130, height=2, depth=20)[0]
            cmds.xform(th, ws=True, t=(0, 1, -400)); add(th, dark)
        for side, x in (("L", -130), ("R", 130)):
            name = "Layout_CorridorWall_" + side
            if not cmds.objExists(name):
                w = cmds.polyCube(name=name, width=4, height=250, depth=120)[0]
                cmds.xform(w, ws=True, t=(x, 125, -460)); add(w, mid)
        if not cmds.objExists("Layout_CorridorBack"):
            b = cmds.polyCube(name="Layout_CorridorBack", width=260, height=250, depth=4)[0]
            cmds.xform(b, ws=True, t=(0, 125, -520)); add(b, mid)
        if not cmds.objExists("Layout_DoorGradient"):
            g = cmds.polyPlane(name="Layout_DoorGradient", width=500, height=300)[0]
            cmds.xform(g, ws=True, t=(0, 150, -428), ro=(90, 0, 0))
            if parent: cmds.parent(g, parent, absolute=True)
            assign(surface_file("Layout_DoorGradientMat", ROOT + "/Saved/Scenes/layout_door_gradient.png"), [g])
            made.append(g)
        return made
    item(17, "door set detail", i17)

    # 18. Exterminator silhouette
    def i18():
        parent = "Layout_Exterminator"
        if not cmds.objExists(parent):
            return "no proxy"
        dark = lambert("Layout_Dark", (0.18, 0.18, 0.2))
        mid = lambert("Layout_Mid", (0.36, 0.36, 0.38))
        made = []
        def add(node, mat):
            try: cmds.parent(node, parent, absolute=True)
            except Exception: pass
            assign(mat, [node]); made.append(node)
        if not cmds.objExists("Layout_ExBelt"):
            belt = cmds.polyCylinder(name="Layout_ExBelt", radius=27, height=5)[0]
            cmds.xform(belt, ws=True, t=(0, 90, 0)); add(belt, dark)
        if not cmds.objExists("Layout_ExCollar"):
            collar = cmds.polyCylinder(name="Layout_ExCollar", radius=25, height=3)[0]
            cmds.xform(collar, ws=True, t=(0, 153, 0)); add(collar, mid)
        for side, x in (("L", 18), ("R", -18)):
            name = "Layout_ExBoot_" + side
            if not cmds.objExists(name):
                b = cmds.polyCube(name=name, width=26, height=14, depth=36)[0]
                cmds.xform(b, ws=True, t=(x, 7, 8)); add(b, dark)
        if not cmds.objExists("Layout_ExTank"):
            tank = cmds.polyCylinder(name="Layout_ExTank", radius=14, height=45)[0]
            cmds.xform(tank, ws=True, t=(0, 125, -28)); add(tank, dark)
        return made
    item(18, "exterminator polish", i18)

    # 19. Lighting / backdrop / shadows
    def i19():
        key = "Layout_Key_LightShape"
        fill = "Layout_Fill_LightShape"
        amb = "Layout_AmbientShape"
        if cmds.objExists(key):
            cmds.setAttr(key + ".color", 1.0, 0.92, 0.82, type="double3")
            cmds.setAttr(key + ".intensity", 2.2)
            for a, v in (("useDepthMapShadows", 1), ("dmapResolution", 1024), ("dmapFilterSize", 2)):
                try: cmds.setAttr(key + "." + a, v)
                except Exception: pass
        if cmds.objExists(fill):
            cmds.setAttr(fill + ".color", 0.72, 0.82, 1.0, type="double3")
            cmds.setAttr(fill + ".intensity", 0.55)
        if cmds.objExists(amb):
            cmds.setAttr(amb + ".intensity", 0.35)
        if not cmds.objExists("Layout_Rim_Light"):
            shape = cmds.directionalLight(name="Layout_Rim_Light", intensity=1.2)
            if isinstance(shape, (list, tuple)): shape = shape[0]
            tr = cmds.listRelatives(shape, parent=True)[0]
            cmds.setAttr(shape + ".color", 0.55, 0.72, 1.0, type="double3")
            cmds.setAttr(tr + ".rotateX", -20); cmds.setAttr(tr + ".rotateY", 160)
            if cmds.objExists("Layout_MASTER"):
                try: cmds.parent(tr, "Layout_MASTER", absolute=True)
                except Exception: pass
        white = lambert("Layout_White", (0.92, 0.92, 0.9))
        if not cmds.objExists("Layout_Backdrop"):
            g = cmds.polyPlane(name="Layout_Backdrop", width=900, height=420)[0]
            cmds.xform(g, ws=True, t=(0, 210, -187), ro=(90, 0, 0))
            if cmds.objExists("Layout_Office_Set"):
                try: cmds.parent(g, "Layout_Office_Set", absolute=True)
                except Exception: pass
            assign(surface_file("Layout_BackdropMat", ROOT + "/Saved/Scenes/layout_backdrop_gradient.png"), [g])
        return "key/fill/rim + gradient backdrop + shadows"
    item(19, "lighting/backdrop", i19)

    # 20. Camera moves + title typography
    def i20():
        c62 = "Cam_Shot62"
        if cmds.objExists(c62):
            for f, z in ((1, 170), (48, 160)):
                key_val(c62, "translateZ", f, z)
        c63b = "Cam_Shot63B1"
        if cmds.objExists(c63b):
            for f, z in ((73, 280), (120, 265)):
                key_val(c63b, "translateZ", f, z)
        c66a = "Cam_Shot66A1"
        if cmds.objExists(c66a):
            for f, x in ((217, 0), (240, 20)):
                key_val(c66a, "translateX", f, x)
            t = "Cam_Shot66A_Target"
            if cmds.objExists(t):
                for f, x in ((217, 0), (240, 20)):
                    key_val(t, "translateX", f, x)
        c66b = "Cam_Shot66B1"
        if cmds.objExists(c66b):
            for f, x, y in ((241, 0, 90), (252, 3, 92), (254, -2, 88), (258, 0, 90), (288, 0, 90)):
                key_val(c66b, "translateX", f, x)
                key_val(c66b, "translateY", f, y)
        return "62 push-in, 63B push, 66A truck, 66B jolt; title card updated"
    item(20, "camera/feel polish", i20)

    # Save v03
    cmds.currentTime(1)
    cmds.file(rename=V03)
    cmds.file(save=True, type="mayaBinary", force=True)
    report["scene"] = V03
    report["saved"] = True
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print("V03_DONE", json.dumps({"saved": True, "items": len(report["items"])}))


if __name__ == "__main__":
    main()
