"""Generates procedural industrial brutalist ceiling beams, HVAC ductwork, conduit tracks, and troffer fixtures via Hython.

Outputs clean Kaydara Binary FBX (exportkind=0) with 3 distinct material slots:
1. /mat/M_Concrete_Beam: Brutalist structural concrete cross-beams
2. /mat/M_Duct_Metal: Galvanized steel ductwork, flanges, drop hangers, conduit, troffer metal housings
3. /mat/M_Troffer_Diffuser: Glowing white acrylic troffer diffuser panels
"""
from pathlib import Path
import math
import hou

REPO = Path(__file__).resolve().parents[2]
OUT_FBX = REPO / "Content" / "Meshes" / "Architecture" / "SM_Houdini_Ceiling_HVAC_Grid.fbx"
OUT_FBX.parent.mkdir(parents=True, exist_ok=True)

def generate_ceiling_grid():
    print(f"[CeilingBuilder] Generating procedural Brutalist ceiling architecture & HVAC grid...")
    hou.hipFile.clear(suppress_save_prompt=True)
    obj = hou.node("/obj")
    geo_node = obj.createNode("geo", "hvac_ceiling_generator")
    
    # Python SOP to build procedural geometry
    py_sop = geo_node.createNode("python", "build_geometry")
    code = r'''
import hou
import math

geo = hou.pwd().geometry()
geo.clear()

geo.addAttrib(hou.attribType.Prim, "shop_materialpath", "")

MAT_CONCRETE = "/mat/M_Concrete_Beam"
MAT_METAL = "/mat/M_Duct_Metal"
MAT_DIFFUSER = "/mat/M_Troffer_Diffuser"

# Work in meters (Houdini), FBX ROP converts to cm
# Room span: X_local from -2.0m to 6.5m, Y_local (cz) from -3.0m to 8.5m, Height (cy) = 3.0m to 3.5m

def add_box(cx, cy, cz, sx, sy, sz, mat_path):
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
        
    faces = [
        (0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4),
        (2, 3, 7, 6), (0, 3, 7, 4), (1, 2, 6, 5)
    ]
    for f in faces:
        poly = geo.createPolygon()
        for idx in f:
            poly.addVertex(h_pts[idx])
        poly.setAttribValue("shop_materialpath", mat_path)

z_start = -3.0
z_end = 8.5
trunk_len = z_end - z_start

# -------------------------------------------------------------------------
# 1. Brutalist Concrete Structural Beams (rhythmic coffered ceiling ribs)
# -------------------------------------------------------------------------
# Spanning across the room in X (width 8.5m, height 0.25m, thickness 0.35m) at Y = 3.38m
beam_z_coords = [-2.0, 0.0, 2.0, 4.0, 6.0, 8.0]
for bz in beam_z_coords:
    add_box(2.25, 3.375, bz, 8.50, 0.25, 0.35, MAT_CONCRETE)

# Longitudinal perimeter header beam along the window wall (X = -1.8m)
add_box(-1.80, 3.375, (z_start + z_end) * 0.5, 0.40, 0.25, trunk_len, MAT_CONCRETE)

# -------------------------------------------------------------------------
# 2. Primary Trunk Ducts (galvanized steel with joint flanges and threaded hangers)
# -------------------------------------------------------------------------
duct_y = 3.18
duct_w = 0.65
duct_h = 0.32

for trunk_x in [1.20, 3.80]:
    # Main continuous duct
    add_box(trunk_x, duct_y, (z_start + z_end) * 0.5, duct_w, duct_h, trunk_len, MAT_METAL)
    
    # Reinforcement Flanges every 1.5m
    z_curr = z_start + 0.5
    while z_curr < z_end:
        add_box(trunk_x, duct_y, z_curr, duct_w + 0.06, duct_h + 0.06, 0.05, MAT_METAL)
        # Vertical Threaded Drop Hangers reaching beam/slab at Y = 3.50m
        add_box(trunk_x - duct_w * 0.5 - 0.03, 3.35, z_curr, 0.025, 0.30, 0.025, MAT_METAL)
        add_box(trunk_x + duct_w * 0.5 + 0.03, 3.35, z_curr, 0.025, 0.30, 0.025, MAT_METAL)
        z_curr += 1.50

# Cross Branch Ducts (running along X across the office)
for bz in [-1.0, 1.0, 3.0, 5.0, 7.0]:
    add_box(2.50, duct_y - 0.06, bz, 3.6, 0.22, 0.28, MAT_METAL)
    for bx in [1.20, 2.50, 3.80]:
        add_box(bx, duct_y - 0.06, bz, 0.05, 0.26, 0.32, MAT_METAL)

# -------------------------------------------------------------------------
# 3. Suspended Fluorescent Troffers (Metal Housing + Emissive Diffuser Panel)
# -------------------------------------------------------------------------
troffer_positions = [
    # Over hero desk cluster:
    (0.60, -1.60), (0.60, 0.80), (0.60, 2.80),
    # Over workstation row:
    (3.50, 4.20), (3.50, 5.60), (3.50, 7.00),
    # Over breakroom / entrance:
    (2.00, 5.50), (2.00, 7.20),
    # Circulation corridor:
    (2.00, -0.50), (2.00, 1.80)
]

for (tx, tz) in troffer_positions:
    # Outer sheet metal fixture housing (0.60m x 1.20m x 0.08m)
    add_box(tx, 3.05, tz, 0.60, 0.08, 1.20, MAT_METAL)
    # Recessed glowing white diffuser lens
    add_box(tx, 3.00, tz, 0.54, 0.02, 1.14, MAT_DIFFUSER)
    # 4 Steel suspension cables anchoring fixture to ceiling
    for sx in [-0.26, 0.26]:
        for sz in [-0.52, 0.52]:
            add_box(tx + sx, 3.25, tz + sz, 0.008, 0.40, 0.008, MAT_METAL)

# -------------------------------------------------------------------------
# 4. Electrical Conduit Runs & Junction Boxes
# -------------------------------------------------------------------------
for cx in [-0.2, 2.2, 4.8]:
    add_box(cx, 3.42, (z_start + z_end) * 0.5, 0.04, 0.04, trunk_len, MAT_METAL)
    for jz in [-2.0, 1.0, 4.0, 7.0]:
        add_box(cx, 3.42, jz, 0.12, 0.12, 0.12, MAT_METAL)
'''
    py_sop.parm("python").set(code)
    
    # Add Normal SOP
    norm = geo_node.createNode("normal", "add_normals")
    norm.setInput(0, py_sop)
    
    # Add ROP FBX Output
    rop = geo_node.createNode("rop_fbx", "export_fbx")
    rop.setInput(0, norm)
    rop.parm("sopoutput").set(str(OUT_FBX).replace("\\", "/"))
    rop.parm("exportkind").set(0) # Binary FBX for UE5
    rop.parm("convertunits").set(1) # Convert meters to cm
    
    print(f"[CeilingBuilder] Baking geometry to {OUT_FBX}...")
    rop.parm("execute").pressButton()
    print(f"[CeilingBuilder] SUCCESS! Baked FBX size: {OUT_FBX.stat().st_size} bytes.")

if __name__ == "__main__":
    generate_ceiling_grid()
