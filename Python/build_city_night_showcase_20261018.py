"""Live 360 horizon, emissive windows, city ground, UDS night shots and aerial VFX."""
from pathlib import Path
import math,json,unreal

def main():
    root=Path(unreal.Paths.project_dir());audit=root/'Saved/Audit/Closeout_20261018/city_night_showcase.json'
    assert not audit.exists()
    ed=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);actors=ed.get_all_level_actors();by={a.get_actor_label():a for a in actors}
    assert not unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).is_rendering()
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world();tools=unreal.AssetToolsHelpers.get_asset_tools();lib=unreal.MaterialEditingLibrary
    dest='/Game/Materials/Recovery_Office_20261018/City';report={'preserved_map':world.get_path_name(),'shots':[]}
    def existing(name):return unreal.load_asset(dest+'/'+name) if unreal.EditorAssetLibrary.does_asset_exist(dest+'/'+name) else None
    working=unreal.load_asset('/Game/Materials/Recovery_Office_20261018/DanaParts/MI_Dana_Hair_StageRestored_v01')
    for name,tint,rough in [('MI_CityConcrete_Night_v01',(.11,.125,.15),.8),('MI_CityRoad_Wet_v01',(.015,.021,.029),.28),('MI_CityGround_v01',(.035,.045,.052),.88)]:
        m=existing(name) or tools.duplicate_asset(name,dest,working);assert m
        lib.set_material_instance_vector_parameter_value(m,'BaseTint',unreal.LinearColor(*tint,1));lib.set_material_instance_scalar_parameter_value(m,'Roughness',rough);unreal.EditorAssetLibrary.save_loaded_asset(m,False)
    mpc=existing('MPC_CityNight_v01') or tools.create_asset('MPC_CityNight_v01',dest,unreal.MaterialParameterCollection,unreal.MaterialParameterCollectionFactoryNew());assert mpc
    scalar=unreal.CollectionScalarParameter();scalar.set_editor_property('parameter_name','WindowGlow');scalar.set_editor_property('default_value',.12);mpc.set_editor_property('scalar_parameters',[scalar]);unreal.EditorAssetLibrary.save_loaded_asset(mpc,False)
    m=existing('M_CityWindows_Emissive_v01') or tools.create_asset('M_CityWindows_Emissive_v01',dest,unreal.Material,unreal.MaterialFactoryNew());assert m
    lib.delete_all_material_expressions(m)
    m.set_editor_property('two_sided',True)
    p=lib.create_material_expression(m,unreal.MaterialExpressionWorldPosition,-650,0)
    color=lib.create_material_expression(m,unreal.MaterialExpressionCustom,-430,0)
    ci=unreal.CustomInput();ci.set_editor_property('input_name','P');color.set_editor_property('inputs',[ci]);color.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    color.set_editor_property('code','float r=frac(sin(dot(floor(P/520.0),float3(12.9898,78.233,37.719)))*43758.5453); return lerp(float3(1.0,0.38,0.09),float3(0.23,0.56,1.0),step(0.78,r))*(0.65+0.35*r);')
    strength=lib.create_material_expression(m,unreal.MaterialExpressionCollectionParameter,-430,200);strength.set_editor_property('collection',mpc);strength.set_editor_property('parameter_name','WindowGlow')
    mul=lib.create_material_expression(m,unreal.MaterialExpressionMultiply,-100,0)
    bsdf=lib.create_material_expression(m,unreal.MaterialExpressionSubstrateUnlitBSDF,150,0)
    for a,out,b,pin in [(p,'',color,'P'),(color,'',mul,'A'),(strength,'',mul,'B'),(mul,'',bsdf,'EmissiveColor')]:assert lib.connect_material_expressions(a,out,b,pin)
    assert lib.connect_material_property(bsdf,'',unreal.MaterialProperty.MP_FRONT_MATERIAL)
    lib.recompile_material(m);assert unreal.EditorAssetLibrary.save_loaded_asset(m,False)
    mi=existing('MI_CityWindows_Emissive_v01') or tools.create_asset('MI_CityWindows_Emissive_v01',dest,unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew());lib.set_material_instance_parent(mi,m);unreal.EditorAssetLibrary.save_loaded_asset(mi,False)
    window=by['EST_HorizonWindows'];window.modify();window.static_mesh_component.modify();report['window_previous_material']=window.static_mesh_component.get_material(0).get_path_name();window.static_mesh_component.set_material(0,mi)
    # Fit the actual room slab to the same measured frame as its Houdini tiles.
    floor=by['Film_Floor'];report['room_floor_before']=floor.get_actor_transform().export_text();floor.modify()
    bounds=json.loads((root/'Tools/houdini/Published/Film304Closeout_20261018/MainOfficeFit_v05/main_room_fit.json').read_text())['input']['interior_local_cm']
    xmin,xmax,ymin,ymax=bounds;cx,cy=(xmin+xmax)/2,(ymin+ymax)/2;co,si=math.cos(math.radians(-25)),math.sin(math.radians(-25))
    floor.set_actor_location(unreal.Vector(co*cx-si*cy,si*cx+co*cy,-10),False,False);floor.set_actor_scale3d(unreal.Vector((xmax-xmin)/100,(ymax-ymin)/100,.2));report['room_floor_after']=floor.get_actor_transform().export_text()
    # The original body/window pair stays exactly registered, now sitting on the city ground datum.
    for name in ['EST_HorizonBody','EST_HorizonWindows']:
        a=by[name];a.modify();pos=a.get_actor_location();a.set_actor_location(unreal.Vector(pos.x,pos.y,-5500),False,False)
    city=by.get('Film_Live_CityHero_Composer')
    if city is None:
        api=unreal.HoudiniPublicAPIBlueprintLib.get_api()
        unreal._film_city_live=api.instantiate_asset(unreal.load_asset('/Game/Houdini/HDA_Brutalist_ShotComposer_v2'),unreal.Transform(),enable_auto_cook=False,enable_auto_bake=False)
        cw=unreal._film_city_live;city=cw.get_houdini_asset_actor();city.modify();city.set_actor_label('Film_Live_CityHero_Composer');cw.process_component_synchronous()
        for key,values in [('cam_pos',[-55,24,-40]),('cam_target',[-190,15,180])]:
            for i,v in enumerate(values):cw.set_float_parameter_value(key,v,i)
        for key,v in [('density_fg',.35),('density_mg',.65),('density_skyline',.75),('negative_space_radius',35),('focal_length',50)]:cw.set_float_parameter_value(key,v)
        cw.set_int_parameter_value('scene_mode',0);cw.set_int_parameter_value('seed',304);cw.recook();cw.process_component_synchronous()
    city.modify();city.set_actor_location(unreal.Vector(0,0,-5500),False,False)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    # The source kit composer remains the near/mid hero layer; the new HDA supplies missing full-horizon coverage.
    task=unreal.AssetImportTask();task.filename=str(root/'Tools/houdini/Published/Film304Closeout_20261018/ContinuousHorizon/Film304_ContinuousHorizon_v01.hda');task.destination_path='/Game/Houdini/Film304Closeout_20261018';task.automated=True;task.save=True;tools.import_asset_tasks([task])
    unreal._film_horizon_live=unreal.HoudiniPublicAPIBlueprintLib.get_api().instantiate_asset(task.get_objects()[0],unreal.Transform(),enable_auto_cook=True,enable_auto_bake=False)
    hw=unreal._film_horizon_live;hw.get_houdini_asset_actor().set_actor_label('Film_Live_ContinuousHorizon_v01');hw.process_component_synchronous();report['continuous_horizon_outputs']=hw.get_num_outputs()
    uds=by['Film_UDS_Daylight'];sky_props=['Time of Day','Sky Light Intensity','Sun Light Intensity','Moon Light Intensity','Overall Intensity','Animate Time of Day','Use System Time','Random Starting Time']
    sky_before={k:uds.get_editor_property(k) for k in sky_props};report['sky_baseline']=sky_before
    # A separate night PPV. It never replaces the owner's material graphs or day settings.
    ppv=ed.spawn_actor_from_class(unreal.PostProcessVolume,unreal.Vector(0,0,700));ppv.set_actor_label('Film_City_NightGrade');ppv.unbound=True;ppv.priority=1100;ppv.enabled=False;ppv.blend_weight=1
    s=by['Film_Compare_B_SoftClean'].settings;s.weighted_blendables=unreal.WeightedBlendables(array=[])
    s.override_auto_exposure_method=True;s.auto_exposure_method=unreal.AutoExposureMethod.AEM_MANUAL;s.override_auto_exposure_apply_physical_camera_exposure=True;s.auto_exposure_apply_physical_camera_exposure=False
    s.override_auto_exposure_bias=True;s.auto_exposure_bias=.35;s.override_bloom_intensity=True;s.bloom_intensity=.45;s.override_bloom_threshold=True;s.bloom_threshold=.9
    s.override_vignette_intensity=True;s.vignette_intensity=.15;ppv.settings=s
    # Searchlight columns, held off in the day scene and enabled only by the night sequences.
    vfx=[]
    for i,(pos,target,value,colorv) in enumerate([((-20350,27926,5600),(-25000,12000,30000),95000,(.28,.50,1)),((-35000,5000,3600),(-18000,25000,24000),70000,(1,.42,.14)),((-24000,32000,4200),(-10000,10000,28000),60000,(.30,.8,1))],1):
        a=ed.spawn_actor_from_class(unreal.SpotLight,unreal.Vector(*pos));a.set_actor_label('Film_City_Searchlight_%02d'%i)
        a.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*pos),unreal.Vector(*target)),False)
        c=a.get_component_by_class(unreal.SpotLightComponent);c.set_mobility(unreal.ComponentMobility.MOVABLE)
        for prop,val in {'intensity_units':unreal.LightUnits.CANDELAS,'intensity':value,'attenuation_radius':45000,'inner_cone_angle':2,'outer_cone_angle':5,'volumetric_scattering_intensity':3,'cast_shadows':False}.items():c.set_editor_property(prop,val)
        c.set_light_color(unreal.LinearColor(*colorv,1));c.set_visibility(False);vfx.append(c)
    fog=film304_fog.get_fog_component(by)
    report['fog_before']={'density':fog.fog_density,'falloff':fog.fog_height_falloff}
    source=unreal.load_asset('/Game/Sequences/Film304Closeout_20261018/LS_MainOffice_Ensemble_Warm_48f_v01')
    libseq=unreal.LevelSequenceEditorBlueprintLibrary;binds=unreal.get_editor_subsystem(unreal.LevelSequenceEditorSubsystem)
    def prop(seq,obj,name,value,boolean=False):
        b=seq.add_possessable(obj);track=b.add_track(unreal.MovieSceneBoolTrack if boolean else unreal.MovieSceneFloatTrack);track.set_property_name_and_path(name,name);sec=track.add_section();sec.set_range(0,48);sec.get_all_channels()[0].set_default(value)
    for name,pos,target,focal,time,glow in [('Skyline_BlueHour',(-5500,-4000,2400),(-19000,18000,1500),50,1930,4),('Skyline_Midnight',(-14000,-12000,4200),(-22000,24000,2500),70,2230,7)]:
        cam=ed.spawn_actor_from_class(unreal.CineCameraActor,unreal.Vector(*pos));cam.set_actor_label('Film_Cam_'+name);cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*pos),unreal.Vector(*target)),False)
        cine=cam.get_cine_camera_component();cine.current_focal_length=focal;cine.current_aperture=8;fb=cine.filmback;fb.sensor_width=36;fb.sensor_height=20.25;cine.filmback=fb
        focus=cine.focus_settings;focus.focus_method=unreal.CameraFocusMethod.DISABLE;cine.focus_settings=focus
        seq=tools.duplicate_asset('LS_'+name+'_48f_v01','/Game/Sequences/Film304Closeout_20261018/Skyline',source);seq.modify()
        for t in list(seq.get_tracks()):
            if isinstance(t,unreal.MovieSceneCameraCutTrack):seq.remove_track(t)
        for b in list(seq.get_possessables()):
            cls=b.get_possessed_object_class()
            if cls and ('CineCameraActor' in cls.get_name() or 'Ultra_Dynamic_Sky' in cls.get_name()):b.remove()
        b=seq.add_possessable(cam);libseq.open_level_sequence(seq);binds.remove_all_bindings(b);binds.add_actors_to_binding([cam],b)
        cut=seq.add_track(unreal.MovieSceneCameraCutTrack).add_section();cut.set_range(0,48);cut.set_camera_binding_id(seq.get_binding_id(b))
        for a in ed.get_all_level_actors():
            if isinstance(a,unreal.PostProcessVolume):prop(seq,a,'bEnabled',a==ppv,True)
        for key,val in {'Time of Day':time,'Sky Light Intensity':.35,'Sun Light Intensity':0.,'Moon Light Intensity':.9,'Overall Intensity':.35}.items():prop(seq,uds,key,val)
        for key in ['Animate Time of Day','Use System Time','Random Starting Time']:prop(seq,uds,key,False,True)
        # Remove inherited directional intensity tracks before adding the night key.
        for b0 in seq.get_possessables():
            cls=b0.get_possessed_object_class()
            if cls and cls.get_name()=='DirectionalLightComponent':
                for track in list(b0.get_tracks()):
                    if isinstance(track,unreal.MovieSceneFloatTrack) and str(track.get_property_name())=='Intensity':b0.remove_track(track)
        for a in ed.get_all_level_actors():
            for c in a.get_components_by_class(unreal.DirectionalLightComponent):prop(seq,c,'Intensity',.65 if a.get_actor_label()=='Light_Cinematic_SunBeam' else 0)
        prop(seq,fog,'FogDensity',.006);prop(seq,fog,'FogHeightFalloff',.08)
        for c in vfx:prop(seq,c,'bVisible',True,True)
        t=seq.add_track(unreal.MovieSceneMaterialParameterCollectionTrack);t.set_editor_property('mpc',mpc);sec=t.add_section();sec.set_range(0,48);sec.add_scalar_parameter_key('WindowGlow',unreal.FrameNumber(0),glow)
        libseq.set_current_time(20);report['shots'].append({'shot':name,'sequence':seq.get_path_name(),'camera':cam.get_actor_label(),'sky_time_readback':uds.get_editor_property('Time of Day'),'window_glow':glow})
        unreal.EditorAssetLibrary.save_loaded_asset(seq,False);libseq.close_level_sequence()
    uds.modify()
    for k,v in sky_before.items():uds.set_editor_property(k,v)
    for c in vfx:c.set_visibility(False)
    ppv.enabled=False
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    audit.write_text(json.dumps(report,indent=2));print(json.dumps(report))

if __name__=='__main__':main()
