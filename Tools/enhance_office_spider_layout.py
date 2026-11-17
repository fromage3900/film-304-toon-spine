"""Enhance the Office Spider layout with image planes, silk thread, and better camera framing."""
try:
    import maya.standalone
    maya.standalone.initialize(name="python")
    STANDALONE = True
except RuntimeError:
    STANDALONE = False

import maya.cmds as cmds

if STANDALONE:
    SCENE = "G:/film-304-toon-spine/Saved/Scenes/OfficeSpider_Layout_62_66_Posed.mb"
    cmds.file(SCENE, open=True, force=True, ignoreVersion=True)
    print("Opened scene:", SCENE)

STORYBOARD_PAGE = "G:/film-304-toon-spine/Humber_FinalYear_Prep/Capstone_Pipeline_Scaffold/01_Preprod/Storyboard/SB_OfficeSpider_Page16.png"

# --- 1. Add image planes to cameras ---
print("Adding storyboard reference image planes...")
cameras = ["Cam_Shot62Shape1", "Cam_Shot63Shape1", "Cam_Shot64Shape1", "Cam_Shot66aShape1", "Cam_Shot66bShape1"]
for cam in cameras:
    if cmds.objExists(cam):
        ip = cmds.imagePlane(camera=cam, fileName=STORYBOARD_PAGE)
        # Scale down and push back so it's a reference, not blocking
        cmds.setAttr(ip[0] + ".sizeX", 200)
        cmds.setAttr(ip[0] + ".sizeY", 112.5)
        cmds.setAttr(ip[0] + ".depth", 500)
        print(f"  Image plane on {cam}: {ip[0]}")

# --- 2. Create silk thread for spider ---
print("Creating silk thread...")
thread = cmds.curve(name="SilkThread", degree=2, point=[(30, 130, 0), (30, 160, 0), (30, 190, 0)])
cmds.setAttr(thread + ".lineWidth", 2)
# Make it visible
cmds.setAttr(thread + ".visibility", 1)

# --- 3. Create a coffee machine prop (for Shot 66 context) ---
print("Creating coffee machine prop...")
cm_body = cmds.polyCube(name="CoffeeMachine_Body", width=15, height=20, depth=12)[0]
cmds.xform(cm_body, ws=True, t=(-40, 80, -15))
cm_top = cmds.polyCylinder(name="CoffeeMachine_Top", radius=5, height=5)[0]
cmds.xform(cm_top, ws=True, t=(-40, 92.5, -15))
# Mug
mug = cmds.polyCylinder(name="CoffeeMug", radius=3, height=8)[0]
cmds.xform(mug, ws=True, t=(-25, 84, -10))

# --- 4. Add a floor plane ---
print("Creating floor...")
floor = cmds.polyPlane(name="OfficeFloor", width=300, height=300)[0]
cmds.xform(floor, ws=True, t=(0, 0, 0), ro=(-90, 0, 0))

# --- 5. Add a back wall ---
print("Creating back wall...")
wall = cmds.polyPlane(name="OfficeWall", width=300, height=200)[0]
cmds.xform(wall, ws=True, t=(0, 100, -150), ro=(0, 0, 0))

# --- 6. Set camera focal lengths more precisely ---
print("Refining camera framing...")
cam_settings = {
    "Cam_Shot62": (35, (0, 100, 180), (0, 0, 0)),
    "Cam_Shot63": (50, (20, 100, 80), (0, -15, 0)),
    "Cam_Shot64": (35, (-60, 110, 120), (0, -20, 0)),
    "Cam_Shot66a": (35, (0, 100, 180), (0, 0, 0)),
    "Cam_Shot66b": (50, (0, 80, 100), (15, 0, 0)),
}
for cam, (fl, pos, rot) in cam_settings.items():
    if cmds.objExists(cam):
        cmds.setAttr(cam + ".focalLength", fl)
        cmds.xform(cam, ws=True, t=pos, ro=rot)

# --- 7. Save enhanced scene ---
if STANDALONE:
    out = "G:/film-304-toon-spine/Saved/Scenes/OfficeSpider_Layout_62_66_Enhanced.mb"
    cmds.file(rename=out)
    cmds.file(save=True, type="mayaBinary", force=True)
    print("Saved enhanced scene:", out)

print("Enhancement complete!")
print("Added: image planes, silk thread, coffee machine, mug, floor, wall")
print("Cameras refined with storyboard reference")

if STANDALONE:
    import maya.standalone
    maya.standalone.uninitialize()
