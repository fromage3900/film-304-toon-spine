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

    # ---------------- reload builder modules from disk ----------------
    # CPython caches imported modules for the life of the process. When these
    # scripts are run repeatedly inside ONE long-lived editor via Monolith
    # run_python, every edit made between runs is silently ignored: __import__
    # hands back the module loaded the first time. That is exactly what was
    # observed - a newly added logging block never printed while older code in
    # the same file kept running. Evicting them first makes a run reflect what
    # is actually on disk, which is the whole contract of "assets are generated
    # from Python, Python is the source of truth".
    import importlib
    for _mod in ("spine_lib", "build_textures", "build_mf_colorramp3",
                 "build_mf_ramplut", "build_mf_patterns", "build_master_toon",
                 "build_m_outline", "build_toon_profiles", "build_instances",
                 "build_office_set_materials"):
        sys.modules.pop(_mod, None)
    for _mod in ("spine_lib",):
        try:
            importlib.import_module(_mod)
        except Exception as exc:
            log(f"WARN could not preload {_mod}: {exc}")

    # ---- textures FIRST ----
    # Build_toon_profiles imports ShadowHatchingPatternTexture /
    # DiffuseRampOffsetTexture by object path, so the texture assets must
    # exist before profiles are authored or those refs import as None and the
    # profile verifies clean while rendering unhatched.
    try:
        import build_textures
        report["textures"] = build_textures.build()
    except Exception as exc:
        lib.log(f"ERROR building textures: {exc}")
        report["errors"].append(f"textures: {exc}")
        report["textures"] = {"ok": False, "error": str(exc)}

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
         ["MF_ColorRamp3", "MF_RampLUT", "MF_ProceduralPatterns"], 30),
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

    # ---- office set material assignment ----
    # Run AFTER instances, because it assigns those instances to meshes. Kept
    # inside the spine so the office meshes can never drift back to an
    # unassigned slot - three of them shipped with material_interface=None and
    # therefore rendered with no material at all.
    if not report["errors"]:
        try:
            import build_office_set_materials
            office = build_office_set_materials.build()
            report["office_set"] = {
                "ok": office["ok"],
                "assigned": sum(1 for e in office["assigned"].values()
                                if e.get("ok")),
                "errors": office["errors"],
                "awaiting_geometry": office["orphaned_office_instances"],
            }
        except Exception as exc:
            lib.log(f"ERROR building office set materials: {exc}")
            report["errors"].append(f"office_set: {exc}")

    lib.save_all()
    lib.write_report(report)

    ok = not report["errors"] and all(
        v.get("ok") for v in list(report["functions"].values())
        + list(report["materials"].values())
        + list(report.get("profiles", {}).values())
        + list(report.get("instances", {}).values()))
    # Textures gate the whole spine: a failed import leaves the profiles'
    # hatching/offset refs unbound, and every profile below would still assert
    # clean. Assert on the same rule the rest of the report uses.
    if report.get("textures", {}).get("ok") is not True:
        ok = False
    lib.log(f"OVERALL: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    main()
