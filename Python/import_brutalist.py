"""Import the exported BRUTALIST FBX set into Content/Environment/Brutalist/.

WHY
---
`Docs/ASSETLIST.md` lists the 25-object brutalist set as "staged headless into
Saved/" and explicitly "not yet in Content/". `Blender/export_brutalist_fbx.py`
now writes the FBX; this is the editor half, so the environment kit exists in
the project instead of only in a .blend.

Reads `Saved/Audit/brutalist_fbx_manifest.json` -- the export's own report --
so the object list, collections and source FBX paths are never retyped here.
`Docs/CONTENT_CONVENTIONS.md`: content is generated from code, and a number
copied by hand drifts with nothing to catch it.

MATERIALS
---------
Imported WITHOUT materials (`import_materials=False`): the FBX carries the
Blender BR_* surface names, and letting UE import them litters the content
browser with 4 dead materials no shot uses. Instead every slot is assigned
`MI_Toon_Environment`, which is what `Docs/CONTENT_CONVENTIONS.md` prescribes for
"the world mass".

Outlines are NOT assigned. `M_Outline_InvertedHull` is a separate inverted-hull
pass (its own mesh), not a slot on the base surface -- assigning `MI_Outline_*`
to a surface slot would REPLACE the toon shading with a flat outline shell.

Per-surface variation (glazing toward the harder `TP_Stone` band) is deliberately
left to the surfacing artist: the manifest records the Blender material list per
object but not which slot is which, so guessing a slot order would be a silent
mis-assignment.

Run (editor open, via Monolith):
    editor_query run_python {command: "Python/import_brutalist.py", mode: execute_file}

Assert on the report FILE, not the log.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import unreal  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
FBX_MANIFEST = REPO / "Saved" / "Audit" / "brutalist_fbx_manifest.json"
DEST_ROOT = "/Game/Environment/Brutalist"
BASE_MATERIAL = "/Game/Materials/Instances/MI_Toon_Environment"

REPORT = Path(os.environ.get("TEMP", ".")) / "brutalist_import_report.json"
AUDIT_COPY = REPO / "Saved" / "Audit" / "brutalist_import_report.json"


def log(m):
    unreal.log("[BrutalistImport] " + str(m))


def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def load_manifest():
    if not FBX_MANIFEST.exists():
        raise RuntimeError(
            "export manifest missing: %s (run Blender/export_brutalist_fbx.py)"
            % FBX_MANIFEST)
    return json.loads(FBX_MANIFEST.read_text(encoding="utf-8"))


def mesh_name(obj_name):
    """Convention prefix for a static mesh (Docs/CONTENT_CONVENTIONS.md)."""
    return "SM_%s" % obj_name


def import_one(entry):
    """Import one FBX as SM_<Object> under its collection folder."""
    coll = entry["collection"]
    dest = "%s/%s" % (DEST_ROOT, coll)
    ensure_dir(dest)

    abs_fbx = str(REPO / entry["fbx"])
    if not os.path.exists(abs_fbx):
        raise RuntimeError("fbx missing on disk: %s" % abs_fbx)

    name = mesh_name(entry["object"])
    asset_path = "%s/%s" % (dest, name)

    # Delete first so a re-run is idempotent and never leaves a _1 duplicate.
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        unreal.EditorAssetLibrary.delete_asset(asset_path)

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", abs_fbx)
    task.set_editor_property("destination_path", dest)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)

    ui = unreal.FbxImportUI()
    ui.set_editor_property("import_mesh", True)
    ui.set_editor_property("import_materials", False)   # see module docstring
    ui.set_editor_property("import_textures", False)
    ui.set_editor_property("import_animations", False)
    ui.set_editor_property("mesh_type_to_import",
                           unreal.FBXImportType.FBXIT_STATIC_MESH)
    try:
        sm = ui.static_mesh_import_data
        sm.set_editor_property("combine_meshes", True)
        sm.set_editor_property("auto_generate_collision", False)  # no gameplay
        sm.set_editor_property("generate_lightmap_u_vs", False)   # Lumen film
    except Exception:                                          # noqa: BLE001
        pass
    task.set_editor_property("options", ui)

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    if not unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        raise RuntimeError("import produced no asset at %s" % asset_path)
    return asset_path


def assign_material(asset_path, mi):
    """Every slot -> the environment toon instance."""
    mesh = unreal.load_asset(asset_path)
    if mesh is None:
        raise RuntimeError("could not load %s" % asset_path)
    try:
        slots = mesh.get_editor_property("static_materials")
        n = len(slots)
    except Exception:                                          # noqa: BLE001
        n = 1
    n = max(1, n)
    for i in range(n):
        mesh.set_material(i, mi)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    return n


def build():
    manifest = load_manifest()
    entries = manifest.get("objects", [])
    report = {"errors": [], "imported": [], "dest_root": DEST_ROOT,
              "base_material": BASE_MATERIAL}

    ensure_dir(DEST_ROOT)

    mi = unreal.load_asset(BASE_MATERIAL)
    if mi is None:
        raise RuntimeError("base material missing: %s" % BASE_MATERIAL)

    for entry in entries:
        try:
            path = import_one(entry)
            slots = assign_material(path, mi)
            report["imported"].append({
                "object": entry["object"],
                "asset": path,
                "collection": entry["collection"],
                "evaluated_verts": entry.get("evaluated_verts"),
                "material_slots": slots,
                "material": BASE_MATERIAL,
            })
            log("imported %s (%d slots)" % (path, slots))
        except Exception as e:                                 # noqa: BLE001
            report["errors"].append("%s: %s" % (entry.get("object"), e))
            log("FAILED %s: %s" % (entry.get("object"), e))

    report["expected_count"] = len(entries)
    report["imported_count"] = len(report["imported"])
    report["assets_on_disk"] = sorted(
        a for a in unreal.EditorAssetLibrary.list_assets(
            DEST_ROOT, recursive=True, include_folder=False))
    return report


def verify(report):
    out = {}
    out["count_ok"] = report["imported_count"] == report["expected_count"] == 25
    out["all_on_disk"] = len(report["assets_on_disk"]) == report["expected_count"]
    # Every imported mesh must point at the toon instance, not a default.
    # A mesh that imported cleanly but kept the grey default material is the
    # exact failure the toon spine exists to prevent, so assert the link.
    unassigned = []
    for rec in report["imported"]:
        mesh = unreal.load_asset(rec["asset"])
        if mesh is None:
            unassigned.append({"asset": rec["asset"], "why": "unloadable"})
            continue
        try:
            # static_materials returns FStaticMaterial STRUCTS; the path lives on
            # the struct's material_interface member. Calling get_path_name() on
            # the struct raises and turns a clean import into a false FAIL.
            names = []
            for m in mesh.get_editor_property("static_materials"):
                try:
                    mi = m.get_editor_property("material_interface")
                except Exception:                              # noqa: BLE001
                    mi = getattr(m, "material_interface", None) or getattr(m, "material", None)
                names.append(str(mi.get_path_name()) if mi else "")
            names = [n for n in names if n]
            if not names or not all("MI_Toon_" in n for n in names):
                unassigned.append({"asset": rec["asset"], "materials": names})
        except Exception as e:                                 # noqa: BLE001
            unassigned.append({"asset": rec["asset"], "why": str(e)})
    out["unassigned_materials"] = unassigned
    out["materials_ok"] = not unassigned
    out["errors"] = report["errors"]
    out["ok"] = (out["count_ok"] and out["all_on_disk"]
                 and out["materials_ok"] and not report["errors"])
    return out


def main():
    report = build()
    report["verify"] = verify(report)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    try:
        AUDIT_COPY.parent.mkdir(parents=True, exist_ok=True)
        AUDIT_COPY.write_text(json.dumps(report, indent=2), encoding="utf-8")
    except Exception:                                          # noqa: BLE001
        pass
    log("report -> %s" % REPORT)
    log("OVERALL: %s" % ("PASS" if report["verify"]["ok"] else "FAIL"))
    return 0 if report["verify"]["ok"] else 1


if __name__ == "__main__":
    main()