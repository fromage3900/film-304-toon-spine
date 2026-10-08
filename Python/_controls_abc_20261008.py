"""The three-control render: WHY is Substrate toon black on this machine?

In-memory (no saves, throwaway materials + camera), in L_Toon_Shot_Office:
  CTRL_A  plain LIT red material  (legacy BaseColor - no Substrate closure)
  CTRL_B  Substrate Toon BSDF, red BaseColor, NO Toon Profile bound
  CTRL_C  Substrate Toon BSDF, red BaseColor, TP_Default bound
One camera looks at all three cubes; one 720p still fires.
Verdict matrix:
  A red + B/C black  -> the Toon BSDF path itself (machine or pipeline)
  A red + B red + C black -> the Toon Profile DATA is the black cause
  A black -> the render pipeline is dark (exposure/lights), re-examine
Run headless: UnrealEditor-Cmd.exe ... -ExecutePythonScript=<abs> -stdout -unattended
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import unreal

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "Saved" / "Renders" / "controls"
CTRL_DIR = "/Game/Materials/Controls_Diag"
STEM = "CTRL_ABC_20261008"
REC = OUT_DIR / ("_pending_" + STEM + ".json")
REPORT = REPO / "Saved" / "Audit" / "controls_verdict_20261008.json"

LEVEL = "/Game/Maps/L_Toon_Shot_Office"
PROFILE_DIR = "/Game/Materials/ToonProfiles"

# 2026-10-08: the pending-record write assumed this directory already existed
# (render_prototypes.__main__ creates ITS out_dir; this script never did, and
# the capture then fired and the write failed AFTER the capture). Create it.
OUT_DIR.mkdir(parents=True, exist_ok=True)

sub = unreal.LevelEditorSubsystem()
if not sub.load_level(LEVEL):
    raise RuntimeError("level did not load: " + LEVEL)

tools = unreal.AssetToolsHelpers.get_asset_tools()
if not unreal.EditorAssetLibrary.does_directory_exist(CTRL_DIR):
    unreal.EditorAssetLibrary.make_directory(CTRL_DIR)

me = unreal.MaterialEditingLibrary


def make_lit_red():
    path = CTRL_DIR + "/M_CTRL_Lit_Red"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        m = unreal.load_asset(path)
        return m
    m = tools.create_asset("M_CTRL_Lit_Red", CTRL_DIR, unreal.Material,
                           unreal.MaterialFactoryNew())
    red = me.create_material_expression(
        m, unreal.MaterialExpressionConstant3Vector, -300, 0)
    red.set_editor_property("constant", unreal.LinearColor(1.0, 0.05, 0.05))
    me.connect_material_property(red, "", unreal.MaterialProperty.MP_BASE_COLOR)
    me.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m)
    return m


def make_toon_red(name, bind_profile):
    path = CTRL_DIR + "/" + name
    m = None
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        m = unreal.load_asset(path)
    else:
        m = tools.create_asset(name, CTRL_DIR, unreal.Material,
                               unreal.MaterialFactoryNew())
    # wipe in place for idempotency
    prev = -1
    for _ in range(24):
        me.delete_all_material_expressions(m)
        remain = len(me.get_material_expressions(m) or [])
        if remain == 0 or remain == prev:
            break
        prev = remain
    if remain:
        raise RuntimeError(name + ": wipe left " + str(remain) + " expressions")

    m.set_editor_property("material_domain", unreal.MaterialDomain.MD_SURFACE)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    try:
        m.set_editor_property("bUsesSubstrate", True)
    except Exception as exc:
        print("[ctrl] bUsesSubstrate: " + str(exc)[:80])

    red = me.create_material_expression(
        m, unreal.MaterialExpressionConstant3Vector, -400, 0)
    red.set_editor_property("constant", unreal.LinearColor(1.0, 0.05, 0.05))
    toon = me.create_material_expression(
        m, unreal.MaterialExpressionSubstrateToonBSDF, -100, 0)
    me.connect_material_expressions(red, "", toon, "BaseColor")
    if bind_profile:
        prof = unreal.load_asset(PROFILE_DIR + "/TP_Default")
        if prof is None:
            raise RuntimeError("TP_Default does not load")
        bound_name = None
        for attempt in range(3):
            try:
                toon.set_editor_property("toon_profile", prof)
            except Exception as exc:
                print("[ctrl] bind attempt: " + str(exc)[:80])
            try:
                have = toon.get_editor_property("toon_profile")
                bound_name = have.get_name() if have else None
            except Exception:
                bound_name = None
            if bound_name:
                break
            me.recompile_material(m)
        print("[ctrl] " + name + " profile bound -> " + str(bound_name))
    me.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m)
    return m


mat_a = make_lit_red()
mat_b = make_toon_red("M_CTRL_Toon_Red_NoProfile", bind_profile=False)
mat_c = make_toon_red("M_CTRL_Toon_Red_TPDefault", bind_profile=True)

# place three cubes in the open bay, front of a fresh camera
placed = []
specs = [("CTRL_A", mat_a, (-500, -1500, 60)),
         ("CTRL_B", mat_b, (0, -1500, 60)),
         ("CTRL_C", mat_c, (500, -1500, 60))]
for label, mat, loc in specs:
    old = None
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            if a.get_actor_label() == label:
                old = a
                break
        except Exception:
            continue
    if old is not None:
        unreal.EditorLevelLibrary.destroy_actor(old)
    cube_mesh = unreal.load_asset("/Engine/BasicShapes/Cube")
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*loc),
        unreal.Rotator(0, 0, 0))
    actor.set_actor_label(label)
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    comp.set_mobility(unreal.ComponentMobility.MOVABLE)
    comp.set_static_mesh(cube_mesh)
    comp.set_material(0, mat)
    comp.set_mobility(unreal.ComponentMobility.STATIC)
    placed.append(label)

cam = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.CineCameraActor, unreal.Vector(-1400, -2600, 180),
    unreal.Rotator(0, 0, 0))
cam.set_actor_label("CTRL_Cam")
rot = unreal.MathLibrary.find_look_at_rotation(
    unreal.Vector(-1400, -2600, 180), unreal.Vector(0, -1500, 60))
cam.set_actor_rotation(rot, False)
comp = cam.get_cine_camera_component()
comp.set_editor_property("current_focal_length", 35.0)
try:
    comp.set_editor_property("filmback",
                             unreal.CameraFilmbackSettings(35.0, 19.6875))
    comp.set_editor_property("constrain_aspect_ratio", True)
    comp.set_editor_property("aspect_ratio", 35.0 / 19.6875)
except Exception as exc:
    print("[ctrl] filmback: " + str(exc)[:80])

t0 = time.time()
task = unreal.AutomationLibrary.take_high_res_screenshot(
    res_x=1280, res_y=720, filename=str(OUT_DIR / STEM), camera=cam,
    mask_enabled=False, capture_hdr=False, force_game_view=True)
REC.write_text(json.dumps({
    "fired_epoch": t0, "stem": STEM,
    "controls": ["M_CTRL_Lit_Red", "M_CTRL_Toon_Red_NoProfile",
                 "M_CTRL_Toon_Red_TPDefault"],
    "note": "in-memory controls; throwaway materials in Controls_Diag; "
            "the cubes/camera are in-memory stage props, level NOT saved",
}, indent=2), encoding="utf-8")
print("[ctrl] fired " + STEM + " placed=" + ",".join(placed))
