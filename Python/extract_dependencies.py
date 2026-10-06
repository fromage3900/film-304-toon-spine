"""Trace the MF dependency graph from M_Master_Toon_Universal.

Run in UE 5.8 editor Python console:
  py "C:/EnvironmentPortfolio/melodia-toon-film/Python/extract_dependencies.py"

Outputs a JSON dependency map to Saved/DependencyMap.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import unreal

MASTER_PATH = "/Game/Materials/Masters/M_Master_Toon_Universal"

# parents[1] is THIS REPO's root (parents[0] is Python/). It used to be
# parents[2], which walks one level ABOVE the repo: from
# P:\film-304-toon-spine\Python it resolved to P:\Saved\DependencyMap.json, i.e.
# it tried to write a report to the root of the drive. Reported 2026-09-30.
REPORT_PATH = Path(__file__).resolve().parents[1] / "Saved" / "DependencyMap.json"


def get_mf_calls(material) -> list[str]:
    """Return all MaterialFunction paths called by this material's graph."""
    mfs = []
    lib = unreal.MaterialEditingLibrary
    for expr in lib.get_material_expressions(material) or []:
        if expr is None:
            continue
        tname = type(expr).__name__
        if tname == "MaterialExpressionMaterialFunctionCall":
            try:
                mf = expr.get_editor_property("material_function")
                if mf:
                    mfs.append(mf.get_path_name())
            except Exception:
                pass
    return mfs


def trace_dependencies(root_path: str, max_depth: int = 5) -> dict:
    """BFS through MF call graph, returning {mf_path: [dependent_mfs]}."""
    visited = {}
    queue = [(root_path, 0)]

    while queue:
        path, depth = queue.pop(0)
        if path in visited or depth > max_depth:
            continue

        asset = unreal.load_asset(path)
        if asset is None:
            visited[path] = {"error": "load_failed", "depth": depth}
            continue

        tname = type(asset).__name__
        if tname == "Material":
            mfs = get_mf_calls(asset)
            visited[path] = {
                "type": "material",
                "depth": depth,
                "calls": mfs,
            }
            for mf_path in mfs:
                if mf_path not in visited:
                    queue.append((mf_path, depth + 1))
        elif tname == "MaterialFunction":
            # MFs can call other MFs
            lib = unreal.MaterialEditingLibrary
            mfs = []
            try:
                for expr in lib.get_material_function_expressions(asset) or []:
                    if expr is None:
                        continue
                    etname = type(expr).__name__
                    if etname == "MaterialExpressionMaterialFunctionCall":
                        try:
                            mf = expr.get_editor_property("material_function")
                            if mf:
                                mfs.append(mf.get_path_name())
                        except Exception:
                            pass
            except Exception:
                pass
            visited[path] = {
                "type": "material_function",
                "depth": depth,
                "calls": mfs,
            }
            for mf_path in mfs:
                if mf_path not in visited:
                    queue.append((mf_path, depth + 1))
        else:
            visited[path] = {
                "type": tname,
                "depth": depth,
                "calls": [],
            }

    return visited


def main():
    unreal.log("=== Toon Master Dependency Trace ===")
    unreal.log(f"Root: {MASTER_PATH}")

    dep_map = trace_dependencies(MASTER_PATH)

    # Summary
    mf_count = sum(1 for v in dep_map.values() if v.get("type") == "material_function")
    mat_count = sum(1 for v in dep_map.values() if v.get("type") == "material")
    err_count = sum(1 for v in dep_map.values() if "error" in v)

    unreal.log(f"Traced: {len(dep_map)} assets ({mat_count} materials, {mf_count} MFs, {err_count} errors)")

    # List all MFs
    mf_paths = sorted([p for p, v in dep_map.items() if v.get("type") == "material_function"])
    unreal.log("Material Functions:")
    for p in mf_paths:
        unreal.log(f"  {p}")

    # Check for plugin dependencies
    plugin_mfs = [p for p in mf_paths if "MeshBlend" in p or "Plugin" in p]
    if plugin_mfs:
        unreal.log_warning(f"Plugin MFs found: {plugin_mfs}")
    else:
        unreal.log("No plugin MF dependencies found.")

    # Save report
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(dep_map, indent=2), encoding="utf-8")
    unreal.log(f"Report: {REPORT_PATH}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
