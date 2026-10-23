"""Three reusable camera shots and three light-only recipes in the original room."""
import json
from pathlib import Path
import unreal

ROOT='/Game/Sequences/Film304Closeout_20261018'
def main():
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_path_name()=='/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office.L_Film_Office'
    assert not unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).is_rendering()
    subsystem=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors=subsystem.get_all_level_actors();by={a.get_actor_label():a for a in actors}
    source=unreal.load_asset('/Game/Sequences/Film304Idle_20261017/LS_OfficeCast_SleepFaces_48f_v03_SoftSnore')
    assert len([b for b in source.get_spawnables() if 'SoftSnore' in b.get_name()])==4
    lib=unreal.LevelSequenceEditorBlueprintLibrary
    bindings=unreal.get_editor_subsystem(unreal.LevelSequenceEditorSubsystem)
    lib.close_level_sequence()
    cameras={
        'Ensemble':('Film_Cam_Showcase_Ensemble_v02',(400,-370,150),(-120,50,90),35),
        'Dana':('Film_Cam_Showcase_DanaPortrait_v02',(110,-65,100),(20,43,82),65),
        'David':('Film_Cam_David_DeskSleep',(-235,-165,104),(-145,-65,77),38),
    }
    camera_before=[]
    for name,(label,position,target,focal) in cameras.items():
        actor=by[label];cine=actor.get_cine_camera_component()
        camera_before.append({'actor':label,'transform':actor.get_actor_transform().export_text(),'focal':cine.current_focal_length,'postprocess':cine.post_process_settings.export_text()})
        actor.set_actor_location(unreal.Vector(*position),False,False)
        actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*position),unreal.Vector(*target)),False)
        cine.current_focal_length=focal;cine.current_aperture=8
        fb=cine.filmback;fb.sensor_width=36;fb.sensor_height=20.25;cine.filmback=fb
        focus=cine.focus_settings;focus.focus_method=unreal.CameraFocusMethod.DISABLE;cine.focus_settings=focus
        pp=cine.post_process_settings
        pp.override_auto_exposure_method=True;pp.auto_exposure_method=unreal.AutoExposureMethod.AEM_MANUAL
        pp.override_auto_exposure_apply_physical_camera_exposure=True;pp.auto_exposure_apply_physical_camera_exposure=False
        pp.override_auto_exposure_bias=True;pp.auto_exposure_bias=0
        cine.post_process_settings=pp;cine.post_process_blend_weight=1
    baseline=[]
    for a in actors:
        c=a.get_component_by_class(unreal.LightComponent)
        if isinstance(a,unreal.Light) and c:
            baseline.append({'actor':a.get_actor_label(),'intensity':c.intensity,'temperature':c.temperature,'use_temperature':c.use_temperature,'color':list(c.light_color.to_tuple())})
    def recipe(label,mode,original):
        # Existing lights only; no exposure/sky changes between studies.
        warm=mode=='Warm';cool=mode=='Cool'
        if label=='SpotLight':return (5 if warm else 4.5 if cool else 6,4300 if warm else 6200 if cool else 5200)
        if label=='Cast_RimKicker_Light':return (.5 if warm or cool else .7,6800 if warm else 7500 if cool else 6000)
        if label=='Light_Cinematic_SunBeam':return (1.5 if warm else 1 if cool else 2.2,4200 if warm else 8000 if cool else 5800)
        if 'Troffer' in label or 'troffer' in label:return (6 if warm else 10 if cool else 15,3800 if warm else 4800 if cool else 4500)
        if 'CeilingWash' in label:return (2.5,4200 if warm else 6500 if cool else 5000)
        if label=='Film_Closeout_WindowBounce':return (8 if warm else 10 if cool else 12,6000 if warm else 7500 if cool else 6500)
        if 'WindowShaft' in label:return (120 if warm else 55 if cool else 80,4000 if warm else 6800 if cool else 5600)
        if 'DeskLamp' in label:return (2.5 if warm else 1.5,3000)
        if label=='Light_Hero_CharacterFill':return (3,5500 if warm else 6500)
        if label=='Light_Sam_HeroKey':return (2.5,4500 if warm else 6000 if cool else 5200)
        if label=='Light_David_KeyFill':return (1.5,4200 if warm else 6000 if cool else 5000)
        if label in ['PointLight','PointLight2']:return (.8,6000)
        if 'Cavity' in label:return (2.8,4500 if warm else 6500 if cool else 5500)
        return (original['intensity'],original['temperature'])
    records=[]
    for shot,mode in [('Ensemble','Neutral'),('Ensemble','Warm'),('Ensemble','Cool'),('Dana','Neutral'),('David','Warm')]:
        name='LS_MainOffice_'+shot+'_'+mode+'_48f_v01'
        assert not unreal.EditorAssetLibrary.does_asset_exist(ROOT+'/'+name),name
        seq=unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(name,ROOT,source)
        for track in list(seq.get_tracks()):
            if isinstance(track,unreal.MovieSceneCameraCutTrack):seq.remove_track(track)
        for b in list(seq.get_possessables()):
            cls=b.get_possessed_object_class()
            if cls and cls.get_name()=='CineCameraActor':b.remove()
        camera=by[cameras[shot][0]]
        b=seq.add_possessable(camera)
        lib.open_level_sequence(seq)
        bindings.remove_all_bindings(b);bindings.add_actors_to_binding([camera],b);b.set_name(camera.get_actor_label())
        cut=seq.add_track(unreal.MovieSceneCameraCutTrack).add_section();cut.set_range(0,48);cut.set_camera_binding_id(seq.get_binding_id(b))
        values=[]
        for original in baseline:
            actor=by[original['actor']];c=actor.get_component_by_class(unreal.LightComponent)
            value,temp=recipe(original['actor'],mode,original)
            binding=seq.add_possessable(c)
            for prop,v in [('Intensity',value),('Temperature',temp)]:
                t=binding.add_track(unreal.MovieSceneFloatTrack);t.set_property_name_and_path(prop,prop)
                s=t.add_section();s.set_range(0,48);s.get_all_channels()[0].set_default(float(v))
            t=binding.add_track(unreal.MovieSceneBoolTrack);t.set_property_name_and_path('bUseTemperature','bUseTemperature')
            s=t.add_section();s.set_range(0,48);s.get_all_channels()[0].set_default(True)
            t=binding.add_track(unreal.MovieSceneColorTrack);t.set_property_name_and_path('LightColor','LightColor')
            s=t.add_section();s.set_range(0,48)
            color=original['color'] if 'Aviation' in original['actor'] else [255,255,255,255]
            for ch,v in zip(s.get_all_channels(),color):ch.set_default(v/255)
            values.append({'actor':original['actor'],'intensity':value,'kelvin':temp})
        lib.set_current_time(20)
        resolved=lib.get_bound_objects(seq.get_binding_id(b));assert len(resolved)==1 and resolved[0]==camera
        cloud_objects=[]
        for binding in seq.get_spawnables():
            if 'SoftSnore' in binding.get_name():
                objects=lib.get_bound_objects(seq.get_binding_id(binding));assert len(objects)==1
                cloud_objects.append({'name':binding.get_name(),'parent':objects[0].get_attach_parent_actor().get_actor_label() if objects[0].get_attach_parent_actor() else None,'socket':str(objects[0].get_attach_parent_socket_name())})
        assert unreal.EditorAssetLibrary.save_loaded_asset(seq)
        lib.close_level_sequence()
        records.append({'shot':shot,'lighting':mode,'sequence':seq.get_path_name(),'camera':camera.get_actor_label(),'clouds':cloud_objects,'lights':values})
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    report={'world':world.get_path_name(),'camera_before':camera_before,'lighting_before':baseline,'shots':records,'new_levels':False,'new_lights':False,'shared_shader_edits':False,'visual_gate':'pending renders'}
    (Path(unreal.Paths.project_dir())/'Saved/Audit/Closeout_20261018/main_office_composed_shots.json').write_text(json.dumps(report,indent=2))
    print('SAVED_COMPOSED_SHOTS',[(r['shot'],r['lighting'],r['sequence']) for r in records])

if __name__=='__main__':main()
