"""Generates cinematic architectural Venetian Blinds / Louvers for L_Film_Office window bays via Hython."""
from pathlib import Path
import math

REPO = Path(__file__).resolve().parents[2]
OUT_FBX = REPO / "Content" / "Meshes" / "Architecture" / "SM_VenetianBlinds_Bay.fbx"
OUT_FBX.parent.mkdir(parents=True, exist_ok=True)

import hou

def generate_blinds():
    hou.hipFile.clear(suppress_save_prompt=True)
    obj = hou.node("/obj")
    geo_node = obj.createNode("geo", "blinds_generator")
    
    # 1. Create Python SOP to construct the blind geometry
    py_sop = geo_node.createNode("python", "build_blinds")
    code = '''
import hou
import math

geo = hou.pwd().geometry()
geo.clear()

# Dimensions (in meters for Houdini, will scale or export cm)
bay_w = 2.24   # meters
bay_h = 0.65   # meters (pulled-up blinds covering top 22% of window bay)
slat_depth = 0.075 # 7.5 cm
slat_thick = 0.004 # 4 mm
num_slats = 10
tilt_deg = 35.0  # film noir light slicing angle

rad_tilt = math.radians(tilt_deg)
cos_t = math.cos(rad_tilt)
sin_t = math.sin(rad_tilt)

def add_box(cx, cy, cz, sx, sy, sz, color=(0.7, 0.72, 0.75)):
    hx, hy, hz = sx * 0.5, sy * 0.5, sz * 0.5
    pts = [
        hou.Vector3(cx - hx, cy - hy, cz - hz),
        hou.Vector3(cx + hx, cy - hy, cz - hz),
        hou.Vector3(cx + hx, cy + hy, cz - hz),
        hou.Vector3(cx - hx, cy + hy, cz - hz),
        hou.Vector3(cx - hx, cy - hy, cz + hz),
        hou.Vector3(cx + hx, cy - hy, cz + hz),
        hou.Vector3(cx + hx, cy + hy, cz + hz),
        hou.Vector3(cx - hx, cy + hy, cz + hz)
    ]
    h_pts = [geo.createPoint() for _ in range(8)]
    for i, p in enumerate(h_pts):
        p.setPosition(pts[i])
        p.setAttribValue("Cd", color)
        
    faces = [
        (0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4),
        (2, 3, 7, 6), (0, 3, 7, 4), (1, 2, 6, 5)
    ]
    for f in faces:
        poly = geo.createPolygon()
        for idx in f:
            poly.addVertex(h_pts[idx])

geo.addAttrib(hou.attribType.Point, "Cd", (1.0, 1.0, 1.0))

# 1. Headrail (at top of window bay)
add_box(0.0, bay_h - 0.04, 0.0, bay_w, 0.08, 0.08, (0.8, 0.82, 0.85))

# 2. Bottom Rail
add_box(0.0, 0.04, 0.0, bay_w * 0.98, 0.05, 0.08, (0.75, 0.77, 0.80))

# 3. Slats (42 tilted slats)
spacing = (bay_h - 0.16) / float(num_slats)
half_w = bay_w * 0.5 * 0.98
half_d = slat_depth * 0.5
half_th = slat_thick * 0.5

for s_idx in range(num_slats):
    curr_y = 0.08 + (s_idx * spacing)
    # Build 8 points of the tilted box
    # Local box offsets: dx in [-half_w, half_w], dy in [-half_th, half_th], dz in [-half_d, half_d]
    # Rotated around X axis by tilt_deg:
    # y_rot = dy * cos_t - dz * sin_t
    # z_rot = dy * sin_t + dz * cos_t
    box_corners = [
        (-half_w, -half_th, -half_d),
        ( half_w, -half_th, -half_d),
        ( half_w,  half_th, -half_d),
        (-half_w,  half_th, -half_d),
        (-half_w, -half_th,  half_d),
        ( half_w, -half_th,  half_d),
        ( half_w,  half_th,  half_d),
        (-half_w,  half_th,  half_d),
    ]
    slat_pts = []
    for (lx, ly, lz) in box_corners:
        rx = lx
        ry = curr_y + (ly * cos_t - lz * sin_t)
        rz = (ly * sin_t + lz * cos_t)
        pt = geo.createPoint()
        pt.setPosition(hou.Vector3(rx, ry, rz))
        pt.setAttribValue("Cd", (0.88, 0.90, 0.92))
        slat_pts.append(pt)
        
    faces = [
        (0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4),
        (2, 3, 7, 6), (0, 3, 7, 4), (1, 2, 6, 5)
    ]
    for f in faces:
        poly = geo.createPolygon()
        for idx in f:
            poly.addVertex(slat_pts[idx])

# 4. Vertical Ladder Cords (3 pairs of thin 3D cords front and back)
for cord_x in [-bay_w * 0.35, 0.0, bay_w * 0.35]:
    add_box(cord_x, bay_h * 0.5, -half_d * 0.9, 0.005, bay_h - 0.08, 0.005, (0.3, 0.3, 0.3))
    add_box(cord_x, bay_h * 0.5,  half_d * 0.9, 0.005, bay_h - 0.08, 0.005, (0.3, 0.3, 0.3))
'''
    py_sop.parm("python").set(code)
    
    # 2. Add normal
    normal = geo_node.createNode("normal", "compute_normals")
    normal.setInput(0, py_sop)
    
    # 3. Export Binary FBX via ROP
    rop = geo_node.createNode("rop_fbx", "export_fbx")
    rop.setInput(0, normal)
    rop.parm("exportkind").set(0)  # Binary FBX for Unreal Engine compatibility
    rop.parm("convertunits").set(1) # Convert meters to cm
    rop.parm("sopoutput").set(str(OUT_FBX).replace("\\", "/"))
    rop.parm("execute").pressButton()
    
    print(f"[Blinds Generator] Successfully baked solid FBX to: {OUT_FBX}")

if __name__ == "__main__":
    generate_blinds()

