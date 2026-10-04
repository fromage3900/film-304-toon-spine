"""DEPRECATED 2026-09-30 - this builder cannot run and must not be revived.

This file was extracted from the source project along with a helper module
(`material_lib`) that was NOT extracted. It imports 12 helpers that do not exist
anywhere in this repo:

    ensure_directory, asset_path, try_set_editor_property, vector_param,
    scalar_param, texture_param, create_expression, connect, connect_unary,
    connect_toon_pin, connect_front_material, save_package

So `import material_lib as lib` raises ModuleNotFoundError the moment anyone runs
it - and the README used to point here as the way to rebuild the master. Two
builders for one master is also the "second authority" defect this project keeps
catching, so this is deprecated rather than repaired against spine_lib.

THE REAL ENTRY POINT IS:

    UnrealEditor-Cmd.exe <this-repo>/MelodiaToonFilm.uproject ^
      -ExecutePythonScript="Python/build_spine.py" -stdout -unattended

`build_spine.py` builds the MFs, both masters, the Toon Profiles and the material
instances in dependency order, then asserts against a written report file. The
master itself is built by `build_master_toon.py`.

Kept as a file rather than deleted so old links and the commit history still
resolve. Nothing below is callable.
"""
from __future__ import annotations


def build_master(*_args, **_kwargs):
    raise RuntimeError(
        "build_master.py is deprecated and cannot run: it depends on a "
        "`material_lib` helper module that was never extracted into this repo. "
        "Use `build_spine.py` (which calls build_master_toon.py) instead:\n"
        "  UnrealEditor-Cmd.exe MelodiaToonFilm.uproject "
        "-ExecutePythonScript=\"Python/build_spine.py\" -stdout -unattended"
    )


if __name__ == "__main__":
    raise SystemExit(build_master())
