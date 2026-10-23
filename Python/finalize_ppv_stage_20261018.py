"""Persist the restored single-writer state and confirm the map is clean."""
import json
from pathlib import Path
import unreal

OUT = Path(unreal.Paths.project_dir()) / "Saved/Audit/PPV"
OUT.mkdir(parents=True, exist_ok=True)

saved = bool(unreal.EditorLoadingAndSavingUtils.save_current_level())
dirty = sorted(p.get_name() for p in
               unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())
report = {"saved": saved, "dirty": dirty,
          "ok": saved and not dirty}
(OUT / "finalize_stage.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report))
