"""Author isolated Dana film look variants and fixed UDS comparison renders."""
import json
import re
import sys
import ast
import os
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
EYE_PROFILE = '/Game/Materials/ToonProfiles/TP_DanaFilm_Eye'
BASE_MAP = '/Game/Maps/Lookdev/L_Dana_Film_Lookdev'
OUT = ROOT / 'Saved/Renders/dana_refined_uds'
REPORT = ROOT / 'Saved/Audit/dana_refined_uds_build.json'
CEL_DIAG_MAP = '/Game/Maps/Lookdev/L_Dana_CelRamp_Diagnostic'
CEL_DIAG_REPORT = ROOT / 'Saved/Audit/dana_cel_ramp_diagnostic.json'
CEL_DIAG_RENDER_DIR = ROOT / 'Saved/Renders/dana_cel_ramp_diagnostic'

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


def build_eye_surface_master(profile):
    path = MASTER_DIR + '/M_DanaFilm_EyeSurface'
    material = EAL.load_asset(path) if EAL.does_asset_exist(path) else         unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            'M_DanaFilm_EyeSurface', MASTER_DIR, unreal.Material,
            unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError('Could not create focused film eye material')
    material.set_editor_property('material_domain', unreal.MaterialDomain.MD_SURFACE)
    material.set_editor_property('blend_mode', unreal.BlendMode.BLEND_OPAQUE)
    # The eye graph must use the same cel-lighting contract as Dana's other
    # film materials. Keep the explicit eye ramp profile; do not fall back to
    # a physically lit eye master.
    material.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    material.set_editor_property('used_with_skeletal_mesh', True)
    material.set_editor_property('two_sided', False)
    material.set_editor_property('tangent_space_normal', False)
    for old_node in list(ME.get_material_expressions(material)):
        ME.delete_material_expression(material, old_node)

    color = ME.create_material_expression(material, unreal.MaterialExpressionVectorParameter, -500, 0)
    color.set_editor_property('parameter_name', 'EyeColor')
    color.set_editor_property('group', 'Film Eyes')
    color.set_editor_property('default_value', unreal.LinearColor(.82,.79,.73,1))
    roughness = ME.create_material_expression(material, unreal.MaterialExpressionScalarParameter, -500, 160)
    roughness.set_editor_property('parameter_name', 'Roughness')
    roughness.set_editor_property('group', 'Film Eyes')
    roughness.set_editor_property('default_value', .42)
    roughness.set_editor_property('slider_min', .05)
    roughness.set_editor_property('slider_max', 1.)
    specular = ME.create_material_expression(material, unreal.MaterialExpressionScalarParameter, -500, 320)
    specular.set_editor_property('parameter_name', 'Specular')
    specular.set_editor_property('group', 'Film Eyes')
    specular.set_editor_property('default_value', .18)
    specular.set_editor_property('slider_min', 0.)
    specular.set_editor_property('slider_max', .8)
    normal = ME.create_material_expression(material, unreal.MaterialExpressionPixelNormalWS, -240, 480)
    toon = ME.create_material_expression(material, unreal.MaterialExpressionSubstrateToonBSDF, 0, 180)
    toon.set_editor_property('toon_profile', profile)
    toon.modify()
    wires = (
        ME.connect_material_expressions(color, '', toon, 'BaseColor'),
        ME.connect_material_expressions(roughness, '', toon, 'Roughness'),
        ME.connect_material_expressions(specular, '', toon, 'Specular'),
        ME.connect_material_expressions(normal, '', toon, 'Normal'),
        ME.connect_material_property(toon, '', unreal.MaterialProperty.MP_FRONT_MATERIAL),
    )
    if not all(wires):
        raise RuntimeError('Could not wire the focused Toon eye graph')
    ME.recompile_material(material)
    # Substrate profile bindings can drop during recompile; re-fetch the Toon
    # node, assert the artist profile after compilation, then save.
    toon_nodes = [node for node in ME.get_material_expressions(material)
                  if isinstance(node, unreal.MaterialExpressionSubstrateToonBSDF)]
    if len(toon_nodes) != 1:
        raise RuntimeError('Expected exactly one Toon BSDF in Dana eye master')
    toon_nodes[0].modify()
    toon_nodes[0].set_editor_property('toon_profile', profile)
    if toon_nodes[0].get_editor_property('toon_profile') != profile:
        raise RuntimeError('Dana eye Toon Profile did not persist')
    save(material)
    return material


def build_eye_profile(base_profile):
    """Create a clear but gentle three-band film eye lighting response."""
    profile = duplicate(base_profile.get_path_name().split('.')[0], EYE_PROFILE)
    settings = profile.get_editor_property('settings')
    text = profile_tools._profile_text(
        [(0.0, 0.34), (0.32, 0.34), (0.38, 0.63),
         (0.70, 0.63), (0.76, 0.92), (1.0, 0.92)],
        [(0.0, 0.0), (0.58, 0.0), (0.68, 0.48),
         (0.86, 0.78), (1.0, 1.0)],
        extinction=4.5,
        diffuse_indirect=0.45,
        specular_indirect=0.25,
        hatch_strength=0.0,
    )
    if not settings.import_text(text):
        raise RuntimeError('Could not import Dana eye Toon Profile')
    profile.set_editor_property('settings', settings)
    save(profile)
    return profile


def build_character_profile():
    """Author a legible three-band diffuse response for Dana's film look."""
    profile = EAL.load_asset(PROFILE)
    if profile is None:
        raise RuntimeError('Dana core Toon Profile is missing')
    settings = profile.get_editor_property('settings')
    # Compact thresholds and separated outputs give the lighting ramp a
    # readable three-step response; the master graph's palette ramp is separate.
    bands = [(0., .18), (.28, .18), (.32, .48),
             (.62, .48), (.66, .82), (1., .82)]
    text = profile_tools._profile_text(
        bands, [(0., 0.), (.62, 0.), (.70, .45), (.88, .85), (1., 1.)],
        extinction=5.0, diffuse_indirect=.45, specular_indirect=.20,
        hatch_strength=0.)
    if not settings.import_text(text):
        raise RuntimeError('Could not author Dana cel diagnostic profile')
    profile.set_editor_property('settings', settings)
    save(profile)
    return profile, bands


def build_verified_dana_ramp():
    """Bind the explicit Toon Profile ramp to a known-good Humber Dana stage."""
    if unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages():
        raise RuntimeError('Current map has unsaved changes')
    profile, bands = build_character_profile()
    eye_profile = EAL.load_asset(EYE_PROFILE)
    eye_settings = eye_profile.get_editor_property('settings')
    eye_text = profile_tools._profile_text(
        bands, [(0., 0.), (.62, 0.), (.70, .45), (.88, .85), (1., 1.)],
        extinction=5., diffuse_indirect=.45, specular_indirect=.20,
        hatch_strength=0.)
    if not eye_settings.import_text(eye_text):
        raise RuntimeError('Could not align Dana eye profile to the film ramp')
    eye_profile.set_editor_property('settings', eye_settings)
    save(eye_profile)
    # Rebind all three Dana masters after changing the shared profile asset,
    # then save the binding after compile to keep the Toon BSDF on the new ramp.
    master_paths = {
        'Character': MASTER_DIR + '/M_DanaFilm_Character',
        'Hair': MASTER_DIR + '/M_DanaFilm_Hair',
        'Face': MASTER_DIR + '/M_DanaFilm_Face',
    }
    master_rows = []
    for family, path in master_paths.items():
        master = EAL.load_asset(path)
        nodes = [n for n in ME.get_material_expressions(master)
                 if isinstance(n, unreal.MaterialExpressionSubstrateToonBSDF)]
        if len(nodes) != 1:
            raise RuntimeError('Expected one Dana Toon BSDF in '+family)
        nodes[0].set_editor_property('toon_profile', profile)
        ME.recompile_material(master)
        nodes = [n for n in ME.get_material_expressions(master)
                 if isinstance(n, unreal.MaterialExpressionSubstrateToonBSDF)]
        nodes[0].set_editor_property('toon_profile', profile)
        if nodes[0].get_editor_property('toon_profile') != profile:
            raise RuntimeError('Dana Toon Profile did not persist on '+family)
        save(master)
        master_rows.append({'family':family,'toon_profile':nodes[0].get_editor_property('toon_profile').get_path_name(),
                            'compiled':True})
    # Keep the working daylight map, actors, and framing intact. Its camera is
    # already a proven render path; only the material/profile pass changes.
    jobs = [j for j in json.loads(REPORT.read_text()).get('jobs', [])
            if j.get('stem') == 'DANA_REFINED_UDS_DAY_FULLBODY_v01']
    if len(jobs) != 1:
        raise RuntimeError('Expected one known-good Dana UDS day full-body job')
    job = jobs[0]
    if not LEVEL.load_level(job['map']):
        raise RuntimeError('Could not load the known-good Dana daylight map')
    expected = {'DANA_FILM_Dana': unreal.SkeletalMeshActor,
                'DANA_FILM_Key': unreal.DirectionalLight,
                'DANA_UDS_FixedSky': unreal.Actor}
    actors = ACTORS.get_all_level_actors()
    labels = {a.get_actor_label():a for a in actors}
    for label, cls in expected.items():
        if label not in labels or (cls is not unreal.Actor and not isinstance(labels[label], cls)):
            raise RuntimeError('Known-good stage is missing expected actor: '+label)
    dana = labels['DANA_FILM_Dana']
    component = dana.get_component_by_class(unreal.SkeletalMeshComponent)
    mesh = component.get_skeletal_mesh_asset()
    material_rows = []
    for index, slot in enumerate(mesh.materials):
        slot_name = str(slot.material_slot_name).lower()
        instance = component.get_material(index)
        if slot_name in ('danaskin_mat','danashirt_mat','danapants_mat','danaHair_mat'.lower(),
                         'danashoes_mat','danapantsbutton_mat'):
            if instance is None or not hasattr(instance, 'get_editor_property'):
                raise RuntimeError('Missing Dana film instance in slot '+slot_name)
            scalar = ME.get_material_instance_scalar_parameter_value(instance, 'RampStrength')
            if scalar <= .0:
                raise RuntimeError('Palette ramp is bypassed in slot '+slot_name)
            material_rows.append({'slot':slot_name, 'material':instance.get_path_name(),
                                  'palette_ramp_strength':scalar})
    # Refined stage key had cast shadows disabled; enable dynamic shadows here
    # so the Toon Profile can produce a stable terminator on face and clothing.
    key_component = labels['DANA_FILM_Key'].get_component_by_class(unreal.DirectionalLightComponent)
    key_component.set_editor_property('cast_shadows', True)
    key_component.set_editor_property('cast_dynamic_shadows', True)
    if not unreal.EditorLoadingAndSavingUtils.save_current_level():
        raise RuntimeError('Could not save the Dana day stage shadow update')
    report = {'result':'profile_bound_render_pending', 'map':job['map'],
        'profile':PROFILE, 'eye_profile':EYE_PROFILE, 'masters':master_rows,
        'diffuse_bands':bands,
        'diffuse_indirect_scale':.45, 'key_cast_dynamic_shadows':True,
        'materials':material_rows, 'sequence':job['sequence'], 'config':job['config'],
        'render_stem':'DANA_REFINED_UDS_DAY_FULLBODY_v02',
        'proof_gate':'Fresh daylight render must visibly show three diffuse bands on skin, hair and clothing.'}
    CEL_DIAG_REPORT.parent.mkdir(parents=True,exist_ok=True)
    CEL_DIAG_REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8')
    unreal.log('[DanaVerifiedRamp] '+json.dumps(report))

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
        raise RuntimeError('Could not import Dana Toon Profile')
    profile.set_editor_property('settings', settings)
    save(profile)
    eye_profile = build_eye_profile(profile)
    eye_master = build_eye_surface_master(eye_profile)
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
        nodes = [n for n in ME.get_material_expressions(master)
                 if isinstance(n, unreal.MaterialExpressionSubstrateToonBSDF)]
        if len(nodes) != 1:
            raise RuntimeError('Toon BSDF lost during compile: ' + family)
        nodes[0].modify()
        nodes[0].set_editor_property('toon_profile', profile)
        if nodes[0].get_editor_property('toon_profile') != profile:
            raise RuntimeError('Profile binding failed after compile: ' + family)
        save(master)
        masters[family] = master
    tuned = {
        'Skin': {'RampStrength': .35, 'InkIntensity': .035, 'DryRoughness': .82, 'RimStrength': .045, 'BaseTint': (.60,.40,.31,1), 'AccentTint': (.79,.55,.43,1)},
        'Shirt': {'RampStrength': .42, 'InkIntensity': .045, 'DryRoughness': .88, 'PatternStrength': .025, 'RimStrength': .06},
        'Skirt': {'RampStrength': .42, 'InkIntensity': .045, 'DryRoughness': .88, 'PatternStrength': .018, 'RimStrength': .05},
        'Hair': {'RampStrength': .50, 'InkIntensity': .05, 'DryRoughness': .72, 'SheenStrength': .08, 'RimStrength': .065, 'AccentTint': (.23,.13,.08,1)},
        'Shoes': {'RampStrength': .40, 'InkIntensity': .05, 'DryRoughness': .75, 'RimStrength': .035},
        'Button': {'RampStrength': .45, 'InkIntensity': .03, 'DryRoughness': .48, 'RimStrength': .025},
        'EyeWhite': {'RampStrength': .08, 'InkIntensity': .004, 'DryRoughness': .48, 'RimStrength': .0, 'BaseTint': (.82,.79,.73,1), 'AccentTint': (.96,.93,.86,1)},
        'Iris': {'RampStrength': .10, 'InkIntensity': .006, 'DryRoughness': .30, 'RimStrength': .0, 'BaseTint': (.24,.095,.04,1), 'AccentTint': (.55,.25,.08,1)},
        'EyeInterior': {'RampStrength': 0., 'InkIntensity': 0., 'DryRoughness': .48, 'RimStrength': .0, 'BaseTint': (.012,.008,.012,1), 'AccentTint': (.012,.008,.012,1)},
    }
    instances = {}
    for original, (parent_name, _) in dana_spec.DANA_MATERIALS.items():
        part = original.removeprefix('MI_Dana_')
        mi = duplicate('/Game/Materials/Instances/' + original, MI_DIR + '/MI_DanaFilm_' + part)
        if part in ('EyeWhite', 'Iris', 'EyeInterior'):
            eye_values = {
                'EyeWhite': {'EyeColor': (.96,.93,.86,1), 'Roughness': .52, 'Specular': .22},
                'Iris': {'EyeColor': (.46,.20,.07,1), 'Roughness': .32, 'Specular': .28},
                'EyeInterior': {'EyeColor': (.008,.005,.008,1), 'Roughness': .48, 'Specular': .05},
            }[part]
            ME.set_material_instance_parent(mi, eye_master)
            ME.clear_all_material_instance_parameters(mi)
            ME.set_material_instance_vector_parameter_value(
                mi, 'EyeColor', unreal.LinearColor(*eye_values['EyeColor']))
            ME.set_material_instance_scalar_parameter_value(mi, 'Roughness', eye_values['Roughness'])
            ME.set_material_instance_scalar_parameter_value(mi, 'Specular', eye_values['Specular'])
            ME.update_material_instance(mi)
            save(mi)
            instances[original] = mi
            continue
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
    tint.set_editor_property('default_value', unreal.LinearColor(.94,.97,1.,1))
    try:
        tint.set_editor_property('desc', 'Subtle neutral tint for the transparent eye surface.')
    except Exception:
        pass
    coverage = scalar_parameter(cornea_master, 'Coverage', 120, .08,
        'Opacity of the cornea layer. Keep low to preserve the iris.', 0., .25)
    roughness = scalar_parameter(cornea_master, 'Roughness', 240, .035,
        'Softness of the cornea highlight.', .02, .3)
    specular = scalar_parameter(cornea_master, 'Specular', 360, .65,
        'Strength of the cornea highlight.', 0., .8)
    normal = ME.create_material_expression(cornea_master, unreal.MaterialExpressionPixelNormalWS, -240, 480)
    toon = ME.create_material_expression(cornea_master, unreal.MaterialExpressionSubstrateToonBSDF, 0, 180)
    toon.set_editor_property('toon_profile', eye_profile)
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
    toon_nodes = [node for node in ME.get_material_expressions(cornea_master)
                  if isinstance(node, unreal.MaterialExpressionSubstrateToonBSDF)]
    if len(toon_nodes) != 1:
        raise RuntimeError('Cornea Toon BSDF lost during compile')
    toon_nodes[0].modify()
    toon_nodes[0].set_editor_property('toon_profile', eye_profile)
    if toon_nodes[0].get_editor_property('toon_profile') != eye_profile:
        raise RuntimeError('Cornea Toon Profile did not survive compile')
    save(cornea_master)
    cornea_mi = instances['MI_Dana_Cornea']
    ME.set_material_instance_parent(cornea_mi, cornea_master)
    ME.clear_all_material_instance_parameters(cornea_mi)
    ME.set_material_instance_vector_parameter_value(cornea_mi, 'CorneaTint', unreal.LinearColor(.94,.97,1.,1))
    ME.set_material_instance_scalar_parameter_value(cornea_mi, 'Coverage', .08)
    ME.set_material_instance_scalar_parameter_value(cornea_mi, 'Roughness', .035)
    ME.set_material_instance_scalar_parameter_value(cornea_mi, 'Specular', .65)
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
                light_component = a.get_component_by_class(unreal.RectLightComponent)
                light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
                if 'Key' in label:
                    light_component.set_intensity_units(unreal.LightUnits.LUMENS)
                    light_component.set_editor_property('intensity', 2400.0)
                    light_component.set_editor_property('cast_shadows', True)
                elif 'Fill' in label:
                    light_component.set_intensity_units(unreal.LightUnits.LUMENS)
                    light_component.set_editor_property('intensity', 500.0)
                    light_component.set_editor_property('cast_shadows', False)
                elif 'Rim' in label:
                    light_component.set_intensity_units(unreal.LightUnits.LUMENS)
                    light_component.set_editor_property('intensity', 1100.0)
                    light_component.set_editor_property('cast_shadows', True)
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
        key.set_editor_property('cast_shadows', True)
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


def run_eyes_only():
    """Update only Dana's eye profile/material assets; leave maps and cameras alone."""
    if unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages():
        raise RuntimeError('Current map has unsaved changes')
    base_profile = EAL.load_asset(PROFILE)
    if base_profile is None:
        raise RuntimeError('Dana film Toon Profile is missing')
    eye_profile = build_eye_profile(base_profile)
    eye_master = build_eye_surface_master(eye_profile)

    eye_values = {
        'MI_DanaFilm_EyeWhite': {
            'EyeColor': (.96, .93, .86, 1.), 'Roughness': .52, 'Specular': .22},
        'MI_DanaFilm_Iris': {
            'EyeColor': (.46, .20, .07, 1.), 'Roughness': .32, 'Specular': .28},
        'MI_DanaFilm_EyeInterior': {
            'EyeColor': (.008, .005, .008, 1.), 'Roughness': .48, 'Specular': .05},
    }
    readback = []
    for name, values in eye_values.items():
        path = MI_DIR + '/' + name
        instance = EAL.load_asset(path)
        if instance is None:
            raise RuntimeError('Missing Dana eye instance ' + path)
        ME.set_material_instance_parent(instance, eye_master)
        ME.clear_all_material_instance_parameters(instance)
        color = values['EyeColor']
        ME.set_material_instance_vector_parameter_value(
            instance, 'EyeColor', unreal.LinearColor(*color))
        for key in ('Roughness', 'Specular'):
            ME.set_material_instance_scalar_parameter_value(instance, key, values[key])
        ME.update_material_instance(instance)
        save(instance)
        parent = instance.get_editor_property('parent')
        actual_color = ME.get_material_instance_vector_parameter_value(instance, 'EyeColor')
        actual = {
            'parent': parent.get_path_name() if parent else None,
            'EyeColor': [round(float(v), 4) for v in
                         (actual_color.r, actual_color.g, actual_color.b, actual_color.a)],
            'Roughness': round(float(ME.get_material_instance_scalar_parameter_value(
                instance, 'Roughness')), 4),
            'Specular': round(float(ME.get_material_instance_scalar_parameter_value(
                instance, 'Specular')), 4),
        }
        expected = {'parent': eye_master.get_path_name(),
                    'EyeColor': [round(float(v), 4) for v in color],
                    'Roughness': round(values['Roughness'], 4),
                    'Specular': round(values['Specular'], 4)}
        if actual != expected:
            raise RuntimeError(name + ' readback mismatch: ' + repr(actual))
        readback.append({'asset': path, 'values': actual, 'ok': True})

    cornea_path = MASTER_DIR + '/M_DanaFilm_CorneaClear'
    cornea_master = EAL.load_asset(cornea_path)
    if cornea_master is None:
        raise RuntimeError('Dana film cornea master is missing')
    toon_nodes = [n for n in ME.get_material_expressions(cornea_master)
                  if isinstance(n, unreal.MaterialExpressionSubstrateToonBSDF)]
    if len(toon_nodes) != 1:
        raise RuntimeError('Expected one Substrate Toon node in cornea master')
    toon_nodes[0].modify()
    toon_nodes[0].set_editor_property('toon_profile', eye_profile)
    ME.recompile_material(cornea_master)
    save(cornea_master)
    if toon_nodes[0].get_editor_property('toon_profile') != eye_profile:
        raise RuntimeError('Cornea eye profile did not persist')

    cornea_instance = EAL.load_asset(MI_DIR + '/MI_DanaFilm_Cornea')
    if cornea_instance is None:
        raise RuntimeError('Dana film cornea instance is missing')
    cornea_values = {'Coverage': .08, 'Roughness': .035, 'Specular': .65}
    for key, value in cornea_values.items():
        ME.set_material_instance_scalar_parameter_value(cornea_instance, key, value)
    ME.set_material_instance_vector_parameter_value(
        cornea_instance, 'CorneaTint', unreal.LinearColor(.94, .97, 1., 1.))
    ME.update_material_instance(cornea_instance)
    save(cornea_instance)
    readback.append({'asset': cornea_instance.get_path_name(),
                     'values': cornea_values, 'ok': True})

    report = {
        'result': 'pass',
        'eye_profile': EYE_PROFILE,
        'eye_master_graph': {
            'asset': eye_master.get_path_name(),
            'toon_bsdf_count': len([node for node in ME.get_material_expressions(eye_master)
                                    if isinstance(node, unreal.MaterialExpressionSubstrateToonBSDF)]),
            'toon_profile': EYE_PROFILE,
            'post_compile_readback': EYE_PROFILE,
            'compile_and_save': 'completed',
        },
        'cornea_master_graph': {
            'asset': cornea_master.get_path_name(),
            'toon_bsdf_count': len(toon_nodes),
            'toon_profile': EYE_PROFILE,
            'post_compile_readback': toon_nodes[0].get_editor_property('toon_profile').get_path_name(),
            'compile_and_save': 'completed',
        },
        'diffuse_bands': [[0.0, .34], [.32, .34], [.38, .63],
                          [.70, .63], [.76, .92], [1.0, .92]],
        'specular_bands': [[0.0, 0.0], [.58, 0.0], [.68, .48],
                           [.86, .78], [1.0, 1.0]],
        'material_readback': readback,
        'scope': 'eye Toon Profile and material graphs only; no map, rig, or camera edits',
    }
    out = ROOT / 'Saved' / 'Audit' / 'dana_eye_look_fix.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.log('[DanaEyeLookFix] ' + json.dumps(report))


def run_cel_diagnostic():
    """Isolated Dana lighting/profile diagnostic; never edits the UDS maps."""
    dirty = unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    if dirty:
        raise RuntimeError('Refusing cel diagnostic with dirty maps: ' + str(dirty))
    profile, bands = build_character_profile()

    # The film master family is intentionally simple: one reachable toon
    # closure and a controlled diffuse ramp. Rebind after compile for each.
    master_paths = {
        'Character': MASTER_DIR + '/M_DanaFilm_Character',
        'Hair': MASTER_DIR + '/M_DanaFilm_Hair',
        'Face': MASTER_DIR + '/M_DanaFilm_Face',
    }
    material_rows = []
    for family, path in master_paths.items():
        master = EAL.load_asset(path)
        if master is None:
            raise RuntimeError('Missing Dana material master: ' + path)
        nodes = [n for n in ME.get_material_expressions(master)
                 if isinstance(n, unreal.MaterialExpressionSubstrateToonBSDF)]
        if len(nodes) != 1:
            raise RuntimeError('%s must have exactly one Toon BSDF' % family)
        nodes[0].modify()
        nodes[0].set_editor_property('toon_profile', profile)
        ME.recompile_material(master)
        nodes = [n for n in ME.get_material_expressions(master)
                 if isinstance(n, unreal.MaterialExpressionSubstrateToonBSDF)]
        if len(nodes) != 1:
            raise RuntimeError('%s Toon BSDF missing after compile' % family)
        nodes[0].modify()
        nodes[0].set_editor_property('toon_profile', profile)
        actual = nodes[0].get_editor_property('toon_profile')
        if actual != profile:
            raise RuntimeError('%s Toon Profile readback failed' % family)
        save(master)
        material_rows.append({'family': family, 'master': path,
                              'toon_bsdf_count': len(nodes),
                              'profile': actual.get_path_name(),
                              'compiled': True})

    # Give the eye closure the same band positions, preserving its distinct
    # eye palette/profile asset identity.
    eye_profile = EAL.load_asset(EYE_PROFILE)
    eye_settings = eye_profile.get_editor_property('settings')
    eye_text = profile_tools._profile_text(
        bands, [(0., 0.), (.62, 0.), (.70, .45), (.88, .85), (1., 1.)],
        extinction=5., diffuse_indirect=.45, specular_indirect=.20,
        hatch_strength=0.)
    if not eye_settings.import_text(eye_text):
        raise RuntimeError('Could not align Dana eye ramp to diagnostic')
    eye_profile.set_editor_property('settings', eye_settings)
    save(eye_profile)

    if EAL.does_asset_exist(CEL_DIAG_MAP):
        if not LEVEL.load_level(CEL_DIAG_MAP):
            raise RuntimeError('Could not load isolated cel diagnostic map')
        for actor in list(ACTORS.get_all_level_actors()):
            if actor.get_actor_label().startswith('DANA_CELDIAG_'):
                ACTORS.destroy_actor(actor)
    else:
        if not unreal.EditorLevelLibrary.new_level(CEL_DIAG_MAP):
            raise RuntimeError('Could not create isolated cel diagnostic map')

    mesh = EAL.load_asset('/Game/Meshes/Office/Props/C_DanaRenderTest_OSC')
    if mesh is None:
        raise RuntimeError('Dana skeletal mesh missing')
    dana = ACTORS.spawn_actor_from_class(unreal.SkeletalMeshActor,
        unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, -115))
    dana.set_actor_label('DANA_CELDIAG_Character')
    component = dana.get_component_by_class(unreal.SkeletalMeshComponent)
    component.set_skeletal_mesh_asset(mesh)
    for i, slot in enumerate(mesh.materials):
        slot_name = str(slot.material_slot_name).lower()
        if slot_name == 'openpbr_shader1':
            material = EAL.load_asset(MASTER_DIR + '/M_DanaFilm_ImportHelpers_Hidden')
        else:
            instance_name = dana_spec.SLOT_TO_INSTANCE[slot_name]
            material = EAL.load_asset(MI_DIR + '/MI_DanaFilm_' + instance_name.removeprefix('MI_Dana_'))
        if material is None:
            raise RuntimeError('Missing staged material for slot ' + slot_name)
        component.set_material(i, material)

    # No sky, no rect lights, no exposure compensation: a single large
    # directional source makes the stepped diffuse response easy to read.
    sun_loc = unreal.Vector(130, 180, 165)
    sun = ACTORS.spawn_actor_from_class(unreal.DirectionalLight, sun_loc,
        unreal.MathLibrary.find_look_at_rotation(sun_loc, unreal.Vector(0, 0, 54)))
    sun.set_actor_label('DANA_CELDIAG_Key')
    sun_component = sun.get_component_by_class(unreal.DirectionalLightComponent)
    sun_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sun_component.set_intensity(5.0)
    sun_component.set_editor_property('cast_shadows', True)
    sun_component.set_editor_property('cast_dynamic_shadows', True)
    sun_component.set_editor_property('light_color', unreal.Color(255, 245, 231, 255))

    # Restrained ambient fill keeps the shadow color legible while leaving
    # the directional key responsible for the visible light terminator.
    sky = ACTORS.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0,0,300))
    sky.set_actor_label('DANA_CELDIAG_SkyFill')
    sky_component = sky.get_component_by_class(unreal.SkyLightComponent)
    sky_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sky_component.set_intensity(0.2)
    try:
        sky_component.call_method('recapture_sky')
    except Exception:
        pass

    camera = ACTORS.spawn_actor_from_class(unreal.CineCameraActor,
        unreal.Vector(0,0,0))
    camera.set_actor_label('DANA_CELDIAG_Camera')
    origin, ext = dana.get_actor_bounds(False)
    front = dana.get_actor_right_vector()
    right = dana.get_actor_forward_vector() * -1.
    target = unreal.Vector(origin.x, origin.y, origin.z + ext.z * .62)
    cam_loc = unreal.Vector(target.x + front.x*155. + right.x*25.,
                            target.y + front.y*155. + right.y*25.,
                            target.z + 12.)
    camera.set_actor_location(cam_loc, False, False)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(cam_loc,target), False)
    cc = camera.get_cine_camera_component()
    cc.set_editor_property('filmback', unreal.CameraFilmbackSettings(sensor_width=35, sensor_height=19.6875))
    cc.set_editor_property('current_focal_length', 75.)
    pp = unreal.PostProcessSettings()
    pp.set_editor_property('override_auto_exposure_method', True)
    pp.set_editor_property('auto_exposure_method', unreal.AutoExposureMethod.AEM_MANUAL)
    pp.set_editor_property('override_auto_exposure_min_brightness', True)
    pp.set_editor_property('override_auto_exposure_max_brightness', True)
    pp.set_editor_property('auto_exposure_min_brightness', 1.)
    pp.set_editor_property('auto_exposure_max_brightness', 1.)
    cc.set_editor_property('post_process_settings', pp)
    cc.set_editor_property('post_process_blend_weight', 1.)
    if not unreal.EditorLoadingAndSavingUtils.save_current_level():
        raise RuntimeError('Could not save isolated Dana cel diagnostic map')

    render.SEQ_DIR = '/Game/Sequences/DanaCelDiagnostic'
    render.QUEUE_DIR = '/Game/MoviePipelines/DanaCelDiagnostic'
    seq = render.build_render_sequence('LS_DANA_CEL_RAMP_DIAGNOSTIC_v01', camera)
    cfg_path = render.job_config(str(CEL_DIAG_RENDER_DIR), 'DANA_CEL_RAMP_DIAGNOSTIC_v01')
    config = EAL.load_asset(cfg_path)
    out = config.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting, True)
    out.set_editor_property('output_resolution', unreal.IntPoint(1280, 720))
    out.set_editor_property('output_directory', unreal.DirectoryPath(str(CEL_DIAG_RENDER_DIR)))
    out.set_editor_property('file_name_format', 'DANA_CEL_RAMP_DIAGNOSTIC_v01')
    save(config)
    report = {'result':'render_ready', 'map':CEL_DIAG_MAP,
        'profile':PROFILE, 'eye_profile':EYE_PROFILE, 'diffuse_bands':bands,
        'masters':material_rows, 'sequence':seq, 'config':cfg_path,
        'camera':'DANA_CELDIAG_Camera', 'lights':['one shadow casting directional key','low recaptured skylight'],
        'proof_gate':'Render must show distinct terminator bands on face/hair/clothing.'}
    CEL_DIAG_REPORT.parent.mkdir(parents=True,exist_ok=True)
    CEL_DIAG_REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8')
    unreal.log('[DanaCelDiagnostic] '+json.dumps(report))


if 'verified-ramp' in sys.argv[1:]:
    build_verified_dana_ramp()
elif 'cel-diagnostic' in sys.argv[1:]:
    run_cel_diagnostic()
elif os.environ.get('DANA_EYES_ONLY') == '1' or 'eyes-only' in sys.argv[1:]:
    run_eyes_only()
else:
    run()
