"""Read-only guard: report fog ownership and value drift without changing anything.

Run this before any delivery render. It never mutates the level, so it is safe to
call from a render preflight.

    UnrealEditor-Cmd.exe HumberToonShader.uproject ^
      -ExecutePythonScript="Python/audit_fog_drift.py" -stdout -unattended

Fixes the original Python/check_fog.py, which read the `volumetric_fog` struct while
every writer in the project set `enable_volumetric_fog`, so the one script built to
verify fog state never reported the flag that governs it.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "G:/film-304-toon-spine/Python")

import unreal
import film304_fog

# The editor keeps one long-lived Python session, so film304_fog is cached after the
# first import and edits to the file would otherwise be invisible until an editor
# restart. Force a reload so an audit always reflects the file on disk.
import importlib

importlib.reload(film304_fog)


def main() -> int:
    report = film304_fog.drift_report()
    path = film304_fog.write_report(report)

    print(json.dumps(report, indent=2, default=str))
    print(f"\n[FogAudit] report written to {path}")

    drive = report["fog_drive"]
    print(f"\n[FogAudit] FOG DRIVE MODE: {drive['mode']}")
    print(f"[FogAudit]   authority        : {drive['authority']}")
    print(f"[FogAudit]   writable here    : {drive['values_writable_here']}")
    print(f"[FogAudit]   volumetrics      : {drive['volumetric_fog_enabled']}")
    print(f"[FogAudit]   godrays possible : {drive['godrays_possible']}")
    print(f"[FogAudit]   {drive['explanation']}")

    drift = report["drift"]
    if drift["error_count"]:
        for finding in drift["findings"]:
            print(f"[FogAudit] {finding['severity'].upper()}: {finding['detail']}")
        print(f"[FogAudit] FAIL: {drift['error_count']} error(s). Delivery render blocked.")
        return 1

    if not drift["clean"]:
        for finding in drift["findings"]:
            print(f"[FogAudit] {finding['severity'].upper()}: {finding['detail']}")
        print("[FogAudit] WARN: fog values differ from the level baseline.")
        return 0

    print("[FogAudit] OK: single fog owner, volumetric settings match the reviewed baseline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())