"""Import the visibility-corrected Dana FBX to an isolated preview folder."""
import json
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[1]
FBX = ROOT / "Saved/Exports/DanaImportAudit/Dana_Film_WeightedLashesVisible_v02.fbx"
DEST = "/Game/Preview/DanaLashesVisibleV02"
REPORT = ROOT / "Saved/Audit/dana_lash_visibility_unreal_import_v02.json"

if not FBX.is_file(): raise RuntimeError("Corrected preview FBX is missing")
unreal.EditorAssetLibrary.make_directory(DEST)
task = unreal.AssetImportTask()
task.set_editor_property("filename", str(FBX))
task.set_editor_property("destination_path", DEST)
task.set_editor_property("destination_name", "Dana_WeightedLashesVisible_v02")
task.set_editor_property("automated", True)
task.set_editor_property("replace_existing", False)
task.set_editor_property("save", True)
options = unreal.FbxImportUI()
options.set_editor_property("import_mesh", True)
options.set_editor_property("import_materials", False)
options.set_editor_property("import_textures", False)
options.set_editor_property("import_animations", False)
options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
options.set_editor_property("import_as_skeletal", True)
options.set_editor_property("create_physics_asset", False)
task.set_editor_property("options", options)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
paths = list(task.get_editor_property("imported_object_paths"))
assets = []
for path in paths:
    asset = unreal.load_asset(path)
    assets.append({"path": path, "class": asset.get_class().get_name() if asset else None,
                   "skeleton": (asset.get_editor_property("skeleton").get_path_name()
                                if asset and isinstance(asset, unreal.SkeletalMesh)
                                and asset.get_editor_property("skeleton") else None)})
report = {"result": "imported" if paths else "failed", "source": str(FBX),
          "destination": DEST, "imported_object_paths": paths, "assets": assets,
          "source_asset_replaced": False,
          "qualification": "Import readback only; inspect skeletal mesh components and render before promotion."}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("[DanaLashVisibilityPreview] " + json.dumps(report))
