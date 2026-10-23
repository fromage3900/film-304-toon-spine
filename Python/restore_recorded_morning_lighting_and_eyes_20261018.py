"""Converge recorded morning lighting and repair only non-skin eye references."""
import json
from pathlib import Path
import unreal

def main():
    root=Path(unreal.Paths.project_dir());audit=root/'Saved/Audit/Closeout_20261018'
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_path_name()=='/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office.L_Film_Office'
    assert not unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).is_rendering()
    unreal.LevelSequenceEditorBlueprintLibrary.close_level_sequence()
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    by={a.get_actor_label():a for a in actors}
    dana=by['Film_Subject_Dana_v08_CleanSkin'];comp=dana.get_component_by_class(unreal.SkeletalMeshComponent)
    skin=comp.get_material(0);skin_before=skin.get_path_name()
    recipe=json.loads((audit/'cinematic_dusk_composition.json').read_text())
    light_before=[];applied=[]
    for row in recipe['lights']:
        actor=by.get(row['actor'])
        if not actor:continue
        c=actor.get_component_by_class(unreal.LightComponent)
        light_before.append({'actor':row['actor'],'intensity':c.intensity,'kelvin':c.temperature})
        actor.modify();c.modify();c.set_intensity(row['intensity'])
        c.set_editor_property('temperature',row['kelvin']);c.set_editor_property('use_temperature',True)
        c.set_editor_property('volumetric_scattering_intensity',row.get('volumetric_scattering',1.0))
        applied.append(row)
    sun=by['Light_Cinematic_SunBeam'].get_component_by_class(unreal.DirectionalLightComponent)
    sun.set_editor_property('forward_shading_priority',3)
    sky=by['Film_UDS_Daylight'];sky.modify()
    sky_before={p:str(sky.get_editor_property(p)) for p in ['Time of Day','Sky Light Intensity','Animate Time of Day','Use System Time','Random Starting Time']}
    ambient=json.loads((audit/'main_office_uds_ambient_before.json').read_text())
    sky.set_editor_property('Use System Time',False)
    sky.set_editor_property('Random Starting Time',False)
    sky.set_editor_property('Animate Time of Day',False)
    sky.set_editor_property('Time of Day',ambient['time'])
    sky.set_editor_property('Sky Light Intensity',ambient['intensity'])
    unreal.SystemLibrary.execute_console_command(world,'ShowFlag.SkyAtmosphere 1')
    for c in sky.get_components_by_class(unreal.SkyLightComponent):
        c.modify();c.set_visibility(True)
        if hasattr(c,'recapture_sky'):c.recapture_sky()
    # Reconnect existing artist-facing eye instances to the restored original
    # Face master. Only the isolated StageRestored instances are edited.
    lib=unreal.MaterialEditingLibrary
    face=unreal.load_asset('/Game/Materials/Masters/DanaFilm/M_DanaFilm_Face');assert face
    cornea=unreal.load_asset('/Game/Materials/Masters/DanaFilm/M_DanaFilm_CorneaClear');assert cornea
    assert cornea.get_editor_property('blend_mode')==unreal.BlendMode.BLEND_TRANSLUCENT_COLORED_TRANSMITTANCE
    eye_before={i:comp.get_material(i).get_path_name() if comp.get_material(i) else None for i in [2,3,4,5]}
    eye_specs={2:('Iris',(.24,.095,.04),(.55,.25,.08),.3,.10),3:('EyeWhite',(.82,.79,.73),(.96,.93,.86),.48,.08),5:('EyeInterior',(.008,.005,.008),(.008,.005,.008),.48,0)}
    dana.modify();comp.modify()
    for slot,(part,base,accent,roughness,ramp) in eye_specs.items():
        mi=unreal.load_asset('/Game/Materials/Recovery_Office_20261018/DanaParts/MI_Dana_'+part+'_StageRestored_v01');assert mi
        mi.modify();lib.set_material_instance_parent(mi,face)
        lib.set_material_instance_vector_parameter_value(mi,'BaseTint',unreal.LinearColor(*base,1))
        lib.set_material_instance_vector_parameter_value(mi,'AccentTint',unreal.LinearColor(*accent,1))
        for name,value in {'DryRoughness':roughness,'RampStrength':ramp,'InkIntensity':.004,'RimStrength':0,'FaceShadowMask':0}.items():lib.set_material_instance_scalar_parameter_value(mi,name,float(value))
        assert unreal.EditorAssetLibrary.save_loaded_asset(mi);comp.set_material(slot,mi)
    comp.set_material(4,cornea)
    # Restore the established PPV exposure authority on only our edited cameras.
    cameras=[]
    for label in ['Film_Cam_Showcase_Ensemble_v02','Film_Cam_Showcase_DanaPortrait_v02','Film_Cam_David_DeskSleep','Film_Cam_DavidSleep_Front','Film_Cam_DavidSleep_Right']:
        actor=by[label];c=actor.get_cine_camera_component();actor.modify();c.modify();pp=c.post_process_settings
        cameras.append({'camera':label,'prior_method':str(pp.auto_exposure_method),'prior_override':pp.override_auto_exposure_method})
        pp.override_auto_exposure_method=False;pp.override_auto_exposure_bias=False;pp.override_auto_exposure_apply_physical_camera_exposure=False
        c.post_process_settings=pp
    # The saved shot sequences must use the transferred recipes too; otherwise
    # opening/rendering them would immediately reapply the rejected light values.
    morning=json.loads((audit/'lighting_shot_sequences.json').read_text())
    morning_by_letter={str(r['variant'])[0]:r['lights'] for r in morning}
    mapped={'Neutral':morning_by_letter.get('B',recipe['lights']),'Warm':recipe['lights'],'Cool':morning_by_letter.get('D',recipe['lights'])}
    seqchanges=[]
    for path in unreal.EditorAssetLibrary.list_assets('/Game/Sequences/Film304Closeout_20261018',False):
        if '/LS_MainOffice_' not in str(path):continue
        seq=unreal.load_asset(path);mode=next((m for m in mapped if '_'+m+'_' in seq.get_name()),None)
        if not mode:continue
        rows={r['actor']:r for r in mapped[mode]}
        for b in seq.get_possessables():
            parent=b.get_parent();label=parent.get_name() if parent and parent.is_valid() else b.get_name()
            row=rows.get(label)
            if not row:continue
            for track in b.get_tracks():
                if not isinstance(track,unreal.MovieSceneFloatTrack):continue
                prop=str(track.get_property_name())
                value=row['intensity'] if prop=='Intensity' else row['kelvin'] if prop=='Temperature' else row.get('volumetric_scattering') if prop=='VolumetricScatteringIntensity' else None
                if value is not None:
                    for section in track.get_sections():section.get_all_channels()[0].set_default(float(value))
        assert unreal.EditorAssetLibrary.save_loaded_asset(seq);seqchanges.append(seq.get_path_name())
    assert comp.get_material(0)==skin,'Skin is frozen'
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    report={'world':world.get_path_name(),'recipe_source':str(audit/'cinematic_dusk_composition.json'),'lights_before':light_before,'lights_applied':applied,'sky_before':sky_before,'sky_after':{p:str(sky.get_editor_property(p)) for p in sky_before},'forward_priority':sun.get_editor_property('forward_shading_priority'),'eyes_before':eye_before,'eyes_after':{i:comp.get_material(i).get_path_name() for i in [2,3,4,5]},'skin_preserved':skin_before,'camera_exposure_restored_to_owner_ppv':cameras,'shot_recipes_updated':seqchanges,'visual_gate':'pending actual scene inspection; no export started'}
    (audit/'recorded_morning_lighting_and_eyes_restored.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'lights_applied':len(applied),'sky':report['sky_after'],'priority':report['forward_priority'],'eyes':report['eyes_after'],'skin_preserved':skin_before,'sequences':len(seqchanges)}))

if __name__=='__main__':main()
