"""Build the Film 304 Dusk final render setup (sequences + MRQ configs).

- 24 fps sequences possessing the three authored cameras, with the cast idle
  clips bound so nothing renders in a rest pose.
- proof config: 1920x1080, TAA 2x8, PNG + EXR
- final config: 1920x1080, TAA 4x64 (256 samples), PNG + 16-bit EXR
- fixes the last legacy prop (vending machine) and saves L_Film_Office_Dusk_v06
- writes exact, non-duplicated command lines for headless renders.

Run inside the live editor while L_Film_Office is open.
"""
import json
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / 'Saved/Audit/Film304_Finish_20261018'
OUT.mkdir(parents=True, exist_ok=True)
SEQ_DIR = '/Game/Sequences/Film304Dusk_20261018'
CFG_DIR = '/Game/MoviePipelines/Film304Dusk_20261018'
ANIM_ROOT = '/Game/Animations/Film304Idle_20261017'
OUT_REL = 'Showcase/Film304_Dusk_20261018'
RES_W, RES_H = 1920, 1080
FPS = 24
FRAME = 18

EAL = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()

CAST = {
    'Film_Cast_Sam': 'AS_Sam_OfficeIdle_48f_v01',
    'Film_Cast_David': 'AS_David_DeskSleep_48f_v02',
    'Film_Subject_Dana_v08_CleanSkin': 'AS_Dana_OfficeIdle_48f_v01',
    'Film_Cast_Spider': 'AS_Spider_OfficeIdle_48f_v01',
}

SHOTS = [
    ('DUSK01_Medium', 'Film_Cam_OfficeMedium', 'cast medium / three-quarter, practicals'),
    ('DUSK02_Window', 'CineCam_Hero_WindowEstablishing', 'window-light hero framing'),
    ('DUSK03_DeskLineup', 'CineCam_Hero_DeskLineup', 'desk row / cast lineup'),
]

report = {'world': None, 'sequences': [], 'configs': [], 'commands': [], 'errors': [],
          'map': None}

world = unreal.EditorLevelLibrary.get_editor_world()
report['world'] = world.get_path_name() if world else None
print('START_WORLD ' + str(report['world']))
if not report['world'].endswith('L_Film_Office.L_Film_Office'):
    raise RuntimeError('Refusing: live world is ' + str(report['world']))

for d in (SEQ_DIR, CFG_DIR):
    if not EAL.does_directory_exist(d):
        EAL.make_directory(d)


def by_label(label):
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            if a.get_actor_label() == label:
                return a
        except Exception:
            pass
    return None



def build_sequence(seq_name, camera):
    if EAL.does_asset_exist(seq_name):
        EAL.delete_asset(seq_name)
    seq = TOOLS.create_asset(seq_name.rsplit('/', 1)[1], SEQ_DIR, unreal.LevelSequence,
                             unreal.LevelSequenceFactoryNew())
    if seq is None:
        raise RuntimeError('sequence create failed: ' + seq_name)
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
            report['errors'].append('cast/clip missing: %s / %s' % (label, anim_name))
            continue
        cb = seq.add_possessable(actor)
        track = cb.add_track(unreal.MovieSceneSkeletalAnimationTrack)
        asec = track.add_section()
        asec.set_range(0, 48)
        params = asec.get_editor_property('params')
        params.set_editor_property('animation', clip)
        asec.set_editor_property('params', params)
    EAL.save_loaded_asset(seq, False)
    return seq.get_path_name()


def build_config(stem, seq_path, final):
    if EAL.does_asset_exist(stem):
        EAL.delete_asset(stem)
    cfg = TOOLS.create_asset(stem.rsplit('/', 1)[1], CFG_DIR,
                             unreal.MoviePipelineMasterConfig,
                             unreal.MoviePipelinePrimaryConfigFactory())
    if cfg is None:
        raise RuntimeError('config create failed: ' + stem)
    out = cfg.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting, True)
    out.set_editor_property('output_resolution', unreal.IntPoint(RES_W, RES_H))
    out.set_editor_property('output_directory', unreal.DirectoryPath(str(ROOT / OUT_REL)))
    out.set_editor_property('file_name_format', stem.rsplit('/', 1)[1])
    out.set_editor_property('override_existing_output', True)
    out.set_editor_property('use_custom_playback_range', True)
    out.set_editor_property('custom_start_frame', FRAME)
    out.set_editor_property('custom_end_frame', FRAME + 1)

    png = cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG, True)
    png.set_is_enabled(True)
    try:
        exr = cfg.find_or_add_setting_by_class(
            unreal.MoviePipelineImageSequenceOutput_EXR, True)
        exr.set_is_enabled(True)
    except Exception as exc:
        report['errors'].append('EXR setting: ' + str(exc)[:90])

    cfg.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase, True)
    aa = cfg.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting, True)
    aa.set_editor_property('override_anti_aliasing', True)
    aa.set_editor_property('anti_aliasing_method', unreal.AntiAliasingMethod.AAM_TEMPORAL_AA)
    aa.set_editor_property('spatial_sample_count', 4 if final else 2)
    aa.set_editor_property('temporal_sample_count', 64 if final else 8)
    aa.set_editor_property('engine_warm_up_count', 120 if final else 48)
    aa.set_editor_property('render_warm_up_count', 32 if final else 16)
    go = cfg.find_or_add_setting_by_class(unreal.MoviePipelineGameOverrideSetting, True)
    go.set_editor_property('texture_streaming',
                           unreal.MoviePipelineTextureStreamingMethod.FULLY_LOAD)
    go.set_editor_property('cinematic_quality_settings', True)
    EAL.save_loaded_asset(cfg, False)
    return cfg.get_path_name()



# Last true legacy prop: the vending machine (its instance uses the misspelled
# "Vennding" token, so the generic mapper skipped it).
vending = unreal.load_asset('/Game/Materials/Instances/Film304/Scene/Dusk20261018/MI_Dusk_Plastic')
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    try:
        label = a.get_actor_label()
    except Exception:
        continue
    if 'Vennding' in label or 'Vending' in label:
        for comp in a.get_components_by_class(unreal.MeshComponent) or []:
            for i in range(len(comp.get_materials() or [])):
                comp.set_material(i, vending)
        report.setdefault('legacy_fixed', []).append(label)

# Build sequences + configs.
for shot, cam_label, note in SHOTS:
    cam = by_label(cam_label)
    if cam is None:
        report['errors'].append('camera missing ' + cam_label)
        continue
    seq_path = build_sequence(SEQ_DIR + '/LS_' + shot, cam)
    report['sequences'].append({'shot': shot, 'note': note, 'sequence': seq_path})
    for variant, final in (('proof', False), ('final', True)):
        cfg_path = build_config(
            CFG_DIR + '/CFG_FILM304_' + shot + '_' + variant + '_v01', seq_path, final)
        report['configs'].append({'shot': shot, 'variant': variant,
                                  'config': cfg_path, 'samples': 256 if final else 16})
    seq_asset = seq_path.rsplit('/', 1)[1].split('.')[0]
    final_cfg = CFG_DIR + '/CFG_FILM304_' + shot + '_final_v01.CFG_FILM304_' + shot + '_final_v01'
    command = ('"C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" '
               '"%s" /Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office_Dusk_20261018_v06 '
               '-game -LevelSequence="%s.%s" -MoviePipelineConfig="%s" '
               '-windowed -log -unattended'
               % (str(ROOT / 'HumberToonShader.uproject'), seq_path, seq_asset, final_cfg))
    report['commands'].append({'shot': shot, 'command': command})

DEST = '/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office_Dusk_20261018_v06'
saved = bool(unreal.EditorLoadingAndSavingUtils.save_map(world, DEST))
report['map'] = {'path': DEST, 'saved': saved}

(OUT / 'final_render_setup.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('MRQ_SETUP sequences=%d configs=%d commands=%d errors=%d saved=%s'
      % (len(report['sequences']), len(report['configs']), len(report['commands']),
         len(report['errors']), saved))
for e in report['errors']:
    print('  ERROR ' + e)
for c in report['commands']:
    print('CMD ' + c['shot'] + ': ' + c['command'])
print('REPORT ' + str(OUT / 'final_render_setup.json'))
