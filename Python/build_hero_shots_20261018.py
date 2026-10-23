"""Quality hero stills for bedtime render campaign, 2026-10-18.

Runs inside the LIVE editor while the hero world
L_Film_HeroTonight_20261018 is loaded (baked from the live dusk state).
Original L_Film_Office on disk is never overwritten.

Authoring per shot: LevelSequence possessing the staged camera (final v2/v3
framing reuses tonight's preview work) + cast idle anim bindings (no T-pose),
a MRQ MasterConfig (1920x1080 PNG, frame 18, FULLY_LOAD streaming, cinematic
quality, engine warmup 48 / render warmup 16), and the exact -game command.

Composition (was validated in tonight's preview rounds):
  HERO01  EST01_NSHOT  28mm  wide diagonal: cast mid-task, desks FG,
                        window bays + city towers bg (the money shot)
  HERO02  EST04_NSHOT  50mm  desk insert: David desk-sleep + monitor/lamp/
                        phone props + spider mid-ground (comedy beat)
  HERO03  EST02_NSHOT  24mm  entry arrival: leading lines down the desk row
                        to blinds (storybook page opener)

Dusk exposure: camera auto-exposure bias 1.4 (dusk wheel 1.3-1.5 rule).
"""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
HERO_LEVEL = '/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_HeroTonight_20261018'
SEQ_DIR = '/Game/Sequences/Film304Hero_20261018'
CFG_DIR = '/Game/MoviePipelines/Hero20261018'
OUT_REL = 'Showcase/Film304_Hero_20261018'
RES_W, RES_H = 1920, 1080
FPS = 24
BIAS = 1.4

EAL = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()

ANIM_ROOT = '/Game/Animations/Film304Idle_20261017'
CAST = {
    'Film_Cast_Sam': 'AS_Sam_OfficeIdle_48f_v01',
    'Film_Cast_David': 'AS_David_DeskSleep_48f_v02',
    'Film_Subject_Dana_v08_CleanSkin': 'AS_Dana_OfficeIdle_48f_v01',
    'Spider_Deform_v2': 'AS_Spider_OfficeIdle_48f_v01',
}

# (stem, camera_label, note)
SHOTS = [
    ('HERO01_WideDiagonal', 'EST01_NSHOT',
     'wide diagonal: cast mid-task, desks FG, window bays + towers bg'),
    ('HERO02_DeskInsert', 'EST04_NSHOT',
     'desk insert: David desk-sleep + props + spider MG, 50mm'),
    ('HERO03_EntryArrival', 'EST02_NSHOT',
     'entry arrival: leading lines down the desk row to blinds, 24mm'),
]


def log(m):
    unreal.log('[Hero20261018] %s' % m)


def by_label(label):
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            if a.get_actor_label() == label:
                return a
        except Exception:
            continue
    return None


def refresh_cam(cam):
    """Dusk exposure + refresh focus distance on the staged camera."""
    cc = cam.get_cine_camera_component()
    pp = cc.get_editor_property('post_process_settings')
    pp.set_editor_property('auto_exposure_bias', BIAS)
    cc.set_editor_property('post_process_settings', pp)
    try:
        focus = cc.get_editor_property('focus_settings')
        focus.set_editor_property('focus_method', unreal.CameraFocusMethod.MANUAL)
        cc.set_editor_property('focus_settings', focus)
    except Exception as exc:
        log('WARN focus refresh: %s' % exc)
    log('cam %s -> bq=%.1f' % (cam.get_actor_label(), BIAS))


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
            log('WARN missing cast/clip: %s / %s' % (label, anim_name))
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
    for d in (SEQ_DIR, CFG_DIR):
        if not EAL.does_directory_exist(d):
            EAL.make_directory(d)
    report = {'hero_level': HERO_LEVEL, 'jobs': [], 'errors': []}
    for stem, cam_label, note in SHOTS:
        cam = by_label(cam_label)
        if cam is None:
            report['errors'].append('camera missing: %s' % cam_label)
            continue
        refresh_cam(cam)
        seq_path = build_sequence(SEQ_DIR + '/LS_' + stem, cam)
        cfg_path = build_config(CFG_DIR + '/CFG_' + stem, seq_path)
        level_name = HERO_LEVEL.rsplit('/', 1)[1]
        job = {'shot': stem, 'note': note, 'sequence': seq_path, 'config': cfg_path,
               'level': level_name,
               'command': ('"C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" '
                           '%s %s -game -LevelSequence="%s.%s" -MoviePipelineConfig="%s.%s" '
                           '-windowed -log -unattended'
                           % (str(ROOT / 'HumberToonShader.uproject'), level_name,
                              seq_path, seq_path.rsplit('/', 1)[1],
                              cfg_path, cfg_path.rsplit('/', 1)[1]))}
        report['jobs'].append(job)
        log('built %s (%s)' % (stem, note))
    if not report['errors'] and len(report['jobs']) == len(SHOTS):
        world = unreal.EditorLevelLibrary.get_editor_world()
        report['level_saved'] = bool(unreal.EditorLoadingAndSavingUtils.save_map(world, HERO_LEVEL))
    out_json = ROOT / 'Saved/Audit/EveningExecution_20261018/hero_shots_commands.json'
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2), encoding='utf-8')
    log('report -> %s' % out_json)
    log('JOBS_OK=%d/%d errors=%s' % (len(report['jobs']), len(SHOTS), report['errors']))


main()
