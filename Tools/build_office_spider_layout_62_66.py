"""Build Maya layout for Office Spider shots 62-66.

Opens the David worker rig + spider rig, creates a simple office desk,
and sets up cameras with framing per the storyboard (Page 16).

Usage:
    mayapy G:/film-304-toon-spine/Tools/build_office_spider_layout_62_66.py

Output:
    G:/film-304-toon-spine/Saved/Scenes/OfficeSpider_Layout_62_66.ma
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path("G:/film-304-toon-spine")
WORKER_SRC = ROOT / "Saved/OfflineIntake/Source/David_Rig_v1.51.mb"
SPIDER_SRC = ROOT / "Saved/OfflineIntake/Source/C_Spider.ma"
OUTPUT_DIR = ROOT / "Saved/Scenes"
OUTPUT_FILE = OUTPUT_DIR / "OfficeSpider_Layout_62_66.ma"

# Maya standalone init
import maya.standalone
maya.standalone.initialize(name="python")

import maya.cmds as cmds
import maya.mel as mel


def main():
    print("=== Office Spider Layout — Shots 62-66 ===")

    # --- 1. New scene ---
    cmds.file(new=True, force=True)
    cmds.currentUnit(linear="centimeter")
    cmds.currentUnit(time="film")  # 24 fps
    cmds.playbackOptions(minTime=1, maxTime=120, animationStartTime=1, animationEndTime=120)

    # --- 2. Import worker rig (David) ---
    print("Importing worker rig (David)...")
    cmds.file(str(WORKER_SRC), i=True, type="mayaBinary", ignoreVersion=True,
              mergeNamespacesOnClash=False, namespace="David")
    # Move worker to desk position
    worker_root = "David:David_Body_GEO"  # placeholder; find root joint
    # Find the root joint of the David rig
    # Find root joint (the one with no parent joint)
    david_joints = cmds.ls("David:*", type="joint") or []
    if david_joints:
        roots = []
        for j in david_joints:
            parents = cmds.listRelatives(j, parent=True) or []
            parent_joints = [p for p in parents if cmds.nodeType(p) == "joint"]
            if not parent_joints:
                roots.append(j)
        # If too many roots, find the one named Root or similar
        if len(roots) > 1:
            root_candidates = [r for r in roots if "Root" in r or "root" in r]
            if root_candidates:
                roots = [root_candidates[0]]
        print(f"  David root joints: {roots}")
        if roots:
            cmds.xform(roots[0], ws=True, t=(0, 0, 0))
    else:
        print("  WARNING: No David joints found")

    # --- 3. Import spider rig ---
    print("Importing spider rig...")
    cmds.file(str(SPIDER_SRC), i=True, type="mayaAscii", ignoreVersion=True,
              mergeNamespacesOnClash=False, namespace="Spider")
    spider_joints = cmds.ls("Spider:*", type="joint") or []
    if spider_joints:
        roots = []
        for j in spider_joints:
            parents = cmds.listRelatives(j, parent=True) or []
            parent_joints = [p for p in parents if cmds.nodeType(p) == "joint"]
            if not parent_joints:
                roots.append(j)
        root_candidates = [r for r in roots if "Root" in r or "root" in r]
        if root_candidates:
            roots = [root_candidates[0]]
        print(f"  Spider root joints: {roots}")
        if roots:
            cmds.xform(roots[0], ws=True, t=(50, 120, 0))
    else:
        print("  WARNING: No spider joints found")

    # --- 4. Create office desk (simple box) ---
    print("Creating office desk...")
    desk = cmds.polyCube(name="Desk", width=120, height=5, depth=60)[0]
    cmds.xform(desk, ws=True, t=(0, 75, 0))
    # Add legs
    for i, (x, z) in enumerate([(50, 25), (50, -25), (-50, 25), (-50, -25)]):
        leg = cmds.polyCylinder(name=f"DeskLeg_{i}", radius=2, height=75)[0]
        cmds.xform(leg, ws=True, t=(x, 37.5, z))

    # --- 5. Create fly swatter (simple geometry) ---
    print("Creating fly swatter...")
    swatter_handle = cmds.polyCylinder(name="SwatterHandle", radius=1, height=40)[0]
    cmds.xform(swatter_handle, ws=True, t=(30, 95, 0), ro=(0, 0, 45))
    swatter_head = cmds.polyPlane(name="SwatterHead", width=15, height=15)[0]
    cmds.xform(swatter_head, ws=True, t=(42, 110, 0), ro=(0, 0, 45))

    # --- 6. Create flammable can (simple cylinder) ---
    print("Creating flammable can...")
    can = cmds.polyCylinder(name="FlammableCan", radius=4, height=12)[0]
    cmds.xform(can, ws=True, t=(-30, 81, 10))

    # --- 7. Create raised platform/desk for worker to stand on ---
    print("Creating raised platform...")
    platform = cmds.polyCube(name="RaisedPlatform", width=60, height=5, depth=40)[0]
    cmds.xform(platform, ws=True, t=(0, 150, 0))

    # --- 8. Create cameras for shots 62-66 ---
    print("Creating cameras...")

    # Shot 62: Wide static — spider descends toward fly swatter on desk
    cam62 = cmds.camera(name="Cam_Shot62")[0]
    cmds.xform(cam62, ws=True, t=(0, 100, 150), ro=(0, 0, 0))
    cmds.setAttr(cam62 + ".focalLength", 35)

    # Shot 63: Medium close-up — worker angry/scowling
    cam63 = cmds.camera(name="Cam_Shot63")[0]
    cmds.xform(cam63, ws=True, t=(20, 100, 80), ro=(0, -15, 0))
    cmds.setAttr(cam63 + ".focalLength", 50)

    # Shot 64: Wide shot — worker in ready stance, facing can
    cam64 = cmds.camera(name="Cam_Shot64")[0]
    cmds.xform(cam64, ws=True, t=(-60, 110, 120), ro=(0, -20, 0))
    cmds.setAttr(cam64 + ".focalLength", 35)

    # Shot 65: Title card — "15 mins later" (no camera needed, use 2D plane)
    title_plane = cmds.polyPlane(name="TitleCard_15Mins", width=192, height=108)[0]
    cmds.xform(title_plane, ws=True, t=(0, 100, 200))
    cmds.setAttr(title_plane + ".visibility", 0)  # hidden by default

    # Shot 66: Wide shot — empty office, arrow pointing left
    cam66a = cmds.camera(name="Cam_Shot66a")[0]
    cmds.xform(cam66a, ws=True, t=(0, 100, 150), ro=(0, 0, 0))
    cmds.setAttr(cam66a + ".focalLength", 35)

    # Shot 66: Medium shot, low angle — worker on raised platform, frustrated
    cam66b = cmds.camera(name="Cam_Shot66b")[0]
    cmds.xform(cam66b, ws=True, t=(0, 80, 100), ro=(15, 0, 0))
    cmds.setAttr(cam66b + ".focalLength", 50)

    # --- 9. Create a simple light ---
    print("Creating lights...")
    light = cmds.directionalLight(name="KeyLight")
    cmds.xform(light, ws=True, t=(100, 200, 100), ro=(-45, -30, 0))

    # --- 10. Save scene ---
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Saving scene to {OUTPUT_FILE}...")
    cmds.file(rename=str(OUTPUT_FILE.with_suffix(".mb")))
    cmds.file(save=True, type="mayaBinary", force=True)
    print("=== Done ===")
    print(f"Scene saved: {OUTPUT_FILE}")
    print(f"Cameras created: Cam_Shot62, Cam_Shot63, Cam_Shot64, Cam_Shot66a, Cam_Shot66b")
    print(f"Rigs imported: David (worker), Spider")
    print(f"Props created: Desk, DeskLegs, SwatterHandle, SwatterHead, FlammableCan, RaisedPlatform, TitleCard")


if __name__ == "__main__":
    main()
    maya.standalone.uninitialize()