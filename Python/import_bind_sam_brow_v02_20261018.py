"""Import Sam brow-patch candidate v02 as SK_Sam_Film304_v02brow; bind all slots.

Mirrors import_repaired_film_cast_20261017.py conventions: gated against the
mayapy export report + consolidated readback-style checks, new staging folder,
deterministic asset names, saved bindings, request-file action trigger.

Actions (Saved/Audit/EveningExecution_20261018/brow_b_action.txt):
  import   -- gated FBX import + structure readback
  bind     -- material binding for all 13 slots incl. new brow patch MI
"""
import hashlib
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / 'Saved/Audit/EveningExecution_20261018'
REQUEST = OUT / 'brow_b_action.txt'
SRC = ROOT / 'Saved/OfflineIntake/20261018/browB/Sam_CleanFilm_UE_v02_brow.fbx'
SRC_REPORT = ROOT / 'Saved/OfflineIntake/20261018/browB/export_report.json'
DESTINATION = '/Game/Staging/Film304BrowPatches_20261018/Sam'
ASSET_NAME = 'SK_Sam_Film304_v02brow'
PARENT = '/Game/Materials/Masters/Film304/M_UniversalToon_Film304_v06'
NEW_MI = '/Game/Materials/Instances/Film304/Cast/Sam'
V01 = '/Game/Staging/Film304Repaired_20261017/Sam/SK_Sam_Film304_v01'
ROLES = {
    'body_skin': 'Skin', 'body_skin_section_default_shader': 'Skin', 'cornea': 'Cornea',
    'eye_interior_auxiliary': 'EyeInterior', 'eyeball_sclera': 'EyeWhite', 'footwear': 'Shoes',
    'hair_brow_and_lash': 'Hair', 'hair_and_lash': 'Hair', 'hair': 'Hair', 'eyelashes': 'Hair',
    'iris': 'Iris', 'jeans_trousers': 'Cloth', 'pants_trousers': 'Cloth', 'shirt': 'Shirt',
    'teeth': 'Teeth', 'gum_oral_soft_tissue': 'Mouth', 'tongue': 'Mouth', 'tongue_and_oral_soft_tissue': 'Mouth',
    'brow_patch': 'BrowPatch'}
PART_TO_MI = {
    'Skin': 'MI_Film304_Sam_Skin_Toon', 'Hair': 'MI_Film304_Sam_Hair_Toon', 'Shoes': 'MI_Film304_Sam_Shoes_Toon',
    'Cornea': 'MI_Film304_Sam_Cornea_Toon', 'Iris': 'MI_Film304_Sam_Iris_Toon', 'EyeWhite': 'MI_Film304_Sam_EyeWhite_Toon',
    'Mouth': 'MI_Film304_Sam_Mouth_Toon', 'Teeth': 'MI_Film304_Sam_Teeth_Toon', 'Cloth': 'MI_Film304_Sam_Cloth_Toon',
    'EyeInterior': 'MI_Film304_Sam_EyeInterior_Toon', 'Shirt': 'MI_Film304_Sam_Shirt_Toon'}


def default_mip():
    return None


def main_import():
    report = json.loads(SRC_REPORT.read_text())
    assert report['status'] == 'exported_brow_patch_gates_passed_pending_ue_readback', report['status']
    assert report['source_unchanged'], 'Source rig was modified during export'
    assert hashlib.sha256(SRC.read_bytes()).hexdigest() == report['output_sha256'], 'Candidate changed after gates'
    eal = unreal.EditorAssetLibrary
    asset_path = DESTINATION + '/' + ASSET_NAME
    report_out = {'source': str(SRC), 'destination': DESTINATION, 'asset': asset_path,
                  'import_action': 'existing_candidate_readback_only'}
    if not eal.does_asset_exist(asset_path):
        eal.make_directory(DESTINATION)
        options = unreal.FbxImportUI()
        options.set_editor_properties({'mesh_type_to_import': unreal.FBXImportType.FBXIT_SKELETAL_MESH,
            'automated_import_should_detect_type': False, 'import_mesh': True, 'import_as_skeletal': True,
            'import_animations': False, 'import_materials': False, 'import_textures': False,
            'import_rigid_mesh': True, 'create_physics_asset': False})
        data = options.get_editor_property('skeletal_mesh_import_data')
        data.set_editor_properties({'import_morph_targets': True, 'import_meshes_in_bone_hierarchy': True,
            'convert_scene': True, 'convert_scene_unit': True, 'import_uniform_scale': 1.0,
            'update_skeleton_reference_pose': False, 'use_t0_as_ref_pose': False})
        task = unreal.AssetImportTask()
        task.set_editor_properties({'filename': str(SRC), 'destination_path': DESTINATION,
            'destination_name': ASSET_NAME, 'automated': True, 'replace_existing': False,
            'save': True, 'options': options})
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        report_out['import_action'] = 'new_brow_patch_candidate'
    mesh = unreal.load_asset(asset_path)
    assert mesh is not None, 'Imported mesh missing'
    slots = [str(m.get_editor_property('material_slot_name')) for m in mesh.get_editor_property('materials')]
    morphs = [str(m) for m in mesh.get_all_morph_target_names()]
    v01 = unreal.load_asset(V01)
    v01_joints = v01.get_editor_property('skeleton')
    joints_new = mesh.get_editor_property('skeleton')
    report_out.update({'slot_names': slots, 'slot_count': len(slots), 'morphs': morphs,
        'skeleton': joints_new.get_path_name(),
        'v01_skeleton': v01_joints.get_path_name(),
        'slot_gate': len(slots) == 13,
        'morph_gate': morphs == ['Blink_L', 'Blink_R']})
    report_out['import_structure_gate'] = report_out['slot_gate'] and report_out['morph_gate']
    report_out['proof'] = 'UE saved import readback; material binding is a separate gated action'
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'ue_import_sam_brow_v02.json').write_text(json.dumps(report_out, indent=2), encoding='utf-8')
    print(json.dumps({k: report_out[k] for k in ('import_action', 'slot_count', 'slot_gate', 'morph_gate', 'skeleton')}))
    assert report_out['import_structure_gate'], 'Imported structure differs from candidate gate'


def ensure_browpatch_mi():
    eal = unreal.EditorAssetLibrary
    me = unreal.MaterialEditingLibrary
    mi_path = NEW_MI + '/MI_Film304_Sam_BrowPatch_Toon'
    if not eal.does_asset_exist(mi_path):
        mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset('MI_Film304_Sam_BrowPatch_Toon', NEW_MI,
            unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        me.set_material_instance_parent(mi, unreal.load_asset(PARENT))
        me.set_material_instance_vector_parameter_value(mi, 'BaseTint', unreal.LinearColor(0.085, 0.055, 0.042, 1.0))
        for parameter, value in {'TextureWeight': 0.0, 'Roughness': 0.85, 'RimIntensity': 0.0,
            'PaletteRampStrength': 0.0, 'BoilIntensity': 0.0, 'SmearStrength': 0.0, 'TemporalStrength': 0.0,
            'FilmGradeShadowLift': 0.0, 'Iridescence': 0.0, 'OpacityStrength': 1.0}.items():
            me.set_material_instance_scalar_parameter_value(mi, parameter, value)
        me.update_material_instance(mi)
        eal.save_loaded_asset(mi, only_if_is_dirty=False)
    return unreal.load_asset(mi_path).get_path_name()


def main_bind():
    eal = unreal.EditorAssetLibrary
    mesh_path = DESTINATION + '/' + ASSET_NAME
    mesh = unreal.load_asset(mesh_path)
    assert mesh, 'v02 mesh missing; run import first'
    v01_names = {}
    v01 = unreal.load_asset(V01)
    for m in v01.get_editor_property('materials'):
        name = str(m.get_editor_property('material_slot_name')).lower()
        v01_names[name] = m.get_editor_property('material_interface')
    brow_mi_path = ensure_browpatch_mi()
    slots = list(mesh.get_editor_property('materials'))
    assignment = []
    for slot in slots:
        name = str(slot.get_editor_property('material_slot_name'))
        key = name.lower()
        if 'browpatch' in key:
            material = unreal.load_asset(brow_mi_path)
        else:
            mirror = v01_names.get(key)
            assert mirror is not None, 'No v01 binding to mirror for slot ' + name
            material = mirror
        slot.set_editor_property('material_interface', material)
        assignment.append({'slot': name, 'material': material.get_path_name()})
    mesh.set_editor_property('materials', slots)
    eal.save_loaded_asset(mesh, only_if_is_dirty=False)
    readback = unreal.load_asset(mesh_path).get_editor_property('materials')
    for actual, wanted in zip(readback, assignment):
        assert actual.get_editor_property('material_interface').get_path_name() == wanted['material']
    report = {'mesh': mesh_path, 'slots': assignment, 'binding_gate': True,
        'brow_patch_material': brow_mi_path}
    (OUT / 'ue_bind_sam_brow_v02.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'slots': len(assignment), 'binding_gate': True}))


if __name__ == '__main__':
    action = (REQUEST.read_text().strip().lower() if REQUEST.exists() else 'import')
    if action == 'import':
        main_import()
    elif action == 'bind':
        main_bind()
    else:
        raise RuntimeError('Unknown brow action: ' + action)
