"""Portable release checks for the FILM-304 toon spine.

Run from the repository root:
    python Python/verify_repo.py

This intentionally does not import Unreal. Editor-backed material validation remains
an Unreal-side check; this script protects the clone/repository contract.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "MelodiaToonFilm.uproject",
    "README.md",
    "CONTRIBUTING.md",
    ".gitignore",
    ".gitattributes",
    "Config/DefaultEngine.ini",
    "Docs/TOON_SPINE.md",
    "Docs/FILM_PIPELINE.md",
    "Python/build_master.py",
    "Python/extract_dependencies.py",
]
FORBIDDEN_TRACKED_PARTS = {"Binaries", "DerivedDataCache", "Intermediate", "Saved", "__pycache__"}
BINARY_SUFFIXES = {".uasset", ".umap", ".fbx", ".exr", ".hdr", ".wav", ".mp4", ".mov"}


def tracked_files() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(f"git ls-files failed: {exc}") from exc
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def check_lfs(path: str) -> bool:
    result = subprocess.run(
        ["git", "check-attr", "filter", "--", path],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.rstrip().endswith(": lfs")


def main() -> int:
    errors: list[str] = []

    for rel in REQUIRED:
        if not (ROOT / rel).exists():
            errors.append(f"missing required path: {rel}")

    try:
        tracked = tracked_files()
    except RuntimeError as exc:
        print(f"FAIL: {exc}")
        return 1

    for rel in tracked:
        parts = set(Path(rel).parts)
        bad = sorted(parts & FORBIDDEN_TRACKED_PARTS)
        if bad:
            errors.append(f"generated path is tracked: {rel} ({', '.join(bad)})")
        if Path(rel).suffix.lower() in BINARY_SUFFIXES and not check_lfs(rel):
            errors.append(f"binary asset is not LFS-owned: {rel}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if "C:/EnvironmentPortfolio" in readme or "C:\\EnvironmentPortfolio" in readme:
        errors.append("README contains a machine-specific EnvironmentPortfolio path")

    if errors:
        print("FILM-304 repository contract: FAIL")
        for error in errors:
            print(f" - {error}")
        return 1

    print(f"FILM-304 repository contract: PASS ({len(tracked)} tracked files checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
