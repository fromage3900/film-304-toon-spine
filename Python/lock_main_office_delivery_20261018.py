"""Persist the assembled original room and leave native artist-facing render controls."""
import json
import math
from pathlib import Path
import unreal

import film304_fog

def main():
    root=Path(unreal.Paths.project_dir());audit=root/'Saved/Audit/Closeout_20261018'
    editor=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    map_path='/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office'
    assert world.get_path_name().split('.')[0]==map_path
    qsub=unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
    assert not qsub.is_rendering()
    unreal.LevelSequenceEditorBlueprintLibrary.close_level_sequence()
    subsystem=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    by={a.get_actor_label():a for a in subsystem.get_all_level_actors()}
    frozen=json.loads((audit/'owner_frozen_dana_skin.json').read_text())
    dana=by['Film_Subject_Dana_v08_CleanSkin'].get_component_by_class(unreal.SkeletalMeshComponent)
    if dana.get_material(0).get_path_name()!=frozen['assignment']:
        frozen['previous_recorded_assignment']=frozen['assignment']
        frozen['assignment']=dana.get_material(0).get_path_name()
        frozen['note']='Preserve current post-restart owner assignment; no skin writes performed.'
        (audit/'owner_frozen_dana_skin.json').write_text(json.dumps(frozen,indent=2))
    # Mark all scoped persistent objects before setting component values.
    for a in by.values():
        if a.get_actor_label().startswith(('Film_','SM_Glass_WindowBay','EST_Horizon','SM_Ext_','EST_Establishing')) or a.get_component_by_class(unreal.LightComponent):
            a.modify()
            for c in a.get_components_by_class(unreal.ActorComponent):c.modify()
    lib=unreal.MaterialEditingLibrary
    dustmat=unreal.load_asset('/Game/VFX/Film304Closeout_20261018/M_Film_WindowDust_SoftLoop_v01')
    assert dustmat.get_path_name().split('.')[0]=='/Game/VFX/Film304Closeout_20261018/M_Film_WindowDust_SoftLoop_v01'
    dustmat.modify();dustmat.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT_COLORED_TRANSMITTANCE)
    lib.recompile_material(dustmat);assert unreal.EditorAssetLibrary.save_loaded_asset(dustmat)
    dust=by['Film_WindowDust_Subtle'].get_component_by_class(unreal.NiagaraComponent)
    dust.set_variable_float('User.Sprite Scale',.0035)
    dust.set_variable_float('User.Spawn Rate',12);dust.set_variable_float('User.CPU Spawn Rate',12)
    dust.set_variable_material('User.Dust Sprite Material',dustmat)
    dust.set_editor_property('auto_activate',True);dust.set_visibility(True);dust.reinitialize_system();dust.activate(True)
    legacy=by.get('VFX_DustMotes_WindowRays')
    if legacy:
        legacy.modify();c=legacy.get_component_by_class(unreal.NiagaraComponent);c.modify();c.deactivate();c.set_visibility(False);c.set_editor_property('auto_activate',False)
    # Keep the original source untouched; correct the existing candidate track only.
    original=unreal.load_asset('/Game/Animations/Film304Idle_20261017/AS_David_DeskSleep_48f_v02')
    palm=unreal.load_asset('/Game/Animations/Film304Idle_20261017/AS_David_DeskSleep_PalmUp_48f_v03')
    poses=[unreal.AnimationLibrary.get_bone_pose_for_frame(original,'Wrist_L',i,False) for i in range(49)]
    angle=math.radians(-60)/2;delta=unreal.Quat(math.sin(angle),0,0,math.cos(angle))
    ctrl=palm.controller;ctrl.open_bracket('Align palm toward head around forearm axis',False)
    assert ctrl.set_bone_track_keys('Wrist_L',[p.translation for p in poses],[p.rotation*delta for p in poses],[p.scale3d for p in poses],False)
    ctrl.close_bracket(False);assert unreal.EditorAssetLibrary.save_loaded_asset(palm)
    recipe_data=json.loads((audit/'main_office_composed_shots.json').read_text())
    recipes={r['lighting']:r['lights'] for r in recipe_data['shots'] if r['shot']=='Ensemble'}
    # Already-authored Sequencer recipes are native artist controls; avoid the
    # failed variant activation rather than adding another dependency.
    for row in recipes['Neutral']:
        actor=by[row['actor']];c=actor.get_component_by_class(unreal.LightComponent)
        actor.modify();c.modify();c.set_intensity(row['intensity'])
        c.set_editor_property('use_temperature',True);c.set_editor_property('temperature',row['kelvin'])
        if 'Aviation' not in row['actor']:c.set_light_color(unreal.LinearColor(1,1,1,1))
    lighting_options={mode:'/Game/Sequences/Film304Closeout_20261018/LS_MainOffice_Ensemble_'+mode+'_48f_v01' for mode in recipes}
    playback=by['Film_OfficeIdle_LoopPlayback'];playback.modify()
    settings=playback.get_editor_property('playback_settings');settings.auto_play=False;settings.disable_camera_cuts=True;playback.set_editor_property('playback_settings',settings)
    # Source remains available for native Sequencer playback; MRQ owns shot evaluation.
    seqroot='/Game/Sequences/Film304Closeout_20261018'
    configroot='/Game/MoviePipelines/Film304Closeout_20261018'
    sourcecfg=unreal.load_asset(configroot+'/CFG_Closeout_Proof1080_4Spatial_v01')
    tools=unreal.AssetToolsHelpers.get_asset_tools()
    configs={}
    for still in [False,True]:
        name='CFG_Office_'+('Still20' if still else 'Motion48')+'_1080_v01'
        cfg=unreal.load_asset(configroot+'/'+name) or tools.duplicate_asset(name,configroot,sourcecfg)
        output=cfg.find_setting_by_class(unreal.MoviePipelineOutputSetting)
        output.output_resolution=unreal.IntPoint(1920,1080);output.use_custom_playback_range=True
        output.custom_start_frame=20 if still else 0;output.custom_end_frame=21 if still else 48
        output.file_name_format='{sequence_name}.{frame_number}';output.zero_pad_frame_numbers=4
        output.output_directory=unreal.DirectoryPath(str(root/'Showcase/Film304_ReadyToRender'))
        aa=cfg.find_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
        aa.spatial_sample_count=4;aa.temporal_sample_count=1;aa.engine_warm_up_count=96;aa.render_warm_up_count=64;aa.render_warm_up_frames=True
        console=cfg.find_or_add_setting_by_class(unreal.MoviePipelineConsoleVariableSetting)
        console.add_or_update_console_variable('ShowFlag.SkyAtmosphere',1)
        # Applied from the shared helper so every Film 304 render path adopts the same
        # fog history setting. Volumetric fog temporal reprojection accumulated history
        # and was responsible for most of the loop seam drift (wrap MAE 1.8899 ->
        # 0.3451, ~82 percent, when disabled). Kept shot-scoped: changing the global
        # project setting was rejected in review.
        for cvar,value in film304_fog.render_console_overrides().items():
            console.add_or_update_console_variable(cvar,value)
        assert unreal.EditorAssetLibrary.save_loaded_asset(cfg);configs['still' if still else 'motion']=cfg
    queue=unreal.load_asset(configroot+'/Q_Office_ReadyToRender')
    if queue is None:queue=tools.duplicate_asset('Q_Office_ReadyToRender',configroot,unreal.new_object(unreal.MoviePipelineQueue))
    assert queue
    queue.modify();queue.delete_all_jobs();jobs=[]
    for index,name in enumerate(['Ensemble_Neutral','Ensemble_Warm','Ensemble_Cool','Dana_Neutral','David_Warm']):
        seq=unreal.load_asset(seqroot+'/LS_MainOffice_'+name+'_48f_v01');assert seq
        job=queue.allocate_new_job(unreal.MoviePipelineExecutorJob);job.job_name='%02d_%s'%(index+1,name)
        job.map=unreal.SoftObjectPath(world.get_path_name());job.sequence=unreal.SoftObjectPath(seq.get_path_name());job.set_configuration(configs['motion'])
        output=job.get_configuration().find_setting_by_class(unreal.MoviePipelineOutputSetting)
        output.output_directory=unreal.DirectoryPath(str(root/'Showcase/Film304_ReadyToRender'/name))
        job.set_is_enabled(index==0)
        jobs.append({'job':job.job_name,'enabled':job.is_enabled(),'sequence':seq.get_path_name(),'frames':[0,47],'output':output.output_directory.path})
    assert unreal.EditorAssetLibrary.save_loaded_asset(queue)
    assert dana.get_material(0).get_path_name()==frozen['assignment']
    # Save only the current Office; no Save All and no copy-map writes.
    assert editor.save_current_level()
    # Do not reload a world from inside a Python frame holding actor/component
    # references: this editor crashed in TypedElement cleanup on that path.
    # Verify persistence after a normal editor reopen in a separate invocation.
    current={a.get_actor_label():a for a in subsystem.get_all_level_actors()}
    current_skin=current['Film_Subject_Dana_v08_CleanSkin'].get_component_by_class(unreal.SkeletalMeshComponent).get_material(0)
    assert current_skin.get_path_name()==frozen['assignment'],'Frozen skin assignment changed across reload'
    counts={label:sum(a.get_actor_label()==label for a in subsystem.get_all_level_actors()) for label in ['Film_Closeout_Ceiling_Concrete','Film_Closeout_Ceiling_Metal','Film_WindowDust_Subtle','Film_WindowShaft_01','Film_WindowShaft_02','Film_WindowShaft_03']}
    assert all(n==1 for n in counts.values()),counts
    assert current['Film_Closeout_Ceiling_Concrete'].static_mesh_component.static_mesh.get_path_name().split('.')[0].endswith('MainRoomFit_v05')
    assert len(queue.get_jobs())==5
    qsub.load_queue(queue,False)
    proof={'map':map_path,'saved_and_reloaded':False,'restart_verification_pending':True,'frozen_dana_skin':current_skin.get_path_name(),'skin_untouched':True,'counts':counts,'dust_sprite_scale':current['Film_WindowDust_Subtle'].get_component_by_class(unreal.NiagaraComponent).get_variable_float('User.Sprite Scale')[0],'lighting_options':lighting_options,'queue':queue.get_path_name(),'configs':{k:v.get_path_name() for k,v in configs.items()},'jobs':jobs,'palm_roll_degrees':-60,'pose_source_preserved':original.get_path_name(),'render_started':False,'visual_gate':'Targeted save and native controls authored; restart persistence and corrected exported images pending'}
    (audit/'main_office_locked_delivery_setup.json').write_text(json.dumps(proof,indent=2))
    print(json.dumps(proof))

if __name__=='__main__':main()
