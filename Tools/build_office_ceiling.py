"""Build a suspended-ceiling system for the L_Film_Office room (deterministic build).

Room measured from the live scene:
    floor  2460 x 2460 cm  (X,Y from -1230..+1230), top at z = 0
    ceiling slab underside z = 340
Everything is authored in CENTIMETRES so the FBX imports 1:1 into UE.

Geometry is written directly as a polygon soup rather than through
grid/copytopoints SOPs - those proved to lay points out on the wrong plane.
"""
import hou
import os

OUT_DIR = r"G:\film-304-toon-spine\Content\Meshes\Architecture"

# The room's FLOOR (Film_Floor, Cube scale 22) is the authority: 2200 x 2200.
# Film_Ceiling_Slab is scale 24 = 2400 and therefore overhangs the floor by
# 100 cm per side; the tile grid deliberately matches the floor instead.
ROOM = 2200.0
HALF = ROOM / 2.0
CEIL_Z = 340.0          # underside of the ceiling slab
BAYS = 20               # 20 x 20 = 120 cm bays
BAY = ROOM / BAYS
YAW = -25.0             # the whole room is yawed -25 deg; bake it into the geometry
_CY, _SY = __import__("math").cos(__import__("math").radians(YAW)), \
    __import__("math").sin(__import__("math").radians(YAW))


def rot_z(x, y):
    return (x * _CY - y * _SY, x * _SY + y * _CY)


# --------------------------------------------------------------- helpers
def add_box(g, cx, cy, cz, sx, sy, sz, yaw=0.0):
    """Axis-aligned (optionally yawed about Z) box, centre (cx,cy,cz), size (sx,sy,sz)."""
    import math
    hx, hy, hz = sx * 0.5, sy * 0.5, sz * 0.5
    ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    base = len(g.points())
    for dx, dy, dz in ((-hx, -hy, -hz), (-hx, -hy, hz), (-hx, hy, -hz), (-hx, hy, hz),
                       (hx, -hy, -hz), (hx, -hy, hz), (hx, hy, -hz), (hx, hy, hz)):
        rx = dx * ca - dy * sa
        ry = dx * sa + dy * ca
        p = g.createPoint()
        p.setPosition((cx + rx, cy + ry, cz + dz))
    for face in ((0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)):
        poly = g.createPolygon(is_closed=True)
        for i in face:
            poly.addVertex(g.points()[base + i])
    return base


def place(g, rx, ry, cz, sx, sy, sz):
    """Add a box positioned in ROOM space (then baked out to the -25 deg world yaw)."""
    wx, wy = rot_z(rx, ry)
    return add_box(g, wx, wy, cz, sx, sy, sz, yaw=YAW)


def new_geo(name):
    n = hou.node("/obj").createNode("geo", name)
    n.setDisplayFlag(True)
    return n


def publish(obj_node, geometry, tmp_bgeo):
    """Persist a hou.Geometry and hook it into the object via a file SOP."""
    geometry.saveToFile(tmp_bgeo)
    f = obj_node.createNode("file", "OUT")
    f.parm("file").set(tmp_bgeo)
    f.parm("filemode").set(0)          # read
    f.setDisplayFlag(True)
    f.setRenderFlag(True)
    return f


# --------------------------------------------------- 1. ceiling tiles (concrete)
g_tiles = new_geo("CeilTiles")
tiles = hou.Geometry()
TILE_T = 1.6
for i in range(BAYS):
    for j in range(BAYS):
        x = -HALF + (i + 0.5) * BAY
        y = -HALF + (j + 0.5) * BAY
        place(tiles, x, y, CEIL_Z - TILE_T - 0.9, BAY - 2.4, BAY - 2.4, TILE_T)
out_tiles = publish(g_tiles, tiles, OUT_DIR + "\\_tmp_tiles.bgeo")
g_tiles.setDisplayFlag(False)
out_tiles.setDisplayFlag(True)

# --------------------------------------------------- 2. T-bars + HVAC (metal)
g_metal = new_geo("CeilMetal")
metal = hou.Geometry()
BAR_W, BAR_H = 2.4, 3.6
BAR_Z = CEIL_Z - BAR_H - 1.8        # top 336.4 - clears the Film_Troffer panels at 336.6
for i in range(BAYS + 1):
    o = -HALF + i * BAY
    place(metal, 0.0, o, BAR_Z, ROOM, BAR_W, BAR_H)          # runner along room X
    place(metal, o, 0.0, BAR_Z, BAR_W, ROOM, BAR_H)          # runner along room Y
for k, y in enumerate((-800.0, 0.0, 800.0)):
    place(metal, 0.0, y, CEIL_Z - 34.0 - 18.0, ROOM - 120.0, 62.0, 34.0)
for k in range(8):
    x = -900.0 + k * 257.0
    place(metal, x, 400.0, CEIL_Z - 22.0 - 18.0, 26.0, 460.0, 22.0)
out_metal = publish(g_metal, metal, OUT_DIR + "\\_tmp_metal.bgeo")
g_metal.setDisplayFlag(False)
out_metal.setDisplayFlag(True)

# --------------------------------------------------- 3. light troffers
# NOT generated here on purpose: the room already contains six hand-placed
# fixtures (Film_Troffer_1..6 Panel/Housing, each 134 x 105 cm at z 336.6..339.6,
# each with a matching RectLight at z=334). Emitting another 100 emissive strips
# on a 220 cm pitch duplicated and contradicted them. We reuse the real ones.

# ------------------------------------------------------------- 4. verify
print("=== HOUDINI-SIDE BOUNDS (must be ~2460 x 2460 x thin) ===")
GROUPS = [("Concrete", g_tiles, "SM_Houdini_Office_Ceiling_Tiles"),
          ("Metal", g_metal, "SM_Houdini_Office_Ceiling_Metal")]
ok = True
for mat, g, stem in GROUPS:
    out = g.node("OUT")
    gd = out.geometry()
    b = gd.boundingBox()
    mn, mx = b.minvec(), b.maxvec()
    # per-point room-space extent (rotating an AABB back would be invalid)
    import math as _m
    ca, sa = _m.cos(_m.radians(-YAW)), _m.sin(_m.radians(-YAW))
    rmaxx = rmaxy = 0.0
    for pt in gd.points():
        p = pt.position()
        rx = abs(p[0] * ca - p[1] * sa)
        ry = abs(p[0] * sa + p[1] * ca)
        if rx > rmaxx:
            rmaxx = rx
        if ry > rmaxy:
            rmaxy = ry
    print("  %-16s world=(%8.1f,%8.1f,%7.1f)  ROOM half=(%7.1f,%7.1f)  z=(%7.1f..%7.1f)  prims=%d" % (
        mat, mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2],
        rmaxx, rmaxy, mn[2], mx[2], len(gd.prims())))
    if rmaxx > HALF + 30 or rmaxy > HALF + 30 or (mx[2] - mn[2]) > 80 or (mx[2] - mn[2]) < 1:
        print("     !! UNEXPECTED SHAPE in room space")
        ok = False
    if mn[2] > CEIL_Z or mx[2] < 200:
        print("     !! UNEXPECTED HEIGHT BAND (must hang under z=340)")
        ok = False
print("GEOMETRY SANITY:", "PASS" if ok else "FAIL")

# ------------------------------------------------------------- 5. export
for mat, g, stem in GROUPS:
    out = g.node("OUT")
    fbx = g.createNode("rop_fbx", "fbx_%s" % mat)
    fbx.setInput(0, out)
    path = os.path.join(OUT_DIR, stem + ".fbx")
    fbx.parm("sopoutput").set(path)
    if fbx.parm("convertunits") is not None:
        fbx.parm("convertunits").set(0)
    if fbx.parm("convertaxis") is not None:
        fbx.parm("convertaxis").set(0)       # keep Z-up so UE needs no rotation
    fbx.parm("execute").pressButton()
    print("EXPORTED %-16s %s  %.1f KB" % (
        mat, os.path.basename(path),
        os.path.getsize(path) / 1024.0 if os.path.exists(path) else -1))