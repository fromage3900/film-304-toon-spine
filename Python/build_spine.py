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
    # The master consumes both ramps, so both must exist before it is built.
    for mod_name, fn_name, min_expr in [
        ("build_mf_colorramp3", "MF_ColorRamp3", 20),
        ("build_mf_ramplut", "MF_RampLUT", 8),
        ("build_mf_patterns", "MF_ProceduralPatterns", 40),
    ]:
        try:
            mod = __import__(mod_name)
            mod.build()
            report["functions"][fn_name] = lib.verify_function_graph(fn_name, max_dead=0)
        except Exception as exc:
            lib.log(f"ERROR building {fn_name}: {exc}")
            report["errors"].append(f"{fn_name}: {exc}")

    # ---- materials ----
    for mod_name, mat_name, expected, min_expr in [
        ("build_master_toon", "M_Master_Toon_Universal",
         ["MF_ColorRamp3", "MF_RampLUT"], 30),
        ("build_m_outline", "M_Outline_InvertedHull", [], 5),
    ]:
        if report["errors"]:
            break
        try:
            mod = __import__(mod_name)
            mod.build()
            report["materials"][mat_name] = lib.verify_material(
                mat_name, expected_calls=expected, min_expressions=min_expr)
        except Exception as exc:
            lib.log(f"ERROR building {mat_name}: {exc}")
            report["errors"].append(f"{mat_name}: {exc}")

    # ---- toon profiles + material instances ----
    if not report["errors"]:
        try:
            import build_toon_profiles
            made = build_toon_profiles.build()
            for pname in made:
                report.setdefault("profiles", {})[pname] = \
                    build_toon_profiles.verify_profile(pname)
        except Exception as exc:
            lib.log(f"ERROR building profiles: {exc}")
            report["errors"].append(f"profiles: {exc}")

    if not report["errors"]:
        try:
            import build_instances
            made = build_instances.build()
            for ipath in made:
                iname = ipath.rsplit("/", 1)[-1].split(".", 1)[0]
                expected = None
                if iname in build_instances.INSTANCES:
                    expected = build_instances.INSTANCES[iname][1]
                report.setdefault("instances", {})[iname] = \
                    build_instances.verify_instance(iname, expected)
        except Exception as exc:
            lib.log(f"ERROR building instances: {exc}")
            report["errors"].append(f"instances: {exc}")

    lib.save_all()
    lib.write_report(report)

    ok = not report["errors"] and all(
        v.get("ok") for v in list(report["functions"].values())
        + list(report["materials"].values())
        + list(report.get("profiles", {}).values())
        + list(report.get("instances", {}).values()))
    lib.log(f"OVERALL: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    main()
