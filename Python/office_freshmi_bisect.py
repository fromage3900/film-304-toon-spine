"""Office fresh-instance falsifier: a NEW MI (parent = M_Master) vs the staged MI.

One render inside L_Toon_Shot_Office through the standing EB_Cam bisect rig:
  * EB_FRESHMI cube  -- a brand-new MaterialInstanceConstant, parent =  the
    real master, default params -- authored ON THIS MACHINE tonight.
  * EB_STAGEDMI cube -- MI_Toon_Environment as loaded from disk (the staged
    .uasset, which the earlier EB bisect proved lights).
  * EB_STAGEDVCT cube -- MI_OfficeSpider_VCTFloor as loaded (the staged
    floor-surface class).
Verdict rules:
  FRESH lit + staged siblings black -> the staged instance .uassets carry
      broken saved state; tomorrow = re-run the instance builders on this
      machine and re-render.
  Both lit  -> the staged PIECES' actor state (not the assets) is the gap.
  Both black -> fresh-from-master is ALSO broken: the master itself is the
      last suspect (builder rebuild on this machine).
Run the render the report prints, then read the PNG.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import unreal  # noqa: E402
from build_render_queue import build_render_sequence, job_config, log, find_camera  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
LEVEL = "/Game/Maps/L_Toon_Shot_Office"
REPORT = Path(os.environ.get("TEMP", ".")) / "office_freshmi_report.json"
AUDIT = REPO / "Saved" / "Audit" / "office_freshmi_report.json"

MASTER = "/Game/Materials/Masters/M_Master_Toon_Universal"
STAGED_ENV = "/Game/Materials/Instances/MI_Toon_Environment"


def main():
    report = {"errors": [], "cube": [], "ok": False}
    try:
        if not unreal.LevelEditorSubsystem().load_level(LEVEL):
            raise RuntimeError("office level did not load")
        sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        tools = unreal.AssetToolsHelpers.get_asset_tools()

        fresh_path = "/Game/Materials/Controls_Diag/MI_EBisect_Fresh"
        if unreal.EditorAssetLibrary.does_asset_exist(fresh_path):
            unreal.EditorAssetLibrary.delete_asset(fresh_path)
        fresh = tools.create_asset("MI_EBisect_Fresh", "/Game/Materials/Controls_Diag",
                                   unreal.MaterialInstanceConstant,
                                   unreal.MaterialInstanceConstantFactoryNew())
        if fresh is None:
            raise RuntimeError("fresh MI did not create")
        master = unreal.load_asset(MASTER)
        if master is None:
            raise RuntimeError("master missing: %s" % MASTER)
        fresh.set_editor_property("parent", master)
        unreal.EditorAssetLibrary.save_loaded_asset(fresh)

        staged_env = unreal.load_asset(STAGED_ENV)
        staged_vct = unreal.load_asset("/Game/Materials/Instances/MI_OfficeSpider_VCTFloor")
        if staged_env is None or staged_vct is None:
            raise RuntimeError("staged instances missing")

        for label, mi, loc in (("EB_FRESHMI", fresh, (600, -1100, 60)),
                               ("EB_STAGEDENV", staged_env, (1000, -1100, 60)),
                               ("EB_STAGEDVCT", staged_vct, (1400, -1100, 60))):
            actor = sub.spawn_actor_from_class(unreal.StaticMeshActor,
                                               unreal.Vector(*loc), unreal.Rotator(0, 0, 0))
            actor.set_actor_label(label)
            comp = actor.get_component_by_class(unreal.StaticMeshComponent)
            comp.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube.Cube"))
            comp.set_material(0, mi)
            report["cube"].append({"label": label,
                                   "material": mi.get_path_name()[:60]})

        cam = find_camera("EB_Cam")
        if cam is None:
            raise RuntimeError("EB_Cam not in level (the bisect rig was removed?)")
        seq_path = build_render_sequence("LS_R_EBisect", cam)
        cfg_path = job_config(str(REPO / "Saved" / "Renders" / "office_stage"),
                              "OS_EBisect_freshMI_v01")
        world = unreal.EditorLevelLibrary.get_editor_world()
        if not unreal.EditorLoadingAndSavingUtils.save_map(world, LEVEL.rsplit(".", 1)[0]):
            raise RuntimeError("office level did not save")
        ue = "C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe"
        report["command"] = ('"%s" "%s" L_Toon_Shot_Office -game '
                             '-LevelSequence="/Game/Sequences/ProtoDiag/LS_R_EBisect.LS_R_EBisect" '
                             '-MoviePipelineConfig="/Game/MoviePipelines/CFG_OS_EBisect_freshMI_v01.CFG_OS_EBisect_freshMI_v01" '
                             '-windowed -unattended'
                             % (ue, str(REPO / "HumberToonShader.uproject")))
    except Exception as exc:                                       # noqa: BLE001
        report["errors"].append("%s: %s" % (type(exc).__name__, exc))
        log("FAILED: %s\n" % exc)
    report["ok"] = not report["errors"]
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    AUDIT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    log("OVERALL: %s -> %s" % ("PASS" if report["ok"] else "FAIL", REPORT))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    main()
