"""The Lumen-GI falsifier for the office black renders.

`specs/humber_toon_spine/prototype_renders.v1.json` pins lumen_gi: false on
the prototype tier, and the Oct-5 real reads were rendered under that
constraint. Tonight's MRQ -game path ran with the project default
(r.DynamicGlobalIlluminationMethod=1 -- Lumen). This fires the SAME
LS_R_EBisect frame with GI off via the pipeline's ConsoleVariableSetting:

  r.DynamicGlobalIlluminationMethod=0
  r.Lumen.DiffuseIndirect.Allow=0

If the staged/fresh surfaces LIGHT with GI off, the black class is the
Lumen+Substrate interaction in the -game renderer (fix: the tier ALWAYS
turns GI off, matching the spec), and tomorrow's batch is a one-cvar change
in the queue builder. If they STAY black, the next suspect is the direct
lighting layer itself (the carpet-only shading pattern in
OS_EBisect_freshMI_v01.png).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import unreal  # noqa: E402
from build_render_queue import job_config, log  # noqa: E402

REPO = Path(__file__).resolve().parents[1]


def build_gi_off_config():
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    cfg_name = "CFG_OS_EBisect_GIoff"
    path = "/Game/MoviePipelines/" + cfg_name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    config = tools.create_asset(cfg_name, "/Game/MoviePipelines",
                                unreal.MoviePipelineMasterConfig,
                                unreal.MoviePipelinePrimaryConfigFactory())
    if config is None:
        raise RuntimeError("GIoff config did not create")
    out_set = config.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting, True)
    out_set.set_editor_property("output_resolution", unreal.IntPoint(1280, 720))
    out_set.set_editor_property("output_directory",
                                unreal.DirectoryPath(str(REPO / "Saved" / "Renders" / "office_stage")))
    out_set.set_editor_property("file_name_format", "OS_EBisect_GIoff")
    out_set.set_editor_property("override_existing_output", True)
    png = config.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG, True)
    png.set_is_enabled(True)
    config.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase, True)
    cvars = config.find_or_add_setting_by_class(unreal.MoviePipelineConsoleVariableSetting, True)
    cvars.add_or_update_console_variable("r.DynamicGlobalIlluminationMethod", 0)
    cvars.add_or_update_console_variable("r.Lumen.DiffuseIndirect.Allow", 0)
    cvars.add_or_update_console_variable("r.ReflectionMethod", 0)
    unreal.EditorAssetLibrary.save_loaded_asset(config)
    return path


def main():
    report = {"errors": [], "ok": False}
    try:
        cfg_path = build_gi_off_config()
        ue = "C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe"
        report["config"] = cfg_path
        report["command"] = ('"%s" "%s" L_Toon_Shot_Office -game '
                             '-LevelSequence="/Game/Sequences/ProtoDiag/LS_R_EBisect.LS_R_EBisect" '
                             '-MoviePipelineConfig="/Game/MoviePipelines/%s.%s" '
                             '-windowed -unattended'
                             % (ue, str(REPO / "HumberToonShader.uproject"),
                                cfg_path.rsplit("/", 1)[1],
                                cfg_path.rsplit("/", 1)[1]))
    except Exception as exc:                                       # noqa: BLE001
        report["errors"].append("%s: %s" % (type(exc).__name__, exc))
        log("FAILED: %s\n" % exc)
    report["ok"] = not report["errors"]
    REPORT = Path(os.environ.get("TEMP", ".")) / "office_gioff_report.json"
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    (REPO / "Saved" / "Audit" / "office_gioff_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    log("report -> %s" % REPORT)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    main()
