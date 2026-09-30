"""Two-hop migration of the toon spine: BS_GodFile -> 304 film project.

WHY TWO HOPS
------------
unreal.EditorAssetLibrary.duplicate_asset(src, dst) only works WITHIN one
project - both paths must resolve in the project currently loaded. It cannot
copy from BS_GodFile into a different project.

So the spine is renamed IN PLACE inside BS_GodFile first (hop 1), which makes
UE remap every internal reference correctly, and the on-disk bytes now form a
self-consistent, single-project folder that can be filesystem-copied. The copy
is renamed again in the destination project (hop 2) to its final path.

Every step is reversible: hop 1 is a rename with an exact recorded target, and
hop 2 happens in the new project only.

Flags arrive as ENV VARS because UnrealEditor-Cmd puts only the script path in
sys.argv (verified 2026-09-29).

    Hop 1 (source project):
        SPINE_PHASE=rename_in SPINE_CONTENT=<src Content dir> MIGRATE_DRY_RUN=0 \
        UnrealEditor-Cmd.exe <BS_GodFile.uproject> -ExecutePythonScript=this.py \
            -stdout -unattended

    Copy the staged folder across by hand.

    Hop 2 (destination project):
        SPINE_PHASE=finalize MIGRATE_DRY_RUN=0 \
        UnrealEditor-Cmd.exe <304.uproject> -ExecutePythonScript=this.py \
            -stdout -unattended

    Revert (if needed):
        SPINE_PHASE=revert SPINE_REPORT=<report.json> MIGRATE_DRY_RUN=0 \
        UnrealEditor-Cmd.exe <BS_GodFile.uproject> -ExecutePythonScript=this.py

Report is written to %TEMP%/spine_migration.json - assert on THAT, not the log.
unreal.log() is unreliable under -stdout capture.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import unreal

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SRC_MF_DIR = "/Game/EnvSandbox/Materials/Functions"
SRC_MASTER_DIR = "/Game/EnvSandbox/Materials/Masters"
SRC_PROFILE_DIR = "/Game/EnvSandbox/Materials/ToonProfiles"

STAGE_ROOT = "/Game/_304FilmSpine"
STAGE_MF_DIR = f"{STAGE_ROOT}/Functions"
STAGE_MASTER_DIR = f"{STAGE_ROOT}/Masters"
STAGE_PROFILE_DIR = f"{STAGE_ROOT}/ToonProfiles"

FINAL_ROOT = "/Game/Materials"
FINAL_MF_DIR = f"{FINAL_ROOT}/Functions"
FINAL_MASTER_DIR = f"{FINAL_ROOT}/Masters"
FINAL_PROFILE_DIR = f"{FINAL_ROOT}/ToonProfiles"

# The 9 plugin-free MFs the headless scan proved the master actually calls.
# MF_MeshBlend_Activator_Index_0 is DELIBERATELY INCLUDED: it is /Game/ project
# content built from stock engine nodes only (Constant, StaticSwitchParameter,
# ScalarParameter, If, PerInstanceCustomData), not plugin content. Its name
# mentions MeshBlend but it needs no plugin. Verified by binary scan 2026-09-29.
SPINE_MFS = [
    "MF_NormalAdjust",
    "MF_ColorRamp3",
    "MF_SpaceParallax",
    "MF_Madoka",
    "MF_Itto",
    "MF_NikkiDreamGrade",
    "MF_DF_ContactBlend",
    "MF_Impressionist_Impasto",
    "MF_ClothWindDrape",
]

# Lives at /Game/Materials/, NOT under EnvSandbox - verified on disk 2026-09-29.
SPINE_MFS_ROOT_MATERIALS = ["MF_MeshBlend_Activator_Index_0"]

MASTER_NAME = "M_Master_Toon_Universal"

SPINE_PROFILES = [
    "TP_Default", "TP_Stone", "TP_Stucco", "TP_Wood", "TP_Gold", "TP_Glass",
    "TP_Foliage", "TP_Ornamental", "TP_Hero", "TP_Character", "TP_Melusina",
    "TP_NikkiDream", "TP_Cosmic", "TP_Water", "TP_Impressionist_Wet",
    "TP_Impressionist_Impasto", "TP_Impressionist_Dry",
]

# Genuine third-party content the master references. UltraDynamicSky only.
KNOWN_PLUGIN_DEPS = {"Day_to_Night_Color", "UltraDynamicWeather_Parameters"}

REPORT = Path(os.environ.get("TEMP", ".")) / "spine_migration.json"


def log(m):
    unreal.log("[Spine] " + str(m))


def obj_path(folder, name):
    return f"{folder}/{name}"


def ensure_dir(p):
    if not unreal.EditorAssetLibrary.does_directory_exist(p):
        unreal.EditorAssetLibrary.make_directory(p)


def save_all():
    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    except Exception as e:
        log(f"save warning: {e}")


def mf_calls(material):
    lib = unreal.MaterialEditingLibrary
    out = []
    for e in lib.get_material_expressions(material) or []:
        if e is not None and type(e).__name__ == "MaterialExpressionMaterialFunctionCall":
            try:
                mf = e.get_editor_property("material_function")
                if mf:
                    out.append(mf.get_path_name())
            except Exception:
                pass
    return out


def mf_leaf(obj_path_str):
    return obj_path_str.rsplit("/", 1)[-1].split(".", 1)[0]


# ---------------------------------------------------------------------------
# Hop 1 - rename in place inside the SOURCE project
# ---------------------------------------------------------------------------

def hop1_rename_in(dry_run):
    report = {
        "phase": "rename_in",
        "dry_run": dry_run,
        "renamed": [],
        "revert_map": [],
        "failed": [],
    }

    log("=== HOP 1: rename spine to staging paths ===")

    pairs = [(f"{SRC_MASTER_DIR}/{MASTER_NAME}", f"{STAGE_MASTER_DIR}/{MASTER_NAME}")]
    pairs += [(f"{SRC_MF_DIR}/{n}", f"{STAGE_MF_DIR}/{n}") for n in SPINE_MFS]
    pairs += [(f"/Game/Materials/{n}", f"{STAGE_MF_DIR}/{n}")
              for n in SPINE_MFS_ROOT_MATERIALS]
    pairs += [(f"{SRC_PROFILE_DIR}/{n}", f"{STAGE_PROFILE_DIR}/{n}") for n in SPINE_PROFILES]

    if dry_run:
        report["would_rename"] = [[s, d] for s, d in pairs]
        for s, d in pairs:
            log(f"would rename {s} -> {d}")
        return report

    for folder in (STAGE_MF_DIR, STAGE_MASTER_DIR, STAGE_PROFILE_DIR):
        ensure_dir(folder)

    # Master FIRST: renaming it remaps its own MF references, so the MFs move
    # afterwards without leaving the master pointing at stale paths.
    for src, dst in pairs:
        if not unreal.EditorAssetLibrary.does_asset_exist(src):
            log(f"SKIP (absent) {src}")
            report["failed"].append({"src": src, "reason": "absent"})
            continue
        if unreal.EditorAssetLibrary.rename_asset(src, dst):
            log(f"OK   {src} -> {dst}")
            report["renamed"].append(dst)
            report["revert_map"].append({"new": dst, "old": src})
        else:
            log(f"FAIL {src} -> {dst}")
            report["failed"].append({"src": src, "dst": dst, "reason": "rename_failed"})

    save_all()

    m = unreal.load_asset(f"{STAGE_MASTER_DIR}/{MASTER_NAME}")
    if m:
        calls = mf_calls(m)
        report["master_after"] = calls
        report["master_after_leaves"] = sorted({mf_leaf(c) for c in calls})
        log(f"master loads after move; {len(calls)} MF calls resolve")
    else:
        report["master_after"] = "LOAD_FAILED"

    return report


# ---------------------------------------------------------------------------
# Hop 2 - finalise inside the DESTINATION project
# ---------------------------------------------------------------------------

def hop2_finalize(dry_run):
    report = {"phase": "finalize", "dry_run": dry_run,
              "renamed": [], "failed": [], "verify": {}}

    log("=== HOP 2: rename staging -> final paths ===")

    pairs = [(f"{STAGE_MASTER_DIR}/{MASTER_NAME}", f"{FINAL_MASTER_DIR}/{MASTER_NAME}")]
    pairs += [(f"{STAGE_MF_DIR}/{n}", f"{FINAL_MF_DIR}/{n}")
              for n in SPINE_MFS + SPINE_MFS_ROOT_MATERIALS]
    pairs += [(f"{STAGE_PROFILE_DIR}/{n}", f"{FINAL_PROFILE_DIR}/{n}") for n in SPINE_PROFILES]

    if dry_run:
        report["would_rename"] = [[s, d] for s, d in pairs]
        for s, d in pairs:
            log(f"would rename {s} -> {d}")
        return report

    for folder in (FINAL_MF_DIR, FINAL_MASTER_DIR, FINAL_PROFILE_DIR):
        ensure_dir(folder)

    for src, dst in pairs:
        if not unreal.EditorAssetLibrary.does_asset_exist(src):
            log(f"SKIP (absent) {src}")
            report["failed"].append({"src": src, "reason": "absent"})
            continue
        if unreal.EditorAssetLibrary.rename_asset(src, dst):
            log(f"OK   {src} -> {dst}")
            report["renamed"].append(dst)
        else:
            log(f"FAIL {src} -> {dst}")
            report["failed"].append({"src": src, "dst": dst, "reason": "rename_failed"})

    save_all()
    return verify_destination()


def verify_destination():
    """Prove the migrated master loads and every called MF resolves here."""
    v = {}
    m = unreal.load_asset(f"{FINAL_MASTER_DIR}/{MASTER_NAME}")
    if m is None:
        v["master"] = "LOAD_FAILED"
        log("VERIFY FAIL: master does not load")
        return v

    calls = mf_calls(m)
    v["master_loads"] = True
    v["mf_call_count"] = len(calls)
    v["mf_leaves"] = sorted({mf_leaf(c) for c in calls})

    resolved, unresolved, plugin = [], [], []
    for c in calls:
        leaf = mf_leaf(c)
        here = unreal.EditorAssetLibrary.does_asset_exist(f"{FINAL_MF_DIR}/{leaf}")
        if here:
            resolved.append(leaf)
            continue
        # is it anywhere else in this project?
        ar = unreal.AssetRegistryHelpers.get_asset_registry()
        found = ar.get_assets_by_package_name(f"/Game/{leaf}", False)
        if found:
            resolved.append(f"{leaf} (elsewhere: /Game/{leaf})")
        elif leaf in KNOWN_PLUGIN_DEPS:
            plugin.append(leaf)
        else:
            unresolved.append(leaf)

    v["resolved"] = sorted(set(resolved))
    v["unresolved"] = sorted(set(unresolved))
    v["plugin_deps"] = sorted(set(plugin))
    v["clean"] = not unresolved and not plugin

    log(f"VERIFY: {len(calls)} calls | resolved={len(v['resolved'])} "
        f"unresolved={v['unresolved']} plugin={v['plugin_deps']} "
        f"CLEAN={v['clean']}")
    return v


# ---------------------------------------------------------------------------
# Revert
# ---------------------------------------------------------------------------

def hop1_revert(report_path, dry_run):
    log("=== REVERT: staging -> original BS_GodFile paths ===")
    data = json.loads(Path(report_path).read_text(encoding="utf-8"))
    pairs = [(r["new"], r["old"]) for r in reversed(data.get("revert_map", []))]
    out = {"phase": "revert", "reverted": [], "failed": [], "dry_run": dry_run}

    if dry_run:
        out["would_revert"] = [[s, d] for s, d in pairs]
        for s, d in pairs:
            log(f"would revert {s} -> {d}")
        return out

    for new, old in pairs:
        if not unreal.EditorAssetLibrary.does_asset_exist(new):
            log(f"SKIP (absent) {new}")
            out["failed"].append({"src": new, "reason": "absent"})
            continue
        if unreal.EditorAssetLibrary.rename_asset(new, old):
            log(f"reverted {new} -> {old}")
            out["reverted"].append(old)
        else:
            log(f"FAIL revert {new} -> {old}")
            out["failed"].append({"src": new, "dst": old, "reason": "rename_failed"})

    save_all()
    m = unreal.load_asset(f"{SRC_MASTER_DIR}/{MASTER_NAME}")
    out["master_restored"] = m is not None
    log(f"REVERT DONE: {len(out['reverted'])} restored | "
        f"master back at original path: {out['master_restored']}")
    return out


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    phase = os.environ.get("SPINE_PHASE", "scan")
    dry = os.environ.get("MIGRATE_DRY_RUN", "1") == "1"
    log(f"phase={phase} dry_run={dry} argv={sys.argv}")

    if phase == "rename_in":
        rep = hop1_rename_in(dry)
    elif phase == "finalize":
        rep = hop2_finalize(dry)
    elif phase == "revert":
        rp = os.environ.get("SPINE_REPORT", "")
        rep = hop1_revert(rp, dry) if rp else {"error": "set SPINE_REPORT"}
    elif phase == "verify":
        rep = {"phase": "verify", "verify": verify_destination()}
    else:
        m = (unreal.load_asset(f"{STAGE_MASTER_DIR}/{MASTER_NAME}")
             or unreal.load_asset(f"{SRC_MASTER_DIR}/{MASTER_NAME}"))
        rep = {"phase": "scan",
               "master": m.get_path_name() if m else None,
               "mf_leaves": sorted({mf_leaf(c) for c in mf_calls(m)}) if m else []}
        log(f"scan: {rep}")

    REPORT.write_text(json.dumps(rep, indent=2), encoding="utf-8")
    log(f"report -> {REPORT}")
    return 0


if __name__ == "__main__":
    main()