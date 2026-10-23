"""Export a single marker cube at a known ROOM-space position.

If the -25 deg bake survives the FBX round trip, a cube at room (900, 0) must
land in world space at:
    x =  900*cos(-25) = +815.7
    y =  900*sin(-25) = -380.6      <-- NEGATIVE
If the in-plane angle flipped to +25, it lands at y = +380.6 instead.
Also a second marker at room (0, 900):
    correct: x = -(-900*sin(-25))... = -(-900*-0.4226)= -380.6, y = +815.7
"""
import hou
import math
import os

OUT = r"G:\film-304-toon-spine\Content\Meshes\Architecture\_probe_marker.fbx"
YAW = -25.0
C, S = math.cos(math.radians(YAW)), math.sin(math.radians(YAW))

geo = hou.node("/obj").createNode("geo", "MarkerProbe")
g = hou.Geometry()


def rot(x, y):
    return (x * C - y * S, x * S + y * C)


def box(cx, cy, cz, sx, sy, sz):
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    base = len(g.points())
    for dx, dy, dz in ((-hx, -hy, -hz), (-hx, -hy, hz), (-hx, hy, -hz), (-hx, hy, hz),
                       (hx, -hy, -hz), (hx, -hy, hz), (hx, hy, -hz), (hx, hy, hz)):
        p = g.createPoint()
        p.setPosition((cx + dx, cy + dy, cz + dz))
    for face in ((0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)):
        poly = g.createPolygon(is_closed=True)
        for i in face:
            poly.addVertex(g.points()[base + i])


# marker A: room (900, 0) - asymmetric along room +X
box(*rot(900, 0), 300.0, 40.0, 40.0, 40.0)
# marker B: room (0, 900) - asymmetric along room +Y
box(*rot(0, 900), 300.0, 40.0, 40.0, 40.0)

bgeo = OUT.replace(".fbx", ".bgeo")
g.saveToFile(bgeo)

f = geo.createNode("file", "OUT")
f.parm("file").set(bgeo)
f.setDisplayFlag(True)

fbx = geo.createNode("rop_fbx", "fbx")
fbx.setInput(0, f)
fbx.parm("sopoutput").set(OUT)
fbx.parm("execute").pressButton()

print("EXPECTED world positions if the -25 deg bake survives:")
print("  marker A (room 900,0) -> world x=%+.1f  y=%+.1f" % (rot(900, 0)[0], rot(900, 0)[1]))
print("  marker B (room 0,900) -> world x=%+.1f  y=%+.1f" % (rot(0, 900)[0], rot(0, 900)[1]))
print("EXPORTED:", OUT, os.path.exists(OUT))
os.remove(bgeo)