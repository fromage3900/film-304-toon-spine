"""Houdini COP2 tilable-texture builder v4 -- seamless by construction.

Technique: every pattern is a ramp whose FIRST and LAST point colours are
identical, so the wrap column meets the start column exactly. Verified with a
seam metric (see 07_Evidence/seam_report.json).

Run headless:  hython build_cop_textures_v4.py
"""
import hou, json, os

OUT = r"G:\film-304-toon-spine\Film304_Packages\Environment_Assets_2026-11-17\05_Textures_Tilable"
HIP = r"G:\film-304-toon-spine\Film304_Packages\Environment_Assets_2026-11-17\06_Houdini_COP\Film304_TilableTextures_v01.hip"
os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.dirname(HIP), exist_ok=True)
RES = 512

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

def band(net, name, periods, axis="horiz", lo=0.0, hi=1.0, phase=0.0, interp="hold"):
    """Periodic band ramp, seamless (first colour == last colour)."""
    r = net.createNode("ramp", name)
    r.parm("ramp").set(axis)
    r.parm("ginterp").set(interp)
    n = max(2, int(periods) * 2)
    P(r, numpoints=n + 1)
    for i in range(n + 1):
        if i == n:
            pos = 1.0 - 1e-6          # last sample stays inside the tile
        else:
            pos = (i / n + phase) % 1.0
        c = hi if (i % 2) else lo
        P(r, **{"p%dpos" % (i + 1): pos,
                "p%dcolorr" % (i + 1): c,
                "p%dcolorg" % (i + 1): c,
                "p%dcolorb" % (i + 1): c})
    return r

def render(net, node, rop, fname):
    node.setDisplayFlag(True)
    P(rop, coppath="/img/%s" % net.name(), copoutput=os.path.join(OUT, fname))
    rop.render()
    return os.path.join(OUT, fname)

rop = hou.node("/out").createNode("comp", "film304_tilable_out")
P(rop, trange="normal", f1=1, f2=1, f3=1, tres="specify", res1=RES, res2=RES, mkpath=1)

made = []

# 1. concrete / plaster -- layered periodic bands, seamless
net = new_net("tx_concrete")
a = band(net, "base", 2, "horiz", 0.35, 0.62)
b = band(net, "mid", 8, "vert", -0.12, 0.12, phase=0.13)
c = band(net, "fine", 32, "horiz", -0.06, 0.06, phase=0.31)
s1 = net.createNode("add", "s1"); s1.setInput(0, a); s1.setInput(1, b)
s2 = net.createNode("add", "s2"); s2.setInput(0, s1); s2.setInput(1, c)
made.append(render(net, s2, rop, "T_Tilable_Concrete_512.png"))

# 2. metal panel -- seamless groove grid + fine seamless grain
net = new_net("tx_metalpanel")
gx = band(net, "gx", 8, "horiz", 0.30, 0.70)
gy = band(net, "gy", 8, "vert", 0.30, 0.70)
grid = net.createNode("multiply", "grid"); grid.setInput(0, gx); grid.setInput(1, gy)
gr = band(net, "grain", 64, "horiz", -0.05, 0.05, phase=0.07)
gr2 = band(net, "grain2", 64, "vert", -0.05, 0.05, phase=0.19)
gsum = net.createNode("add", "gsum"); gsum.setInput(0, gr); gsum.setInput(1, gr2)
panel = net.createNode("add", "panel"); panel.setInput(0, grid); panel.setInput(1, gsum)
made.append(render(net, panel, rop, "T_Tilable_MetalPanel_512.png"))

# 3. blinds / mullions -- crisp seamless vertical bands
net = new_net("tx_blinds")
bl = band(net, "stripes", 24, "horiz", 0.05, 0.85)
made.append(render(net, bl, rop, "T_Tilable_Blinds_512.png"))

# 4. toon hatch -- thin seamless horizontal rules
net = new_net("tx_hatch")
ha = band(net, "rules", 48, "vert", 0.55, 0.95, phase=0.02)
made.append(render(net, ha, rop, "T_Tilable_Hatch_512.png"))

# 5. facade -- two-axis panels at different pitch, seamless
net = new_net("tx_facade")
fx = band(net, "fx", 6, "horiz", 0.25, 0.75)
fy = band(net, "fy", 20, "vert", 0.25, 0.75, phase=0.33)
ov = net.createNode("over", "panels"); ov.setInput(0, fx); ov.setInput(1, fy)
made.append(render(net, ov, rop, "T_Tilable_Facade_512.png"))

hou.hipFile.save(HIP)
print(json.dumps({"networks": ["tx_concrete", "tx_metalpanel", "tx_blinds", "tx_hatch", "tx_facade"],
                  "hip": HIP, "outputs": made, "parm_errors": ERRS}, indent=2))
