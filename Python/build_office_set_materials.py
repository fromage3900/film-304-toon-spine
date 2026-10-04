"""Assign toon materials to the 304 office set - generated, never hand-placed.

WHY THIS EXISTS (2026-10-02)
    The 8 office material instances authored earlier are structurally valid and
    fully verified, and NOTHING REFERENCES THEM. Measured: a binary scan found
    MI_Toon_Environment on 5 of 8 office meshes and no material at all on the
    other 3. The office suite could never have rendered.

    A live probe (Saved/Audit/office_mesh_material_probe.json) measured what the
    meshes actually are: every one has exactly ONE material slot named
    Material_0, and StaticMesh.set_material exists on this build.

WHAT THIS DOES, AND WHAT IT DELIBERATELY DOES NOT
    Assigns each mesh a material from the explicit table below, then READS THE
    VALUE BACK - assignment is the one thing here that can fail silently, so the
    assertion is on the result, never on the absence of an exception.

    It does NOT invent art direction. Where no authored instance fits the
    geometry it says so in the report instead of forcing a nearest-miss:
      * the office BLOCKS are exterior brutalist concrete. The Wave-3 interior
        surfaces (carpet, drop ceiling, troffer, whiteboard...) have NO GEOMETRY
        in this repo yet - Wave 1 of the prop brief is 1 of 8 builders done - so
        there is nothing to assign them to. Those instances stay orphaned ON
        PURPOSE, and the report records which and why.

Run directly or via build_spine.py.
Report: Saved/Audit/office_set_materials_report.json - assert on the FILE.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Saved" / "Audit" / "office_set_materials_report.json"
INSTANCE_DIR = "/Game/Materials/Instances"
OFFICE_DIR = "/Game/Environment/Brutalist/03_OFFICE_BLOCK"
CUBICLE_DIR = "/Game/Environment/Brutalist/04_INTERIOR_CUBICLES"

# mesh stem -> instance name.
#
# Cubicles are the only office geometry that is INTERIOR. Their partitions are
# fabric-wrapped acoustic panels, which MI_Toon_Office_Polypropylene models
# (Weave pattern, soft mid specular, no hard terminator) - a real match, not a
# default. Exterior concrete keeps MI_Toon_Environment, the authored world-mass
# look; no INTERIOR office instance is correct for a facade, so none is forced.
ASSIGNMENTS = {
    "SM_CUBICLE_Canonical": "MI_Toon_Office_Polypropylene",
    "SM_CUBICLE_MazeShift": "MI_Toon_Office_Polypropylene",
    "SM_CUBICLE_OpenPlan": "MI_Toon_Office_Polypropylene",
    "SM_CUBICLE_Swarm": "MI_Toon_Office_Polypropylene",
    "SM_OFFICE_BarbicanScale": "MI_Toon_Environment",
    "SM_OFFICE_Bunker": "MI_Toon_Environment",
    "SM_OFFICE_CivicSlab": "MI_Toon_Environment",
    "SM_OFFICE_SlenderTower": "MI_Toon_Environment",
}

# Instances authored for interior surfaces that have no geometry yet. Recorded so
# "orphaned" is a decision with a reason, not an unexplained gap.
AWAITING_GEOMETRY = {
    "MI_Toon_Office_Carpet": "carpet tile - no interior floor mesh yet",
    "MI_Toon_Office_Laminate": "desk laminate - desk prop not built (Wave 1)",
    "MI_Toon_Office_DropCeiling": "ceiling tile - no interior ceiling mesh yet",
    "MI_Toon_Office_Troffer": "light panel - no troffer mesh yet",
    "MI_Toon_Office_Whiteboard": "whiteboard - no prop mesh yet",
}

def _instance(name):
    path = f"{INSTANCE_DIR}/{name}.{name}"
    mi = unreal.load_asset(path)
    if mi is None:
        raise RuntimeError(f"material instance missing: {path}")
    return mi


def _mesh_dir(directory):
    """name -> package path. list_assets returns "Pkg.Name.Name", not .uasset."""
    assets = unreal.EditorAssetLibrary.list_assets(directory, recursive=True)
    return {a.rsplit("/", 1)[-1].rsplit(".", 1)[0]: a for a in (assets or [])}


def build():
    report = {"assigned": {}, "errors": [], "orphaned_office_instances": {},
              "awaiting_geometry": AWAITING_GEOMETRY}

    meshes = {}
    meshes.update(_mesh_dir(OFFICE_DIR))
    meshes.update(_mesh_dir(CUBICLE_DIR))

    for mesh_name, inst_name in ASSIGNMENTS.items():
        entry = {"instance": inst_name}
        try:
            asset = meshes.get(mesh_name)
            if asset is None:
                entry["ok"] = False
                entry["error"] = "mesh not found"
                report["errors"].append(f"{mesh_name}: mesh not found")
                report["assigned"][mesh_name] = entry
                continue

            mesh = unreal.load_asset(asset)
            mi = _instance(inst_name)
            entry["before"] = [str(getattr(m, "material_interface", None))
                               for m in (mesh.static_materials or [])]

            mesh.set_material(0, mi)
            unreal.EditorAssetLibrary.save_loaded_asset(mesh,
                                                       only_if_is_dirty=False)

            # READ BACK - set_material returning None is not evidence.
            after = list(unreal.load_asset(asset).static_materials or [])
            got = getattr(after[0], "material_interface", None) if after else None
            entry["after"] = got.get_name() if got else None
            entry["ok"] = bool(got) and got.get_name() == inst_name
            if not entry["ok"]:
                report["errors"].append(
                    f"{mesh_name}: slot 0 reads {entry['after']}, "
                    f"wanted {inst_name}")
        except Exception as exc:
            entry["ok"] = False
            entry["error"] = str(exc)[:200]
            report["errors"].append(f"{mesh_name}: {str(exc)[:160]}")
        report["assigned"][mesh_name] = entry

    used = {e.get("instance") for e in report["assigned"].values() if e.get("ok")}
    for inst_name in AWAITING_GEOMETRY:
        report["orphaned_office_instances"][inst_name] = {
            "referenced_by_office_meshes": inst_name in used,
            "reason": AWAITING_GEOMETRY[inst_name],
        }

    report["ok"] = not report["errors"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    n_ok = sum(1 for e in report["assigned"].values() if e.get("ok"))
    print(f"[OFFICE] wrote {OUT} ok={report['ok']} assigned={n_ok}"
          f"/{len(report['assigned'])}")
    return report


if __name__ == "__main__":
    build()
    sys.exit(0)