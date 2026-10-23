"""RETIRED: the owner requires donor animations retargeted onto film cast."""
raise RuntimeError('Retired rejected stand-in builder. Sparrow is an animation donor only. Use reconcile_universal_film_cast.py and a validated film-cast rig/retarget.')
import json
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'Saved/Audit/UniversalFilm_20261016'
E = unreal.EditorAssetLibrary
M = unreal.MaterialEditingLibrary
A = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
L = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
motion = json.loads((AUDIT / 'motion_source.json').read_text())
if motion.get('result') not in ['migrated', 'migrated_with_unsupported_legacy_editor_rig_omitted']:
    raise RuntimeError('Working mesh/action migration required')
mesh = E.load_asset(motion['mesh'])
clip = E.load_asset(motion['clip'])
if mesh.get_editor_property('skeleton') != clip.get_editor_property('skeleton'):
    raise RuntimeError('Motion skeleton mismatch')
uds_class = unreal.load_class(None, '/Game/UltraDynamicSky/Blueprints/Ultra_Dynamic_Sky.Ultra_Dynamic_Sky_C')
if not uds_class:
    raise RuntimeError('Existing Humber UDS class unavailable')
master = E.load_asset('/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal')
texture_names = []
for node in M.get_material_expressions(master):
    if 'TextureSampleParameter' in node.get_class().get_name():
        texture_names.append(str(node.get_editor_property('parameter_name')))
base_texture_names = [n for n in texture_names
                      if any(s in n.lower() for s in ['albedo', 'basecolor', 'diffuse'])
                      and 'layer' not in n.lower()]
materials = []
for index, slot in enumerate(mesh.materials):
    name = str(slot.material_slot_name)
    path = '/Game/Materials/Instances/UniversalFilm_20261016/MI_Film_SparrowMotion_%02d' % index
    if E.does_asset_exist(path):
        instance = E.load_asset(path)
    else:
        instance = E.duplicate_asset('/Game/Materials/Instances/UniversalFilm_20261016/MI_Film_Shirt', path)
    original = slot.material_interface
    texture = None
    if isinstance(original, unreal.MaterialInstanceConstant):
        try:
            params = list(M.get_texture_parameter_names(original))
            for param in sorted(params, key=lambda p: 0 if any(s in str(p).lower() for s in ['diffuse', 'albedo', 'basecolor']) else 1):
                if any(s in str(param).lower() for s in ['diffuse', 'albedo', 'basecolor', 'color']):
                    candidate = M.get_material_instance_texture_parameter_value(original, param)
                    if candidate:
                        texture = candidate
                        break
        except Exception:
            pass
    color = (.035, .065, .075, 1) if 'hair' in name.lower() else (.36, .25, .14, 1)
    if texture and base_texture_names:
        M.set_material_instance_texture_parameter_value(instance, base_texture_names[0], texture)
        M.set_material_instance_scalar_parameter_value(instance, 'TextureWeight', 1.)
        color = (1., 1., 1., 1.)
    M.set_material_instance_vector_parameter_value(instance, 'BaseTint', unreal.LinearColor(*color))
    M.set_material_instance_scalar_parameter_value(instance, 'Roughness', .82)
    M.set_material_instance_scalar_parameter_value(instance, 'Metallic', 0.)
    M.update_material_instance(instance)
    if not E.save_loaded_asset(instance, False):
        raise RuntimeError('Motion material save failed')
    materials.append(instance)

report = json.loads((AUDIT / 'scenes.json').read_text())
rows = []
for scene in report['scenes']:
    if not L.load_level(scene['map']):
        raise RuntimeError('Cannot load owned scene ' + scene['map'])
    actors = {a.get_actor_label(): a for a in A.get_all_level_actors()}
    subject = next(a for label, a in actors.items() if label.startswith('Film_Subject_'))
    subject.set_actor_label('Film_Subject_Sparrow_MOTION_STANDIN_NOT_DANA')
    comp = subject.get_component_by_class(unreal.SkeletalMeshComponent)
    subject.set_actor_scale3d(unreal.Vector(1, 1, 1))
    subject.set_actor_location(unreal.Vector(), False, False)
    comp.set_skeletal_mesh_asset(mesh)
    for index, material in enumerate(materials):
        comp.set_material(index, material)
    origin, extent = subject.get_actor_bounds(False)
    factor = 170. / (extent.z * 2.)
    subject.set_actor_scale3d(unreal.Vector(factor, factor, factor))
    origin, extent = subject.get_actor_bounds(False)
    subject.set_actor_location(unreal.Vector(-origin.x, -origin.y, -(origin.z - extent.z)), False, False)
    comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    comp.set_animation(clip)
    comp.set_position(.75, False)
    comp.play(True)
    front = subject.get_actor_right_vector()
    right = subject.get_actor_forward_vector() * -1
    # UDS supplies a fixed daylight environment; no procedural time changes.
    sky = actors.get('Film_UDS_Daylight')
    if not sky:
        sky = A.spawn_actor_from_class(uds_class, unreal.Vector())
        sky.set_actor_label('Film_UDS_Daylight')
    sky.set_actor_rotation(unreal.Rotator(yaw=150), False)
    sky_values = {'Time of Day': 1100., 'Animate Time of Day': False,
                  'Random Starting Time': False, 'Use System Time': False,
                  'Apply Exposure Settings': False, 'Sun Light Intensity': 8.,
                  'Sky Light Intensity': 1.5, 'Cloud Coverage': 1., 'Fog': .05,
                  'Aurora Intensity': 0.}
    for key, value in sky_values.items():
        sky.set_editor_property(key, value)
    sky.call_method('UserConstructionScript')
    for label, intensity in [('Key', 6.), ('Fill', 2.), ('Rim', 2.)]:
        light_actor = actors['Film_' + label]
        component = light_actor.get_component_by_class(unreal.DirectionalLightComponent)
        component.set_intensity(intensity)
        component.set_editor_property('cast_shadows', label == 'Key')
        component.set_editor_property('cast_static_shadows', False)
    # Frame the actual replacement body, not the bounds of Dana's proxy shapes.
    for job in scene['jobs']:
        sequence = E.load_asset(job['sequence'])
        sequence.set_playback_start(0)
        sequence.set_playback_end(48)
        for track in sequence.get_tracks():
            if isinstance(track, unreal.MovieSceneCameraCutTrack):
                for section in track.get_sections():
                    section.set_range(0, 48)
        binding = next((b for b in sequence.get_bindings() if str(b.get_name()) == 'Sparrow motion stand-in'), None)
        if binding is None:
            binding = sequence.add_possessable(subject)
            binding.set_name('Sparrow motion stand-in')
            track = binding.add_track(unreal.MovieSceneSkeletalAnimationTrack)
            section = track.add_section()
            section.set_range(0, 48)
            params = section.get_editor_property('params')
            params.set_editor_property('animation', clip)
            # UE 5.8 stores PlayRate as MovieSceneTimeWarpVariant; retain its
            # constructor's normal-speed value instead of assigning a float.
            section.set_editor_property('params', params)
        if not E.save_loaded_asset(sequence, False):
            raise RuntimeError('Action sequence save failed')
        suffix = job['stem'].split('_', 2)[-1].replace('_v01', '')
        camera = next(a for label, a in actors.items()
                      if label.startswith('Film_Cam_') and label[9:].upper() in suffix)
        portrait = 'PORTRAIT' in job['stem']
        wide = 'WIDE' in job['stem']
        height = 145. if portrait else (95. if wide else 90.)
        distance = 300. if portrait else (900. if scene['scene'] == 'Arrival' else (720. if wide else 490.))
        target = unreal.Vector(0, 0, height)
        location = target + front * distance + right * (20. if portrait else 70.) + unreal.Vector(0, 0, 8.)
        camera.set_actor_location(location, False, False)
        camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
        cc = camera.get_cine_camera_component()
        pp = cc.get_editor_property('post_process_settings')
        pp.set_editor_property('auto_exposure_bias', 0.)
        cc.set_editor_property('post_process_settings', pp)
        config = E.load_asset(job['config'])
        output = config.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting, True)
        job['stem'] = job['stem'].replace('_v01', '_UDS_ACTION_v02')
        output.set_editor_property('file_name_format', job['stem'])
        output.set_editor_property('use_custom_playback_range', True)
        output.set_editor_property('custom_start_frame', 18)
        output.set_editor_property('custom_end_frame', 19)
        aa = config.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting, True)
        aa.set_editor_property('engine_warm_up_count', 48)
        aa.set_editor_property('render_warm_up_count', 16)
        if not E.save_loaded_asset(config, False):
            raise RuntimeError('Action render config save failed')
        if scene['scene'] == 'Office' and 'OFFICEWIDE' in job['stem']:
            motion_config_path = '/Game/MoviePipelines/UniversalFilm_20261016/CFG_FILM_OFFICE_MOTION_UDS_v02'
            motion_config = E.load_asset(motion_config_path) if E.does_asset_exist(motion_config_path) else E.duplicate_asset(job['config'], motion_config_path)
            motion_output = motion_config.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting, True)
            motion_output.set_editor_property('output_resolution', unreal.IntPoint(960, 540))
            motion_output.set_editor_property('output_directory', unreal.DirectoryPath(str(ROOT / 'Showcase/UniversalFilm_20261016/Motion')))
            motion_output.set_editor_property('file_name_format', 'Sparrow_UDS_Jog.{frame_number}')
            motion_output.set_editor_property('custom_start_frame', 0)
            motion_output.set_editor_property('custom_end_frame', 48)
            if not E.save_loaded_asset(motion_config, False):
                raise RuntimeError('Motion preview config save failed')
            report['motion_job'] = {'map': scene['map'], 'sequence': job['sequence'],
                                    'config': motion_config_path, 'stem': 'Sparrow_UDS_Jog'}
    if not unreal.EditorLoadingAndSavingUtils.save_current_level():
        raise RuntimeError('UDS action map save failed')
    scene['subject'] = 'Sparrow motion stand-in; Dana rig approval remains pending'
    scene['pose'] = 'real Jog_Fwd animation; 48-frame sequence; preview at frame 18'
    rows.append({'scene': scene['scene'], 'uds': sky_values, 'action': motion['clip'], 'display_scale': factor})
report['result'] = 'uds_action_scenes_saved_pending_render_review'
(AUDIT / 'scenes.json').write_text(json.dumps(report, indent=2))
(AUDIT / 'uds_action.json').write_text(json.dumps({'scenes': rows, 'texture_parameters': texture_names}, indent=2))
print('FILM_UDS_ACTION_SAVED')
