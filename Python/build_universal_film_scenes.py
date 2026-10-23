"""Build additive, replaceable-cast compositions using the migrated working shader.

Does not modify source meshes, rigs, existing maps or master graphs.
Run in Humber after finalize_universal_film.py has passed.
"""
import json
import math
import os
import sys
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Python'))
import build_render_queue as render

E = unreal.EditorAssetLibrary
M = unreal.MaterialEditingLibrary
A = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
L = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
MASTER = '/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal'
BASE = '/Game/Materials/Instances/UniversalFilm_20261016'
MAPS = '/Game/Maps/Lookdev/UniversalFilm_20261016'
REPORT = ROOT / 'Saved/Audit/UniversalFilm_20261016'
SOURCE_MI = '/Game/Staging/DanaProfessor_20261016/WarmCourtyard'
REPORT.mkdir(parents=True, exist_ok=True)


def save(asset):
    if not E.save_loaded_asset(asset, False):
        raise RuntimeError('Cannot save ' + asset.get_path_name())


def instance(name, color=None, source=None):
    path = BASE + '/MI_Film_' + name
    if E.does_asset_exist(path):
        return E.load_asset(path)
    if source:
        obj = E.duplicate_asset(source, path)
    else:
        obj = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            'MI_Film_' + name, BASE, unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew())
        M.set_material_instance_parent(obj, unreal.load_asset(MASTER))
        for key, value in {'TextureWeight': 0., 'Metallic': 0., 'Roughness': .85,
                           'ToonRampStrength': 1., 'TemporalStrength': 0.,
                           'BoilIntensity': 0., 'SmearStrength': 0.}.items():
            M.set_material_instance_scalar_parameter_value(obj, key, value)
    if not obj:
        raise RuntimeError('Instance creation failed ' + path)
    if color:
        for key in ['BaseTint', 'PaletteRampMid', 'PaletteRampHigh']:
            M.set_material_instance_vector_parameter_value(obj, key, unreal.LinearColor(*color))
    M.update_material_instance(obj)
    save(obj)
    return obj


def setup_materials():
    result = {}
    for part in ['Skin', 'Hair', 'Shirt', 'Skirt', 'EyeWhite', 'Iris', 'Stone', 'Bronze', 'Leaves']:
        result[part] = instance(part, source=SOURCE_MI + '/MI_Dana_' + part)
    for name, color in {'Shoes': (.022, .016, .028, 1),
                        'Button': (.28, .14, .045, 1),
                        'EyeInterior': (.004, .003, .004, 1),
                        'Floor': (.075, .09, .11, 1),
                        'Wall': (.11, .14, .16, 1),
                        'WarmWall': (.28, .19, .12, 1),
                        'Desk': (.16, .115, .075, 1),
                        'Frame': (.018, .025, .032, 1)}.items():
        result[name] = instance(name, color)
    path = '/Game/Materials/Masters/UniversalFilm_20261016/M_ImportHelpersHidden'
    if not E.does_asset_exist(path):
        hidden = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            'M_ImportHelpersHidden', path.rsplit('/', 1)[0], unreal.Material, unreal.MaterialFactoryNew())
        hidden.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
        hidden.set_editor_property('used_with_skeletal_mesh', True)
        node = M.create_material_expression(hidden, unreal.MaterialExpressionConstant, -200, 0)
        node.set_editor_property('r', 0.)
        M.connect_material_property(node, '', unreal.MaterialProperty.MP_OPACITY_MASK)
        M.recompile_material(hidden)
        save(hidden)
    result['Hidden'] = E.load_asset(path)
    return result


def build(scene, profile, mats):
    map_path = MAPS + '/L_Film_' + scene
    if E.does_asset_exist(map_path):
        raise RuntimeError('Preserve existing composition: ' + map_path)
    if not L.new_level(map_path):
        raise RuntimeError('Cannot create ' + map_path)
    mesh = E.load_asset(profile['mesh'])
    if not mesh:
        raise RuntimeError('Cast mesh missing ' + profile['mesh'])
    subject = A.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(),
                                       unreal.Rotator(yaw=profile['yaw']))
    subject.set_actor_label('Film_Subject_' + profile['name'] + '_ReferencePose')
    component = subject.get_component_by_class(unreal.SkeletalMeshComponent)
    component.set_skeletal_mesh_asset(mesh)
    origin, extent = subject.get_actor_bounds(False)
    if extent.z <= 0:
        raise RuntimeError('Cast bounds have zero height')
    scale = profile.get('display_height_cm', 170.) / (2 * extent.z)
    subject.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    origin, extent = subject.get_actor_bounds(False)
    subject.set_actor_location(unreal.Vector(-origin.x, -origin.y, -(origin.z - extent.z)), False, False)
    origin, extent = subject.get_actor_bounds(False)
    front = subject.get_actor_right_vector()
    right = subject.get_actor_forward_vector() * -1.
    yaw = math.degrees(math.atan2(front.y, front.x))
    slots = []
    for index, slot in enumerate(mesh.materials):
        name = str(slot.material_slot_name).lower()
        part = profile['slots'].get(name)
        if part is None:
            raise RuntimeError('Unmapped cast slot: ' + name)
        component.set_material(index, mats[part])
        slots.append({'slot': name, 'material': component.get_material(index).get_path_name()})

    def position(f, s, z):
        return front * f + right * s + unreal.Vector(0, 0, z)

    def box(label, f, s, z, depth, width, height, material):
        actor = A.spawn_actor_from_class(unreal.StaticMeshActor, position(f, s, z), unreal.Rotator(yaw=yaw))
        actor.set_actor_label('Film_' + label)
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        comp.set_mobility(unreal.ComponentMobility.MOVABLE)
        comp.set_static_mesh(E.load_asset('/Engine/BasicShapes/Cube'))
        comp.set_material(0, mats[material])
        actor.set_actor_scale3d(unreal.Vector(depth / 100., width / 100., height / 100.))
        return actor

    def fit_mesh(label, asset_path, f, s, height, material):
        if not E.does_asset_exist(asset_path):
            return None
        asset = E.load_asset(asset_path)
        if not isinstance(asset, unreal.StaticMesh):
            return None
        actor = A.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(), unreal.Rotator(yaw=yaw))
        actor.set_actor_label('Film_' + label)
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        comp.set_mobility(unreal.ComponentMobility.MOVABLE)
        comp.set_static_mesh(asset)
        for slot in range(comp.get_num_materials()):
            comp.set_material(slot, mats[material])
        center, bounds = actor.get_actor_bounds(False)
        if bounds.z <= 0:
            raise RuntimeError('Invalid prop bounds ' + asset_path)
        factor = height / (2 * bounds.z)
        actor.set_actor_scale3d(unreal.Vector(factor, factor, factor))
        center, bounds = actor.get_actor_bounds(False)
        wanted = position(f, s, 0)
        actor.set_actor_location(unreal.Vector(wanted.x - center.x, wanted.y - center.y,
                                               -(center.z - bounds.z)), False, False)
        return actor

    box('Floor', 0, 0, -10, 2200, 2200, 20, 'Floor')
    if scene == 'Studio':
        box('Backdrop', -280, 0, 210, 20, 1100, 440, 'Wall')
        # Six empty, named cast anchors; no unverified rig is auto-imported.
        for index in range(6):
            marker = A.spawn_actor_from_class(unreal.TargetPoint, position(0, (index - 2.5) * 220, 0))
            marker.set_actor_label('Film_CastSlot_%02d_ReplaceWithValidatedRig' % (index + 1))
    elif scene == 'Office':
        box('BackWall', -310, 0, 160, 18, 1000, 340, 'Wall')
        box('WarmWallPanel', -295, -245, 145, 12, 200, 260, 'WarmWall')
        for side in [-90, 140, 370]:
            box('WindowMullion_%d' % side, -290, side, 180, 22, 10, 300, 'Frame')
        desk = fit_mesh('ExistingOfficeDesk', '/Game/Meshes/Office/Props/Desk', -70, -160, 78, 'Desk')
        if desk is None:
            box('Desk', -70, -140, 77, 95, 155, 7, 'Desk')
            for f in [-105, -35]:
                for s in [-195, -85]:
                    box('DeskLeg_%d_%d' % (f, s), f, s, 37, 6, 6, 74, 'Frame')
        box('Monitor', -92, -140, 113, 8, 65, 42, 'Frame')
        box('DeskReturn', -180, 150, 75, 95, 165, 8, 'Desk')
    elif scene == 'Arrival':
        for f, side, height, width, asset in [
            (-420, -420, 720, 280, '/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_SlenderTower'),
            (-560, 320, 960, 320, '/Game/Environment/Brutalist/03_OFFICE_BLOCK/SM_OFFICE_CivicSlab'),
            (-860, -50, 1200, 400, '/Game/Environment/Brutalist/02_CITY_KOMIKAZE/SM_KMZ_TowerCluster')]:
            if fit_mesh('Building_%d' % side, asset, f, side, height, 'Stone') is None:
                box('Building_%d' % side, f, side, height / 2., 320, width, height, 'Stone')
        for side in [-150, 150]:
            box('PortalPier_%d' % side, -200, side, 210, 100, 55, 420, 'Wall')
        box('PortalLintel', -200, 0, 420, 100, 355, 50, 'Wall')
        box('ArrivalStep', -130, 0, 10, 130, 360, 20, 'Stone')

    target = unreal.Vector(0, 0, 105)
    for label, f, side, z, intensity, color in [
        ('Key', 360, 220, 340, 4., (255, 229, 205, 255)),
        ('Fill', 220, -260, 230, 1.1, (220, 232, 255, 255)),
        ('Rim', -200, -100, 310, 2., (255, 205, 153, 255))]:
        loc = position(f, side, z)
        actor = A.spawn_actor_from_class(unreal.DirectionalLight, loc)
        actor.set_actor_label('Film_' + label)
        actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(loc, target), False)
        light = actor.get_component_by_class(unreal.DirectionalLightComponent)
        light.set_mobility(unreal.ComponentMobility.MOVABLE)
        light.set_intensity(intensity)
        light.set_editor_property('light_color', unreal.Color(*color))
        light.set_editor_property('cast_shadows', label == 'Key')
    render.SEQ_DIR = '/Game/Sequences/UniversalFilm_20261016'
    render.QUEUE_DIR = '/Game/MoviePipelines/UniversalFilm_20261016'
    jobs = []
    shots = [('Portrait', 290, 18, 146, 75), ('FullBody', 490, 58, 88, 50)]
    if scene == 'Office':
        shots = [('OfficeMedium', 430, 90, 120, 50), ('OfficeWide', 720, 160, 110, 35)]
    elif scene == 'Arrival':
        shots = [('ArrivalWide', 900, 170, 125, 28)]
    for shot, distance, side, height, focal in shots:
        look = unreal.Vector(0, 0, height)
        loc = position(distance, side, height + 10)
        cam = A.spawn_actor_from_class(unreal.CineCameraActor, loc)
        cam.set_actor_label('Film_Cam_' + shot)
        cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(loc, look), False)
        cc = cam.get_cine_camera_component()
        cc.set_editor_property('filmback', unreal.CameraFilmbackSettings(sensor_width=36., sensor_height=20.25))
        cc.set_editor_property('current_focal_length', float(focal))
        focus = cc.get_editor_property('focus_settings')
        focus.set_editor_property('focus_method', unreal.CameraFocusMethod.DISABLE)
        cc.set_editor_property('focus_settings', focus)
        pp = cc.get_editor_property('post_process_settings')
        for key, value in {'override_auto_exposure_method': True,
                           'auto_exposure_method': unreal.AutoExposureMethod.AEM_MANUAL,
                           'override_auto_exposure_apply_physical_camera_exposure': True,
                           'auto_exposure_apply_physical_camera_exposure': False,
                           'override_auto_exposure_bias': True, 'auto_exposure_bias': 0.,
                           'override_bloom_intensity': True, 'bloom_intensity': 0.,
                           'override_vignette_intensity': True, 'vignette_intensity': .1}.items():
            pp.set_editor_property(key, value)
        cc.set_editor_property('post_process_settings', pp)
        cc.set_editor_property('post_process_blend_weight', 1.)
        stem = 'FILM_' + scene.upper() + '_' + shot.upper() + '_v01'
        seq = render.build_render_sequence('LS_' + stem, cam)
        cfg = render.job_config(str(ROOT / 'Showcase/UniversalFilm_20261016'), stem)
        config = E.load_asset(cfg)
        output = config.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting, True)
        output.set_editor_property('output_resolution', unreal.IntPoint(1600, 900))
        aa = config.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting, True)
        aa.set_editor_property('engine_warm_up_count', 24)
        aa.set_editor_property('render_warm_up_count', 8)
        save(config)
        jobs.append({'stem': stem, 'map': map_path, 'sequence': seq, 'config': cfg})
    if not unreal.EditorLoadingAndSavingUtils.save_current_level():
        raise RuntimeError('Composition save failed: ' + map_path)
    return {'scene': scene, 'map': map_path, 'subject': profile['name'],
            'pose': 'existing reference pose, rig deformation remains owned by Luna',
            'display_scale': scale, 'materials': slots, 'jobs': jobs}


if __name__ == '__main__':
    if not (REPORT / 'humber_migration.json').exists():
        raise RuntimeError('Run and verify shader migration first')
    if Path(unreal.Paths.project_dir()).resolve() != ROOT.resolve():
        raise RuntimeError('Run this builder only in Humber')
    source = json.loads((REPORT / 'source_inventory.json').read_text())
    master = E.load_asset(MASTER)
    nodes = M.get_material_expressions(master)
    calls = [node.get_editor_property('material_function').get_path_name()
             for node in nodes
             if node.get_class().get_name() == 'MaterialExpressionMaterialFunctionCall']
    if len(nodes) != source['expression_count'] or calls != source['function_calls']:
        raise RuntimeError('Humber master graph differs from inspected source')
    (REPORT / 'humber_graph_readback.json').write_text(json.dumps({
        'master': MASTER, 'expression_count': len(nodes), 'function_calls': calls,
        'result': 'humber_graph_matches_source'}, indent=2))
    profile = json.loads((ROOT / 'specs/humber_toon_spine/universal_film_cast.v1.json').read_text())
    alternate = os.environ.get('FILM_CAST_PROFILE')
    if alternate:
        profile = json.loads(Path(alternate).read_text())
    mats = setup_materials()
    report = {'result': 'building', 'master': MASTER, 'scenes': []}
    for scene in ['Studio', 'Office', 'Arrival']:
        report['scenes'].append(build(scene, profile, mats))
        (REPORT / 'scenes.json').write_text(json.dumps(report, indent=2))
    report['result'] = 'saved_editor_assets_not_yet_render_reviewed'
    (REPORT / 'scenes.json').write_text(json.dumps(report, indent=2))
    print('FILM_SCENES_SAVED')
