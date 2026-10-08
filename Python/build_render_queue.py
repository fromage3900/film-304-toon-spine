"""Build the headless MRQ render queue: control level + render sequences + .umrq queue.

WHY
---
The 2026-10-08 control session proved 5.8's -ExecutePythonScript semantics:
the editor issues `Cmd: QUIT_EDITOR` ~0.4 s after the startup script returns
(three sessions measured), so a python post-tick state machine can never
outlive the script and the caller can never poll the latent capture. The
engine's own answer is in
`MovieRenderPipelineCore/Private/MovieRenderPipelineCommandLine.cpp`
(Option 2b): run

    UnrealEditor-Cmd.exe <proj> -game -MoviePipelineConfig="/Game/<Queue>.<Queue>"

The -game loop ticks itself; the module renders the queue and calls
RequestExit(0) on completion. No python, no pump, no caller.

This builder authors everything that path consumes, headlessly and
idempotently:

* `/Game/Maps/L_CTRL_ABC_Diag` -- the three-control verdict matrix as a
  SAVED level (a -game render loads the saved world, so the control script's
  in-memory cubes would vanish). Cube A plain lit red (legacy path),
  cube B Substrate Toon no profile, cube C Substrate Toon with TP_Default,
  over a non-Substrate grey plane, under the office stage's key light.
* `/Game/Sequences/ProtoDiag/LS_R_<shot>` -- one 1-frame render sequence per
  still, possessing the staged camera (the owner's LS_SH* shells are
  untouched; the render tests shoot CineCameraActors directly per the
  prototype tier contract).
* `/Game/MoviePipelines/ProtoDiagQueue` -- a saved MoviePipelineQueue asset
  with one job per still. Each job: its own map, its own sequence, its own
  output (stem/dir) via a transient MasterConfig on the job.

Texture streaming is FULLY_LOAD on every job -- the machine-local fresh-load
decay (textures collapsing to 32x32 in fresh processes, work order 1) then
cannot corrupt a still mid-render; MRQ loads all mips before rendering.

Stems are bumped v01 -> v02 so the black-laptop evidence in v01 stays on
disk untouched (it is the other machine's record, synced through the shared
tree).

Run:
    UnrealEditor-Cmd.exe HumberToonShader.uproject -ExecutePythonScript="Python/build_render_queue.py" -stdout -unattended
Then render:
    UnrealEditor-Cmd.exe HumberToonShader.uproject -game -MoviePipelineConfig="/Game/MoviePipelines/ProtoDiagQueue.ProtoDiagQueue" -windowed -log -unattended
Assert on the report FILE, not the log.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# sys.path must be extended BEFORE sibling imports: under -ExecutePythonScript
# the script's own directory is NOT on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import unreal  # noqa: E402

REPO = Path(__file__).resolve().parents[1]

CTRL_MAT_DIR = "/Game/Materials/Controls_Diag"
SEQ_DIR = "/Game/Sequences/ProtoDiag"
QUEUE_DIR = "/Game/MoviePipelines"
QUEUE_NAME = "ProtoDiagQueue"
CTRL_LEVEL = "/Game/Maps/L_CTRL_ABC_Diag"

RES_W, RES_H = 1280, 720
FPS = 24

REPORT = Path(os.environ.get("TEMP", ".")) / "render_queue_report.json"
AUDIT_COPY = REPO / "Saved" / "Audit" / "render_queue_report.json"

CTRL_CUBE_LIT = CTRL_MAT_DIR + "/M_CTRL_Lit_Red"
CTRL_CUBE_B = CTRL_MAT_DIR + "/M_CTRL_Toon_Red_NoProfile"
CTRL_CUBE_C = CTRL_MAT_DIR + "/M_CTRL_Toon_Red_TPDefault"
CTRL_STEM = "CTRL_ABC_20261008"

# (spec, [(shot_id, camera_label, level_package)])
BATCHES = [
    ("specs/office_spider/stage_shots.v1.json", "Saved/Renders/office_stage",
     ["SH020", "SH030", "SH040", "SH050", "SH060"]),
    ("specs/humber_toon_spine/prototype_renders.v1.json", "Saved/Renders/prototypes",
     ["SH010", "SH020", "SH030", "SH070"]),
]


def log(m):
    unreal.log("[RenderQueue] " + str(m))


def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def asset_path(folder, name):
    return "%s/%s" % (folder, name)


# ---------------------------------------------------------------------------
# control materials (same recipe as Python/_controls_abc_20261008.py, so the
# diag level can stand alone on a fresh clone)
# ---------------------------------------------------------------------------

def build_ctrl_materials():
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    me = unreal.MaterialEditingLibrary
    if not unreal.EditorAssetLibrary.does_directory_exist(CTRL_MAT_DIR):
        unreal.EditorAssetLibrary.make_directory(CTRL_MAT_DIR)

    def red_constant(mat):
        red = me.create_material_expression(
            mat, unreal.MaterialExpressionConstant3Vector, -400, 0)
        red.set_editor_property("constant", unreal.LinearColor(1.0, 0.05, 0.05))
        return red

    # A: plain legacy lit red
    path_a = CTRL_CUBE_LIT
    if unreal.EditorAssetLibrary.does_asset_exist(path_a):
        mat_a = unreal.load_asset(path_a)
    else:
        mat_a = tools.create_asset("M_CTRL_Lit_Red", CTRL_MAT_DIR, unreal.Material,
                                   unreal.MaterialFactoryNew())
        red = red_constant(mat_a)
        me.connect_material_property(red, "", unreal.MaterialProperty.MP_BASE_COLOR)
        me.recompile_material(mat_a)
        unreal.EditorAssetLibrary.save_loaded_asset(mat_a)

    # B/C: Substrate Toon BSDF, red BaseColor, optional profile bind
    profile = unreal.load_asset("/Game/Materials/ToonProfiles/TP_Default")
    if profile is None:
        raise RuntimeError("TP_Default does not load")

    for name, bind in (("M_CTRL_Toon_Red_NoProfile", False),
                       ("M_CTRL_Toon_Red_TPDefault", True)):
        path = CTRL_MAT_DIR + "/" + name
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            m = tools.create_asset(name, CTRL_MAT_DIR, unreal.Material,
                                   unreal.MaterialFactoryNew())
        else:
            m = unreal.load_asset(path)
        me.delete_all_material_expressions(m)
        m.set_editor_property("material_domain", unreal.MaterialDomain.MD_SURFACE)
        m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
        red = red_constant(m)
        toon = me.create_material_expression(
            m, unreal.MaterialExpressionSubstrateToonBSDF, -100, 0)
        me.connect_material_expressions(red, "", toon, "BaseColor")
        if bind:
            toon.set_editor_property("toon_profile", profile)
        me.recompile_material(m)
        unreal.EditorAssetLibrary.save_loaded_asset(m)


# ---------------------------------------------------------------------------
# the saved control level
# ---------------------------------------------------------------------------

def build_ctrl_level():
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    def new_level_for(level_name):
        path = asset_path("/Game/Maps", level_name)
        unreal.EditorAssetLibrary.delete_asset(path)
        unreal.EditorLevelLibrary.new_level(path)
        return path

    def save_map(path):
        world = unreal.EditorLevelLibrary.get_editor_world()
        dest = path.rsplit(".", 1)[0]
        return bool(unreal.EditorLoadingAndSavingUtils.save_map(world, dest))

    build_ctrl_materials()

    path = new_level_for("L_CTRL_ABC_Diag")

    # Non-Substrate reference floor: default material (grey, lit legacy).
    ground = sub.spawn_actor_from_class(unreal.StaticMeshActor,
                                        unreal.Vector(0, 0, -50),
                                        unreal.Rotator(0, 0, 0))
    ground.set_actor_label("CTRL_Ground")
    comp = ground.get_component_by_class(unreal.StaticMeshComponent)
    comp.set_mobility(unreal.ComponentMobility.MOVABLE)
    comp.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Plane.Plane"))
    comp.set_world_scale3d(unreal.Vector(20.0, 20.0, 1.0))
    comp.set_mobility(unreal.ComponentMobility.STATIC)

    # The three control cubes at the control script's exact positions.
    for label, mat_path, loc in (("CTRL_A", CTRL_CUBE_LIT, (-500, -1500, 60)),
                                 ("CTRL_B", CTRL_CUBE_B, (0, -1500, 60)),
                                 ("CTRL_C", CTRL_CUBE_C, (500, -1500, 60))):
        actor = sub.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(*loc), unreal.Rotator(0, 0, 0))
        actor.set_actor_label(label)
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        comp.set_mobility(unreal.ComponentMobility.MOVABLE)
        comp.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube.Cube"))
        comp.set_material(0, unreal.load_asset(mat_path))
        comp.set_mobility(unreal.ComponentMobility.STATIC)

    # The office stage's key light, aimed the same way: sun int 5.0 (-40,115,0).
    sun = sub.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(0, 0, 2600), unreal.Rotator(-40, 115, 0))
    sun.set_actor_label("CTRL_Sun")
    sc = sun.get_component_by_class(unreal.DirectionalLightComponent)
    sc.set_intensity(5.0)

    sky = sub.spawn_actor_from_class(
        unreal.SkyLight, unreal.Vector(0, 0, 3200), unreal.Rotator(0, 0, 0))
    sky.set_actor_label("CTRL_Sky")
    skc = sky.get_component_by_class(unreal.SkyLightComponent)
    skc.set_intensity(1.6)
    try:
        skc.call_method("recapture_sky")
    except Exception as exc:                                       # noqa: BLE001
        log("WARN skylight recapture: %s" % exc)

    # The control camera: same position/focal/filmback as the control script.
    cam = sub.spawn_actor_from_class(
        unreal.CineCameraActor, unreal.Vector(-1400, -2600, 180), unreal.Rotator(0, 0, 0))
    cam.set_actor_label("CTRL_Cam")
    rot = unreal.MathLibrary.find_look_at_rotation(
        unreal.Vector(-1400, -2600, 180), unreal.Vector(0, -1500, 60))
    cam.set_actor_rotation(rot, False)
    cc = cam.get_cine_camera_component()
    cc.set_editor_property("current_focal_length", 35.0)
    try:
        cc.set_editor_property("filmback", unreal.CameraFilmbackSettings(35.0, 19.6875))
        cc.set_editor_property("constrain_aspect_ratio", True)
        cc.set_editor_property("aspect_ratio", 35.0 / 19.6875)
    except Exception as exc:                                       # noqa: BLE001
        log("WARN filmback: %s" % exc)

    ok = save_map(path)
    log("control level saved=%s -> %s" % (ok, path))
    return path, ok


# ---------------------------------------------------------------------------
# render sequences + queue jobs
# ---------------------------------------------------------------------------

def soft(path):
    """SoftObjectPath -- strings fail to nativize (probed 2026-10-08)."""
    return unreal.SoftObjectPath(path)


def build_render_sequence(seq_name, camera):
    """One 1-frame render sequence possessing the staged camera. Mirrors
    build_shot_deck.rebuild_sequence (the proven authoring API)."""
    ensure_dir(SEQ_DIR)
    path = asset_path(SEQ_DIR, seq_name)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    seq = tools.create_asset(seq_name, SEQ_DIR, unreal.LevelSequence,
                             unreal.LevelSequenceFactoryNew())
    if seq is None:
        raise RuntimeError("could not create %s" % path)
    seq.set_display_rate(unreal.FrameRate(FPS, 1))
    seq.set_playback_start(0)
    seq.set_playback_end(1)
    binding = seq.add_possessable(camera)
    if binding is None:
        raise RuntimeError("%s: could not possess %s" % (seq_name, camera))
    cut = seq.add_track(unreal.MovieSceneCameraCutTrack)
    section = cut.add_section()
    section.set_range(0, 1)
    # set_camera_binding_id wants a MovieSceneObjectBindingID struct; the
    # possessable's Guid rides in the struct's `guid` field (empty sequence
    # guid = root sequence -- probed 2026-10-08; build_shot_deck's identical
    # call sits in a try/except that swallowed this error, so its LS_SH*
    # shells may carry no camera cut at all).
    bind_id = unreal.MovieSceneObjectBindingID()
    bind_id.set_editor_property("guid", binding.get_id())
    section.set_camera_binding_id(bind_id)
    unreal.EditorAssetLibrary.save_loaded_asset(seq)
    return path


def job_config(out_dir_abs, stem):
    """A SAVED MasterConfig asset for one still (Option 1 CLI contract: one
    sequence + one config per -game launch)."""
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    ensure_dir(QUEUE_DIR)
    cfg_name = "CFG_%s" % stem
    path = asset_path(QUEUE_DIR, cfg_name)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    config = tools.create_asset(cfg_name, QUEUE_DIR, unreal.MoviePipelineMasterConfig,
                                unreal.MoviePipelinePrimaryConfigFactory())
    if config is None:
        raise RuntimeError("could not create config %s" % path)
    out_set = config.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting, True)
    out_set.set_editor_property("output_resolution", unreal.IntPoint(RES_W, RES_H))
    out_set.set_editor_property("output_directory", unreal.DirectoryPath(out_dir_abs))
    out_set.set_editor_property("file_name_format", stem)
    out_set.set_editor_property("override_existing_output", True)
    png = config.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG, True)
    png.set_is_enabled(True)
    # The render pass itself -- without it the shot builds with 0 passes and
    # nothing renders (measured 2026-10-08). The engine's own default class
    # set (UMovieRenderPipelineProjectSettings) carries exactly JPG + this.
    config.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase, True)
    aa = config.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting, True)
    aa.set_editor_property("override_anti_aliasing", True)
    aa.set_editor_property("anti_aliasing_method", unreal.AntiAliasingMethod.AAM_TEMPORAL_AA)
    aa.set_editor_property("spatial_sample_count", 1)
    aa.set_editor_property("temporal_sample_count", 1)
    go = config.find_or_add_setting_by_class(unreal.MoviePipelineGameOverrideSetting, True)
    # FULLY_LOAD: all mips resident -- the fresh-load 32x32 decay (work order 1)
    # cannot corrupt a still mid-render when streaming is fully loaded.
    go.set_editor_property("texture_streaming",
                           unreal.MoviePipelineTextureStreamingMethod.FULLY_LOAD)
    go.set_editor_property("cinematic_quality_settings", True)
    unreal.EditorAssetLibrary.save_loaded_asset(config)
    return path


def build_queue():
    """Per-still: a render sequence + a saved config + a record of the exact
    -game command line that renders it."""

    jobs = []
    # Job 0: the control.
    ctrl_cfg = job_config(str(REPO / "Saved" / "Renders" / "controls"), CTRL_STEM)
    if not unreal.LevelEditorSubsystem().load_level("/Game/Maps/L_CTRL_ABC_Diag"):
        raise RuntimeError("control level did not load")
    ctrl_seq = build_render_sequence("LS_R_CTRL", find_camera("CTRL_Cam"))
    jobs.append({
        "job": "CTRL_ABC", "out_dir": "controls", "stem": CTRL_STEM,
        "level": "L_CTRL_ABC_Diag", "sequence": ctrl_seq, "config": ctrl_cfg,
    })

    for spec_rel, out_dir_rel, shot_ids in BATCHES:
        spec = json.loads((REPO / spec_rel).read_text(encoding="utf-8-sig"))
        level_pkg = spec["level"]["package"]
        by_id = {s["shot_id"]: s for s in spec["shots"]}
        # Load the level ONCE per batch, build all its sequences.
        if not unreal.LevelEditorSubsystem().load_level(level_pkg):
            raise RuntimeError("level did not load: %s" % level_pkg)
        level_name = level_pkg.rsplit("/", 1)[1]
        for shot_id in shot_ids:
            shot = by_id[shot_id]
            cam = find_camera(shot["camera_label"])
            if cam is None:
                raise RuntimeError("camera %s not in %s"
                                   % (shot["camera_label"], level_pkg))
            stem = shot["still_name"].replace("v01", "v02")
            seq_name = "LS_R_%s" % shot_id
            seq_path = build_render_sequence(seq_name, cam)
            cfg_path = job_config(str(REPO / out_dir_rel), stem)
            jobs.append({
                "job": shot_id, "out_dir": out_dir_rel, "stem": stem,
                "level": level_name, "sequence": seq_path, "config": cfg_path,
            })
            log("job %s -> %s (%s)" % (shot_id, stem, seq_path))
    return jobs


def find_camera(label):
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            if a.get_actor_label() == label:
                return a
        except Exception:                                          # noqa: BLE001
            continue
    return None


def main():
    report = {"errors": [], "jobs": []}
    try:
        ctrl_level, ctrl_saved = build_ctrl_level()
        report["ctrl_level"] = ctrl_level
        report["ctrl_level_saved"] = ctrl_saved
        if not ctrl_saved:
            raise RuntimeError("control level did not save -- -game cannot load it")
        jobs = build_queue()
        report["jobs"] = jobs
        # The exact -game launch line per job (Option 1 of the CLI contract) so
        # the batch is re-runnable on any machine with zero code changes.
        ue = "C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe"
        proj = str(REPO / "HumberToonShader.uproject")
        for j in jobs:
            j["command"] = ('"%s" "%s" %s -game '
                            '-LevelSequence="%s.%s" '
                            '-MoviePipelineConfig="%s.%s" '
                            '-windowed -log -unattended'
                            % (ue, proj, j["level"],
                               j["sequence"], j["sequence"].rsplit("/", 1)[1],
                               j["config"], j["config"].rsplit("/", 1)[1]))
    except Exception as exc:                                       # noqa: BLE001
        report["errors"].append("%s: %s" % (type(exc).__name__, exc))
        log("FAILED: %s\n" % exc)

    report["ok"] = not report["errors"] and len(report["jobs"]) == 10
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    AUDIT_COPY.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_COPY.write_text(json.dumps(report, indent=2), encoding="utf-8")
    log("report -> %s" % REPORT)
    log("OVERALL: %s" % ("PASS" if report["ok"] else "FAIL"))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    main()
