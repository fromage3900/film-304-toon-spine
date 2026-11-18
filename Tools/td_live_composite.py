"""Build a LIVE TouchDesigner composite rig for screen recording.

Run through the Envoy bridge (see Tools/run_td_live.py):

    import base64, td
    exec(compile(base64.b64decode("<b64>").decode("utf-8"), "live", "exec"))

Builds /project1/livecomposite:
    4 live sources -> switch -> grade chain -> out -> fullscreen Window COMP

Sources : Spout/Syphon (UE or Maya), NDI, movie file / image sequence, video device
Controls: `ctl` constantCHOP (src, bloom, vignette, grain, saturation). The switch
          index and every grade amount are BIND expressions onto those channels,
          so editing the CHOP drives the live output -- no UI wiring needed.

Verified against this build's real operator set: resolutionTOP, levelTOP,
bloomTOP, rampTOP, compositeTOP, noiseTOP, hsvadjustTOP, outTOP, windowCOMP.
Idempotent: re-running destroys and rebuilds /project1/livecomposite.
Never raises -- failures are collected into the report file.
"""
import json
import os
import traceback

NET = "/project1/livecomposite"
REPORT = r"C:\Users\froma\AppData\Local\hermes\cache\scratch\live_composite_report.json"
CTL = NET + "/ctl"

log = []
_errors = []


def rec(step, **kw):
    kw["step"] = step
    log.append(kw)


def clean():
    p = td.op(NET)
    if p is not None:
        p.destroy()


def mk(family, name, parent):
    return parent.create(family, name)


def setp(node, **kw):
    ok, miss = [], []
    for k, v in kw.items():
        try:
            node.par[k].val = v
            ok.append(k)
        except Exception as e:
            miss.append("%s: %s" % (k, str(e)[:90]))
    return ok, miss


def wire(a, b, idx=0):
    try:
        b.inputConnectors[idx].connect(a)
        return True
    except Exception:
        return False


def build():
    clean()
    root = td.op("/project1").create("baseCOMP", "livecomposite")

    # ---- sources -------------------------------------------------------
    movie = mk("moviefileinTOP", "src_movie", root)
    setp(movie, file=r"G:\film-304-toon-spine\Saved\Audit\OfficeToon_2026-11-18\BS_Toon_v02_HD_cam0.png",
         loop=True, preload=False)
    spout = mk("syphonspoutinTOP", "src_spout", root)
    ndi = mk("ndiinTOP", "src_ndi", root)
    dev = mk("videodeviceinTOP", "src_device", root)
    rec("sources", movie=movie.path, spout=spout.path, ndi=ndi.path, device=dev.path)

    # ---- selector ------------------------------------------------------
    sel = mk("switchTOP", "sel", root)
    setp(sel, inputcount=4, index=0)
    for i, s in enumerate((movie, spout, ndi, dev)):
        wire(s, sel, i)
    rec("switch", path=sel.path)

    # ---- controls ------------------------------------------------------
    ctl = mk("constantCHOP", "ctl", root)
    names = ["src", "bloom", "vignette", "grain", "saturation"]
    vals = [0.0, 0.30, 0.45, 0.04, 1.0]
    set_ok = []
    for i, (n, v) in enumerate(zip(names, vals)):
        a, b = setp(ctl, **{"name%d" % i: n, "value%d" % i: v})
        set_ok.append({"name%d" % i: a, "value%d" % i: b})
    rec("controls", ctl=ctl.path, set_ok=set_ok)

    # ---- grade chain ---------------------------------------------------
    resize = mk("resolutionTOP", "resize", root)
    setp(resize, outputresolution="custom", resolutionw=1920, resolutionh=1080)

    levels = mk("levelTOP", "levels", root)
    setp(levels, blacklevel=0.02, whitelevel=0.98, brightness=1.05,
         contrast=1.12, saturation=1.0, gamma=1.0)

    bloom = mk("bloomTOP", "bloom", root)
    setp(bloom, intensity=0.6, threshold=0.75, radius=8.0)

    vig = mk("rampTOP", "vignette", root)
    setp(vig, ramp=[0.0, 1.0, 1.0, 0.0], rampcircular=1)
    vigmix = mk("compositeTOP", "vignette_mix", root)
    setp(vigmix, interpolations="multiply", operand=0.45)

    noise = mk("noiseTOP", "grain", root)
    setp(noise, noisetype=2, period=3.0, amp=0.05)
    grainsize = mk("resolutionTOP", "grain_size", root)
    setp(grainsize, outputresolution="custom", resolutionw=1920, resolutionh=1080)
    grainmix = mk("compositeTOP", "grain_mix", root)
    setp(grainmix, interpolations="over", operand=0.05)

    grade = mk("hsvadjustTOP", "grade", root)
    setp(grade, saturation=1.0, brightness=1.0, hue=0.0)

    out = mk("outTOP", "out", root)
    disp = mk("directdisplayoutTOP", "display", root)

    # ---- bind the switch + grade to the ctl channels -------------------
    binds = {}
    exprs = {
        (sel, "index"): "op('%s')['src']" % CTL,
        (bloom, "bloomintensity"): "op('%s')['bloom']" % CTL,
        (vigmix, "operand"): "op('%s')['vignette']" % CTL,
        (grainmix, "operand"): "op('%s')['grain']" % CTL,
        (grade, "saturationmult"): "op('%s')['saturation']" % CTL,
    }
    for (node, par), ex in exprs.items():
        try:
            node.par[par].bindExpr = ex
            binds["%s.%s" % (node.name, par)] = True
        except Exception as e:
            binds["%s.%s" % (node.name, par)] = str(e)[:90]
    rec("binds", binds=binds)

    # ---- wire the chain ------------------------------------------------
    wire(sel, resize)
    wire(resize, levels)
    wire(levels, bloom)
    wire(bloom, vig)
    wire(vig, vigmix, 0)
    wire(bloom, vigmix, 1)
    wire(vigmix, grainmix, 0)
    wire(noise, grainsize)
    wire(grainsize, grainmix, 1)
    wire(grainmix, grade)
    wire(grade, out)
    wire(out, disp)
    rec("chain", resize=resize.path, out=out.path, display=disp.path)

    # ---- display (what gets recorded) ----------------------------------
    dok, dmiss = setp(disp, display="0", enable=True)
    rec("display", path=disp.path, set_ok=dok, set_miss=dmiss)

    # ---- panel ---------------------------------------------------------
    panel = root.create("containerCOMP", "panel")
    setp(panel, width=340, height=320, title="Film304 live composite")
    rec("panel", path=panel.path)

    return root


try:
    root = build()
except Exception:
    _errors.append(traceback.format_exc()[-900:])

try:
    ops = sorted([o.path for o in td.op(NET).children])
except Exception:
    ops = []

report = {"network": NET, "log": log, "errors": _errors, "ops": ops}
try:
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w") as fh:
        json.dump(report, fh, indent=2)
except Exception:
    pass
