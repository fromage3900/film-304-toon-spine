"""Give film-owned dust a Sequencer clock and an invisible reset, without shared shader edits."""
import json
from pathlib import Path
import unreal

def main():
    root=Path(unreal.Paths.project_dir())
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert 'L_Film_Office_Assembly_20261018_v02.' in world.get_path_name()
    assert not unreal._closeout_mrq_executor.is_rendering()
    dest='/Game/VFX/Film304Closeout_20261018'
    tools=unreal.AssetToolsHelpers.get_asset_tools()
    clock=unreal.load_asset(dest+'/MPC_Film_DustLoop_v01')
    if clock is None:clock=tools.create_asset('MPC_Film_DustLoop_v01',dest,unreal.MaterialParameterCollection,unreal.MaterialParameterCollectionFactoryNew())
    scalar=unreal.CollectionScalarParameter();scalar.set_editor_property('parameter_name','FilmLoopPhase');scalar.set_editor_property('default_value',0)
    clock.set_editor_property('scalar_parameters',[scalar])
    assert unreal.EditorAssetLibrary.save_loaded_asset(clock)
    material=unreal.load_asset(dest+'/M_Film_WindowDust_SoftLoop_v01')
    if material is None:material=tools.create_asset('M_Film_WindowDust_SoftLoop_v01',dest,unreal.Material,unreal.MaterialFactoryNew())
    unreal.MaterialEditingLibrary.delete_all_material_expressions(material)
    material.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT)
    material.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property('two_sided',True)
    material.set_editor_property('used_with_niagara_sprites',True)
    lib=unreal.MaterialEditingLibrary
    uv=lib.create_material_expression(material,unreal.MaterialExpressionTextureCoordinate,-700,0)
    phase=lib.create_material_expression(material,unreal.MaterialExpressionCollectionParameter,-700,220)
    phase.set_editor_property('collection',clock);phase.set_editor_property('parameter_name','FilmLoopPhase')
    opacity=lib.create_material_expression(material,unreal.MaterialExpressionCustom,-380,0)
    inputs=[]
    for name in ['UV','Phase']:
        item=unreal.CustomInput();item.set_editor_property('input_name',name);inputs.append(item)
    opacity.set_editor_property('inputs',inputs)
    opacity.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    opacity.set_editor_property('code','float2 d=(UV-0.5)*2; float radial=pow(saturate(1-dot(d,d)),3); float envelope=smoothstep(0.0416667,0.1666667,Phase)*(1-smoothstep(0.75,0.875,Phase)); return radial*envelope*0.07;')
    assert lib.connect_material_expressions(uv,'',opacity,'UV')
    assert lib.connect_material_expressions(phase,'',opacity,'Phase')
    color=lib.create_material_expression(material,unreal.MaterialExpressionConstant3Vector,-360,-200)
    color.constant=unreal.LinearColor(.65,.50,.30,1)
    rgb=lib.create_material_expression(material,unreal.MaterialExpressionMultiply,-100,-150)
    trans=lib.create_material_expression(material,unreal.MaterialExpressionOneMinus,-100,100)
    bsdf=lib.create_material_expression(material,unreal.MaterialExpressionSubstrateUnlitBSDF,160,0)
    for a,pin,b,input_name in [(color,'',rgb,'A'),(opacity,'',rgb,'B'),(opacity,'',trans,''),
                              (rgb,'',bsdf,'EmissiveColor'),(trans,'',bsdf,'TransmittanceColor')]:
        assert lib.connect_material_expressions(a,pin,b,input_name)
    assert lib.connect_material_property(bsdf,'',unreal.MaterialProperty.MP_FRONT_MATERIAL)
    lib.recompile_material(material);assert unreal.EditorAssetLibrary.save_loaded_asset(material)
    records=[]
    paths=unreal.EditorAssetLibrary.list_assets('/Game/Sequences/Film304Closeout_20261018',recursive=False)
    for path in paths:
        seq=unreal.load_asset(path)
        if not isinstance(seq,unreal.LevelSequence):continue
        for old in list(seq.get_tracks()):
            if isinstance(old,unreal.MovieSceneMaterialParameterCollectionTrack) and old.get_editor_property('mpc') is None:seq.remove_track(old)
        if any(isinstance(t,unreal.MovieSceneMaterialParameterCollectionTrack) and t.get_editor_property('mpc')==clock for t in seq.get_tracks()):continue
        t=seq.add_track(unreal.MovieSceneMaterialParameterCollectionTrack);t.set_editor_property('mpc',clock)
        section=t.add_section();section.set_range(0,48)
        tick=seq.get_tick_resolution();rate=seq.get_display_rate()
        factor=tick.numerator*rate.denominator/(tick.denominator*rate.numerator)
        for frame in [0,2,8,36,42,48]:
            section.add_scalar_parameter_key('FilmLoopPhase',unreal.FrameNumber(round(frame*factor)),frame/48,
                                             unreal.MovieSceneKeyInterpolation.LINEAR)
        assert unreal.EditorAssetLibrary.save_loaded_asset(seq)
        records.append(seq.get_path_name())
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    dust=next(a for a in actors.get_all_level_actors() if a.get_actor_label()=='Film_WindowDust_Subtle')
    c=dust.niagara_component
    c.set_variable_position('User.Custom Camera Position',unreal.Vector(-180,140,130))
    c.set_variable_material('User.Dust Sprite Material',material)
    c.set_variable_float('User.Sprite Scale',.15)
    c.set_variable_float('User.Sprite Alpha',1)
    c.reinitialize_system()
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    report={'material':material.get_path_name(),'clock':clock.get_path_name(),'sequences':records,
            'opacity_max':.07,'first_visible_frame':3,'invisible_reset_frames':[42,47],
            'position_parameter_type_corrected':'Niagara Position instead of Vector3',
            'shared_toon_materials_changed':False,'visual_gate':'pending render'}
    (root/'Saved/Audit/Closeout_20261018/dust_loop_clock.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report))

if __name__=='__main__':main()
