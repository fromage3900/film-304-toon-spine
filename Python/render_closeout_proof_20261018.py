"""Render an isolated, saved-map MRQ proof with a recorded completion callback."""
import json
from datetime import datetime,timezone
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir());OUT=ROOT/'Saved/Audit/Closeout_20261018'
MAP='/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office_Assembly_20261018_v02'
SEQ='/Game/Sequences/Film304Closeout_20261018/LS_Closeout_Medium48f_v01'
CONFIG='/Game/MoviePipelines/Film304Closeout_20261018/CFG_Closeout_Proof1080_4Spatial_v01'

def main():
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_path_name()==MAP+'.'+MAP.rsplit('/',1)[1]
    assert not unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).is_rendering()
    assert not hasattr(unreal,'_closeout_mrq_executor') or not unreal._closeout_mrq_executor.is_rendering()
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    unreal.LevelSequenceEditorBlueprintLibrary.close_level_sequence()
    for a in actors.get_all_level_actors():
        if a.get_actor_label() in ['SESSION_CAPTURE_CAST_GROUP_v01','SESSION_CAPTURE_Sam_closed_confirmed']:
            actors.destroy_actor(a)
        if a.get_actor_label()=='Film_OfficeIdle_LoopPlayback':
            settings=a.playback_settings;settings.auto_play=False;a.set_editor_property('playback_settings',settings)
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    assert not unreal.EditorAssetLibrary.does_asset_exist(CONFIG)
    cfg=unreal.AssetToolsHelpers.get_asset_tools().create_asset(CONFIG.rsplit('/',1)[1],CONFIG.rsplit('/',1)[0],
                 unreal.MoviePipelinePrimaryConfig,unreal.MoviePipelinePrimaryConfigFactory())
    output=cfg.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
    output.output_resolution=unreal.IntPoint(1920,1080)
    output.output_directory=unreal.DirectoryPath(str(ROOT/'Showcase/Film304_Closeout_20261018/ProofWarm_v01'))
    output.file_name_format='{sequence_name}.{frame_number}'
    output.use_custom_playback_range=True;output.custom_start_frame=20;output.custom_end_frame=21
    output.override_existing_output=False
    cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)
    cfg.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
    aa=cfg.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
    aa.override_anti_aliasing=True;aa.anti_aliasing_method=unreal.AntiAliasingMethod.AAM_NONE
    aa.spatial_sample_count=4;aa.temporal_sample_count=1
    aa.engine_warm_up_count=48;aa.render_warm_up_count=16
    go=cfg.find_or_add_setting_by_class(unreal.MoviePipelineGameOverrideSetting)
    go.texture_streaming=unreal.MoviePipelineTextureStreamingMethod.FULLY_LOAD
    go.cinematic_quality_settings=True
    assert unreal.EditorAssetLibrary.save_loaded_asset(cfg)
    queue=unreal.new_object(unreal.MoviePipelineQueue)
    job=queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
    job.job_name='Office Warm Window Rays — proof'
    job.map=unreal.SoftObjectPath(world.get_path_name())
    job.sequence=unreal.SoftObjectPath(SEQ+'.'+SEQ.rsplit('/',1)[1]);job.set_configuration(cfg)
    receipt={'started_utc':datetime.now(timezone.utc).isoformat(),'map':MAP,'sequence':SEQ,'config':CONFIG,
             'lighting':'C_WarmDesk','resolution':[1920,1080],'frames':[20,21],
             'spatial_samples':4,'temporal_samples':1,'state':'running','errors':[]}
    path=OUT/'mrq_warm_proof.json'
    def write():path.write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    def finished(executor,success):
        receipt['state']='finished';receipt['success']=bool(success)
        receipt['finished_utc']=datetime.now(timezone.utc).isoformat();write()
    def errored(executor,pipeline,is_fatal,error_text):
        receipt['errors'].append({'fatal':bool(is_fatal),'text':str(error_text)});write()
    executor=unreal.new_object(unreal.MoviePipelinePIEExecutor)
    executor.on_executor_finished_delegate.add_callable(finished)
    executor.on_executor_errored_delegate.add_callable(errored)
    unreal._closeout_mrq_executor=executor;unreal._closeout_mrq_queue=queue
    unreal._closeout_mrq_callbacks=(finished,errored)
    write();executor.execute(queue)
    print('MRQ_PROOF_STARTED '+str(path))

if __name__=='__main__':main()
