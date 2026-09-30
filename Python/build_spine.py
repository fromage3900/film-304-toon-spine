"""Runner: build the 304 film toon spine from code and verify it.

    UnrealEditor-Cmd.exe <project>.uproject ^
      -ExecutePythonScript="Python/build_spine.py" -stdout -unattended

Always asserts on the report file, never on log output.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow running this file directly from -ExecutePythonScript, where the script
# directory is not on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import spine_lib as lib  # noqa: E402


def main():
    lib.log("=" * 60)
    lib.log("304 FILM TOON SPINE - CODE GENERATION")
    lib.log("=" * 60)

    report = {"functions": {}, "materials": {}, "errors": []}

    # ---- material functions, in dependency order ----
    try:
        import build_mf_colorramp3
        build_mf_colorramp3.build()
        report["functions"]["MF_ColorRamp3"] = lib.verify_function(
            "MF_ColorRamp3", min_expressions=20)
    except Exception as exc:
        lib.log(f"ERROR building MF_ColorRamp3: {exc}")
        report["errors"].append(f"MF_ColorRamp3: {exc}")

    # ---- master material ----
    if not report["errors"]:
        try:
            import build_master_toon
            build_master_toon.build()
            report["materials"]["M_Master_Toon_Universal"] = \
                lib.verify_material("M_Master_Toon_Universal",
                                    expected_calls=["MF_ColorRamp3"],
                                    min_expressions=30)
        except Exception as exc:
            lib.log(f"ERROR building master: {exc}")
            report["errors"].append(f"M_Master_Toon_Universal: {exc}")

    lib.save_all()
    lib.write_report(report)

    ok = not report["errors"] and all(
        v.get("ok") for v in list(report["functions"].values())
        + list(report["materials"].values()))
    lib.log(f"OVERALL: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    main()
