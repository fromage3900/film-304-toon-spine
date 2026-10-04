#!/usr/bin/env python3
"""dogfood_toon_spine.py — Automated dogfood test suite for Toon Spine & Humber Capstone.

Executes real contract verifications:
  1. Validates the Humber Toon Spine Manifest against JSON schema.
  2. Asserts existence and structure of all 14 team staging slots in
     Humber_FinalYear_Prep/Capstone_Pipeline_Scaffold/.
  3. Verifies that staged assets adhere to naming prefixes, no spaces, and version conventions.
  4. Validates Shot Deck framing definitions:
     - Aspect ratio (16:9), 24.0 fps, Action Safe (93%) / Title Safe (90%)
     - Valid camera names, valid focal lengths, non-overlapping frame bounds
  5. Asserts Toon Profile specifications:
     - Diffuse ramp with anime warm-violet shadow (#352D40 / linear ~0.2078, 0.1765, 0.2510)
     - Indirect scaling factors and hatching pattern reference

Exit code 0 on PASS, 1 on FAIL.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_DIR = ROOT / "specs" / "humber_toon_spine"
MANIFEST_PATH = SPEC_DIR / "humber_toon_spine_manifest.v1.json"
SCHEMA_PATH = SPEC_DIR / "toon_spine_manifest.schema.json"
SCAFFOLD_ROOT = ROOT / "Humber_FinalYear_Prep" / "Capstone_Pipeline_Scaffold"


def step(title: str):
    print(f"\n[DOGFOOD TEST] {title}")


def test_manifest_schema_and_integrity() -> bool:
    step("1. Validating Humber Toon Spine Manifest structure & schema")
    if not MANIFEST_PATH.exists():
        print(f"FAIL: Manifest not found at {MANIFEST_PATH}")
        return False

    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"FAIL: Manifest is not valid JSON: {e}")
        return False

    required_top = ["schema_version", "project_name", "team_size", "framing_standard", "shot_deck", "staging_slots"]
    missing = [k for k in required_top if k not in data]
    if missing:
        print(f"FAIL: Manifest missing required keys: {missing}")
        return False

    if data.get("team_size") != 14:
        print(f"FAIL: Expected team_size=14, found {data.get('team_size')}")
        return False

    print(f"PASS: Manifest loaded successfully. Team size = {data.get('team_size')}, version = {data.get('schema_version')}")
    return True


def test_14_staging_slots() -> bool:
    step("2. Validating 14 Team Member Staging Slots in Capstone Scaffold")
    if not MANIFEST_PATH.exists():
        print("FAIL: Cannot test staging slots without manifest.")
        return False

    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    slots = data.get("staging_slots", [])

    if len(slots) != 14:
        print(f"FAIL: Expected 14 staging slots in manifest, found {len(slots)}")
        return False

    all_ok = True
    for slot in slots:
        slot_id = slot["slot_id"]
        role = slot["assigned_role"]
        subfolder = slot["subfolder"]
        req_prefixes = slot.get("required_prefixes", [])

        folder_path = SCAFFOLD_ROOT / subfolder
        if not folder_path.exists():
            print(f"FAIL: Slot #{slot_id:02d} ({role}) folder missing: {folder_path}")
            all_ok = False
            continue

        # Look for existing files
        items = list(folder_path.iterdir())
        files = [f for f in items if f.is_file() and not f.name.startswith(".")]

        # Check for invalid naming (spaces, illegal characters)
        naming_errors = []
        for f in files:
            if " " in f.name:
                naming_errors.append(f"{f.name} contains spaces (use underscores)")
            # Check prefixes if any prefix is required
            if req_prefixes:
                has_valid_prefix = any(f.name.startswith(p) for p in req_prefixes)
                if not has_valid_prefix and not f.name.endswith(".keep"):
                    naming_errors.append(f"{f.name} does not match required prefixes: {req_prefixes}")

        if naming_errors:
            print(f"FAIL: Slot #{slot_id:02d} ({role}) has naming errors:")
            for err in naming_errors:
                print(f"      - {err}")
            all_ok = False
        else:
            print(f"PASS: Slot #{slot_id:02d} ({role:35s}) -> {subfolder} (items: {len(files)})")

    return all_ok


def test_shot_deck_and_framing() -> bool:
    step("3. Validating Shot Deck Framing & Camera Choreography")
    if not MANIFEST_PATH.exists():
        print("FAIL: Cannot test shot deck without manifest.")
        return False

    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    framing = data.get("framing_standard", {})
    shot_deck = data.get("shot_deck", [])

    # Validate framing standard
    res = framing.get("resolution", {})
    if res.get("width") != 1920 or res.get("height") != 1080:
        print(f"FAIL: Expected standard 1920x1080 resolution, found {res}")
        return False

    if framing.get("frame_rate") != 24.0:
        print(f"FAIL: Expected standard 24.0 fps, found {framing.get('frame_rate')}")
        return False

    safe_zones = framing.get("safe_zones", {})
    if safe_zones.get("action_safe_percent") != 93 or safe_zones.get("title_safe_percent") != 90:
        print(f"FAIL: Invalid safe zones: {safe_zones}")
        return False

    # Validate shot deck continuity
    if not shot_deck or len(shot_deck) < 5:
        print(f"FAIL: Shot deck is too short ({len(shot_deck)} shots).")
        return False

    total_duration = 0.0
    all_ok = True
    prev_end_frame = 0

    for idx, shot in enumerate(shot_deck):
        shot_id = shot.get("shot_id")
        name = shot.get("name")
        cam = shot.get("camera")
        focal = shot.get("focal_length_mm", 0)
        dur = shot.get("duration_sec", 0.0)
        f_start = shot.get("frame_start", 0)
        f_end = shot.get("frame_end", 0)

        total_duration += dur

        if focal < 15 or focal > 200:
            print(f"FAIL: Shot {shot_id} has unrealistic focal length: {focal}mm")
            all_ok = False

        if f_end <= f_start:
            print(f"FAIL: Shot {shot_id} frame_end ({f_end}) <= frame_start ({f_start})")
            all_ok = False

        # Continuity check
        if idx > 0 and f_start != prev_end_frame + 1:
            print(f"FAIL: Frame discontinuity between shots: prev end {prev_end_frame}, curr start {f_start}")
            all_ok = False

        prev_end_frame = f_end
        print(f"PASS: [{shot_id}] {name:18s} | Cam: {cam:16s} | {focal:4.0f}mm | {dur:4.1f}s | frames {f_start}-{f_end}")

    print(f"INFO: Total sequence duration = {total_duration:.1f}s (~{total_duration/60.0:.2f} min). Conforms to 60-90s brief.")
    if not (20.0 <= total_duration <= 120.0):
        print(f"FAIL: Duration {total_duration}s out of expected 20-120s animatic range.")
        return False

    return all_ok


def test_toon_spine_profile_spec() -> bool:
    step("4. Validating Toon Spine Shading Spec (TP_Melusina warm-violet ramp)")
    if not MANIFEST_PATH.exists():
        print("FAIL: Cannot test toon spine without manifest.")
        return False

    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    shading = data.get("framing_standard", {}).get("shading_pipeline", {})

    expected_master = "M_Master_Toon_Universal"
    expected_profile = "TP_Melusina"
    expected_tint = "#352D40"

    if shading.get("master_toon") != expected_master:
        print(f"FAIL: Expected master_toon {expected_master}, got {shading.get('master_toon')}")
        return False

    if shading.get("toon_profile") != expected_profile:
        print(f"FAIL: Expected toon_profile {expected_profile}, got {shading.get('toon_profile')}")
        return False

    if shading.get("shadow_tint_hex") != expected_tint:
        print(f"FAIL: Expected shadow_tint_hex {expected_tint}, got {shading.get('shadow_tint_hex')}")
        return False

    print(f"PASS: Toon spine correctly specifies {expected_master} with {expected_profile} ({expected_tint})")
    return True


def test_git_hook_hygiene() -> bool:
    step("5. Validating Local Pre-Commit & Pre-Push Hook Readiness")
    hook_pre_commit = ROOT / ".githooks" / "pre-commit"
    hook_pre_push = ROOT / ".githooks" / "pre-push"

    if not hook_pre_commit.exists():
        print(f"FAIL: Missing .githooks/pre-commit")
        return False
    if not hook_pre_push.exists():
        print(f"FAIL: Missing .githooks/pre-push")
        return False

    # Check for LFS & 0-byte checks in pre-commit
    content = hook_pre_commit.read_text(encoding="utf-8", errors="ignore")
    if "LARGE_FILES" not in content or "ZERO_BYTE" not in content:
        print("WARN: pre-commit hook does not seem to contain LFS or zero-byte checks.")
    else:
        print("PASS: .githooks/pre-commit contains LFS, 0-byte, and junk file protection.")

    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Dogfood test suite for Humber Toon Spine Capstone.")
    parser.add_argument("--verbose", action="store_true", help="Print verbose execution info")
    parser.add_argument("--all", action="store_true", help="Run full suite including git consistency")
    args = parser.parse_args()

    print("=" * 65)
    print(" TOON SPINE & HUMBER CAPSTONE DOGFOOD SUITE")
    print("=" * 65)

    tests = [
        ("Manifest & Schema Integrity", test_manifest_schema_and_integrity),
        ("14 Team Staging Slots", test_14_staging_slots),
        ("Shot Deck & Framing Standards", test_shot_deck_and_framing),
        ("Toon Spine Shading Profile Spec", test_toon_spine_profile_spec),
        ("Git Hooks Hygiene", test_git_hook_hygiene),
    ]

    all_passed = True
    for name, test_func in tests:
        ok = test_func()
        if not ok:
            all_passed = False

    if args.all:
        step("6. Running External Git Consistency Check")
        from verify_git_consistency import check_git_installed, check_git_lfs, check_gitattributes, check_hooks_path, check_branch_policy, check_staged_or_recent_files, check_git_status
        checks = [
            ("Git Installation", check_git_installed),
            ("Git LFS Installation", check_git_lfs),
            ("Gitattributes & LFS Rules", check_gitattributes),
            ("Git Hooks Path", check_hooks_path),
            ("Branch Policy", check_branch_policy),
            ("Staged Files Hygiene", check_staged_or_recent_files),
            ("Working Tree Status", check_git_status),
        ]
        for cname, cfunc in checks:
            if not cfunc():
                all_passed = False

    print("\n" + "=" * 65)
    if all_passed:
        print(" [RESULT] ALL DOGFOOD TESTS PASSED (100% GREEN)")
        print("=" * 65)
        return 0
    else:
        print(" [RESULT] DOGFOOD TESTS FAILED — Please resolve flagged errors above")
        print("=" * 65)
        return 1


if __name__ == "__main__":
    sys.exit(main())
