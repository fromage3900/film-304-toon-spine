"""Additive cloud-only closeout. Never edits the shared toon materials or saves a map."""
import json
import math
from pathlib import Path
import unreal


def main():
    dest = '/Game/Sequences/Film304Idle_20261017'
    name = 'LS_OfficeCast_SleepFaces_48f_v03_SoftSnore'
    assert not unreal.EditorAssetLibrary.does_asset_exist(dest + '/' + name), 'Already built; inspect instead of rebuilding'
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    source = unreal.load_asset(dest + '/LS_OfficeCast_SleepFaces_48f_v02')
    assert source
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    seq = tools.duplicate_asset(name, dest, source)
    for binding in list(seq.get_bindings()):
        if 'SnorePuff' in binding.get_name():
            binding.remove()

    # A dedicated FX material, independent of every production toon graph.
    matname = 'M_DavidSnorePuff_v03_SoftFade'
    matdir = '/Game/Materials/Film304Idle_20261017'
    assert not unreal.EditorAssetLibrary.does_asset_exist(matdir + '/' + matname)
    mat = tools.create_asset(matname, matdir, unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property('two_sided', True)
    lib = unreal.MaterialEditingLibrary
    color = lib.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -500, -200)
    color.constant = unreal.LinearColor(.14, .22, .32, 1)
    fresnel = lib.create_material_expression(mat, unreal.MaterialExpressionFresnel, -700, 100)
    fresnel.set_editor_property('exponent', 1.2)
    inv = lib.create_material_expression(mat, unreal.MaterialExpressionOneMinus, -500, 100)
    opacity = lib.create_material_expression(mat, unreal.MaterialExpressionMultiply, -200, 100)
    fade = lib.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -500, 300)
    fade.set_editor_property('parameter_name', 'CloudOpacity')
    fade.set_editor_property('default_value', 0.0)
    trans = lib.create_material_expression(mat, unreal.MaterialExpressionOneMinus, 0, 140)
    rgb = lib.create_material_expression(mat, unreal.MaterialExpressionMultiply, 0, -120)
    bsdf = lib.create_material_expression(mat, unreal.MaterialExpressionSubstrateUnlitBSDF, 240, 0)
    for a, output, b, pin in [(fresnel,'',inv,''),(inv,'',opacity,'A'),(fade,'',opacity,'B'),
            (opacity,'',trans,''),(color,'',rgb,'A'),(opacity,'',rgb,'B'),
            (rgb,'',bsdf,'EmissiveColor'),(trans,'',bsdf,'TransmittanceColor')]:
        assert lib.connect_material_expressions(a, output, b, pin)
    assert lib.connect_material_property(bsdf, '', unreal.MaterialProperty.MP_FRONT_MATERIAL)
    lib.recompile_material(mat)
    assert unreal.EditorAssetLibrary.save_loaded_asset(mat)

    sphere = unreal.load_asset('/Engine/BasicShapes/Sphere')
    tick = seq.get_tick_resolution(); rate = seq.get_display_rate()
    ticks_per_frame = tick.numerator * rate.denominator / (tick.denominator * rate.numerator)
    records = []
    for index, (offset, ratio) in enumerate([((0,0,0),1),((2.9,.3,.6),.72),((-2.6,-.2,.9),.73),((.2,.2,-3),.30)]):
        temp = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(-144,-79,79))
        temp.set_actor_label('Film_David_SoftSnore_' + str(index + 1))
        component = temp.static_mesh_component
        component.set_static_mesh(sphere); component.set_material(0, mat)
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        component.set_cast_shadow(False)
        binding = unreal.get_editor_subsystem(unreal.LevelSequenceEditorSubsystem).add_spawnable_from_instance(seq, temp)
        binding.set_name('Film_David_SoftSnore_' + str(index + 1))
        component_binding = seq.add_possessable(component)
        component_binding.set_parent(binding)
        material_track = component_binding.add_track(unreal.MovieSceneComponentMaterialTrack)
        material_track.set_material_index(0)
        material_section = material_track.add_section(); material_section.set_range(0,48)
        transform_track = binding.add_track(unreal.MovieScene3DTransformTrack)
        section = transform_track.add_section(); section.set_range(0,48)
        channels = section.get_all_channels()
        opacities = []
        for frame in range(49):
            p = frame / 48
            # Fade completely out for the final six frames, before the invisible reset.
            fade_in = min(1.0, p / .18)
            fade_out = max(0.0, min(1.0, (.875 - p) / .30))
            smooth = lambda x: x*x*(3-2*x)
            alpha = .92 * smooth(fade_in) * smooth(fade_out)
            size = (.025 + .036 * smooth(p)) * ratio
            values = [-144+offset[0]+5*p, -79+offset[1]+2*math.sin(math.pi*p),
                      79+offset[2]+12*p, 0,0,0, size,size,size]
            for channel, value in zip(channels, values):
                channel.add_key(unreal.FrameNumber(frame), value, interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
            material_section.add_scalar_parameter_key(unreal.MaterialParameterInfo(name='CloudOpacity'),
                    unreal.FrameNumber(round(frame*ticks_per_frame)), alpha, '', '',
                    unreal.MovieSceneKeyInterpolation.LINEAR)
            opacities.append(alpha)
        actors.destroy_actor(temp)
        records.append({'binding':binding.get_name(), 'opacity_first':opacities[0], 'opacity_last':opacities[-1],
                        'invisible_reset_frames':6, 'spawnable':True})
    for binding in list(seq.get_possessables()):
        if not binding.get_tracks() and (binding.get_name() == '' or binding.get_name().startswith('Film_David_SoftSnore_')):
            binding.remove()
    fill = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(-170,-120,100))
    fill.set_actor_label('Film_David_DeskSleep_Fill35')
    light = fill.point_light_component
    light.set_editor_property('intensity_units', unreal.LightUnits.LUMENS)
    light.set_intensity(35); light.set_attenuation_radius(90)
    light.set_cast_shadows(False); light.set_editor_property('source_radius',20)
    light_binding = unreal.get_editor_subsystem(unreal.LevelSequenceEditorSubsystem).add_spawnable_from_instance(seq,fill)
    light_binding.set_name('Film_David_DeskSleep_Fill35')
    actors.destroy_actor(fill)
    assert unreal.EditorAssetLibrary.save_loaded_asset(seq)
    unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(seq)
    unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(20)
    out = Path(unreal.Paths.project_dir())/'Saved/Audit/Closeout_20261018'
    out.mkdir(parents=True, exist_ok=True)
    report = {'sequence':seq.get_path_name(),'material':mat.get_path_name(),'clouds':records,
              'duration_frames':48,'fps':24,'map_saved':False,'head_attachment':False,
              'note':'World-space cloud preserved from v02; soft fade and spawnable persistence added. Visual review pending.'}
    (out/'soft_snore_build.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report))


if __name__ == '__main__':
    main()
