"""Composed professional establishing shots for the Film304 office.

Runs inside the live editor via Claireon python_execute. Non-destructive to the
original level: duplicates the SAVED L_Film_Office into a staged copy, stages
six cameras + render sequences + MRQ configs there, saves, and writes the
exact -game command lines for the per-still renders.

Composition rules applied (indie establishing-shot practice):
  where + when + mood in one read; deep-space layering (FG/mid/bg);
  thirds with head/eyes on the upper line; wide 24-28 adds depth, 35-40 group,
  50-55 = character/detail; per-character lens rules.
"""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
STAGE_DIR = '/Game/Maps/Lookdev/UniversalFilm_20261016'
SRC_LEVEL = STAGE_DIR + '/L_Film_Office'
DST_LEVEL = STAGE_DIR + '/L_Film_Office_Estab_20261018'
SEQ_DIR = '/Game/Sequences/Film304Establishing_20261018'
CFG_DIR = '/Game/MoviePipelines/Estab20261018'
OUT_REL = 'Showcase/Film304_Estab_20261018'
RES_W, RES_H = 1920, 1080
FPS = 24

EAL = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()

ANIM_ROOT = '/Game/Animations/Film304Idle_20261017'
CAST = {
    'Film_Cast_Sam': 'AS_Sam_OfficeIdle_48f_v01',
    'Film_Cast_David': 'AS_David_OfficeIdle_48f_v01',
    'Film_Subject_Dana_v08_CleanSkin': 'AS_Dana_OfficeIdle_48f_v01',
    'Spider_Deform_v2': 'AS_Spider_OfficeIdle_48f_v01',
}

# (id, label, pos, aim, focal_mm, ev_bias, note)
SHOTS = [
    ('EST01', 'EST01_WideDiagonal', (285, 285, 170), (-105, -55, 95), 28,
     1.5, 'big diagonal establishing: desks FG right, cast mid, window wall bg'),
    ('EST02', 'EST02_EntryArrival', (215, -250, 160), (-135, -35, 90), 24,
     1.5, 'arrival POV down the room: Sam reads first, desk row leading lines'),
    ('EST03', 'EST03_CastTrioMedium', (150, -20, 118), (-65, -25, 85), 35,
     1.5, 'cast trio across the middle plane; spiders+desk FG'),
    ('EST04', 'EST04_SpiderInsert', (-75, -25, 100), (-159, -103, 55), 50,
     1.5, 'detail insert: spider on desk MG, cast soft behind'),
    ('EST05', 'EST05_WindowBacklight', (55, -85, 145), (-289, -120, 100), 35,
     2.0, 'aim through the cast toward the west window wall; silhouette logic'),
    ('EST06', 'EST06_GraphicTopDown', (-85, -45, 310), (-90, -75, 80), 24,
     1.5, 'graphic overhead: cast + desks + webs as toon layout'),
]


def log(m):
    unreal.log('[Estab20261018] %s' % m)


def stage_level():
    if not EAL.does_asset_exist(DST_LEVEL):
        if not EAL.duplicate_asset(SRC_LEVEL, DST_LEVEL):
            raise RuntimeError('could not duplicate level')
    log('staged level: %s' % DST_LEVEL)
    les = unreal.LevelEditorSubsystem()
    if not les.load_level(DST_LEVEL):
        raise RuntimeError('could not load staged level')
    return unreal.EditorLevelLibrary.get_editor_world()


def get_all_actors():
    return unreal.EditorLevelLibrary.get_all_level_actors()


def by_label(label):
    for a in get_all_actors():
        try:
            if a.get_actor_label() == label:
                return a
        except Exception:
            continue
    return None


def stage_camera(shot_id, label, pos, aim, focal, bias):
    cam = by_label(label)
    if cam is None:
        sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        cam = sub.spawn_actor_from_class(unreal.CineCameraActor, unreal.Vector(*pos))
        cam.set_actor_label(label)
    cam.set_actor_location(unreal.Vector(*pos), False, False)
    rot = unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*pos), unreal.Vector(*aim))
    cam.set_actor_rotation(rot, False)
    cc = cam.get_cine_camera_component()
    cc.set_editor_property('current_focal_length', float(focal))
    try:
        cc.set_editor_property('current_aperture', 2.8)
        cc.set_editor_property('constrain_aspect_ratio', False)
    except Exception as exc:
        log('WARN aperture: %s' % exc)
    pp = cc.get_editor_property('post_process_settings')
    pp.set_editor_property('auto_exposure_bias', float(bias))
    cc.set_editor_property('post_process_settings', pp)
    dist = (unreal.Vector(*aim) - unreal.Vector(*pos)).length()
    try:
        focus = cc.get_editor_property('focus_settings')
        focus.set_editor_property('focus_method', unreal.CameraFocusMethod.MANUAL)
        focus.set_editor_property('manual_focus_distance', dist)
        cc.set_editor_property('focus_settings', focus)
    except Exception as exc:
        log('WARN focus (leaving defaults): %s' % exc)
    log('%s staged pos=%s aim=%s focal=%d focus=%.0f' % (label, pos, aim, focal, dist))
    return cam


def build_sequence(seq_name, camera):
    if EAL.does_asset_exist(seq_name):
        EAL.delete_asset(seq_name)
    seq = TOOLS.create_asset(seq_name.rsplit('/', 1)[1], SEQ_DIR, unreal.LevelSequence,
                             unreal.LevelSequenceFactoryNew())
    if seq is None:
        raise RuntimeError('sequence create failed: %s' % seq_name)
    seq.set_display_rate(unreal.FrameRate(FPS, 1))
    seq.set_playback_start(0)
    seq.set_playback_end(48)
    binding = seq.add_possessable(camera)
    cut = seq.add_track(unreal.MovieSceneCameraCutTrack)
    section = cut.add_section()
    section.set_range(0, 48)
    bind_id = unreal.MovieSceneObjectBindingID()
    bind_id.set_editor_property('guid', binding.get_id())
    section.set_camera_binding_id(bind_id)
    for label, anim_name in CAST.items():
        actor = by_label(label)
        clip = unreal.load_asset(ANIM_ROOT + '/' + anim_name)
        if actor is None or clip is None:
            log('WARN missing cast/clip for %s' % label)
            continue
        cbinding = seq.add_possessable(actor)
        track = cbinding.add_track(unreal.MovieSceneSkeletalAnimationTrack)
        asec = track.add_section()
        asec.set_range(0, 48)
        params = asec.get_editor_property('params')
        params.set_editor_property('animation', clip)
        asec.set_editor_property('params', params)
    EAL.save_loaded_asset(seq, False)
    return seq.get_path_name()


def build_config(stem, seq_path):
    if EAL.does_asset_exist(stem):
        EAL.delete_asset(stem)
    cfg = TOOLS.create_asset(stem.rsplit('/', 1)[1], CFG_DIR,
                             unreal.MoviePipelineMasterConfig,
                             unreal.MoviePipelinePrimaryConfigFactory())
    if cfg is None:
        raise RuntimeError('config create failed: %s' % stem)
    out_set = cfg.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting, True)
    out_set.set_editor_property('output_resolution', unreal.IntPoint(RES_W, RES_H))
    out_set.set_editor_property('output_directory', unreal.DirectoryPath(str(ROOT / OUT_REL)))
    out_set.set_editor_property('file_name_format', stem.rsplit('/', 1)[1])
    out_set.set_editor_property('override_existing_output', True)
    out_set.set_editor_property('use_custom_playback_range', True)
    out_set.set_editor_property('custom_start_frame', 18)
    out_set.set_editor_property('custom_end_frame', 19)
    png = cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG, True)
    png.set_is_enabled(True)
    cfg.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase, True)
    aa = cfg.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting, True)
    aa.set_editor_property('override_anti_aliasing', True)
    aa.set_editor_property('anti_aliasing_method', unreal.AntiAliasingMethod.AAM_TEMPORAL_AA)
    aa.set_editor_property('spatial_sample_count', 1)
    aa.set_editor_property('temporal_sample_count', 1)
    aa.set_editor_property('engine_warm_up_count', 48)
    aa.set_editor_property('render_warm_up_count', 16)
    go = cfg.find_or_add_setting_by_class(unreal.MoviePipelineGameOverrideSetting, True)
    go.set_editor_property('texture_streaming', unreal.MoviePipelineTextureStreamingMethod.FULLY_LOAD)
    go.set_editor_property('cinematic_quality_settings', True)
    EAL.save_loaded_asset(cfg, False)
    return cfg.get_path_name()


def main():
    report = {'shots': [], 'errors': []}
    for module_dir in (SEQ_DIR, CFG_DIR, STAGE_DIR):
        if not EAL.does_directory_exist(module_dir):
            EAL.make_directory(module_dir)
    stage_level()
    jobs = []
    for shot_id, label, pos, aim, focal, bias, note in SHOTS:
        cam = stage_camera(shot_id, label, pos, aim, focal, bias)
        seq_path = build_sequence(SEQ_DIR + '/LS_' + shot_id, cam)
        cfg_path = build_config(CFG_DIR + '/CFG_' + shot_id, seq_path)
        level_name = DST_LEVEL.rsplit('/', 1)[1]
        job = {'shot': shot_id, 'note': note, 'sequence': seq_path, 'config': cfg_path,
               'level': level_name,
               'command': ('"C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" '
                           '%s %s -game -LevelSequence="%s.%s" -MoviePipelineConfig="%s.%s" '
                           '-windowed -log -unattended'
                           % (str(ROOT / 'HumberToonShader.uproject'), level_name,
                              seq_path, seq_path.rsplit('/', 1)[1],
                              cfg_path, cfg_path.rsplit('/', 1)[1]))}
        jobs.append(job)
    world = unreal.EditorLevelLibrary.get_editor_world()
    dest = DST_LEVEL.rsplit('.', 1)[0]
    saved = bool(unreal.EditorLoadingAndSavingUtils.save_map(world, dest))
    report['level_saved'] = saved
    if not saved:
        report['errors'].append('staged level did not save; -game renders cannot load it')
    report['jobs'] = jobs
    out_json = ROOT / 'Saved/Audit/EveningExecution_20261018/estab_shots_commands.json'
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2), encoding='utf-8')
    log('report -> %s' % out_json)
    for job in jobs:
        log('CMD %s: %s' % (job['shot'], job['command']))


main()
