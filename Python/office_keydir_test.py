"""Office KeyLightDir knob test: does the toon band follow the hand-set key?

The fresh-instance falsifier proved staged assets == fresh MI behavior; the
blackening lives in the toon shading stage itself. This test sets the
master's documented KeyLightDir vector (the toon key, hand-set BY DESIGN -- it
is not tied to the sun) on a fresh instance and re-renders through EB_Cam.

  * EB_KEY_A: KeyLightDir toward +Y-ish (matching the camera view)
  * EB_KEY_B: KeyLightDir toward -Y (reverse, for an unmistakable flip)
If the bright band MOVES between A and B, the toon-key machinery works and
the black renders are an un-aimed key + zero shadow lift. Tomorrow's fix is
then a builder-authored param set, not graph surgery.
Output: report JSON + one PNG (OS_EBisect_keydir_v01).
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
REPORT = Path(os.environ.get("TEMP", ".")) / "office_keydir_report.json"
AUDIT = REPO / "Saved" / "Audit" / "office_keydir_report.json"
MASTER = "/Game/Materials/Masters/M_Master_Toon_Universal"


def make_mi(name, key_dir):
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    path = "/Game/Materials/Controls_Diag/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mi = tools.create_asset(name, "/Game/Materials/Controls_Diag",
                            unreal.MaterialInstanceConstant,
                            unreal.MaterialInstanceConstantFactoryNew())
    if mi is None:
        raise RuntimeError(name + " did not create")
    mi.set_editor_property("parent", unreal.load_asset(MASTER))
    me = unreal.MaterialEditingLibrary
    # the instance-parameter API lives on MaterialEditingLibrary (the same
    # calls build_instances._apply uses); KeyLightDir is a vector param
    # carried as LinearColor.
    me.set_material_instance_vector_parameter_value(
        mi, "KeyLightDir", unreal.LinearColor(key_dir[0], key_dir[1],
                                              key_dir[2], 1.0))
    got = me.get_material_instance_vector_parameter_value(mi, "KeyLightDir")
    if got is None:
        raise RuntimeError(name + ": KeyLightDir read back None (not a param?)")
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    return path


def main():
    report = {"errors": [], "cube": [], "ok": False}
    try:
        if not unreal.LevelEditorSubsystem().load_level(LEVEL):
            raise RuntimeError("office level did not load")
        sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

        mi_a = make_mi("MI_KEYDIR_A", (0.0, 1.0, -0.3))
        mi_b = make_mi("MI_KEYDIR_B", (0.0, -1.0, -0.3))

        for label, mi_path, loc in (("EB_KEY_A", mi_a, (600, -1100, 60)),
                                    ("EB_KEY_B", mi_b, (1000, -1100, 60))):
            actor = sub.spawn_actor_from_class(unreal.StaticMeshActor,
                                               unreal.Vector(*loc), unreal.Rotator(0, 0, 0))
            actor.set_actor_label(label)
            comp = actor.get_component_by_class(unreal.StaticMeshComponent)
            comp.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube.Cube"))
            comp.set_material(0, unreal.load_asset(mi_path))
            report["cube"].append({"label": label, "material": mi_path})

        cam = find_camera("EB_Cam")
        if cam is None:
            raise RuntimeError("EB_Cam missing")
        build_render_sequence("LS_R_EBisect", cam)
        job_config(str(REPO / "Saved" / "Renders" / "office_stage"),
                   "OS_EBisect_keydir_v01")
        world = unreal.EditorLevelLibrary.get_editor_world()
        if not unreal.EditorLoadingAndSavingUtils.save_map(world, LEVEL.rsplit(".", 1)[0]):
            raise RuntimeError("office level did not save")
        ue = "C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe"
        report["command"] = ('"%s" "%s" L_Toon_Shot_Office -game '
                             '-LevelSequence="/Game/Sequences/ProtoDiag/LS_R_EBisect.LS_R_EBisect" '
                             '-MoviePipelineConfig="/Game/MoviePipelines/CFG_OS_EBisect_keydir_v01.CFG_OS_EBisect_keydir_v01" '
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
