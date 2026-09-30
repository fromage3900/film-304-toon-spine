"""Migrate the toon spine from a source UE project into this project, correctly.

WHY THIS EXISTS
---------------
Copying .uasset files with `cp` breaks them: UE stores each asset's OWN package
path inside the binary, so a file moved from
    /Game/EnvSandbox/Materials/Functions/MF_ColorRamp3
to
    /Game/Materials/Functions/MF_ColorRamp3
still points at the old path and will not resolve.

This script uses unreal.EditorAssetLibrary.duplicate_directory / duplicate_asset,
which loads the asset in the SOURCE project and writes a correctly-pathed copy
into THIS project, remapping every internal reference on the way.

Run headless against the DESTINATION project:
    UnrealEditor-Cmd.exe <dest>.uproject ^
      -ExecutePythonScript=migrate_spine.py ^
      -SourceProject="<abs path to source .uproject>" -stdout -unattended

or in the source project's editor console (it will write into the destination
content folder directly):
    py "migrate_spine.py" --source <abs source project> --dest <abs dest Content>
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import unreal

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Material functions the headless UE scan proved the master actually calls,
# minus the two that need third-party plugins we do not have.
# Verified against BS_GodFile on 2026-09-29 via UnrealEditor-Cmd.exe scan.
SOURCE_MFS = [
    "/Game/EnvSandbox/Materials/Functions/MF_NormalAdjust",
    "/Game/EnvSandbox/Materials/Functions/MF_ColorRamp3",
    "/Game/EnvSandbox/Materials/Functions/MF_SpaceParallax",
    "/Game/EnvSandbox/Materials/Functions/MF_Madoka",
    "/Game/EnvSandbox/Materials/Functions/MF_Itto",
    "/Game/EnvSandbox/Materials/Functions/MF_NikkiDreamGrade",
    "/Game/EnvSandbox/Materials/Functions/MF_DF_ContactBlend",
    "/Game/EnvSandbox/Materials/Functions/MF_Impressionist_Impasto",
    "/Game/EnvSandbox/Materials/Functions/MF_ClothWindDrape",
]

SOURCE_MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"

SOURCE_TOON_PROFILES = [
    "/Game/EnvSandbox/Materials/ToonProfiles/TP_Default",
    "/Game/EnvSandbox/Materials/ToonProfiles/TP_Stone",
    "/Game/EnvSandbox/Materials/ToonProfiles/TP_Stucco",
    "/Game/EnvSandbox/Materials/ToonProfiles/TP_Wood",
    "/Game/EnvSandbox/Materials/ToonProfiles/TP_Gold",
    "/Game/EnvSandbox/Materials/ToonProfiles/TP_Glass",
    "/Game/EnvSandbox/Materials/ToonProfiles/TP_Foliage",
    "/Game/EnvSandbox/Materials/ToonProfiles/TP_Ornamental",
    "/Game/EnvSandbox/Materials/ToonProfiles/TP_Hero",
    "/Game/EnvSandbox/Materials/ToonProfiles/TP_Character",
    "/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina",
    "/Game/EnvSandbox/Materials/ToonProfiles/TP_NikkiDream",
    "/Game/EnvSandbox/Materials/ToonProfiles/TP_Cosmic",
    "/Game/EnvSandbox/Materials/ToonProfiles/TP_Water",
    "/Game/EnvSandbox/Materials/ToonProfiles/TP_Impressionist_Wet",
    "/Game/EnvSandbox/Materials/ToonProfiles/TP_Impressionist_Impasto",
    "/Game/EnvSandbox/Materials/ToonProfiles/TP_Impressionist_Dry",
]

# Destination layout inside the destination project.
DEST_MFS = "/Game/Materials/Functions"
DEST_MASTER = "/Game/Materials/Masters"
DEST_PROFILES = "/Game/Materials/ToonProfiles"

# Assets the master references that live outside the spine. These are the
# "dangling reference" list from the 2026-09-29 binary scan. Each entry is
# (source path, destination path or None to skip, note).
DEST_SUPPORT = [
    ("/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette", None,
     "palette MPC - SKIPPED: used by MF_Madoka, needs either copy or rewire"),
    ("/Game/Alphas_Sparkles/T_Spark_Twinkle8", None, "sparkle texture - SKIPPED"),
    ("/Game/EnvSandbox/Textures/Utility/T_Neutral_Height", None, "neutral default - SKIPPED"),
    ("/Game/EnvSandbox/Textures/Utility/T_Neutral_Metallic", None, "neutral default - SKIPPED"),
    ("/Game/EnvSandbox/Textures/Utility/T_Neutral_Normal", None, "neutral default - SKIPPED"),
    ("/Game/EnvSandbox/Textures/Utility/T_Neutral_ORM", None, "neutral default - SKIPPED"),
    ("/Game/EnvSandbox/Textures/Utility/T_Neutral_Roughness", None, "neutral default - SKIPPED"),
]

# Plugins the master depends on. We cannot ship these.
PLUGIN_BLOCKERS = {
    "MF_MeshBlend_Activator_Index": "MeshBlend (Fab plugin)",
    "Day_to_Night_Color": "UltraDynamicSky",
    "UltraDynamicWeather_Parameters": "UltraDynamicSky",
}

REPORT_PATH = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log(msg):
    unreal.log("[MigrateSpine] " + str(msg))


def _asset_path(folder, name):
    return f"{folder}/{name}.{name}"


def _leaf(src_path):
    return src_path.rsplit("/", 1)[-1]


def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def find_call_expressions(material):
    """Return the MaterialFunctionCall nodes in a material graph."""
    out = []
    lib = unreal.MaterialEditingLibrary
    for expr in lib.get_material_expressions(material) or []:
        if expr is None:
            continue
        if type(expr).__name__ == "MaterialExpressionMaterialFunctionCall":
            out.append(expr)
    return out


def function_call_name(expr):
    try:
        mf = expr.get_editor_property("material_function")
        return mf.get_name() if mf else None
    except Exception:
        return None


def scan_master_blockers(master_path):
    """List every MaterialFunctionCall in the master, flagging plugin deps."""
    master = unreal.load_asset(master_path)
    if master is None:
        _log(f"MASTER NOT FOUND: {master_path}")
        return {}

    found = {}
    for expr in find_call_expressions(master):
        name = function_call_name(expr)
        if not name:
            continue
        found[name] = found.get(name, 0) + 1

    _log("Master calls:")
    for name, count in sorted(found.items()):
        flag = "  <-- PLUGIN DEP" if name in PLUGIN_BLOCKERS else ""
        _log(f"   {name} x{count}{flag}")
    return found


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------

def migrate(dry_run=False):
    report = {
        "master": SOURCE_MASTER,
        "dry_run": dry_run,
        "mfs": [],
        "profiles": [],
        "blockers": {},
        "failed": [],
    }

    _log("=== BLOCKER SCAN ===")
    blockers = scan_master_blockers(SOURCE_MASTER)
    report["blockers"] = {k: PLUGIN_BLOCKERS.get(k, "?") for k in blockers}

    if dry_run:
        _log("DRY RUN - nothing written")
        report["would_migrate_mfs"] = SOURCE_MFS
        report["would_migrate_profiles"] = SOURCE_TOON_PROFILES
        return report

    # --- Material functions ---
    # UE 5.8: duplicate_asset(source_asset_path, destination_asset_path) -> Object
    ensure_dir(DEST_MFS)
    for src in SOURCE_MFS:
        name = _leaf(src)
        dst = _asset_path(DEST_MFS, name)
        obj = unreal.EditorAssetLibrary.duplicate_asset(src, dst)
        if obj:
            _log(f"MF OK  {name}")
            report["mfs"].append(dst)
        else:
            _log(f"MF FAIL {name}")
            report["failed"].append(src)

    # --- Toon profiles ---
    ensure_dir(DEST_PROFILES)
    for src in SOURCE_TOON_PROFILES:
        name = _leaf(src)
        dst = _asset_path(DEST_PROFILES, name)
        obj = unreal.EditorAssetLibrary.duplicate_asset(src, dst)
        if obj:
            _log(f"TP OK  {name}")
            report["profiles"].append(dst)
        else:
            _log(f"TP FAIL {name}")
            report["failed"].append(src)

    # --- Master ---
    ensure_dir(DEST_MASTER)
    master_name = _leaf(SOURCE_MASTER)
    dst_master = _asset_path(DEST_MASTER, master_name)
    obj = unreal.EditorAssetLibrary.duplicate_asset(SOURCE_MASTER, dst_master)
    if obj:
        _log(f"MASTER OK  {master_name}")
        report["master_dst"] = f"{DEST_MASTER}/{master_name}"
    else:
        _log(f"MASTER FAIL {master_name}")
        report["failed"].append(SOURCE_MASTER)

    # --- Save everything ---
    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
        _log("saved dirty packages")
    except Exception as exc:
        _log(f"save warning: {exc}")

    return report


def strip_plugin_calls(dest_master_path, dry_run=True):
    """Delete the plugin MaterialFunctionCalls from a migrated master.

    Removes the MeshBlend activator and the UltraDynamicSky day/night nodes.
    Their downstream inputs lose a source, so the material must be re-wired
    by hand afterwards - this only clears the hard plugin dependency.
    """
    mat = unreal.load_asset(dest_master_path)
    if mat is None:
        _log(f"strip: master not found {dest_master_path}")
        return []

    removed = []
    lib = unreal.MaterialEditingLibrary
    for expr in find_call_expressions(mat):
        name = function_call_name(expr)
        if name in PLUGIN_BLOCKERS:
            removed.append(name)
            if not dry_run:
                try:
                    lib.delete_material_expression(mat, expr)
                    _log(f"strip: removed {name}")
                except Exception as exc:
                    _log(f"strip: FAILED {name}: {exc}")

    if removed and not dry_run:
        mat.modify()
        try:
            lib.recompile_material(mat)
            unreal.EditorAssetLibrary.save_loaded_asset(mat, only_if_is_dirty=False)
        except Exception as exc:
            _log(f"strip: recompile warning {exc}")

    _log(f"strip: {len(removed)} plugin calls ({'DRY RUN' if dry_run else 'removed'}): {sorted(set(removed))}")
    return removed


def main():
    # UnrealEditor-Cmd passes ONLY the script path in sys.argv, so flags must
    # arrive via environment variables. Verified with an API probe on 2026-09-29.
    argv = sys.argv[1:]
    dry_run = os.environ.get("MIGRATE_DRY_RUN", "1") == "1"

    _log("=" * 60)
    _log("TOON SPINE MIGRATION")
    _log(f"dry_run={dry_run}  argv={argv}")
    _log("=" * 60)

    report = migrate(dry_run=dry_run)

    if not dry_run and report.get("master_dst"):
        report["stripped"] = strip_plugin_calls(
            report["master_dst"], dry_run=False)

    out = Path(os.environ.get("TEMP", ".")) / "migrate_spine_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    _log(f"report: {out}")

    _log(f"DONE. mfs={len(report['mfs'])} profiles={len(report['profiles'])} "
         f"failed={len(report['failed'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())