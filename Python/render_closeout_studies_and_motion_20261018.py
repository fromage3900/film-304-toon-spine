"""Render the four controlled lighting studies and two complete 48-frame loops."""
import json
from datetime import datetime,timezone
from pathlib import Path
import unreal

def main(version='v01', shots_override=None, aa_overrides=None, console_overrides=None, resolution=None,
         expected_map='/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office_Assembly_20261018_v02',
         sequence_overrides=None, suspend_level_autoplay=False, still_frame=10):
    assert version.startswith('v') and version[1:].isdigit(), version
    root=Path(unreal.Paths.project_dir())
    receipt_name='mrq_studies_motion.json' if version=='v01' else 'mrq_studies_motion_'+version+'.json'
    audit=root/'Saved/Audit/Closeout_20261018'/receipt_name
    assert not audit.exists(), 'Inspect existing receipt before dispatch'
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_path_name().split('.',1)[0]==expected_map, world.get_path_name()
    executor=getattr(unreal,'_closeout_mrq_executor',None)
    assert executor is None or not executor.is_rendering()
    assert not unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).is_rendering()
    unreal.LevelSequenceEditorBlueprintLibrary.close_level_sequence()
    autoplay_states=[]
    if suspend_level_autoplay:
        for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
            if isinstance(actor,unreal.LevelSequenceActor):
                settings=actor.get_editor_property('playback_settings')
                if settings.auto_play:
                    autoplay_states.append(actor.get_actor_label())
                    settings.auto_play=False
                    actor.set_editor_property('playback_settings',settings)
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    src=unreal.load_asset('/Game/MoviePipelines/Film304Closeout_20261018/CFG_Closeout_Proof1080_4Spatial_v01')
    queue=unreal.new_object(unreal.MoviePipelineQueue);records=[]
    shots=shots_override or [('Lighting_'+letter,False) for letter in 'ABCD']+[('David',True),('WindowHero',True)]
    for shot,motion in shots:
        name='CFG_Closeout_'+shot+('_Motion48_' if motion else '_Study_')+version
        dest='/Game/MoviePipelines/Film304Closeout_20261018'
        assert not unreal.EditorAssetLibrary.does_asset_exist(dest+'/'+name)
        cfg=unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(name,dest,src)
        output=cfg.find_setting_by_class(unreal.MoviePipelineOutputSetting)
        if resolution:
            output.output_resolution=unreal.IntPoint(*resolution)
        output.custom_start_frame=0 if motion else still_frame;output.custom_end_frame=48 if motion else still_frame+1
        family=('Motion48_'+version) if motion else ('LightingStudies_v02' if version=='v01' else 'LightingStudies_'+version)
        directory=root/'Showcase/Film304_Closeout_20261018'/family/shot
        output.output_directory=unreal.DirectoryPath(str(directory))
        aa=cfg.find_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
        aa.spatial_sample_count=8 if motion else 4
        for key,value in (aa_overrides or {}).items():aa.set_editor_property(key,value)
        if console_overrides:
            console=cfg.find_or_add_setting_by_class(unreal.MoviePipelineConsoleVariableSetting)
            for key,value in console_overrides.items():
                console.add_or_update_console_variable(key,float(value))
        assert unreal.EditorAssetLibrary.save_loaded_asset(cfg)
        seq=unreal.load_asset((sequence_overrides or {}).get(shot,'/Game/Sequences/Film304Closeout_20261018/LS_Closeout_'+shot+'48f_v01'));assert seq
        job=queue.allocate_new_job(unreal.MoviePipelineExecutorJob);job.job_name=shot
        job.map=unreal.SoftObjectPath(world.get_path_name());job.sequence=unreal.SoftObjectPath(seq.get_path_name())
        job.set_configuration(cfg)
        records.append({'shot':shot,'sequence':seq.get_path_name(),'output':str(directory),'frames':48 if motion else 1})
    receipt={'state':'running','started_utc':datetime.now(timezone.utc).isoformat(),'jobs':records,'errors':[]}
    def write():audit.write_text(json.dumps(receipt,indent=2))
    def finished(executor,success):
        if autoplay_states:
            for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
                if isinstance(actor,unreal.LevelSequenceActor) and actor.get_actor_label() in autoplay_states:
                    settings=actor.get_editor_property('playback_settings')
                    settings.auto_play=True
                    actor.set_editor_property('playback_settings',settings)
            receipt['autoplay_restored']=bool(unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
        receipt.update(state='finished',success=bool(success),finished_utc=datetime.now(timezone.utc).isoformat());write()
    def errored(executor,pipeline,is_fatal,text):receipt['errors'].append({'fatal':bool(is_fatal),'text':str(text)});write()
    executor=unreal.new_object(unreal.MoviePipelinePIEExecutor)
    executor.on_executor_finished_delegate.add_callable(finished);executor.on_executor_errored_delegate.add_callable(errored)
    unreal._closeout_mrq_executor=executor;unreal._closeout_mrq_queue=queue;unreal._closeout_mrq_callbacks=(finished,errored)
    write();executor.execute(queue);print('STUDIES_AND_MOTION_RENDER_STARTED')

if __name__=='__main__':main()
