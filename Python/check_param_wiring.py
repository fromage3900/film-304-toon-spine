"""Static check: every parameter declared in a material builder must be CONSUMED.

WHY THIS EXISTS
    The toon master shipped 19 scalars that an artist could drag and nothing
    would happen (Saved/Audit/lookdev_census.json). That was only caught by
    walking the live graph inside the editor. This catches the same class of
    mistake in a second, without the editor, so it can run in a pre-commit hook
    or CI where no UE is available.

WHAT IT DOES
    Parses the builder with `ast`, finds every node created through a parameter
    factory (lib.scalar / lib.vector / lib.texture_param), extracts the bound
    local variable name, then counts how often that name is LOADED anywhere in
    the module. A declaration that is assigned once and never loaded is dead by
    construction - it cannot reach the graph.

Exit code 1 if any declared parameter is dead.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

# lib.scalar(...), lib.vector(...), lib.texture_param(...) -> the arg that
# names the created node is arg 0 (after the owner, which is not a literal).
PARAM_FACTORIES = {"scalar", "vector", "texture_param"}


def analyse(path: Path) -> dict:
    # utf-8-sig, not utf-8: a fixture written by PowerShell 5.1's
    # `Set-Content -Encoding utf8` carries a BOM, which would otherwise blow up
    # ast.parse with a confusing "invalid character" error.
    source = path.read_text(encoding="utf-8-sig")

    # --- structural guard: a dedented line inside a function body ---------
    # A column-0 CODE line in the MIDDLE of a function is a silent graph bug.
    # It happened in build_gouache_material.py: an edit left
    # "L.unary(rough_add, rough_clamped)" at column 0. py_compile ACCEPTED the
    # original form (it just ended one block early), and the real caller
    # silently lost the wiring - the material shipped with a Saturate wired to
    # nothing and compiled to "Missing Saturate input".
    #
    # This check runs on the RAW TEXT, before ast.parse, and cannot be skipped
    # by a parse failure. An earlier version ran after ast.parse and therefore
    # reported clean on exactly the fixture it was written to catch, because the
    # dedented line made the file unparseable.
    dedented = []
    in_fn = False
    for i, line in enumerate(source.splitlines(), 1):
        s = line.strip()
        if s.startswith("def "):
            in_fn = True
            continue
        if not in_fn or not s:
            continue
        if line[0].isspace():
            continue
        if s.startswith(("def ", "class ", "@", "if __name__", "from ",
                         "import ")):
            in_fn = False
            continue
        # A COMMENT at column 0 inside a function body is this codebase's normal
        # style (see build_master_toon.py's section banners), not a bug. Only
        # actual CODE at column 0 mid-function is the defect.
        if s.startswith("#"):
            continue
        dedented.append((i, s[:70]))

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return {"declared": 0, "dead": {}, "dedented": dedented,
                "parse_error": f"{type(exc).__name__}: {exc}",
                "live": []}

    declared = {}   # local var name -> parameter_name
    loaded = set()  # every Name in Load context

    for node in ast.walk(tree):
        # f(...) = lib.scalar(mat, "GouacheBandShadow", "Wash", 0.40, ...)
        # The factory signature is (owner, name, ...), so the human-readable
        # parameter name is args[1], NOT args[0] - args[0] is the material.
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            fn = node.value.func
            name = getattr(fn, "attr", None)
            if name in PARAM_FACTORIES and len(node.value.args) >= 2:
                target = node.targets[0]
                second = node.value.args[1]
                pname = second.value if isinstance(second, ast.Constant) else None
                if isinstance(target, ast.Name) and pname:
                    declared[target.id] = pname
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            loaded.add(node.id)

    dead = {var: pname for var, pname in declared.items() if var not in loaded}
    return {"declared": len(declared), "dead": dead,
            "dedented": dedented,
            "live": sorted(declared[v] for v in declared if v not in dead)}


def main(argv):
    if len(argv) < 2:
        print("usage: check_param_wiring.py <builder.py> [...]")
        return 2

    failed = False
    for arg in argv[1:]:
        path = Path(arg)
        res = analyse(path)
        print(f"{path.name}: {res['declared']} declared, "
              f"{len(res['live'])} live, {len(res['dead'])} dead")
        if res.get("parse_error"):
            print(f"  PARSE ERROR  {res['parse_error']}")
            failed = True
        for var, pname in sorted(res["dead"].items()):
            print(f"  DEAD  {pname}  (bound to unused local '{var}')")
            failed = True
        for lineno, text in res["dedented"]:
            print(f"  DEDENTED line {lineno}: {text}")
            print("         a column-0 line inside a function silently drops "
                  "the graph wiring above it")
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))