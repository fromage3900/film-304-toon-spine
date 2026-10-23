"""Read back the final/proof MRQ configs. Read-only."""
import unreal

CFG = '/Game/MoviePipelines/Film304Dusk_20261018/CFG_FILM304_DUSK01_Medium_final_v01'
PROOF = '/Game/MoviePipelines/Film304Dusk_20261018/CFG_FILM304_DUSK01_Medium_proof_v01'
SEQ = '/Game/Sequences/Film304Dusk_20261018/LS_DUSK01_Medium'

for path, label in ((CFG, 'FINAL'), (PROOF, 'PROOF')):
    cfg = unreal.load_asset(path)
    print('%s CONFIG %s' % (label, cfg.get_path_name() if cfg else 'MISSING'))
    if not cfg:
        continue
    out = cfg.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting, False)
    if out:
        r = out.get_editor_property('output_resolution')
        print('  OUT %dx%d dir=%s name=%s range=%s-%s' % (
            r.x, r.y, out.get_editor_property('output_directory').path,
            out.get_editor_property('file_name_format'),
            out.get_editor_property('custom_start_frame'),
            out.get_editor_property('custom_end_frame')))
    aa = cfg.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting, False)
    if aa:
        print('  AA method=%s spatial=%d temporal=%d warm=%d/%d' % (
            aa.get_editor_property('anti_aliasing_method'),
            aa.get_editor_property('spatial_sample_count'),
            aa.get_editor_property('temporal_sample_count'),
            aa.get_editor_property('engine_warm_up_count'),
            aa.get_editor_property('render_warm_up_count')))
    png = cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG, False)
    exr = cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_EXR, False)
    print('  PNG=%s EXR=%s' % (png.is_enabled() if png else 'missing',
                               exr.is_enabled() if exr else 'missing'))
    go = cfg.find_or_add_setting_by_class(unreal.MoviePipelineGameOverrideSetting, False)
    if go:
        print('  STREAM=%s CINEMATIC=%s' % (
            go.get_editor_property('texture_streaming'),
            go.get_editor_property('cinematic_quality_settings')))

seq = unreal.load_asset(SEQ)
print('SEQUENCE %s' % (seq.get_path_name() if seq else 'MISSING'))
if seq:
    print('  range %s-%s' % (seq.get_playback_start(), seq.get_playback_end()))
    try:
        print('  bindings %d' % len(seq.get_bindings()))
    except Exception as exc:
        print('  bindings ERR %s' % str(exc)[:80])
