"""Only non-skin Dana slots and a reversible left-palm correction for David."""
import json
from pathlib import Path
import unreal

def main():
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_path_name()=='/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office.L_Film_Office'
    assert not unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).is_rendering()
    subsystem=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    by={a.get_actor_label():a for a in subsystem.get_all_level_actors()}
    lib=unreal.MaterialEditingLibrary;tools=unreal.AssetToolsHelpers.get_asset_tools()
    dana=by['Film_Subject_Dana_v08_CleanSkin'].get_component_by_class(unreal.SkeletalMeshComponent)
    skin=dana.get_material(0)
    before=[m.get_path_name() if m else None for m in dana.get_materials()]
    parts={1:('Hair',(.055,.030,.025),.62),2:('Iris',(.15,.065,.04),.3),3:('EyeWhite',(.64,.58,.51),.5),5:('EyeInterior',(.035,.025,.030),.55),6:('Skirt',(.22,.10,.32),.84),7:('Shirt',(.035,.24,.27),.84),8:('Shoes',(.075,.055,.09),.66),9:('Gum',(.25,.06,.08),.5),10:('Teeth',(.8,.75,.65),.5),11:('Tongue',(.25,.06,.08),.5)}
    for slot,(part,color,roughness) in parts.items():
        name='MI_Dana_'+part+'_StageRestored_v01';dest='/Game/Materials/Recovery_Office_20261018/DanaParts'
        material=unreal.load_asset(dest+'/'+name) or tools.duplicate_asset(name,dest,dana.get_material(slot))
        for p,v in {'TextureWeight':0,'Roughness':roughness,'PaletteRampStrength':0,'RoughnessScale':1,'RoughnessBias':0}.items():lib.set_material_instance_scalar_parameter_value(material,p,float(v))
        lib.set_material_instance_vector_parameter_value(material,'BaseTint',unreal.LinearColor(*color,1))
        lib.set_material_instance_static_switch_parameter_value(material,'bFilmUseUDIM',False)
        lib.set_material_instance_static_switch_parameter_value(material,'bUseHeightToNormal',False)
        assert unreal.EditorAssetLibrary.save_loaded_asset(material)
        dana.set_material(slot,material)
    assert dana.get_material(0)==skin, 'Owner explicitly froze skin'
    source=unreal.load_asset('/Game/Animations/Film304Idle_20261017/AS_David_DeskSleep_48f_v02')
    dest='/Game/Animations/Film304Idle_20261017';name='AS_David_DeskSleep_PalmUp_48f_v03'
    clip=unreal.load_asset(dest+'/'+name)
    if clip is None:
        clip=tools.duplicate_asset(name,dest,source)
        poses=[unreal.AnimationLibrary.get_bone_pose_for_frame(source,'Wrist_L',i,False) for i in range(49)]
        # X is the measured wrist-to-finger axis; rotate locally about the forearm.
        delta=unreal.Quat(1,0,0,0)
        ctrl=clip.controller;ctrl.open_bracket('Turn left palm up under sleeping head',False)
        assert ctrl.set_bone_track_keys('Wrist_L',[p.translation for p in poses],[p.rotation*delta for p in poses],[p.scale3d for p in poses],False)
        ctrl.close_bracket(False)
        assert unreal.EditorAssetLibrary.save_loaded_asset(clip)
    seqpaths=['/Game/Sequences/Film304Idle_20261017/LS_OfficeCast_SleepFaces_48f_v03_SoftSnore']
    seqpaths += [str(p).split('.')[0] for p in unreal.EditorAssetLibrary.list_assets('/Game/Sequences/Film304Closeout_20261018',False) if '/LS_MainOffice_' in str(p)]
    changed=[]
    for path in seqpaths:
        seq=unreal.load_asset(path)
        for binding in seq.get_possessables():
            if binding.get_name()!='Film_Cast_David':continue
            for track in binding.get_tracks():
                for section in track.get_sections():
                    if isinstance(section,unreal.MovieSceneSkeletalAnimationSection):
                        params=section.params
                        if params.animation in [source,clip]:
                            params.animation=clip;section.params=params;changed.append(seq.get_path_name())
        assert unreal.EditorAssetLibrary.save_loaded_asset(seq)
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    report={'world':world.get_path_name(),'dana_skin_unchanged':skin.get_path_name(),'dana_before':before,'dana_after':[m.get_path_name() for m in dana.get_materials()],'david_source_preserved':source.get_path_name(),'david_palm_clip':clip.get_path_name(),'hand':'Wrist_L','local_forearm_roll_degrees':180,'frame_intervals':48,'sequences':changed,'visual_gate':'pending three-angle render'}
    (Path(unreal.Paths.project_dir())/'Saved/Audit/Closeout_20261018/parts_and_palm_touchup.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report))

if __name__=='__main__':main()
