"""Add a Maya toon shader (rampShader) to the Office Spider layout scene."""
try:
    import maya.standalone
    maya.standalone.initialize(name="python")
    STANDALONE = True
except RuntimeError:
    STANDALONE = False

import maya.cmds as cmds

if STANDALONE:
    SCENE = "G:/film-304-toon-spine/Saved/Scenes/OfficeSpider_Layout_62_66_Enhanced.mb"
    cmds.file(SCENE, open=True, force=True, ignoreVersion=True)
    print("Opened scene:", SCENE)

# --- 1. Create toon ramp shader for David (worker) ---
print("Creating toon shader for David (worker)...")
david_shader = cmds.shadingNode("rampShader", asShader=True, name="Toon_David")
david_sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="Toon_David_SG")
cmds.connectAttr(david_shader + ".outColor", david_sg + ".surfaceShader")

# Set up toon ramp colors (3 bands: shadow, mid, highlight)
# Ramp entries: position, color
# Entry 0: shadow (dark)
cmds.setAttr(david_shader + ".color[0].color_Position", 0.0)
cmds.setAttr(david_shader + ".color[0].color_Color", 0.1, 0.15, 0.25, type="double3")
# Entry 1: mid tone
cmds.setAttr(david_shader + ".color[1].color_Position", 0.4)
cmds.setAttr(david_shader + ".color[1].color_Color", 0.3, 0.45, 0.65, type="double3")
# Entry 2: highlight
cmds.setAttr(david_shader + ".color[2].color_Position", 0.8)
cmds.setAttr(david_shader + ".color[2].color_Color", 0.6, 0.75, 0.9, type="double3")
# Color input: Light Angle (0) for toon shading
cmds.setAttr(david_shader + ".colorInput", 0)  # 0 = Light Angle

# --- 2. Create toon ramp shader for Spider ---
print("Creating toon shader for Spider...")
spider_shader = cmds.shadingNode("rampShader", asShader=True, name="Toon_Spider")
spider_sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="Toon_Spider_SG")
cmds.connectAttr(spider_shader + ".outColor", spider_sg + ".surfaceShader")

cmds.setAttr(spider_shader + ".color[0].color_Position", 0.0)
cmds.setAttr(spider_shader + ".color[0].color_Color", 0.05, 0.03, 0.01, type="double3")
cmds.setAttr(spider_shader + ".color[1].color_Position", 0.35)
cmds.setAttr(spider_shader + ".color[1].color_Color", 0.2, 0.12, 0.06, type="double3")
cmds.setAttr(spider_shader + ".color[2].color_Position", 0.75)
cmds.setAttr(spider_shader + ".color[2].color_Color", 0.4, 0.25, 0.12, type="double3")
cmds.setAttr(spider_shader + ".colorInput", 0)  # 0 = Light Angle

# --- 3. Create outline material (inverted hull) ---
print("Creating outline material...")
outline_shader = cmds.shadingNode("lambert", asShader=True, name="Toon_Outline")
outline_sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="Toon_Outline_SG")
cmds.connectAttr(outline_shader + ".outColor", outline_sg + ".surfaceShader")
cmds.setAttr(outline_shader + ".color", 0, 0, 0, type="double3")  # black outline

# --- 4. Assign shaders to meshes ---
print("Assigning shaders to meshes...")

# David body meshes
david_meshes = cmds.ls("David:*", type="mesh") or []
david_assigned = 0
for mesh in david_meshes:
    # Skip intermediate objects
    if cmds.getAttr(mesh + ".intermediateObject"):
        continue
    try:
        cmds.sets(mesh, edit=True, forceElement=david_sg)
        david_assigned += 1
    except Exception:
        pass
print(f"  David: {david_assigned} meshes assigned to Toon_David")

# Spider body meshes
spider_meshes = cmds.ls("Spider:*", type="mesh") or []
spider_assigned = 0
for mesh in spider_meshes:
    if cmds.getAttr(mesh + ".intermediateObject"):
        continue
    try:
        cmds.sets(mesh, edit=True, forceElement=spider_sg)
        spider_assigned += 1
    except Exception:
        pass
print(f"  Spider: {spider_assigned} meshes assigned to Toon_Spider")

# --- 5. Set up Arnold toon render (if available) ---
print("Configuring render settings for toon look...")
try:
    cmds.setAttr("defaultRenderGlobals.imageFormat", 8)  # JPEG
    print("  Render format: JPEG")
except Exception:
    pass

# --- 6. Save ---
if STANDALONE:
    out = "G:/film-304-toon-spine/Saved/Scenes/OfficeSpider_Layout_62_66_Toon.mb"
    cmds.file(rename=out)
    cmds.file(save=True, type="mayaBinary", force=True)
    print("Saved toon scene:", out)

print("Toon shader setup complete!")
print("Shaders: Toon_David (blue-gray ramp), Toon_Spider (brown ramp), Toon_Outline (black)")

if STANDALONE:
    import maya.standalone
    maya.standalone.uninitialize()
