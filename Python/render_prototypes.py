"""Render measured prototype stills from the shot-environment level.

WHY
---
The render tier in `Docs/FILM_PIPELINE.md` section 9 (16-bit EXR, 256+ samples) is
a 1-2 week job on this GTX 1050 Ti / 4-thread i5-7300HQ. Before committing to any
batch we need ONE measured frame: how long a 720p still actually takes here, and
whether the composition reads. So this script fires a single still per invocation
and the caller measures the result on disk.

WHY take_high_res_screenshot AND NOT MOVIE RENDER QUEUE
-------------------------------------------------------
MRQ derives its frame range from the LevelSequence playback range, and the shipped
`LS_SH*` sequences are 72-96 frames long -- a still would mean mutating a shared
sequence owned by `Python/build_shot_deck.py`. `AutomationLibrary
.take_high_res_screenshot` renders exactly one frame from a named CameraActor with
no sequence involvement, and returns an `AutomationEditorTask` rather than a file,
because the capture is LATENT: it completes over subsequent editor frames.

CONSEQUENCE: THIS SCRIPT CANNOT WAIT FOR THE PNG
------------------------------------------------
It fires the capture, records what it asked for in `_pending.json`, and returns.
The CALLER polls the output directory and measures elapsed time. Polling from the
caller also keeps the editor's request path free -- an HTTP client abandoned
mid-request leaves Monolith's handler stuck (6 CloseWait sockets, 2026-10-01).

ONE SHOT PER INVOCATION
-----------------------
Only the first requested shot whose PNG is missing is fired. Two high-res captures
in flight at once is not a thing the API promises, and re-invoking walks the list.
That also makes the script idempotent: a finished still is skipped, never re-fired.

Modes, via `Saved/Renders/prototypes/_request.json`:
    {"mode": "stills", "shots": ["SH010"]}   fire the next missing still
    {"mode": "report"}                       write the audit JSON from the PNGs

Evidence is the PNG on disk plus its measured IHDR dimensions -- not a log line
claiming success (`success: true` only means nothing threw).

Run (editor open, via Monolith):
    editor_query run_python {command: "Python/render_prototypes.py",
                             mode: execute_file}
"""
from __future__ import annotations

import json
import os
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import unreal  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
SPEC = REPO / "specs" / "humber_toon_spine" / "prototype_renders.v1.json"
OUT_DIR = REPO / "Saved" / "Renders" / "prototypes"
REQUEST = OUT_DIR / "_request.json"
AUDIT = REPO / "Saved" / "Audit" / "render_prototype_report.json"

PNG_SIG = b"\x89PNG\r\n\x1a\n"


def log(m):
    unreal.log("[ProtoRender] " + str(m))


def load_spec():
    if not SPEC.exists():
        raise RuntimeError("render spec missing: %s" % SPEC)
    return json.loads(SPEC.read_text(encoding="utf-8-sig"))


def load_request(spec):
    """Default is ONE still -- the first shot. Batching needs an explicit request."""
    default = {"mode": "stills", "shots": [spec["shots"][0]["shot_id"]]}
    if not REQUEST.exists():
        log("no request file; defaulting to %s" % default["shots"])
        return default
    # utf-8-sig: a request file written from PowerShell carries a BOM, which
    # json.loads rejects outright. This reads both forms.
    req = json.loads(REQUEST.read_text(encoding="utf-8-sig"))
    req.setdefault("mode", "stills")
    if req["mode"] == "stills" and not req.get("shots"):
        req["shots"] = default["shots"]
    return req


def png_size(path):
    """Width/height straight from the IHDR chunk -- no imaging dependency."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(33)
    except OSError:
        return None
    if len(head) < 24 or head[:8] != PNG_SIG or head[12:16] != b"IHDR":
        return None
    w, h = struct.unpack(">II", head[16:24])
    return int(w), int(h)


def find_still(stem):
    """The PNG the capture produced, whatever extension convention it used.

    `take_high_res_screenshot` takes a filename that may or may not already carry
    an extension, so glob the stem rather than guess.
    """
    hits = sorted(OUT_DIR.glob(stem + "*"))
    real = [h for h in hits if png_size(h) is not None]
    return real[0] if real else None


def pending_path(stem):
    """One record per still, so a batch accumulates instead of overwriting."""
    return OUT_DIR / ("_pending_" + stem + ".json")


def ensure_level(spec):
    """Load the shot set if the editor is sitting in some other level."""
    pkg = spec["level"]["package"]
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = ues.get_editor_world()
    current = world.get_path_name() if world else ""
    if current.startswith(pkg + "."):
        return "already-loaded"

    # Same modal hazard as compose_shot_env_level.py: switching levels with a
    # dirty map raises a blocking "save changes?" dialog and MCP goes silent.
    dirty = [p.get_name() for p in
             unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
    if dirty:
        raise RuntimeError(
            "dirty map package(s) %s -- resolve them in the editor first" % dirty)

    if not unreal.LevelEditorSubsystem().load_level(pkg):
        raise RuntimeError("could not load %s" % pkg)
    log("loaded %s" % pkg)
    return "loaded"


def find_camera(label):
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            if a.get_actor_label() == label:
                return a
        except Exception:                                          # noqa: BLE001
            continue
    return None


def fire_shot(shot, tier):
    """Fire ONE latent capture and record what was asked for. Returns immediately."""
    cam = find_camera(shot["camera_label"])
    if cam is None:
        raise RuntimeError(
            "camera %s is not in the level -- run compose_shot_env_level.py first"
            % shot["camera_label"])

    res = tier["resolution"]
    stem = shot["still_name"]

    # Stamp BEFORE the call. take_high_res_screenshot BLOCKS for the capture:
    # the first SH010 frame took 258 s, almost all of it shader compilation.
    # Stamping after the return recorded 1.54 s and hid the real cost -- the one
    # number this checkpoint exists to measure.
    t0 = time.time()
    task = unreal.AutomationLibrary.take_high_res_screenshot(
        res_x=int(res["width"]), res_y=int(res["height"]),
        filename=str(OUT_DIR / stem), camera=cam,
        mask_enabled=False, capture_hdr=False,
        force_game_view=bool(tier.get("force_game_view", True)))
    blocked = time.time() - t0

    rec = {
        "shot_id": shot["shot_id"], "stem": stem,
        "expected_png": str(OUT_DIR / (stem + ".png")),
        "requested_resolution": [int(res["width"]), int(res["height"])],
        "camera_label": shot["camera_label"],
        "focal_length_mm": shot["focal_length_mm"],
        "render_frame": shot["render_frame"],
        "call_started_epoch": t0,
        "call_started_local": time.strftime("%Y-%m-%d %H:%M:%S",
                                            time.localtime(t0)),
        "call_blocked_seconds": round(blocked, 2),
        "task_type": type(task).__name__ if task is not None else None,
        "note": "call blocks, then the capture finishes latently; caller polls",
    }
    pending_path(stem).write_text(json.dumps(rec, indent=2), encoding="utf-8")
    log("fired %s (%dx%d) from %s -> poll %s"
        % (stem, res["width"], res["height"], shot["camera_label"],
           OUT_DIR / (stem + ".png")))
    return rec


def build_report(spec, requested):
    """Evidence from the files on disk, plus the timing each firing recorded."""
    tier = spec["render_tier"]
    want = [int(tier["resolution"]["width"]), int(tier["resolution"]["height"])]
    stills = []
    for shot in spec["shots"]:
        stem = shot["still_name"]
        png = find_still(stem)
        row = {"shot_id": shot["shot_id"], "stem": stem,
               "requested": shot["shot_id"] in requested,
               "exists": png is not None}
        if png is not None:
            dims = png_size(png)
            row.update({
                "path": str(png), "bytes": png.stat().st_size,
                "width": dims[0], "height": dims[1],
                "resolution_matches_spec": [dims[0], dims[1]] == want,
            })
        pend = pending_path(stem)
        if pend.exists():
            p = json.loads(pend.read_text(encoding="utf-8-sig"))
            row["fired_at_local"] = (p.get("call_started_local")
                                     or p.get("fired_at_local"))
            row["call_blocked_seconds"] = p.get("call_blocked_seconds")
            started = p.get("call_started_epoch") or p.get("fired_at_epoch")
            if png is not None and started:
                # End-to-end wall cost. The blocking call alone understates it;
                # the latent tail alone (1.54 s on SH010) hides the compile.
                row["total_seconds"] = round(
                    png.stat().st_mtime - float(started), 2)
        stills.append(row)

    done = [s for s in stills if s["requested"] and s["exists"]
            and s.get("resolution_matches_spec")]
    report = {
        "ok": len(done) == len([s for s in stills if s["requested"]])
              and len(done) > 0,
        "tier": tier["name"], "method": tier["method"],
        "resolution": want, "output_dir": str(OUT_DIR),
        "requested": requested,
        "rendered_count": len(done),
        "requested_count": len([s for s in stills if s["requested"]]),
        "hardware": "GTX 1050 Ti 4GB / i5-7300HQ 4C4T / 16GB",
        "not_the_final_tier": "Docs/FILM_PIPELINE.md section 9 (16-bit EXR, 256+ "
                              "samples) is the shipping tier; this is prototype.",
        "stills": stills,
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    log("report -> %s (ok=%s %d/%d)" % (AUDIT, report["ok"],
                                        report["rendered_count"],
                                        report["requested_count"]))
    return report


if __name__ == "__main__" or "unreal" in sys.modules:
    spec = load_spec()
    req = load_request(spec)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if req["mode"] == "report":
        build_report(spec, req.get("shots")
                     or [s["shot_id"] for s in spec["shots"]])
    else:
        by_id = {s["shot_id"]: s for s in spec["shots"]}
        unknown = [i for i in req["shots"] if i not in by_id]
        if unknown:
            raise RuntimeError("unknown shot_id(s) %s -- not in the spec" % unknown)

        log("level %s" % ensure_level(spec))

        fired = None
        for sid in req["shots"]:
            shot = by_id[sid]
            if find_still(shot["still_name"]) is not None:
                log("skip %s -- %s already on disk" % (sid, shot["still_name"]))
                continue
            fired = fire_shot(shot, spec["render_tier"])
            break                       # one latent capture in flight at a time

        if fired is None:
            log("nothing to fire -- every requested still already exists")
            build_report(spec, req["shots"])