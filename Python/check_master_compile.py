"""Compile-at-load gate for the film material core (2026-10-07).

The reliable compile verdict for a saved master is the load itself, not an
in-process recompile: after a spine rebuild wipes and re-adds a graph in the
same session, recompile_material() can report a transient
"(Node StaticSwitchParameter) Missing A input" state that is NOT in the file
(measured: a fresh load-only process of the same bytes compiles clean,
Saved/Audit/switch_diagnostic* and the run-4 load-only ledger). So this
script is LOAD-ONLY: it materializes every master + texture the spine owns
and exits; the gate is the captured stdout being free of
"Failed to compile" / "(Node ...) Missing" / "use of undeclared identifier"
lines.

Run headless:
UnrealEditor-Cmd.exe HumberToonShader.uproject -ExecutePythonScript=<abs> -stdout -unattended
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import unreal  # noqa: E402

M = "/Game/Materials"
MASTERS = [
    "M_Master_Toon_Universal", "M_Master_Toon_Foliage", "M_Master_Toon_Water",
    "M_Master_Toon_Character", "M_Outline_InvertedHull",
    "M_Toon_Unlit_Character", "M_Master_Toon_Sky", "M_Master_Toon_Landscape",
    "M_Master_Toon_Face", "M_Master_Toon_Hair", "M_Master_Toon_Glass",
    "M_Master_Toon_EmissiveFX", "M_Master_Toon_Particles",
    "M_Master_Toon_PostComposite", "M_PainterlyGouache",
]
FUNCTIONS = ["MF_ColorRamp3", "MF_RampLUT", "MF_ProceduralPatterns",
             "MF_PBRDetail", "MF_RimOffset", "MF_SpaceParallax",
             "MF_ClothWindDrape", "MF_NormalAdjust", "MF_SurfaceWear",
             "MF_DF_ContactBlend", "MF_Impasto", "MF_FilmGrade"]

report = {"masters": 0, "functions": 0, "missing": []}
for name in MASTERS:
    m = unreal.load_asset(f"{M}/Masters/{name}")
    if m is None:
        report["missing"].append(f"master {name}")
    else:
        report["masters"] += 1
for name in FUNCTIONS:
    f = unreal.load_asset(f"{M}/Functions/{name}")
    if f is None:
        report["missing"].append(f"function {name}")
    else:
        report["functions"] += 1

out = Path(__file__).resolve().parent.parent / "Saved" / "Audit" / \
    "loadonly_gate_20261007.json"
out.write_text(json.dumps(report, indent=2), encoding="utf-8")

BAD = ", ".join(report["missing"])
print(f"[load-gate] masters={report['masters']}/{len(MASTERS)} "
      f"functions={report['functions']}/{len(FUNCTIONS)} "
      f"missing: {BAD if BAD else '(none)'}")
print("[load-gate] the process stdout must contain no 'Failed to compile', "
      "'Missing A/B input', or 'undeclared identifier' lines - that is the "
      "compile-at-load verdict.")
sys.exit(0 if not report["missing"] else 1)
