"""Headless render driver: fire stills + classify them from decoded pixels.

WHY
---
The proven harness (`render_prototypes.py`) is built around an OPEN editor
driven through Monolith's HTTP path: `fire_shot` fires a latent capture and
the CALLER polls the output directory from a separate process. The
2026-10-08 desktop control session runs in a SECOND editor instance started
with -ExecutePythonScript, and 5.8 closes that editor ~0.4 s after the
startup script returns (measured: `Cmd: QUIT_EDITOR`, reason
`UUnrealEdEngine::CloseEditor()`, three sessions) -- so a post-tick callback
can never outlive the script and the caller can never poll. THEREFORE this
driver never returns: it fires the still (the capture's blocking call pumps
editor frames internally -- measured: 258 s block on the laptop, capture
complete inside the call) and then pumps further frames with
`SystemLibrary.delay_until_next_frame()` until the PNG is on disk, one still
at a time, before finally returning (which is what quits the editor).

ONE PROCESS PER LEVEL (the harness rule): a request names exactly ONE spec
and only the shots staged in that spec's level. Mixed-level batches are run
as separate invocations.

WHY DECODE THE PNG
------------------
"A PNG on its own is not evidence" -- byte size alone misreads (a 28 KB
near-black frame vs a lit frame differ, but faint patches muddy the read).
This driver decodes the 8-bit PNG with pure stdlib (zlib + struct, no
imaging dependency -- same rule as `build_textures.py` / `png_size`) and
reports mean luminance, bright fraction, and (for the controls) per-third
red/dark fractions. The verdicts are printed in the report, never guessed.

Modes, via `Saved/Renders/_headless_request.json`:
    {"mode": "controls"}
        Run `Python/_controls_abc_20261008.py` (the three-control verdict
        matrix: plain lit red vs Substrate Toon no-profile vs with
        TP_Default), then classify the PNG into the verdict matrix.
    {"mode": "stills", "spec": <path>, "shots": [...]}
        Fire the requested stills from the spec (stems bumped v01 -> v02 so
        the black-laptop evidence in v01 is preserved untouched), recording
        measured IHDR dims + pixel luminance per still.

Run (second editor instance):
    UnrealEditor.exe HumberToonShader.uproject -ExecutePythonScript=<abs this file> -nosplash -unattended -stdout
Evidence: PNGs on disk + `Saved/Audit/controls_verdict_20261008.json` /
`Saved/Audit/render_batch_desktop_20261008.json`; live progress in
`Saved/Renders/_headless_status.json`.
"""
from __future__ import annotations

import json
import struct
import time
import traceback
import zlib
from pathlib import Path

import unreal

REPO = Path(__file__).resolve().parents[1]
REQUEST = REPO / "Saved" / "Renders" / "_headless_request.json"
STATUS = REPO / "Saved" / "Renders" / "_headless_status.json"
CONTROL_SCRIPT = REPO / "Python" / "_controls_abc_20261008.py"
CONTROLS_DIR = REPO / "Saved" / "Renders" / "controls"
CONTROL_STEM = "CTRL_ABC_20261008"
CONTROL_REPORT = REPO / "Saved" / "Audit" / "controls_verdict_20261008.json"
BATCH_REPORT = REPO / "Saved" / "Audit" / "render_batch_desktop_20261008.json"

PNG_SIG = b"\x89PNG\r\n\x1a\n"

PER_STILL_TIMEOUT_S = 1500.0
GLOBAL_TIMEOUT_S = 3600.0

# The fresh-load decay probe (work order 1): do generated textures load at
# their authored size in a fresh process, or collapse to the 32x32 default?
PROBE_TEXTURES = [
    "/Game/Materials/Textures/T_SDF_Strokes",
    "/Game/Materials/Textures/T_SDF_CarpetLoop",
    "/Game/Materials/Textures/T_SDF_PaperGrain",
    "/Game/Materials/Textures/T_Noise_White",
    "/Game/Materials/Textures/T_Ramp_Smooth",
    "/Game/Materials/Textures/T_Neutral_Normal",
]

HARDWARE = "RTX 3080 Ti 12GB / i9-12900KF (8P+8E, 24 threads) / 128GB / NVIDIA 610.88"
MACHINE = "desktop (Alienware Aurora R13) -- the machine class the Oct-5 real reads came from"


def log(m):
    line = "[HeadlessRender] " + str(m)
    try:
        unreal.log(line)
    except Exception:
        pass
    print(line)


def load_request():
    if not REQUEST.exists():
        raise RuntimeError("no request file: %s" % REQUEST)
    req = json.loads(REQUEST.read_text(encoding="utf-8-sig"))
    if req.get("mode") not in ("controls", "stills"):
        raise RuntimeError("request mode must be 'controls' or 'stills': %r"
                           % req.get("mode"))
    if req["mode"] == "stills":
        if not req.get("spec") or not req.get("shots"):
            raise RuntimeError("stills request needs 'spec' + 'shots'")
    return req


# --------------------------------------------------------------------------
# pure-stdlib PNG decode (color types 2/6, bit depth 8, no interlace)
# --------------------------------------------------------------------------

def decode_png(path):
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:8] != PNG_SIG:
        return None
    pos = 8
    idat = bytearray()
    ihdr = None
    while pos + 8 <= len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body[:13])
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            break
        pos += 12 + ln
    if ihdr is None or not idat:
        return None
    w, h, depth, ctype, _comp, _filt, interlace = ihdr
    if depth != 8 or interlace != 0 or ctype not in (2, 6):
        return None
    ch = 3 if ctype == 2 else 4
    stride = w * ch
    try:
        raw = zlib.decompress(bytes(idat))
    except Exception:
        return None
    if len(raw) != (stride + 1) * h:
        return None
    out = bytearray(stride * h)
    prev = bytearray(stride)
    for y in range(h):
        f = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        if f == 1:
            for i in range(ch, stride):
                line[i] = (line[i] + line[i - ch]) & 0xFF
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif f == 3:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif f == 4:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                c = prev[i - ch] if i >= ch else 0
                b = prev[i]
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return w, h, ch, out


def png_pixels_stats(path):
    """Mean luminance + bright fraction over a decimated grid; thirds for the
    control matrix (cube A sits in the left third, B mid, C right)."""
    dec = decode_png(path)
    if dec is None:
        return None
    w, h, ch, px = dec
    sx = max(1, w // 160)
    sy = max(1, h // 90)
    luma_sum = 0.0
    n = 0
    bright = 0
    thirds = [{"luma_sum": 0.0, "n": 0, "red": 0, "dark": 0} for _ in range(3)]
    for y in range(sy // 2, h, sy):
        for x in range(sx // 2, w, sx):
            i = (y * w + x) * ch
            r = px[i]
            g = px[i + 1]
            b = px[i + 2]
            luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
            luma_sum += luma
            n += 1
            if luma > 48.0:
                bright += 1
            t = thirds[min(2, x * 3 // w)]
            t["luma_sum"] += luma
            t["n"] += 1
            if r >= 70.0 and r > 1.6 * g and r > 1.6 * b:
                t["red"] += 1
            if luma < 10.0:
                t["dark"] += 1
    if n == 0:
        return None
    return {
        "mean_luma": round(luma_sum / n, 2),
        "bright_frac": round(bright / n, 4),
        "thirds": [
            {
                "mean_luma": round(t["luma_sum"] / t["n"], 2),
                "red_frac": round(t["red"] / t["n"], 4),
                "dark_frac": round(t["dark"] / t["n"], 4),
            }
            for t in thirds
        ],
    }


def classify_third(third):
    if third is None:
        return None
    if third["red_frac"] > 0.0015:
        return "red"
    if third["mean_luma"] < 10.0:
        return "black"
    return "other"


def find_stem_png(out_dir, stem):
    """The finished PNG for a stem, whatever extension convention. A fully
    written PNG decodes; a torn one does not (the decode IS the readiness
    check), so no size-stability dance is needed."""
    out_dir = Path(out_dir)
    hits = sorted(p for p in out_dir.glob(stem + "*") if decode_png(p) is not None)
    return hits[0] if hits else None


# --------------------------------------------------------------------------
# editor helpers (mirrors of render_prototypes.py -- importing that module
# would run its __main__ block, which fires a capture as an import side
# effect, so the small helpers are mirrored here instead)
# --------------------------------------------------------------------------

def find_camera(label):
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            if a.get_actor_label() == label:
                return a
        except Exception:                                          # noqa: BLE001
            continue
    return None


def ensure_level(pkg):
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = ues.get_editor_world()
    current = world.get_path_name() if world else ""
    if current.startswith(pkg + "."):
        return "already-loaded"
    dirty = [p.get_name() for p in
             unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
    if dirty:
        raise RuntimeError(
            "dirty map package(s) %s -- resolve them first" % dirty)
    if not unreal.LevelEditorSubsystem().load_level(pkg):
        raise RuntimeError("could not load %s" % pkg)
    log("loaded %s" % pkg)
    return "loaded"


def fire_still(spec, shot, out_dir):
    """Fire ONE capture. The call blocks while its internal pump renders the
    capture; the PNG may still need a few pumped frames afterwards (the
    measured 1.54 s latent tail), so the caller pumps after this returns."""
    res = spec["render_tier"]["resolution"]
    stem = shot["still_name"]
    cam = find_camera(shot["camera_label"])
    if cam is None:
        raise RuntimeError("camera %s not in level" % shot["camera_label"])
    t0 = time.time()
    task = unreal.AutomationLibrary.take_high_res_screenshot(
        res_x=int(res["width"]), res_y=int(res["height"]),
        filename=str(Path(out_dir) / stem), camera=cam,
        mask_enabled=False, capture_hdr=False,
        force_game_view=bool(spec["render_tier"].get("force_game_view", True)))
    blocked = time.time() - t0
    log("fired %s (%dx%d) blocked=%.1fs" % (stem, res["width"], res["height"], blocked))
    return {"stem": stem, "started": t0, "blocked": round(blocked, 2),
            "task_type": type(task).__name__ if task is not None else None}


def editor_world():
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    return ues.get_editor_world()


def pump_until_png(out_dir, stem, deadline):
    """Pump editor frames until the PNG decodes. delay_until_next_frame is
    the 5.8 primitive for 'yield the game thread until the next frame' --
    the editor keeps ticking while the capture's latent tail lands.

    FAILURE MODE MEASURED INTO THE REPORT: if the call is latent-only
    (returns without pumping) the loop tight-spins -- detectable as an
    absurd iteration rate, recorded and broken out of the log."""
    world = editor_world()
    it = 0
    t0 = time.time()
    while time.time() < deadline:
        png = find_stem_png(out_dir, stem)
        if png is not None:
            return png, it
        unreal.SystemLibrary.delay_until_next_frame(world)
        it += 1
        if it == 600 and time.time() - t0 < 5.0:
            log("WARN: delay_until_next_frame is not pumping frames "
                "(%d iters in %.1fs) -- capture tail will starve" % (it, time.time() - t0))
            note("pump-starved: delay_until_next_frame returned without frames")
    return None, it


def texture_probe():
    rows = []
    for path in PROBE_TEXTURES:
        row = {"asset": path, "exists": bool(unreal.EditorAssetLibrary.does_asset_exist(path))}
        if row["exists"]:
            tex = unreal.EditorAssetLibrary.load_asset(path)
            w = h = None
            try:
                # blueprint_get_size_x/y -- the same call the builders use
                # (build_textures.py / verify_expansion.py); UTexture's
                # get_surface_width is not exposed to 5.8 Python.
                w = tex.blueprint_get_size_x()
                h = tex.blueprint_get_size_y()
            except Exception as exc:                               # noqa: BLE001
                row["error"] = str(exc)[:80]
            row["surface_size"] = [w, h]
        rows.append(row)
    return rows


# --------------------------------------------------------------------------
# session state + report
# --------------------------------------------------------------------------

STATE = {
    "started_epoch": time.time(),
    "mode": None,
    "spec": None,
    "shots": [],
    "out_dir": None,
    "done": [],               # per-still rows
    "events": [],
    "fatal": None,
    "probe": [],
}


def note(event):
    STATE["events"].append({"t": round(time.time() - STATE["started_epoch"], 1),
                            "event": event})
    write_status()


def write_status():
    try:
        STATUS.write_text(json.dumps({
            "mode": STATE["mode"],
            "elapsed_s": round(time.time() - STATE["started_epoch"], 1),
            "done": [d["stem"] for d in STATE["done"]],
            "fatal": STATE["fatal"],
            "events": STATE["events"][-40:],
        }, indent=2), encoding="utf-8")
    except Exception:
        pass


def report_path():
    return CONTROL_REPORT if STATE["mode"] == "controls" else BATCH_REPORT


def build_report():
    return {
        "written": "2026-10-08",
        "purpose": "headless render session on the desktop -- A/B/C control + "
                   "stills batch, pixel-measured verdicts (no size-only reads)",
        "machine": MACHINE,
        "hardware": HARDWARE,
        "mode": STATE["mode"],
        "request": {k: STATE[k] for k in ("spec",) if STATE.get(k)},
        "probe_textures": STATE.get("probe", []),
        "stills": STATE["done"],
        "fatal": STATE["fatal"],
        "events": STATE["events"],
    }


def finish(extra=None):
    report = build_report()
    if extra:
        report.update(extra)
    path = report_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    log("report -> %s" % path)
    note("report written: %s" % path.name)
    write_status()


# -- controls mode ---------------------------------------------------------

def run_controls():
    png = find_stem_png(CONTROLS_DIR, CONTROL_STEM)
    if png is None:
        note("running control script")
        ns = {"__file__": str(CONTROL_SCRIPT), "__name__": "controls_session"}
        src = CONTROL_SCRIPT.read_text(encoding="utf-8-sig")
        try:
            exec(compile(src, str(CONTROL_SCRIPT), "exec"), ns)   # noqa: S102
        except Exception as exc:                                   # noqa: BLE001
            STATE["fatal"] = "control script failed: %s: %s" % (type(exc).__name__, exc)
            log("control script failed: %s\n%s" % (STATE["fatal"], traceback.format_exc()))
        png, iters = pump_until_png(CONTROLS_DIR, CONTROL_STEM,
                                    time.time() + PER_STILL_TIMEOUT_S)
        note("control pump finished (%d pump iterations, png=%s)"
             % (iters, "found" if png else "MISSING"))
    if png is None:
        finish({"verdict": "CONTROL_TIMEOUT"})
        return
    stats = png_pixels_stats(png)
    thirds = (stats or {}).get("thirds") or [None, None, None]
    cls = [classify_third(t) for t in thirds]
    red_a, red_b, red_c = (c == "red" for c in cls)
    if red_a and not red_b and not red_c:
        verdict = "TOON_BSDF_PATH_BLOCKED (machine or pipeline class)"
    elif red_a and red_b and not red_c:
        verdict = "TOON_PROFILE_DATA_IS_THE_BLACK_CAUSE"
    elif red_a and red_b and red_c:
        verdict = "TOON_PATH_HEALTHY_ON_DESKTOP -- earlier blacks were the laptop machine"
    elif not red_a:
        verdict = "RENDER_PIPELINE_DARK (exposure/lights) -- re-examine"
    else:
        verdict = "AMBIGUOUS -- read the thirds numbers"
    finish({
        "control_png": str(png),
        "control_stats": stats,
        "thirds_class": cls,
        "verdict": verdict,
    })


# -- stills mode -----------------------------------------------------------

def run_stills():
    spec = STATE["spec"]
    by_id = {s["shot_id"]: s for s in spec["shots"]}
    for shot_id in STATE["shots"]:
        if time.time() - STATE["started_epoch"] > GLOBAL_TIMEOUT_S:
            STATE["fatal"] = STATE["fatal"] or "global watchdog hit mid-batch"
            break
        if shot_id not in by_id:
            STATE["done"].append({"shot_id": shot_id,
                                  "error": "shot_id not in spec"})
            note("unknown shot %s" % shot_id)
            continue
        shot = dict(by_id[shot_id])
        stem = shot["still_name"]
        if "v01" in stem:
            stem = stem.replace("v01", "v02")
            shot["still_name"] = stem
        png = find_stem_png(STATE["out_dir"], stem)
        if png is not None:
            STATE["done"].append(still_row(shot, png, None, "skipped -- already on disk"))
            note("skip %s" % stem)
            continue
        try:
            ensure_level(spec["level"]["package"])
        except Exception as exc:                                   # noqa: BLE001
            STATE["done"].append({"shot_id": shot_id, "error": str(exc)})
            note("level load failed for %s: %s" % (shot_id, exc))
            continue
        try:
            fired = fire_still(spec, shot, STATE["out_dir"])
        except Exception as exc:                                   # noqa: BLE001
            STATE["done"].append({"shot_id": shot_id, "stem": stem,
                                  "error": "fire failed: %s" % exc})
            note("fire failed %s: %s" % (stem, exc))
            continue
        deadline = min(time.time() + PER_STILL_TIMEOUT_S,
                       STATE["started_epoch"] + GLOBAL_TIMEOUT_S)
        png, iters = pump_until_png(STATE["out_dir"], stem, deadline)
        if png is None:
            STATE["done"].append({"shot_id": shot_id, "stem": stem,
                                  "error": "PNG never landed within %ds" % int(PER_STILL_TIMEOUT_S)})
            note("timeout %s" % stem)
            continue
        row = still_row(shot, png, fired, None)
        row["pump_iterations"] = iters
        STATE["done"].append(row)
        note("still landed: %s verdict=%s mean_luma=%s"
             % (stem, row.get("verdict"), row.get("mean_luma")))
    finish()


def still_row(shot, png, fired, note_text):
    with open(png, "rb") as fh:
        head = fh.read(33)
    dims = None
    if head[:8] == PNG_SIG and head[12:16] == b"IHDR":
        dims = list(struct.unpack(">II", head[16:24]))
    stats = png_pixels_stats(png)
    mean_luma = (stats or {}).get("mean_luma")
    verdict = None
    if mean_luma is not None:
        if mean_luma < 8.0:
            verdict = "BLACK"
        elif mean_luma >= 20.0:
            verdict = "REAL"
        else:
            verdict = "AMBIGUOUS"
    row = {
        "shot_id": shot["shot_id"], "stem": shot["still_name"],
        "path": str(png), "bytes": png.stat().st_size,
        "width": dims[0] if dims else None, "height": dims[1] if dims else None,
        "resolution_matches_spec": bool(dims == [1280, 720]),
        "mean_luma": mean_luma, "bright_frac": (stats or {}).get("bright_frac"),
        "verdict": verdict,
        "total_seconds": round(png.stat().st_mtime - fired["started"], 2)
                         if fired else None,
        "call_blocked_seconds": fired["blocked"] if fired else None,
    }
    if note_text:
        row["note"] = note_text
    return row


# --------------------------------------------------------------------------
# boot: read the request, probe textures, run the blocking session, return
# (returning is what quits the editor -- 5.8 auto-issues QUIT_EDITOR)
# --------------------------------------------------------------------------

def boot():
    req = load_request()
    STATE["mode"] = req["mode"]
    if req["mode"] == "stills":
        spec_path = REPO / req["spec"]
        STATE["spec"] = json.loads(spec_path.read_text(encoding="utf-8-sig"))
        STATE["shots"] = list(req["shots"])
        STATE["out_dir"] = str(REPO / STATE["spec"]["render_tier"]["output_dir"])
        Path(STATE["out_dir"]).mkdir(parents=True, exist_ok=True)
    note("session start: mode=%s" % STATE["mode"])
    STATE["probe"] = texture_probe()
    note("texture probe done")


try:
    boot()
    if STATE["mode"] == "controls":
        run_controls()
    else:
        run_stills()
except Exception as exc:                                           # noqa: BLE001
    STATE["fatal"] = "session failed: %s: %s" % (type(exc).__name__, exc)
    log("SESSION FAILED: %s\n%s" % (STATE["fatal"], traceback.format_exc()))
    try:
        finish()
    except Exception:
        pass
    write_status()
