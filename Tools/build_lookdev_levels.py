"""Build the three lookdev fixture levels - one editor process per level.

WHY A DRIVER INSTEAD OF PART OF build_spine.py
-----------------------------------------------
ONE LEVEL LOAD PER PROCESS is a hard constraint of the headless editor path.
Loading a second level in the same process fatals with

    Fatal error: ... EditorServer.cpp Line 2544
    World Memory Leaks: 2 leaks objects and packages

even after an explicit `unreal.SystemLibrary.collect_garbage()`. That was
measured twice on 2026-10-03 (spine runs 12 and 13), and the second run
proved GC does not clear it: the previous world is still referenced at load
time.

So the fixtures are built here, sequentially, one UnrealEditor-Cmd process
per level, each with its own report. The spine build (build_spine.py) owns
everything that is NOT a level; this driver owns the levels.

    python Tools/build_lookdev_levels.py            # all three
    python Tools/build_lookdev_levels.py water      # one

Exit code is non-zero if any level failed. Each run writes
Saved/Audit/lookdev_level_<name>_report.json, and the combined verdict to
Saved/Audit/lookdev_levels_report.json.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROJECT = REPO / "MelodiaToonFilm.uproject"
EDITOR = Path("P:/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe")
AUDIT = REPO / "Saved" / "Audit"

# key -> (builder module path, level name)
LEVELS = {
    "gouache": ("Python/build_gouache_lookdev.py", "L_Gouache_Lookdev"),
    "foliage": ("Python/build_foliage_lookdev.py", "L_Foliage_Lookdev"),
    "water": ("Python/build_water_lookdev.py", "L_Water_Lookdev"),
}


def run_one(key: str) -> dict:
    script_rel, level_name = LEVELS[key]
    script = REPO / script_rel
    log = AUDIT / f"lookdev_level_{key}_2026-10-03.log"
    disk = REPO / "Content" / "Maps" / f"{level_name}.umap"
    if disk.exists():
        disk.unlink()          # rebuild from scratch, so a stale file cannot pass
    cmd = [
        str(EDITOR), str(PROJECT),
        f"-ExecutePythonScript={script}",
        "-stdout", "-unattended", "-nosplash",
        "-NullRHI", "-DDC-ForceMemoryCache",
    ]
    print(f"[lookdev] {key}: {level_name} ...", flush=True)
    with open(log, "w", encoding="utf-8") as fh:
        proc = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT,
                              timeout=1500)
    text = log.read_text(encoding="utf-8", errors="replace")
    fatal = "Fatal error" in text
    traceback = "Traceback (most recent call last)" in text
    # THE VERDICT IS THE FILE ON DISK. A python exception makes the editor exit
    # 0 with nothing built (measured twice on 2026-10-03), so exit code alone
    # is not evidence - see the driver docstring.
    ok = disk.exists() and not fatal and not traceback
    return {
        "key": key, "level": level_name, "exit": proc.returncode,
        "log": str(log), "fatal": fatal, "python_error": traceback,
        "umap": str(disk), "umap_bytes": disk.stat().st_size if disk.exists() else 0,
        "ok": ok,
    }


def main(argv) -> int:
    wanted = argv[1:] or list(LEVELS)
    bad = [k for k in wanted if k not in LEVELS]
    if bad:
        print(f"unknown level key(s): {bad}; known: {list(LEVELS)}")
        return 2

    results = [run_one(k) for k in wanted]
    report = {"written": "2026-10-03", "levels": {r["key"]: r for r in results},
              "ok": all(r["ok"] for r in results)}
    AUDIT.mkdir(parents=True, exist_ok=True)
    out = AUDIT / "lookdev_levels_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    for r in results:
        print(f"[lookdev] {r['key']:<8} {r['level']:<20} "
              f"exit={r['exit']} fatal={r['fatal']} ok={r['ok']}")
    print(f"[lookdev] report -> {out}")
    print("RESULT:", "PASS" if report["ok"] else "FAIL")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
