"""Four angles x three explicit PPV treatments, preserving the owner baseline."""
import unreal,json
from pathlib import Path

def main():
    ed=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_path_name().startswith('/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office.')
    assert not unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).is_rendering()
    actors=ed.get_all_level_actors();by={a.get_actor_label():a for a in actors}
    baseline_pp=[a for a in actors if isinstance(a,unreal.PostProcessVolume)]
    # Separate look volumes: original post-process actors and shared materials are untouched.
    looks={}
    for key,source in [('A_CinematicStack','PPV_ToonOutlineHalftoneStack'),('B_SoftClean','PPV_ToonOutlineClean'),('C_Without','PPV_ToonOutlineOnly')]:
        label='Film_Compare_'+key
        assert label not in by,label
        a=ed.spawn_actor_from_class(unreal.PostProcessVolume,unreal.Vector(0,0,600))
        a.set_actor_label(label);a.modify();a.unbound=True;a.priority=1000;a.enabled=False;a.blend_weight=1
        s=by[source].settings
        if key=='C_Without':s.weighted_blendables=unreal.WeightedBlendables(array=[])
        s.override_color_saturation=True;s.color_saturation=unreal.Vector4(1,1,1,0.94 if key.startswith('A') else 0.98 if key.startswith('B') else 1)
        s.override_color_contrast=True;s.color_contrast=unreal.Vector4(1,1,1,1.05 if key.startswith('A') else 1.02 if key.startswith('B') else 1)
        s.override_vignette_intensity=True;s.vignette_intensity=0.18 if key.startswith('A') else .10 if key.startswith('B') else 0
        s.override_film_grain_intensity=True;s.film_grain_intensity=.08 if key.startswith('A') else .025 if key.startswith('B') else 0
        # Identical exposure authority across the three treatments.
        s.override_auto_exposure_method=True;s.auto_exposure_method=unreal.AutoExposureMethod.AEM_HISTOGRAM
        s.override_auto_exposure_bias=True;s.auto_exposure_bias=-.85
        a.settings=s;looks[key]=a
    # Actual live-cooked HDA lights drive the comparison; native baseline stays intact outside the sequences.
    w=unreal._film_window_live;children=w.get_houdini_asset_actor().get_attached_actors()
    assert len(children)==3
    source_lights=[by['Film_WindowShaft_%02d'%i] for i in range(1,4)]
    hda_lights=[]
    for i,child in enumerate(sorted(children,key=lambda a:a.get_actor_location().y)):
        c=child.get_component_by_class(unreal.SpotLightComponent);src=source_lights[i].get_component_by_class(unreal.SpotLightComponent)
        child.modify();c.modify();child.set_actor_label('Film_Live_Shaft_%02d'%(i+1))
        child.set_actor_transform(source_lights[i].get_actor_transform(),False,False)
        for prop in ['intensity','intensity_units','attenuation_radius','inner_cone_angle','outer_cone_angle','temperature','use_temperature','light_color','volumetric_scattering_intensity','cast_shadows']:
            c.set_editor_property(prop,src.get_editor_property(prop))
        c.set_visibility(False);child.set_actor_hidden_in_game(False);hda_lights.append(c)
    w.set_auto_cooking_enabled(False)
    cam_specs={
        '01_Office':('Film_Cam_Showcase_Ensemble_v02',None,None,35,'Warm'),
        '02_Architecture':('SESSION_CAM_Verify',(300,-500,160),(190,100,300),24,'Neutral'),
        '03_Breakroom':('CineCam_Hero_DeskLineup',(720,80,150),(350,600,130),28,'Cool'),
        '04_David':('Film_Cam_David_DeskSleep',None,None,38,'Warm')}
    lib=unreal.LevelSequenceEditorBlueprintLibrary;binding_ed=unreal.get_editor_subsystem(unreal.LevelSequenceEditorSubsystem)
    def bool_track(seq,obj,prop,value):
        b=seq.add_possessable(obj);t=b.add_track(unreal.MovieSceneBoolTrack);t.set_property_name_and_path(prop,prop)
        sec=t.add_section();sec.set_range(0,48);sec.get_all_channels()[0].set_default(value)
    records=[]
    for angle,(camera_label,pos,target,focal,mode) in cam_specs.items():
        cam=by[camera_label];cam.modify();cine=cam.get_cine_camera_component();cine.modify()
        if pos:
            cam.set_actor_location(unreal.Vector(*pos),False,False);cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*pos),unreal.Vector(*target)),False)
        cine.current_focal_length=focal;cine.current_aperture=8
        fb=cine.filmback;fb.sensor_width=36;fb.sensor_height=20.25;cine.filmback=fb
        focus=cine.focus_settings;focus.focus_method=unreal.CameraFocusMethod.DISABLE;cine.focus_settings=focus
        pp=cine.post_process_settings
        for p in ['override_auto_exposure_method','override_auto_exposure_bias','override_auto_exposure_apply_physical_camera_exposure']:setattr(pp,p,False)
        cine.post_process_settings=pp
        for look,volume in looks.items():
            name='LS_Compare_'+angle+'_'+look+'_48f_v01';dest='/Game/Sequences/Film304Closeout_20261018/Comparisons'
            assert not unreal.EditorAssetLibrary.does_asset_exist(dest+'/'+name)
            source=unreal.load_asset('/Game/Sequences/Film304Closeout_20261018/LS_MainOffice_Ensemble_'+mode+'_48f_v01')
            seq=unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(name,dest,source);seq.modify()
            for t in list(seq.get_tracks()):
                if isinstance(t,unreal.MovieSceneCameraCutTrack):seq.remove_track(t)
            for b in list(seq.get_possessables()):
                cls=b.get_possessed_object_class()
                if cls and cls.get_name()=='CineCameraActor':b.remove()
            b=seq.add_possessable(cam);lib.open_level_sequence(seq);binding_ed.remove_all_bindings(b);binding_ed.add_actors_to_binding([cam],b)
            cut=seq.add_track(unreal.MovieSceneCameraCutTrack).add_section();cut.set_range(0,48);cut.set_camera_binding_id(seq.get_binding_id(b))
            for a in baseline_pp+list(looks.values()):bool_track(seq,a,'bEnabled',a==volume)
            for a in source_lights:bool_track(seq,a.get_component_by_class(unreal.SpotLightComponent),'bVisible',False)
            for c in hda_lights:bool_track(seq,c,'bVisible',True)
            lib.set_current_time(20);resolved=lib.get_bound_objects(seq.get_binding_id(b));assert resolved==[cam],resolved
            unreal.EditorAssetLibrary.save_loaded_asset(seq,False);lib.close_level_sequence()
            records.append({'shot':angle+'_'+look,'sequence':seq.get_path_name(),'camera':camera_label,'lighting':mode,'look':look,'live_hda_lights':3})
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    Path(unreal.Paths.project_dir()+'Saved/Audit/Closeout_20261018/four_angle_ppv_comparison.json').write_text(json.dumps(records,indent=2))
    print(json.dumps(records))

if __name__=='__main__':main()
