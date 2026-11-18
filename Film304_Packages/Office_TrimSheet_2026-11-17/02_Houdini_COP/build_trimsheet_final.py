"""Film 304 office trim sheet -- FINAL.

Houdini COP2 generates 8 seamless trim tiles (height + albedo). The atlas
placement, normal map and ORM are derived afterwards in Python (2D work that
does not need a compositing network).

Run headless:  hython build_trimsheet_final.py
"""
import hou, json, os

ROOT = r"G:\film-304-toon-spine"
OUT = ROOT + r"\Film304_Packages\Office_TrimSheet_2026-11-17"
ATLAS = OUT + r"\01_Atlas"
HIP = OUT + r"\02_Houdini_COP\Film304_OfficeTrimSheet_v01.hip"
os.makedirs(ATLAS, exist_ok=True)
os.makedirs(os.path.dirname(HIP), exist_ok=True)

TILE, COLS, ROWS = 512, 4, 2
AW, AH = TILE * COLS, TILE * ROWS

ERRS = []
def P(node, **kw):
    for k, v in kw.items():
        try:
            node.parm(k).set(v)
        except Exception as e:
            ERRS.append("%s.%s=%r -> %s" % (node.name(), k, v, e))

def new_net(name):
    img = hou.node("/img")
    old = img.node(name)
    if old:
        old.destroy()
    return img.createNode("img", name)

def profile(net, name, pts, interp="linear"):
    r = net.createNode("ramp", name)
    r.parm("ramp").set("horiz")
    r.parm("ginterp").set(interp)
    n = len(pts)
    P(r, numpoints=n + 1)
    for i, (pos, val) in enumerate(pts):
        P(r, **{"p%dpos" % (i + 1): pos, "p%dcolorr" % (i + 1): val,
                "p%dcolorg" % (i + 1): val, "p%dcolorb" % (i + 1): val})
    P(r, **{"p%dpos" % (n + 1): 1.0 - 1e-6, "p%dcolorr" % (n + 1): pts[0][1],
            "p%dcolorg" % (n + 1): pts[0][1], "p%dcolorb" % (n + 1): pts[0][1]})
    return r

TILES = [
    ("tbar",    "ceiling T-bar suspension rib", [(0.00, 0.22), (0.34, 0.22), (0.42, 0.92), (0.58, 0.92), (0.66, 0.22)], (0.55, 0.56, 0.58)),
    ("troffer", "light troffer bezel frame", [(0.00, 0.18), (0.08, 0.18), (0.14, 0.72), (0.22, 0.72), (0.28, 0.18),
                 (0.72, 0.18), (0.78, 0.72), (0.86, 0.72), (0.92, 0.18)], (0.88, 0.88, 0.86)),
    ("duct",    "HVAC duct flange run", [(0.00, 0.48), (0.08, 0.48), (0.13, 0.78), (0.21, 0.78), (0.26, 0.48),
                 (0.50, 0.48), (0.55, 0.78), (0.63, 0.78), (0.68, 0.48)], (0.62, 0.64, 0.66)),
    ("panel",   "wall panel edge trim", [(0.00, 0.60), (0.06, 0.60), (0.10, 0.96), (0.16, 0.96), (0.22, 0.60)], (0.78, 0.74, 0.68)),
    ("base",    "baseboard", [(0.00, 0.02), (0.62, 0.02), (0.72, 0.46), (0.82, 0.46), (0.92, 0.02)], (0.70, 0.68, 0.64)),
    ("mullion", "window mullion", [(0.00, 0.30), (0.40, 0.30), (0.50, 0.86), (0.60, 0.30)], (0.30, 0.32, 0.36)),
    ("slat",    "blind slat stack", [(0.00, 0.82), (0.12, 0.82), (0.20, 0.22), (0.32, 0.22), (0.40, 0.82),
                 (0.60, 0.82), (0.68, 0.22), (0.80, 0.22), (0.88, 0.82)], (0.72, 0.70, 0.66)),
    ("reveal",  "ceiling tile reveal", [(0.00, 0.50), (0.44, 0.50), (0.50, 0.14), (0.56, 0.50)], (0.80, 0.78, 0.74)),
]

rop = hou.node("/out").createNode("comp", "trimsheet_out")
P(rop, trange="normal", f1=1, f2=1, f3=1, tres="specify", res1=TILE, res2=TILE, mkpath=1)

tiles = {}
for name, desc, pts, tint in TILES:
    nh = new_net("trim_%s_h" % name)
    h = profile(nh, "height", pts); h.setDisplayFlag(True)
    P(rop, coppath="/img/trim_%s_h" % name)
    P(rop, copoutput=os.path.join(ATLAS, "_t_%s_h.png" % name)); rop.render()

    na = new_net("trim_%s_a" % name)
    hp = profile(na, "height", pts)
    tc = na.createNode("color", "tint")
    P(tc, colorr=tint[0], colorg=tint[1], colorb=tint[2])
    al = na.createNode("multiply", "albedo"); al.setInput(0, hp); al.setInput(1, tc)
    al.setDisplayFlag(True)
    P(rop, coppath="/img/trim_%s_a" % name)
    P(rop, copoutput=os.path.join(ATLAS, "_t_%s_a.png" % name)); rop.render()
    tiles[name] = desc

hou.hipFile.save(HIP)
print(json.dumps({"tiles": tiles, "hip": HIP, "parm_errors": ERRS}, indent=2, default=str))
