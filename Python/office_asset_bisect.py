"""Office asset-state bisect: fresh cubes with the SAME MI .uassets inside L_Toon_Shot_Office.

WHY
---
The 2026-10-08 material probe (L_OfficeMaterialProbe) rendered MI_Toon_Environment
taupe-lit and MI_Toon_Office_Polypropylene tan-lit in the probe bay, while the SAME
instance classes render BLACK on the staged pieces of L_Toon_Shot_Office -- and the
v02 black reproduces identically on BOTH machines (laptop take_high_res, desktop MRQ
-game). Machine-local effects (fresh-load texture decay, drivers) are therefore NOT
the cause; the suspects are (1) the staged LEVEL's context/rig and (2) SHARED broken
asset state saved by the laptop's Oct-7 builder session.

This bisect decides between them WITHOUT touching the staged pieces:

* THREE fresh small cubes, carrying directly the SAME .uasset instances the staged
  pieces carry (MI_Toon_Environment, MI_OfficeSpider_Paper,
  MI_Toon_OfficePolypropylene), placed ON THE OFFICE FLOOR,
* ONE fitted camera looking at the cubes + floor + wall in frame,
* one LS_R_EBisect sequence + one CFG, then the caller fires the -game render
  printed in the report.

Verdict rules:
  fresh cubes BLACK like the staged pieces  -> SHARED broken asset state (fix in
      the material builders on THIS machine; the staged .uassets need a rebuild)
  fresh cubes LIT like the probe bay        -> the LEVEL context/rig is the cause
      (deeper: compare the office rig vs the probe rig element by element)
Run:
    UnrealEditor-Cmd.exe HumberToonShader.uproject -ExecutePythonScript="Python/office_asset_bisect.py" -stdout -unattended
Assert on the report FILE, not the log.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import unreal  # noqa: E402
from build_render_queue import build_render_sequence, job_config, log  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
LEVEL = "/Game/Maps/L_Toon_Shot_Office"
REPORT = Path(os.environ.get("TEMP", ".")) / "office_asset_bisect_report.json"
AUDIT = REPO / "Saved" / "Audit" / "office_asset_bisect_report.json"

CUBES = [
    ("EB_Env", "/Game/Materials/Instances/MI_Toon_Environment", (300, -900, 60)),
    ("EB_Paper", "/Game/Materials/Instances/MI_OfficeSpider_Paper", (650, -900, 60)),
    ("EB_Poly", "/Game/Materials/Instances/MI_Toon_Office_Polypropylene", (1000, -900, 60)),
]
CAM_POS = (1400, 350, 260)
CAM_TARGET = (650, -900, 60)


def main():
    report = {"errors": [], "cubes": [], "ok": False}
    try:
        if not unreal.LevelEditorSubsystem().load_level(LEVEL):
            raise RuntimeError("office level did not load")
        sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

        for label, mat_path, loc in CUBES:
            actor = sub.spawn_actor_from_class(unreal.StaticMeshActor,
                                               unreal.Vector(*loc), unreal.Rotator(0, 0, 0))
            actor.set_actor_label(label)
            comp = actor.get_component_by_class(unreal.StaticMeshComponent)
            comp.set_mobility(unreal.ComponentMobility.MOVABLE)
            comp.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube.Cube"))
            mat = unreal.load_asset(mat_path)
            if mat is None:
                raise RuntimeError("instance missing: %s" % mat_path)
            comp.set_material(0, mat)
            comp.set_mobility(unreal.ComponentMobility.STATIC)
            report["cubes"].append({"label": label, "material": mat_path})

        cam = sub.spawn_actor_from_class(unreal.CineCameraActor,
                                         unreal.Vector(*CAM_POS), unreal.Rotator(0, 0, 0))
        cam.set_actor_label("EB_Cam")
        rot = unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*CAM_POS),
                                                       unreal.Vector(*CAM_TARGET))
        cam.set_actor_rotation(rot, False)
        cc = cam.get_cine_camera_component()
        cc.set_editor_property("current_focal_length", 35.0)
        try:
            cc.set_editor_property("filmback", unreal.CameraFilmbackSettings(35.0, 19.6875))
            cc.set_editor_property("constrain_aspect_ratio", True)
            cc.set_editor_property("aspect_ratio", 35.0 / 19.6875)
        except Exception as exc:                                   # noqa: BLE001
            log("WARN filmback: %s" % exc)

        world = unreal.EditorLevelLibrary.get_editor_world()
        if not unreal.EditorLoadingAndSavingUtils.save_map(world,
                                                           LEVEL.rsplit(".", 1)[0]):
            raise RuntimeError("office level did not save (bisect cubes are in-memory only)")

        seq_path = build_render_sequence("LS_R_EBisect", cam)
        cfg_path = job_config(str(REPO / "Saved" / "Renders" / "office_stage"),
                              "OS_EBisect_v01")
        ue = "C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe"
        report["sequence"] = seq_path
        report["config"] = cfg_path
        report["command"] = ('"%s" "%s" L_Toon_Shot_Office -game '
                             '-LevelSequence="/Game/Sequences/ProtoDiag/LS_R_EBisect.LS_R_EBisect" '
                             '-MoviePipelineConfig="/Game/MoviePipelines/CFG_OS_EBisect_v01.CFG_OS_EBisect_v01" '
                             '-windowed -log -unattended'
                             % (ue, str(REPO / "HumberToonShader.uproject")))
        report["level_saved"] = True
    except Exception as exc:                                       # noqa: BLE001
        report["errors"].append("%s: %s" % (type(exc).__name__, exc))
        log("FAILED: %s\n" % exc)
    report["ok"] = not report["errors"]
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    AUDIT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    log("report -> %s" % REPORT)
    log("OVERALL: %s" % ("PASS" if report["ok"] else "FAIL"))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    main()
