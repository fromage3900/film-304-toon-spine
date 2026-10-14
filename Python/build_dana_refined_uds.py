"""Author isolated Dana film look variants and fixed UDS comparison renders."""
import json
import re
import sys
import ast
from types import SimpleNamespace
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Python'))
import build_render_queue as render
import build_toon_profiles as profile_tools
# Read the palette contract without importing the staging script: that file
# runs its editor mutation at import time.
dana_spec = SimpleNamespace(**{node.targets[0].id: ast.literal_eval(node.value)
    for node in ast.parse((ROOT / 'Python/build_dana_materials.py').read_text()).body
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
    and node.targets[0].id in ('DANA_MATERIALS', 'SLOT_TO_INSTANCE')})

EAL = unreal.EditorAssetLibrary
ME = unreal.MaterialEditingLibrary
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LEVEL = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
MI_DIR = '/Game/Materials/Instances/DanaFilm'
MASTER_DIR = '/Game/Materials/Masters/DanaFilm'
PROFILE = '/Game/Materials/ToonProfiles/TP_DanaFilm_Clean'
BASE_MAP = '/Game/Maps/Lookdev/L_Dana_Film_Lookdev'
OUT = ROOT / 'Saved/Renders/dana_refined_uds'
REPORT = ROOT / 'Saved/Audit/dana_refined_uds_build.json'

def duplicate(source, target):
    if EAL.does_asset_exist(target):
        return unreal.load_asset(target)
    asset = EAL.duplicate_asset(source, target)
    if asset is None:
        raise RuntimeError('Could not duplicate ' + target)
    return asset

def save(asset):
    asset.modify()
    if not EAL.save_loaded_asset(asset, only_if_is_dirty=False):
        raise RuntimeError('Save failed: ' + asset.get_path_name())

def scalar_parameter(material, name, y, default, description, minimum, maximum):
    node = ME.create_material_expression(material, unreal.MaterialExpressionScalarParameter, -300, y)
    node.set_editor_property('parameter_name', name)
    node.set_editor_property('group', 'Clear Cornea')
    node.set_editor_property('default_value', default)
    # Keep the description and slider bounds when supported by this engine
    # build; the parameter names and defaults remain the stable contract.
    for property_name, value in (
        ('desc', description), ('slider_min', minimum), ('slider_max', maximum)):
        try:
            node.set_editor_property(property_name, value)
        except Exception:
            pass
    return node

def run():
    if unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages():
        raise RuntimeError('Current map has unsaved changes')
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    registry.scan_paths_synchronous(['/Game/UltraDynamicSky', '/Game/_ThirdParty/UltraDynamicSky'], force_rescan=True)
    opts = unreal.AssetRegistryDependencyOptions(include_hard_package_references=True, include_soft_package_references=True)
    vendor_assets = registry.get_assets_by_path('/Game/UltraDynamicSky', recursive=True) + registry.get_assets_by_path('/Game/_ThirdParty/UltraDynamicSky', recursive=True)
    external = sorted(set(str(d) for a in vendor_assets for d in registry.get_dependencies(a.package_name, opts) if str(d).startswith('/Game/') and not str(d).startswith(('/Game/UltraDynamicSky/', '/Game/_ThirdParty/UltraDynamicSky/'))))
    repaired_helpers = []
    source_ramp = '/Game/EnvSandbox/Materials/Functions/MF_ColorRamp3'
    if external == [source_ramp]:
        ramp = unreal.load_asset('/Game/Materials/Functions/MF_ColorRamp3')
        if ramp is None:
            raise RuntimeError('Humber colour ramp is missing')
        for asset in vendor_assets:
            deps = [str(d) for d in registry.get_dependencies(asset.package_name, opts)]
            if source_ramp not in deps:
                continue
            path = str(asset.package_name)
            if '/Editor_UI/Editor_Materials/' not in path:
                raise RuntimeError('Source customization reached runtime UDS: ' + path)
            material = unreal.load_asset(path)
            for node in ME.get_material_expressions(material):
                if isinstance(node, unreal.MaterialExpressionMaterialFunctionCall):
                    fn = node.get_editor_property('material_function')
                    if fn is None or fn.get_name() == 'MF_ColorRamp3':
                        node.modify()
                        node.set_editor_property('material_function', ramp)
            ME.recompile_material(material)
            save(material)
            repaired_helpers.append(path)
        external = ['/Game/Materials/Functions/MF_ColorRamp3']
    elif external and external != ['/Game/Materials/Functions/MF_ColorRamp3']:
        raise RuntimeError('Unexpected UDS project dependencies: ' + str(external))
    profile = duplicate('/Game/Materials/ToonProfiles/TP_Melusina', PROFILE)
    settings = profile.get_editor_property('settings')
    text = settings.export_text()
    changes = {'ShadowHatchingPatternStrength': 0.0, 'SpecularIndirectScale': 0.35, 'DiffuseIndirectScale': 1.0, 'ShadowExtinctionCoefficient': 4.5}
    for field, value in changes.items():
        text, count = re.subn(r'\b' + field + r'=[^,)]+', field + '=' + str(value), text)
        if count != 1:
            raise RuntimeError('Profile field missing: ' + field)
    diffuse_bands = [(0.,.42),(.34,.42),(.40,.72),(.68,.72),(.74,1.),(1.,1.)]
    text = profile_tools._profile_text(diffuse_bands, [(0.,0.),(.78,0.),(.84,.35),(1.,.45)], extinction=4.5, diffuse_indirect=1., specular_indirect=.35, hatch_strength=0.)
    if not settings.import_text(text):
        raise RuntimeError('Could not import clean Dana profile')
    profile.set_editor_property('settings', settings)
    save(profile)
    masters = {}
    for family in ('Character', 'Hair', 'Face'):
        master = duplicate('/Game/Materials/Masters/M_Master_Toon_' + family, MASTER_DIR + '/M_DanaFilm_' + family)
        master.set_editor_property('used_with_skeletal_mesh', True)
        # These source graphs feed PixelNormalWS into the Toon BSDF.
        # Preserve that world-space contract rather than transform it twice.
        master.set_editor_property('tangent_space_normal', False)
        nodes = [n for n in ME.get_material_expressions(master) if isinstance(n, unreal.MaterialExpressionSubstrateToonBSDF)]
        if len(nodes) != 1:
            raise RuntimeError('Expected one Toon BSDF in ' + family)
        nodes[0].modify()
        nodes[0].set_editor_property('toon_profile', profile)
        ME.recompile_material(master)
        save(master)
        if nodes[0].get_editor_property('toon_profile') != profile:
            raise RuntimeError('Profile binding failed')
        masters[family] = master
    tuned = {
        'Skin': {'RampStrength': .35, 'InkIntensity': .035, 'DryRoughness': .82, 'RimStrength': .045, 'BaseTint': (.60,.40,.31,1), 'AccentTint': (.79,.55,.43,1)},
        'Shirt': {'RampStrength': .42, 'InkIntensity': .045, 'DryRoughness': .88, 'PatternStrength': .025, 'RimStrength': .06},
        'Skirt': {'RampStrength': .42, 'InkIntensity': .045, 'DryRoughness': .88, 'PatternStrength': .018, 'RimStrength': .05},
        'Hair': {'RampStrength': .50, 'InkIntensity': .05, 'DryRoughness': .72, 'SheenStrength': .08, 'RimStrength': .065, 'AccentTint': (.23,.13,.08,1)},
        'Shoes': {'RampStrength': .40, 'InkIntensity': .05, 'DryRoughness': .75, 'RimStrength': .035},
        'Button': {'RampStrength': .45, 'InkIntensity': .03, 'DryRoughness': .48, 'RimStrength': .025},
        'EyeWhite': {'RampStrength': .25, 'InkIntensity': .015, 'RimStrength': .0},
        'Iris': {'RampStrength': .3, 'InkIntensity': .025, 'RimStrength': .0},
        'EyeInterior': {'RimStrength': .0},
    }
    instances = {}
    for original, (parent_name, _) in dana_spec.DANA_MATERIALS.items():
        part = original.removeprefix('MI_Dana_')
        mi = duplicate('/Game/Materials/Instances/' + original, MI_DIR + '/MI_DanaFilm_' + part)
        family = parent_name.removeprefix('M_Master_Toon_')
        if part == 'Cornea':
            instances[original] = mi
            continue
        ME.set_material_instance_parent(mi, masters[family])
        if family == 'Character':
            ME.set_material_instance_static_switch_parameter_value(mi, 'bContactShadow', False)
        values = {'BandStrength': 0., 'ParallaxScale': 0., 'ParallaxHeight': 0., 'TemporalStrength': 0., 'PatternStrength': 0.}
        values.update(tuned.get(part, {}))
        for key, value in values.items():
            if isinstance(value, tuple):
                ME.set_material_instance_vector_parameter_value(mi, key, unreal.LinearColor(*value))
            else:
                ME.set_material_instance_scalar_parameter_value(mi, key, value)
        ME.update_material_instance(mi)
        save(mi)
        instances[original] = mi
    # The imported cornea was parented to the Toon Glass master, whose
    # Substrate Toon BSDF has no opacity input. Build a small, real translucent
    # film cornea material so its coverage controls the visible iris directly.
    cornea_path = MASTER_DIR + '/M_DanaFilm_CorneaClear'
    if EAL.does_asset_exist(cornea_path):
        cornea_master = unreal.load_asset(cornea_path)
    else:
        cornea_master = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            'M_DanaFilm_CorneaClear', MASTER_DIR, unreal.Material,
            unreal.MaterialFactoryNew())
    if cornea_master is None:
        raise RuntimeError('Could not create clear cornea material')
    cornea_master.set_editor_property('material_domain', unreal.MaterialDomain.MD_SURFACE)
    cornea_master.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT_COLORED_TRANSMITTANCE)
    cornea_master.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    cornea_master.set_editor_property('used_with_skeletal_mesh', True)
    cornea_master.set_editor_property('two_sided', True)
    cornea_master.set_editor_property('tangent_space_normal', False)
    # A bulk clear can leave nodes referenced by a legacy material output.
    # Delete each node so Unreal disconnects every old output as well.
    for old_node in list(ME.get_material_expressions(cornea_master)):
        ME.delete_material_expression(cornea_master, old_node)
    tint = ME.create_material_expression(cornea_master, unreal.MaterialExpressionVectorParameter, -500, 0)
    tint.set_editor_property('parameter_name', 'CorneaTint')
    tint.set_editor_property('group', 'Clear Cornea')
    tint.set_editor_property('default_value', unreal.LinearColor(.88,.93,.98,1))
    try:
        tint.set_editor_property('desc', 'Subtle neutral tint for the transparent eye surface.')
    except Exception:
        pass
    coverage = scalar_parameter(cornea_master, 'Coverage', 120, .09,
        'Opacity of the cornea layer. Keep low to preserve the iris.', 0., .25)
    roughness = scalar_parameter(cornea_master, 'Roughness', 240, .10,
        'Softness of the cornea highlight.', .02, .3)
    specular = scalar_parameter(cornea_master, 'Specular', 360, .35,
        'Strength of the cornea highlight.', 0., .8)
    normal = ME.create_material_expression(cornea_master, unreal.MaterialExpressionPixelNormalWS, -240, 480)
    toon = ME.create_material_expression(cornea_master, unreal.MaterialExpressionSubstrateToonBSDF, 0, 180)
    toon.set_editor_property('toon_profile', profile)
    weight = ME.create_material_expression(cornea_master, unreal.MaterialExpressionSubstrateWeight, 300, 180)
    wires = (
        ME.connect_material_expressions(tint, '', toon, 'BaseColor'),
        ME.connect_material_expressions(specular, '', toon, 'Specular'),
        ME.connect_material_expressions(roughness, '', toon, 'Roughness'),
        ME.connect_material_expressions(normal, '', toon, 'Normal'),
        ME.connect_material_expressions(toon, '', weight, 'A'),
        ME.connect_material_expressions(coverage, '', weight, 'Weight'),
        ME.connect_material_property(weight, '', unreal.MaterialProperty.MP_FRONT_MATERIAL),
    )
    if not all(wires):
        raise RuntimeError('Could not wire the weighted Substrate Toon cornea graph')
    ME.recompile_material(cornea_master)
    save(cornea_master)
    cornea_mi = instances['MI_Dana_Cornea']
    ME.set_material_instance_parent(cornea_mi, cornea_master)
    ME.clear_all_material_instance_parameters(cornea_mi)
    ME.set_material_instance_vector_parameter_value(cornea_mi, 'CorneaTint', unreal.LinearColor(.88,.93,.98,1))
    ME.set_material_instance_scalar_parameter_value(cornea_mi, 'Coverage', .09)
    ME.set_material_instance_scalar_parameter_value(cornea_mi, 'Roughness', .10)
    ME.set_material_instance_scalar_parameter_value(cornea_mi, 'Specular', .35)
    ME.update_material_instance(cornea_mi)
    save(cornea_mi)
    floor_mi = duplicate('/Game/Materials/Instances/MI_Toon_Environment', MI_DIR + '/MI_DanaFilm_StageFloor')
    ME.set_material_instance_vector_parameter_value(floor_mi, 'BaseTint', unreal.LinearColor(.16,.19,.21,1))
    ME.set_material_instance_scalar_parameter_value(floor_mi, 'RampStrength', 0.)
    ME.set_material_instance_scalar_parameter_value(floor_mi, 'BandStrength', 0.)
    ME.set_material_instance_scalar_parameter_value(floor_mi, 'InkIntensity', 0.)
    ME.update_material_instance(floor_mi)
    save(floor_mi)
    stage_mat_path = MASTER_DIR + '/M_DanaFilm_StageFloor'
    if EAL.does_asset_exist(stage_mat_path):
        stage_mat = unreal.load_asset(stage_mat_path)
    else:
        stage_mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_DanaFilm_StageFloor', MASTER_DIR, unreal.Material, unreal.MaterialFactoryNew())
        color = ME.create_material_expression(stage_mat, unreal.MaterialExpressionConstant3Vector, -300, 0)
        color.set_editor_property('constant', unreal.LinearColor(.18,.20,.22,1))
        roughness = ME.create_material_expression(stage_mat, unreal.MaterialExpressionConstant, -300, 150)
        roughness.set_editor_property('r', .88)
        ME.connect_material_property(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
        ME.connect_material_property(roughness, '', unreal.MaterialProperty.MP_ROUGHNESS)
        ME.recompile_material(stage_mat)
        save(stage_mat)
    uds_class = unreal.load_class(None, '/Game/UltraDynamicSky/Blueprints/Ultra_Dynamic_Sky.Ultra_Dynamic_Sky_C')
    if uds_class is None:
        raise RuntimeError('UDS class did not load')
    hidden_path = MASTER_DIR + '/M_DanaFilm_ImportHelpers_Hidden'
    if EAL.does_asset_exist(hidden_path):
        hidden_material = unreal.load_asset(hidden_path)
    else:
        hidden_material = unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_DanaFilm_ImportHelpers_Hidden', MASTER_DIR, unreal.Material, unreal.MaterialFactoryNew())
        hidden_material.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
        hidden_material.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
        hidden_material.set_editor_property('used_with_skeletal_mesh', True)
        zero = ME.create_material_expression(hidden_material, unreal.MaterialExpressionConstant, -250, 0)
        zero.set_editor_property('r', 0.)
        ME.connect_material_property(zero, '', unreal.MaterialProperty.MP_OPACITY_MASK)
        ME.connect_material_property(zero, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        ME.recompile_material(hidden_material)
        save(hidden_material)
    render.SEQ_DIR = '/Game/Sequences/DanaLookdev'
    render.QUEUE_DIR = '/Game/MoviePipelines/DanaLookdev'
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = []
    stages = []
    selected_mode = 'Night' if 'night' in sys.argv[1:] else 'Day'
    for mode, time_of_day in [(selected_mode,2200. if selected_mode=='Night' else 1100.)]:
        map_path = '/Game/Maps/Lookdev/L_Dana_Toon_UDS_' + mode
        if EAL.does_asset_exist(map_path):
            if not LEVEL.load_level(map_path):
                raise RuntimeError('Map load failed')
        else:
            if not unreal.EditorLevelLibrary.new_level(map_path):
                raise RuntimeError('New map failed')
            mesh = unreal.load_asset('/Game/Meshes/Office/Props/C_DanaRenderTest_OSC')
            dana = ACTORS.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0,0,0), unreal.Rotator(0,0,-115))
            dana.set_actor_label('DANA_FILM_Dana')
            dana.get_component_by_class(unreal.SkeletalMeshComponent).set_skeletal_mesh_asset(mesh)
            floor = ACTORS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0,0,-.5))
            floor.set_actor_label('DANA_FILM_Floor')
            floor.get_component_by_class(unreal.StaticMeshComponent).set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Plane'))
            for name in ('FullBody','MaterialDetail'):
                camera = ACTORS.spawn_actor_from_class(unreal.CineCameraActor, unreal.Vector(0,0,0))
                camera.set_actor_label('DANA_FILM_Camera_' + name)
                c = camera.get_cine_camera_component()
                c.set_editor_property('filmback', unreal.CameraFilmbackSettings(sensor_width=35., sensor_height=19.6875))
                pp = unreal.PostProcessSettings()
                pp.set_editor_property('override_auto_exposure_method', True)
                pp.set_editor_property('auto_exposure_method', unreal.AutoExposureMethod.AEM_MANUAL)
                c.set_editor_property('post_process_settings', pp)
                c.set_editor_property('post_process_blend_weight', 1.)
        actors = ACTORS.get_all_level_actors()
        dana = next(a for a in actors if a.get_actor_label() == 'DANA_FILM_Dana')
        component = dana.get_component_by_class(unreal.SkeletalMeshComponent)
        mesh = component.get_skeletal_mesh_asset()
        for index, slot in enumerate(mesh.materials):
            slot_name = str(slot.material_slot_name).lower()
            component.set_material(index, hidden_material if slot_name == 'openpbr_shader1' else instances[dana_spec.SLOT_TO_INSTANCE[slot_name]])
        origin, ext = dana.get_actor_bounds(False)
        location = dana.get_actor_location()
        location.z -= origin.z - ext.z
        dana.set_actor_location(location, False, False)
        origin, ext = dana.get_actor_bounds(False)
        # This Maya import faces local +Y, rather than Unreal's +X.
        front = dana.get_actor_right_vector()
        right = dana.get_actor_forward_vector() * -1.
        for a in actors:
            label = a.get_actor_label()
            if label == 'DANA_FILM_Backdrop':
                ACTORS.destroy_actor(a)
            elif label == 'DANA_FILM_Floor':
                c = a.get_component_by_class(unreal.StaticMeshComponent)
                c.set_mobility(unreal.ComponentMobility.MOVABLE)
                c.set_material(0, stage_mat)
                a.set_actor_location(unreal.Vector(0,0,-.5), False, False)
                a.set_actor_scale3d(unreal.Vector(200,200,1))
            elif isinstance(a, unreal.RectLight):
                a.get_component_by_class(unreal.RectLightComponent).set_intensity(0.)
            elif isinstance(a, unreal.CineCameraActor):
                detail = 'Detail' in label
                distance = 155. if detail else 280.
                target = unreal.Vector(origin.x, origin.y, origin.z + (ext.z*.62 if detail else 0.))
                offset = 50. if detail else 90.
                camloc = unreal.Vector(target.x+front.x*distance+right.x*offset, target.y+front.y*distance+right.y*offset, target.z+18.)
                a.set_actor_location(camloc, False, False)
                a.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camloc,target), False)
                c = a.get_cine_camera_component()
                focus = c.get_editor_property('focus_settings')
                focus.set_editor_property('focus_method', unreal.CameraFocusMethod.DISABLE)
                c.set_editor_property('focus_settings', focus)
                c.set_editor_property('current_focal_length', 75. if detail else 50.)
                pp = c.get_editor_property('post_process_settings')
                pp.set_editor_property('override_auto_exposure_apply_physical_camera_exposure', True)
                pp.set_editor_property('auto_exposure_apply_physical_camera_exposure', False)
                pp.set_editor_property('override_auto_exposure_bias', True)
                pp.set_editor_property('auto_exposure_bias', 0.)
                c.set_editor_property('post_process_settings', pp)
        existing = [a for a in ACTORS.get_all_level_actors() if a.get_actor_label() == 'DANA_UDS_FixedSky']
        sky = existing[0] if existing else ACTORS.spawn_actor_from_class(uds_class, unreal.Vector(0,0,0))
        sky.set_actor_label('DANA_UDS_FixedSky')
        sky.set_actor_rotation(unreal.Rotator(0,0,180), False)
        sky_values = {'Time of Day':time_of_day, 'Animate Time of Day':False, 'Random Starting Time':False, 'Use System Time':False, 'Apply Exposure Settings':False, 'Sun Light Intensity':5., 'Moon Light Intensity':1.2 if mode=='Night' else .15, 'Sky Light Intensity':.65 if mode=='Night' else 1.0, 'Aurora Intensity':0., 'Cloud Coverage':1., 'Fog':.15}
        for name, value in sky_values.items():
            sky.set_editor_property(name, value)
        sky.call_method('UserConstructionScript')
        # A fixed film key keeps the character readable as sky conditions vary.
        # It has no light function and no baked-shadow dependency.
        film_key = next((a for a in ACTORS.get_all_level_actors() if a.get_actor_label() == 'DANA_FILM_Key'), None)
        key_location = unreal.Vector(origin.x + front.x*200. + right.x*100., origin.y + front.y*200. + right.y*100., origin.z + 140.)
        if film_key is None:
            film_key = ACTORS.spawn_actor_from_class(unreal.DirectionalLight, key_location)
            film_key.set_actor_label('DANA_FILM_Key')
        film_key.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(key_location, origin), False)
        key = film_key.get_component_by_class(unreal.DirectionalLightComponent)
        key.set_mobility(unreal.ComponentMobility.MOVABLE)
        key.set_intensity(5. if mode == 'Day' else 8.)
        key.set_editor_property('cast_static_shadows', False)
        key.set_editor_property('cast_shadows', False)
        key.set_editor_property('light_color', unreal.Color(255,245,231,255) if mode=='Day' else unreal.Color(190,212,255,255))
        if not unreal.EditorLoadingAndSavingUtils.save_current_level():
            raise RuntimeError('Failed to save ' + map_path)
        labels = [a.get_actor_label() for a in ACTORS.get_all_level_actors()]
        if labels.count('DANA_FILM_Dana') != 1:
            raise RuntimeError('Dana count failed')
        stages.append({'map':map_path, 'dana_count':1, 'slots':len(mesh.materials), 'film_key_intensity':key.intensity, 'sky':{k:str(sky.get_editor_property(k)) for k in sky_values}})
        for shot in (('FullBody','DANA_FILM_Camera_FullBody'), ('Detail','DANA_FILM_Camera_MaterialDetail')) if mode=='Day' else (('FullBody','DANA_FILM_Camera_FullBody'),):
            stem = 'DANA_REFINED_UDS_' + mode.upper() + '_' + shot[0].upper() + '_v01'
            camera = next(a for a in ACTORS.get_all_level_actors() if a.get_actor_label()==shot[1])
            seq_path = render.build_render_sequence('LS_' + stem, camera)
            cfg_path = render.job_config(str(OUT), stem)
            config = unreal.load_asset(cfg_path)
            aa = config.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting, True)
            aa.set_editor_property('engine_warm_up_count', 32)
            aa.set_editor_property('render_warm_up_count', 16)
            save(config)
            jobs.append({'stem':stem, 'map':map_path, 'sequence':seq_path, 'config':cfg_path})
    report = {'result':'authored', 'profile':PROFILE, 'profile_changes':changes, 'diffuse_bands':diffuse_bands, 'normal_space':'world', 'character_contact_shadow_tint':False, 'uds_vendor_assets':len(vendor_assets), 'uds_external_project_dependencies':external, 'uds_editor_helpers_retargeted_to_humber':repaired_helpers, 'materials':{k:v.get_path_name() for k,v in instances.items()}, 'hidden_import_helpers':{'slot':'openPBR_shader1','material':hidden_path,'triangles':274539,'note':'preview mitigation; source mesh and skeleton unchanged'}, 'stages':stages, 'jobs':jobs, 'qualification':'static source rig pose; body/facial export binding requires native Maya verification'}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    if REPORT.exists():
        previous = json.loads(REPORT.read_text())
        report['jobs'] = [j for j in previous.get('jobs',[]) if j['map'] != stages[0]['map']] + jobs
        report['stages'] = [s for s in previous.get('stages',[]) if s['map'] != stages[0]['map']] + stages
    REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8')
    unreal.log('[DanaRefinedUDS] ' + json.dumps(report))

run()
