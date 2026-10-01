"""Fork synchronisation check: is the vendored brutalist set still truthful?

WHY THIS EXISTS
---------------
This repo carries a vendored copy of part of the Melodia geometry-node library
(`Blender/surreal_arch/`). The copy is ONE-WAY: assets come down from the source
project, never back up. On 2026-09-30 that copy was found **226 lines stale** in
`brutalist_city.py`, and the staleness was only noticed because a probe returned
an impossible vertex count. A stale fork does not error - it silently measures
the wrong code and reports it as fact.

So drift is checked, not remembered.

    python Tools/resync_fork.py                     # report, exit 1 on drift
    python Tools/resync_fork.py --write             # re-extract + manifest
    python Tools/resync_fork.py --upstream <path>   # override the source project

FILE POLICY - two lists, and the difference is load-bearing:

VERBATIM  copied byte-for-byte from upstream. Any difference is drift.
THINNED   deliberately trimmed for this repo (`presets.py` carries only the 21
          BR_* preset blocks out of a 222 KB catalogue; `__init__.py` registers
          only the vendored builders). These are NEVER overwritten - a blind
          copy would drag ~200 KB of unrelated builders and their imports into
          the film repo. Drift here is reported for a human decision only.

Anything not on either list is reported as UNTRACKED so a new dependency cannot
ride in unnoticed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FORK = REPO / "Blender" / "surreal_arch" / "melodia_gn"
MANIFEST = REPO / "Blender" / "FORK_SYNC.json"

DEFAULT_UPSTREAM = Path(
    r"P:\MelodiaMelusinaV2-Laptop\deploy\surreal_arch\melodia_gn")

# Copied verbatim from upstream - any byte difference is drift.
VERBATIM = (
    "brutalist_city.py",
    "brutalist_cubicles.py",
    "brutalist_materials.py",
    "brutalist_office.py",
    "brutalist_roofs.py",
    "brutalist_uv.py",
    "core.py",
    "higgsas_pipeline.py",
    "logging.py",
    "paris_common.py",
    "time.py",
)

# Deliberately trimmed for this repo. Never overwritten.
THINNED = (
    "presets.py",
    "__init__.py",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def upstream_commit(path: Path) -> str:
    """Best-effort commit id of the source project, or a marker if unavailable."""
    try:
        out = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=15)
        if out.returncode == 0:
            return out.stdout.strip()
        return "unknown (not a git work tree)"
    except Exception as exc:                       # pragma: no cover
        return "unknown (%s)" % type(exc).__name__


def compare(upstream: Path):
    """Per-file state for everything the fork carries."""
    rows = []
    for name in VERBATIM:
        up, fk = upstream / name, FORK / name
        if not up.exists():
            rows.append((name, "UPSTREAM_MISSING", None, None))
        elif not fk.exists():
            rows.append((name, "MISSING_IN_FORK", sha256(up), None))
        else:
            a, b = sha256(up), sha256(fk)
            rows.append((name, "IN_SYNC" if a == b else "DRIFT", a, b))
    for name in THINNED:
        up, fk = upstream / name, FORK / name
        rows.append((name, "THINNED",
                     sha256(up) if up.exists() else None,
                     sha256(fk) if fk.exists() else None))
    known = set(VERBATIM) | set(THINNED)
    for p in sorted(FORK.glob("*.py")):
        if p.name not in known:
            rows.append((p.name, "UNTRACKED_IN_FORK", None, sha256(p)))
    return rows


def verify_against_manifest() -> int:
    """For a clone without upstream: check the fork against recorded hashes."""
    if not MANIFEST.exists():
        print("  ! no manifest recorded yet (run --write where the upstream "
              "is available)")
        return 0
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    files = m.get("files", {})
    print("  recorded : %s from commit %s"
          % (m.get("written"), m.get("upstream_commit")))
    bad = []
    for name, digest in files.items():
        p = FORK / name
        if not p.exists():
            bad.append((name, "MISSING"))
        elif sha256(p) != digest:
            bad.append((name, "CHANGED"))
    if bad:
        for name, state in bad:
            print("  x %-26s %s since the manifest was written" % (name, state))
        print("RESULT: FAIL - vendored files no longer match the manifest")
        return 1
    print("  v all %d vendored file(s) match the recorded manifest" % len(files))
    print("RESULT: PASS (manifest check only - upstream not available here)")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--write", action="store_true",
                    help="re-extract VERBATIM files and write FORK_SYNC.json")
    ap.add_argument("--upstream", default=str(DEFAULT_UPSTREAM),
                    help="path to the source project's melodia_gn folder")
    args = ap.parse_args(argv)

    upstream = Path(args.upstream)
    print("=" * 72)
    print("FORK SYNC CHECK")
    print("  upstream : %s" % upstream)
    print("  fork     : %s" % FORK)

    if not FORK.is_dir():
        print("  x fork folder not found - is Blender/ present in this clone?")
        return 2

    # A group member's clone has the film repo but NOT the source project. That
    # is the normal case, not an error - fall back to the recorded manifest.
    if not upstream.is_dir():
        print("  ! upstream not present here (normal for a group clone)")
        return verify_against_manifest()

    rows = compare(upstream)
    print("  commit   : %s" % upstream_commit(upstream.parent.parent))
    print("-" * 72)
    marks = {"IN_SYNC": "v", "THINNED": "~", "DRIFT": "x",
             "MISSING_IN_FORK": "x", "UNTRACKED_IN_FORK": "?",
             "UPSTREAM_MISSING": "x"}
    for name, state, _a, _b in rows:
        print("  %s %-26s %s" % (marks.get(state, "?"), name, state))

    if args.write:
        written = {}
        for name in VERBATIM:
            src = upstream / name
            if src.exists():
                (FORK / name).write_bytes(src.read_bytes())
                written[name] = sha256(FORK / name)
                print("    wrote %s" % name)
        MANIFEST.write_text(json.dumps({
            "written": date.today().isoformat(),
            "upstream": str(upstream),
            "upstream_commit": upstream_commit(upstream.parent.parent),
            "verbatim": list(VERBATIM),
            "thinned": list(THINNED),
            "files": written,
        }, indent=2), encoding="utf-8")
        print("  manifest -> %s" % MANIFEST)
        # Re-derive AFTER writing. Without this the tool prints the pre-write
        # verdict and exits 1 even though it just fixed everything - which would
        # make verify_all.ps1 fail on a successful resync. Caught by running it.
        rows = compare(upstream)

    drift = [r for r in rows if r[1] in ("DRIFT", "MISSING_IN_FORK",
                                         "UNTRACKED_IN_FORK", "UPSTREAM_MISSING")]
    print("-" * 72)
    if not drift:
        print("RESULT: PASS - vendored set matches upstream")
        return 0
    print("RESULT: DRIFT - %d file(s) differ" % len(drift))
    for name, state, _a, _b in drift[:10]:
        print("   %s: %s" % (state, name))
    print("   re-extract with:  python Tools/resync_fork.py --write")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

