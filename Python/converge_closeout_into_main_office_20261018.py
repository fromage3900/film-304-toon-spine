"""Promote existing closeout effects into the owner's original Office only."""
import json
from pathlib import Path
import unreal

def main():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_path_name() == '/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office.L_Film_Office'
    assert not unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).is_rendering()
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    by = {a.get_actor_label(): a for a in actors.get_all_level_actors()}
    seq = unreal.load_asset('/Game/Sequences/Film304Idle_20261017/LS_OfficeCast_SleepFaces_48f_v03_SoftSnore')
    lib = unreal.LevelSequenceEditorBlueprintLibrary
    lib.open_level_sequence(seq)
    lib.set_current_time(0)
    david = next(b for b in seq.get_possessables() if b.get_name() == 'Film_Cast_David')
    head = by['Film_Cast_David'].get_component_by_class(unreal.SkeletalMeshComponent).get_socket_transform('Head_M', unreal.RelativeTransformSpace.RTS_WORLD)
    target = seq.get_binding_id(david)
    clouds = []
    for binding in seq.get_spawnables():
        if not binding.get_name().startswith('Film_David_SoftSnore_'):
            continue
        if not any(isinstance(t, unreal.MovieScene3DAttachTrack) for t in binding.get_tracks()):
            track = next(t for t in binding.get_tracks() if isinstance(t, unreal.MovieScene3DTransformTrack))
            keys = [c.get_keys() for c in track.get_sections()[0].get_all_channels()]
            assert all(len(k) == 49 for k in keys)
            for i in range(49):
                local = head.inverse_transform_location(unreal.Vector(*(keys[c][i].get_value() for c in range(3))))
                for c, value in enumerate(local.to_tuple()):
                    keys[c][i].set_value(value)
                for c, scale in zip(range(6, 9), head.scale3d.to_tuple()):
                    keys[c][i].set_value(keys[c][i].get_value() / scale)
            section = binding.add_track(unreal.MovieScene3DAttachTrack).add_section()
            section.set_range(0, 48)
            section.set_constraint_binding_id(target)
            section.attach_component_name = 'SkeletalMeshComponent0'
            section.attach_socket_name = 'Head_M'
            section.attachment_location_rule = unreal.AttachmentRule.KEEP_RELATIVE
            section.attachment_rotation_rule = unreal.AttachmentRule.KEEP_RELATIVE
            section.attachment_scale_rule = unreal.AttachmentRule.KEEP_RELATIVE
            section.detachment_location_rule = unreal.DetachmentRule.KEEP_WORLD
            section.detachment_rotation_rule = unreal.DetachmentRule.KEEP_WORLD
            section.detachment_scale_rule = unreal.DetachmentRule.KEEP_WORLD
        clouds.append(binding.get_name())
    assert len(clouds) == 4
    clock = unreal.load_asset('/Game/VFX/Film304Closeout_20261018/MPC_Film_DustLoop_v01')
    assert clock
    if not any(isinstance(t, unreal.MovieSceneMaterialParameterCollectionTrack) and t.get_editor_property('mpc') == clock for t in seq.get_tracks()):
        track = seq.add_track(unreal.MovieSceneMaterialParameterCollectionTrack)
        track.set_editor_property('mpc', clock)
        section = track.add_section()
        section.set_range(0, 48)
        tick, rate = seq.get_tick_resolution(), seq.get_display_rate()
        factor = tick.numerator * rate.denominator / (tick.denominator * rate.numerator)
        for frame in [0, 2, 8, 36, 42, 48]:
            section.add_scalar_parameter_key('FilmLoopPhase', unreal.FrameNumber(round(frame * factor)), frame / 48, unreal.MovieSceneKeyInterpolation.LINEAR)
    assert unreal.EditorAssetLibrary.save_loaded_asset(seq)
    dust = by.get('Film_WindowDust_Subtle')
    if dust is None:
        dust = actors.spawn_actor_from_class(unreal.NiagaraActor, unreal.Vector(-180, 140, 130))
        dust.set_actor_label('Film_WindowDust_Subtle')
        dust.set_folder_path('Film304/FinalAssembly/WindowRays')
    c = dust.get_component_by_class(unreal.NiagaraComponent)
    c.set_asset(unreal.load_asset('/Game/VFX/Film304Closeout_20261018/NS_Film_WindowDust_v01'))
    params = {'User.Spawn Rate':80, 'User.CPU Spawn Rate':80, 'User.Sprite Alpha':1, 'User.Sprite Scale':.35, 'User.Max Lifetime':6, 'User.Spawn Box Height':180, 'User.Max Spawn Distance':220, 'User.Camera Forward Offset':0, 'User.Spawn Distance Distribution':1, 'User.Custom Time Dilation':1, 'User.Wind Velocity Scale':.02, 'User.Twirl Velocity':.12, 'User.Ambient Intensity':.1, 'User.Fog Particle Percentage':0}
    for name, value in params.items():
        c.set_variable_float(name, value)
    c.set_variable_bool('User.Override Camera Transform', True)
    c.set_variable_bool('User.Particle Collision Enabled', False)
    c.set_variable_position('User.Custom Camera Position', unreal.Vector(-180, 140, 130))
    c.set_variable_vec3('User.Custom Camera Forward', unreal.Vector(.9063, -.4226, 0))
    c.set_variable_material('User.Dust Sprite Material', unreal.load_asset('/Game/VFX/Film304Closeout_20261018/M_Film_WindowDust_SoftLoop_v01'))
    c.reinitialize_system()
    playback = by['Film_OfficeIdle_LoopPlayback']
    previous = playback.get_sequence().get_path_name()
    playback.set_sequence(seq)
    settings = playback.get_editor_property('playback_settings')
    settings.disable_camera_cuts = True
    settings.auto_play = True
    playback.set_editor_property('playback_settings', settings)
    proof = []
    for frame in [0, 20, 47]:
        lib.set_current_time(frame)
        proof.append({'frame':frame, 'bindings':{b.get_name():len(lib.get_bound_objects(seq.get_binding_id(b))) for b in seq.get_bindings()}})
    lib.close_level_sequence()
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    report = {'world':world.get_path_name(), 'previous_playback':previous, 'current_playback':seq.get_path_name(), 'head_anchored_clouds':clouds, 'dust_actor':dust.get_actor_label(), 'binding_samples':proof, 'shared_shader_edits':False, 'new_levels':False, 'visual_motion_gate':'pending main-room render'}
    (Path(unreal.Paths.project_dir())/'Saved/Audit/Closeout_20261018/main_office_effects_convergence.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report))

if __name__ == '__main__':
    main()
