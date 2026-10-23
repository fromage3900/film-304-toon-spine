"""Import the cast rig FBXs into UE as skeletal meshes, using the engine's own
FBX import path rather than a convenience wrapper.

Why this exists: `mesh.import_mesh` reported `total_imported: 1` for David's
FBX and produced a single mesh named after one of its parts. That is not a
file problem - an independent read of the same FBX with Blender
(Tools/_probe_fbx_contents.py) shows two armatures in it:

    DeformationSystem       101 bones
    FaceDeformationSystem    64 bones

The legacy FBX importer builds one SkeletalMesh per armature, so a two-armature
character cannot arrive as a single asset. Importing here with FbxImportUI
records EVERY asset the importer actually creates, so the split is reported
rather than silently collapsed to whichever mesh happened to win.

Reads specs/cast/cast_rigs.v1.json. Run inside the editor.
"""
from __future__ import annotations

import json
import traceback
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "specs/cast/cast_rigs.v1.json"
REPORT_PATH = ROOT / "Saved/Audit/CastRigs_20261016/cast_import.json"

EAL = unreal.EditorAssetLibrary
ASSET_TOOLS = unreal.AssetToolsHelpers.get_asset_tools()


def import_character(name: str, entry: dict) -> dict:
    fbx = entry.get("fbx")
    if not fbx:
        return {"result": "skipped", "reason": "spec declares no fbx"}

    source = (ROOT / fbx).resolve()
    if not source.is_file():
        return {"result": "blocked", "reason": "exported fbx not on disk: %s" % source}

    destination = entry["mesh"].rsplit("/", 1)[0]
    stem = source.stem
    if EAL.does_directory_exist(destination):
        EAL.make_directory(destination)

    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_SKELETAL_MESH,
        "import_mesh": True,
        "import_as_skeletal": True,
        "import_animations": False,
        "import_materials": False,
        "import_textures": False,
        # Skinned geometry lives on the deform systems; the facial pieces that
        # are not skinned still have to come across or the mouth and lashes
        # are lost on import.
        "import_rigid_mesh": True,
    })

    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(source),
        "destination_path": destination,
        "destination_name": stem,
        "automated": True,
        "replace_existing": False,
        "save": True,
        "options": options,
    })
    ASSET_TOOLS.import_asset_tasks([task])

    imported = [str(p).split(".")[0] for p in task.get_editor_property("imported_object_paths")]
    skeletal, supporting = [], []
    for path in imported:
        asset = EAL.load_asset(path)
        if isinstance(asset, unreal.SkeletalMesh):
            skeletal.append({
                "path": path,
                "slots": [str(s.material_slot_name) for s in asset.get_editor_property("materials")],
            })
        else:
            supporting.append({"path": path, "type": type(asset).__name__})

    return {
        "result": "imported",
        "fbx": str(source),
        "destination": destination,
        "imported_paths": imported,
        "skeletal_meshes": skeletal,
        "supporting_assets": supporting,
        "note": ("more than one SkeletalMesh means the FBX carries more than one "
                 "armature; decide the merge policy before binding materials"
                 if len(skeletal) > 1 else None),
    }


def main() -> None:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    report = {"schema": "humber-cast-rig-import.v1", "characters": {}}
    try:
        for name, entry in spec["characters"].items():
            unreal.log_warning("cast import: %s" % name)
            report["characters"][name] = import_character(name, entry)
    except Exception as exc:
        report["result"] = "failed"
        report["error"] = str(exc)
        report["traceback"] = traceback.format_exc()
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
        raise

    report["summary"] = {n: r.get("result") for n, r in report["characters"].items()}
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("CAST_IMPORT_JSON " + json.dumps(report))


if __name__ == "__main__":
    main()