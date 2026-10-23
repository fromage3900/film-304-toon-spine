"""Three real MRQ proof frames after dynamic-light and texture fixes."""
import json
from datetime import datetime,timezone
from pathlib import Path
import unreal

def main():
    root=Path(unreal.Paths.project_dir());audit=root/'Saved/Audit/Closeout_20261018/mrq_pack_proofs.json'
    assert not audit.exists(), 'Inspect previous executor receipt before dispatching again'
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert 'L_Film_Office_Assembly_20261018_v02.' in world.get_path_name()
    assert not unreal._closeout_mrq_executor.is_rendering()
    src=unreal.load_asset('/Game/MoviePipelines/Film304Closeout_20261018/CFG_Closeout_Proof1080_4Spatial_v01')
    queue=unreal.new_object(unreal.MoviePipelineQueue)
    records=[]
    for shot in ['WindowHero','Ceiling','David']:
        name='CFG_Closeout_'+shot+'_Proof1080_v01';dest='/Game/MoviePipelines/Film304Closeout_20261018'
        assert not unreal.EditorAssetLibrary.does_asset_exist(dest+'/'+name)
        config=unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(name,dest,src)
        output=config.find_setting_by_class(unreal.MoviePipelineOutputSetting)
        output.custom_start_frame=10;output.custom_end_frame=11
        output.output_directory=unreal.DirectoryPath(str(root/'Showcase/Film304_Closeout_20261018/PackProofs_v01'/shot))
        assert unreal.EditorAssetLibrary.save_loaded_asset(config)
        path='/Game/Sequences/Film304Closeout_20261018/LS_Closeout_'+shot+'48f_v01'
        sequence=unreal.load_asset(path);assert sequence
        job=queue.allocate_new_job(unreal.MoviePipelineExecutorJob);job.job_name=shot+' warm light proof'
        job.map=unreal.SoftObjectPath(world.get_path_name());job.sequence=unreal.SoftObjectPath(sequence.get_path_name())
        job.set_configuration(config)
        records.append({'shot':shot,'sequence':sequence.get_path_name(),'config':config.get_path_name()})
    receipt={'state':'running','started_utc':datetime.now(timezone.utc).isoformat(),'jobs':records,'errors':[]}
    def write():audit.write_text(json.dumps(receipt,indent=2))
    def finished(executor,success):
        receipt.update(state='finished',success=bool(success),finished_utc=datetime.now(timezone.utc).isoformat());write()
    def errored(executor,pipeline,is_fatal,text):receipt['errors'].append({'fatal':bool(is_fatal),'text':str(text)});write()
    executor=unreal.new_object(unreal.MoviePipelinePIEExecutor)
    executor.on_executor_finished_delegate.add_callable(finished);executor.on_executor_errored_delegate.add_callable(errored)
    unreal._closeout_mrq_executor=executor;unreal._closeout_mrq_queue=queue
    unreal._closeout_mrq_callbacks=(finished,errored)
    write();executor.execute(queue);print('MRQ_PACK_STARTED '+str(audit))

if __name__=='__main__':main()
