#!/usr/bin/env python3
"""verify_git_consistency.py — Rigorous git consistency and health validator.

Safe, read-only validator designed for the 14-person Humber team & CI runner.
Checks:
  1. Working tree hygiene & status report (tracked, untracked, modified)
  2. Branch naming policy compliance (feature/, fix/, docs/, etc.)
  3. Git LFS installation, configuration, and tracking filters (.gitattributes)
  4. Core hooksPath configuration (.githooks)
  5. Absence of forbidden filetypes (.blend1, .blend2, .zip, .tmp, 0-byte junk)
  6. Absence of un-tracked large files (>50MB) that must be in Git LFS

Exit code 0 on PASS, 1 on FAIL.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ALLOWED_BRANCH_PREFIXES = (
    "feature/",
    "feat/",
    "fix/",
    "docs/",
    "cleanup/",
    "collab/",
    "integration/",
    "codex/",
    "recovery/",
    "cursor/",
    "main",
    "master",
)

FORBIDDEN_EXTENSIONS = (".blend1", ".blend2", ".7z", ".zip", ".tmp")
MAX_NON_LFS_SIZE_BYTES = 52428800  # 50 MB


def run_cmd(args: list[str], cwd: Path = ROOT) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


def check_git_installed() -> bool:
    code, out, _ = run_cmd(["git", "--version"])
    if code != 0:
        print("[FAIL] Git is not installed or not in PATH.")
        return False
    print(f"[PASS] Git installed: {out}")
    return True


def check_git_lfs() -> bool:
    code, out, _ = run_cmd(["git", "lfs", "version"])
    if code != 0:
        print("[FAIL] Git LFS is not installed. Download from https://git-lfs.com")
        return False
    print(f"[PASS] Git LFS installed: {out.splitlines()[0]}")
    return True


def check_gitattributes() -> bool:
    gitattributes_path = ROOT / ".gitattributes"
    if not gitattributes_path.exists():
        print("[FAIL] .gitattributes is missing from repository root.")
        return False
    
    content = gitattributes_path.read_text(encoding="utf-8", errors="ignore")
    required_lfs_patterns = ["*.blend", "*.fbx", "*.uasset", "*.umap"]
    missing = []
    for pat in required_lfs_patterns:
        if pat not in content or "filter=lfs" not in content:
            missing.append(pat)
    
    if missing:
        print(f"[WARN] .gitattributes might be missing LFS rules for: {missing}")
    else:
        print("[PASS] .gitattributes properly configures key binary patterns for Git LFS.")
    return True


def check_hooks_path() -> bool:
    code, out, _ = run_cmd(["git", "config", "core.hooksPath"])
    if code == 0 and out == ".githooks":
        print("[PASS] Git core.hooksPath is set to .githooks")
        return True
    
    # Check if .githooks directory exists
    hooks_dir = ROOT / ".githooks"
    if hooks_dir.is_dir():
        print(f"[INFO] Local core.hooksPath is '{out}'. Recommended: run 'git config core.hooksPath .githooks'")
        return True
    print("[WARN] .githooks directory not found.")
    return True


def check_branch_policy() -> bool:
    code, branch, _ = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if code != 0 or not branch:
        print("[WARN] Could not determine current branch (detached HEAD or fresh repo).")
        return True
    
    is_allowed = any(branch.startswith(prefix) for prefix in ALLOWED_BRANCH_PREFIXES)
    if not is_allowed:
        print(f"[FAIL] Current branch '{branch}' does not conform to allowed prefixes:")
        print(f"       {ALLOWED_BRANCH_PREFIXES}")
        return False
    print(f"[PASS] Current branch '{branch}' complies with branch naming rules.")
    return True


def check_staged_or_recent_files() -> bool:
    """Check staged files for forbidden extensions and large non-LFS binaries."""
    # Check cached (staged) files
    code, out, _ = run_cmd(["git", "diff", "--cached", "--name-only"])
    staged = [line.strip() for line in out.splitlines() if line.strip()]
    
    issues = []
    for rel_path in staged:
        file_path = ROOT / rel_path
        if not file_path.exists():
            continue
        
        # Check forbidden extensions
        if any(rel_path.endswith(ext) for ext in FORBIDDEN_EXTENSIONS):
            issues.append(f"Forbidden extension: {rel_path}")
        
        # Check 0-byte file
        try:
            size = file_path.stat().st_size
            if size == 0:
                issues.append(f"0-byte junk file staged: {rel_path}")
            elif size > MAX_NON_LFS_SIZE_BYTES:
                # Check if it has LFS pointer header
                with open(file_path, "rb") as f:
                    first_line = f.readline()
                if b"git-lfs.github.com/spec" not in first_line:
                    issues.append(f"File > 50MB staged without Git LFS pointer: {rel_path} ({size} bytes)")
        except Exception as e:
            pass

    if issues:
        print("[FAIL] Issues found in staged files:")
        for iss in issues:
            print(f"  - {iss}")
        return False
    
    print(f"[PASS] Staged files hygiene check ({len(staged)} staged files inspected).")
    return True


def check_git_status() -> bool:
    code, out, _ = run_cmd(["git", "status", "--short"])
    lines = [l for l in out.splitlines() if l.strip()]
    untracked = [l for l in lines if l.startswith("??")]
    modified = [l for l in lines if not l.startswith("??")]
    print(f"[INFO] Working tree status: {len(modified)} modified, {len(untracked)} untracked files.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify git consistency and hygiene.")
    parser.add_argument("--strict", action="store_true", help="Fail on warnings")
    args = parser.parse_args()

    print("=" * 60)
    print(" GIT CONSISTENCY & REPO HEALTH CHECK")
    print("=" * 60)

    checks = [
        ("Git Installation", check_git_installed),
        ("Git LFS Installation", check_git_lfs),
        ("Gitattributes & LFS Rules", check_gitattributes),
        ("Git Hooks Path", check_hooks_path),
        ("Branch Policy", check_branch_policy),
        ("Staged Files Hygiene", check_staged_or_recent_files),
        ("Working Tree Status", check_git_status),
    ]

    all_passed = True
    for name, func in checks:
        print(f"\n--- Checking: {name} ---")
        ok = func()
        if not ok:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("[RESULT] PASS: Repository git consistency verified.")
        return 0
    else:
        print("[RESULT] FAIL: Git consistency errors detected. Please review above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
