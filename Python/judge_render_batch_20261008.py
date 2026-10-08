"""Judge the 2026-10-08 desktop render batch: decode PNGs, measure luminance, write the verdict audit.

WHY
---
"A PNG on its own is not evidence." The Oct-5 real reads and the Oct-7/8
black frames are both PNGs; what separates them is measurable: mean
luminance over a decimated pixel grid, bright fraction, and (for the
A/B/C control) which thirds of the frame read red. This judges every PNG
of the desktop batch with pure stdlib (zlib + struct, no imaging
dependency -- same rule as build_textures.py) and writes
Saved/Audit/render_batch_desktop_20261008.json.

Run:
    UnrealEditor-Cmd.exe HumberToonShader.uproject -ExecutePythonScript="Python/judge_render_batch_20261008.py" -stdout -unattended
Assert on the report FILE, not the log.
"""
from __future__ import annotations

import json
import struct
import time
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AUDIT = REPO / "Saved" / "Audit" / "render_batch_desktop_20261008.json"

PNG_SIG = b"\x89PNG\r\n\x1a\n"

HARDWARE = "RTX 3080 Ti 12GB / i9-12900KF (8P+8E, 24 threads) / 128GB / NVIDIA 610.88"
MACHINE = "desktop (Alienware Aurora R13) -- MRQ -game command-line render path"

# (dir, glob-stem, role)
TARGETS = [
    ("controls", "CTRL_ABC_20261008", "control A/B/C"),
    ("office_stage", "OS_SH020_proto_v02", "office worker typing OTS"),
    ("office_stage", "OS_SH030_proto_v02", "paper shuffle insert"),
    ("office_stage", "OS_SH040_proto_v02", "desk supplies medium"),
    ("office_stage", "OS_SH050_proto_v02", "stretch break medium"),
    ("office_stage", "OS_SH060_proto_v02", "calendar macro"),
    ("prototypes", "COMP_SH010_proto_v02", "exterior establishing"),
    ("prototypes", "COMP_SH020_proto_v02", "exterior reveal profile"),
    ("prototypes", "COMP_SH030_proto_v02", "exterior water rise"),
    ("prototypes", "COMP_SH070_proto_v02", "exterior song release"),
]

# References for the verdict basis: the measured reads that frame this batch.
BASIS = {
    "black_reference": "Saved/Renders/office_stage/OS_SH020_proto_v01.png (2026-10-07 laptop: 28KB, mean~0)",
    "real_reference": "Saved/Renders/prototypes/COMP_SH020_proto_v01.png (2026-10-05, lit)",
}


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


def stats(path):
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
            r, g, b = px[i], px[i + 1], px[i + 2]
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
    def third_row(t):
        return {"mean_luma": round(t["luma_sum"] / t["n"], 2),
                "red_frac": round(t["red"] / t["n"], 4),
                "dark_frac": round(t["dark"] / t["n"], 4)}
    return {
        "width": w, "height": h, "bytes": path.stat().st_size,
        "mean_luma": round(luma_sum / n, 2),
        "bright_frac": round(bright / n, 4),
        "thirds": [third_row(t) for t in thirds],
    }


def verdict(mean_luma):
    if mean_luma is None:
        return "UNDECODABLE"
    if mean_luma < 8.0:
        return "BLACK"
    if mean_luma >= 20.0:
        return "REAL"
    return "AMBIGUOUS"


def main():
    t0 = time.time()
    rows = []
    for out_rel, stem, role in TARGETS:
        base = REPO / "Saved" / "Renders" / out_rel
        hits = sorted(p for p in base.glob(stem + "*")
                      if p.suffix.lower() == ".png")
        row = {"stem": stem, "role": role, "dir": out_rel}
        if not hits:
            row["verdict"] = "MISSING"
            rows.append(row)
            continue
        png = hits[0]
        s = stats(png)
        row.update(s or {"verdict": "UNDECODABLE"})
        row["path"] = str(png)
        row["verdict"] = verdict((s or {}).get("mean_luma"))
        rows.append(row)

    ctrl = next((r for r in rows if r["stem"] == "CTRL_ABC_20261008"
                 and "thirds" in r), None)
    if ctrl is None:
        ctrl_verdict = "CONTROL_MISSING_OR_UNDECODABLE"
    else:
        cls = []
        for t in ctrl["thirds"]:
            if t["red_frac"] > 0.0015:
                cls.append("red")
            elif t["mean_luma"] < 10.0:
                cls.append("black")
            else:
                cls.append("other")
        ctrl["thirds_class"] = cls
        red_a, red_b, red_c = (c == "red" for c in cls)
        if red_a and red_b and red_c:
            ctrl_verdict = "TOON_PATH_HEALTHY (A red, B red, C red)"
        elif not red_a:
            ctrl_verdict = ("CONTROL_MATRIX_UNEXPECTED (A not red, B=%s, C=%s) -- read thirds"
                            % (cls[1], cls[2]))
        elif red_a and not red_b and not red_c:
            ctrl_verdict = "TOON_BSDF_PATH_BLOCKED"
        elif red_a and red_b and not red_c:
            ctrl_verdict = "TOON_PROFILE_DATA_IS_THE_BLACK_CAUSE"
        else:
            ctrl_verdict = "AMBIGUOUS"

    stills = [r for r in rows if r["stem"] != "CTRL_ABC_20261008"]
    real = [r for r in stills if r.get("verdict") == "REAL"]
    black = [r for r in stills if r.get("verdict") == "BLACK"]
    missing = [r for r in stills if r.get("verdict") == "MISSING"]
    if missing:
        batch_verdict = "INCOMPLETE (%d missing)" % len(missing)
    elif black:
        batch_verdict = "FAIL -- %d still(s) black on the desktop" % len(black)
    elif len(real) == len(stills):
        batch_verdict = "REAL -- the toon reads are lit on the desktop (black was the laptop machine)"
    else:
        batch_verdict = "AMBIGUOUS (%d ambiguous)" % (len(stills) - len(real))

    report = {
        "written": "2026-10-08",
        "purpose": "judged pixel-measured verdict for the desktop MRQ -game still batch "
                   "(the black-render resolution evidence for tomorrow's presentation)",
        "machine": MACHINE,
        "hardware": HARDWARE,
        "render_method": "UnrealEditor-Cmd -game -LevelSequence=<LS_R_*> "
                         "-MoviePipelineConfig=<CFG_*>, MoviePipelineDeferredPassBase + PNG",
        "basis": BASIS,
        "control_verdict": ctrl_verdict,
        "batch_verdict": batch_verdict,
        "seconds": round(time.time() - t0, 1),
        "rows": rows,
    }
    AUDIT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print("[judge] -> %s" % AUDIT)
    print("[judge] control=%s" % ctrl_verdict)
    print("[judge] batch=%s" % batch_verdict)


if __name__ == "__main__":
    main()
