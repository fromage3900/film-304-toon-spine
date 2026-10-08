"""Build the office material/lighting probe: one saved bay level + one render job.

WHY
---
The 2026-10-08 desktop batch reproduced the black renders on the RTX 3080 Ti
(driver 610.88 -- the machine class the docs blamed), AND the control level
proved the direct Toon-BSDF+TP_Default path renders red and banded. The
remaining ambiguity: are the master-derived instances black because of
(1) the office lighting rig ("lighting and skylights are broken") or
(2) the master/instance material path? This probe separates the two WITHOUT
touching the owner's staged levels:

L_OfficeMaterialProbe = new saved bay level with
  * the stage spec's EXACT lighting rig (sun 5.0 at (-40,115,0) + fill 1.6
    at (-25,-105,0) + SkyLight 1.0 -- no atmosphere, matching the spec),
  * cube A: engine default material (the lit reference, proven lit in the
    A/B/C control render),
  * cube B: MI_Toon_Environment  (walls/ground class -- master-derived),
  * cube C: MI_OfficeSpider_Paper (prop class),
  * cube D: MI_Toon_Office_Polypropylene (the cubicle partition's class).
A LS_R_PROBE sequence binds a fitted camera; CFG probe config renders it.

Verdict rules (one -game render):
  A lit + B/C/D black  -> master/instance material path is the black cause
  everything black     -> the lighting rig is broken (owner hypothesis)
  everything lit       -> neither; the staged stills fail somewhere else
Run:
    UnrealEditor-Cmd.exe HumberToonShader.uproject -ExecutePythonScript="Python/build_render_queue.py" ... then this script; the report prints the exact -game command.
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
LEVEL = "/Game/Maps/L_OfficeMaterialProbe"
REPORT = Path(os.environ.get("TEMP", ".")) / "office_material_probe_report.json"

CUBES = [
    ("PROBE_A_default", None, (-600, -1200, 60)),
    ("PROBE_B_Env", "/Game/Materials/Instances/MI_Toon_Environment", (-200, -1200, 60)),
    ("PROBE_C_Paper", "/Game/Materials/Instances/MI_OfficeSpider_Paper", (200, -1200, 60)),
    ("PROBE_D_Poly", "/Game/Materials/Instances/MI_Toon_Office_Polypropylene", (600, -1200, 60)),
]
CAM_POS = (-1200, -2400, 180)
CAM_TARGET = (0, -1200, 60)


def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def main():
    report = {"errors": [], "cubes": [], "ok": False}
    try:
        ensure_dir("/Game/Maps")
        unreal.EditorAssetLibrary.delete_asset(LEVEL)
        unreal.EditorLevelLibrary.new_level(LEVEL)
        sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

        # floor slab: non-Substrate VCT stand-in (default material) so
        # shadows land and the exposure law reads
        ground = sub.spawn_actor_from_class(unreal.StaticMeshActor,
                                            unreal.Vector(0, 0, -10),
                                            unreal.Rotator(0, 0, 0))
        ground.set_actor_label("PROBE_Ground")
        comp = ground.get_component_by_class(unreal.StaticMeshComponent)
        comp.set_mobility(unreal.ComponentMobility.MOVABLE)
        comp.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Plane.Plane"))
        comp.set_world_scale3d(unreal.Vector(30.0, 30.0, 1.0))
        comp.set_mobility(unreal.ComponentMobility.STATIC)

        for label, mat_path, loc in CUBES:
            actor = sub.spawn_actor_from_class(unreal.StaticMeshActor,
                                               unreal.Vector(*loc), unreal.Rotator(0, 0, 0))
            actor.set_actor_label(label)
            comp = actor.get_component_by_class(unreal.StaticMeshComponent)
            comp.set_mobility(unreal.ComponentMobility.MOVABLE)
            comp.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube.Cube"))
            if mat_path:
                mat = unreal.load_asset(mat_path)
                if mat is None:
                    raise RuntimeError("material missing: %s" % mat_path)
                comp.set_material(0, mat)
            comp.set_mobility(unreal.ComponentMobility.STATIC)
            report["cubes"].append(label)

        # The stage spec's exact rig: sun 5.0 at (-40,115,0); fill 1.6 at
        # (-25,-105,0); SkyLight 1.0 (spec: sky true, atmosphere false).
        sun = sub.spawn_actor_from_class(unreal.DirectionalLight,
                                         unreal.Vector(0, 0, 2600),
                                         unreal.Rotator(-40, 115, 0))
        sun.set_actor_label("PROBE_Sun_key")
        sun.get_component_by_class(unreal.DirectionalLightComponent).set_intensity(5.0)

        fill = sub.spawn_actor_from_class(unreal.DirectionalLight,
                                          unreal.Vector(0, 0, 2600),
                                          unreal.Rotator(-25, -105, 0))
        fill.set_actor_label("PROBE_Sun_fill")
        fill.get_component_by_class(unreal.DirectionalLightComponent).set_intensity(1.6)

        sky = sub.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 3200),
                                         unreal.Rotator(0, 0, 0))
        sky.set_actor_label("PROBE_Sky")
        skc = sky.get_component_by_class(unreal.SkyLightComponent)
        skc.set_intensity(1.0)
        try:
            skc.call_method("recapture_sky")
        except Exception as exc:                                   # noqa: BLE001
            log("WARN skylight recapture: %s" % exc)

        # PostProcess: auto-exposure OFF like the project config asserts
        # (r.DefaultFeature.AutoExposure=False) -- the volume keeps manual
        # exposure law only if a PPV component exists; the actor comes with
        # its own component, so no class reference is needed here.
        pp = sub.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 300),
                                        unreal.Rotator(0, 0, 0))
        pp.set_actor_label("PROBE_PPV")

        cam = sub.spawn_actor_from_class(unreal.CineCameraActor,
                                         unreal.Vector(*CAM_POS), unreal.Rotator(0, 0, 0))
        cam.set_actor_label("PROBE_Cam")
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
            raise RuntimeError("probe level did not save")

        seq_path = build_render_sequence("LS_R_PROBE", cam)
        cfg_path = job_config(str(REPO / "Saved" / "Renders" / "office_stage"),
                              "OS_PROBE_materials_v01")
        report["sequence"] = seq_path
        report["config"] = cfg_path
        ue = "C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe"
        report["command"] = ('"%s" "%s" L_OfficeMaterialProbe -game '
                             '-LevelSequence="/Game/Sequences/ProtoDiag/LS_R_PROBE.LS_R_PROBE" '
                             '-MoviePipelineConfig="/Game/MoviePipelines/CFG_OS_PROBE_materials_v01.CFG_OS_PROBE_materials_v01" '
                             '-windowed -log -unattended'
                             % (ue, str(REPO / "HumberToonShader.uproject")))
        report["level_saved"] = True
    except Exception as exc:                                       # noqa: BLE001
        report["errors"].append("%s: %s" % (type(exc).__name__, exc))
        log("FAILED: %s\n" % exc)
    report["ok"] = not report["errors"]
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    (REPO / "Saved" / "Audit" / "office_material_probe_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    log("report -> %s" % REPORT)
    log("OVERALL: %s" % ("PASS" if report["ok"] else "FAIL"))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    main()
