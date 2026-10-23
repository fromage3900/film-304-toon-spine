"""Import one independently checked cast candidate into a new staging directory.
Does not replace old meshes, assign scene actors, save maps or submit renders.
"""
import hashlib
import json
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()); OUT=ROOT/'Saved/Audit/EveningExecution_20261017'
REQUEST=OUT/'cast_import_request.json'
CANDIDATES={
 'David':('Saved/OfflineIntake/20261017/clean_cast/David/David_CleanFilm_UE_v01.fbx',11,2),
 'Sam':('Saved/OfflineIntake/20261017/clean_cast/Sam/Sam_CleanFilm_UE_v01.fbx',12,2),
 'Dana':('Saved/OfflineIntake/20261017/task1_face_eyes/fbx/Dana_CleanSkin_v09.fbx',12,8)}

def main():
    if unreal.Paths.project_dir().replace('\\','/').rstrip('/').lower()!='g:/film-304-toon-spine':
        raise RuntimeError('Wrong project')
    if unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).is_rendering():
        raise RuntimeError('Render active: import deferred')
    request=json.loads(REQUEST.read_text())
    character=request['character']
    relative,expected_slots,expected_morphs=CANDIDATES[character]
    source=ROOT/relative; destination='/Game/Staging/Film304Repaired_20261017/'+character
    version=request.get('version','v01')
    if version=='v10e' and character=='Dana':
        relative='Saved/OfflineIntake/20261017/task1_face_eyes/fbx/Dana_CleanSkin_v10e_InputConnections.fbx'
        source=ROOT/relative
        assert hashlib.sha256(source.read_bytes()).hexdigest()=='4c565521f080f21bf0b5346fe36b950497936175f5442291cf2eb6f5d2009baf', 'Dana gated candidate changed'
        check=json.loads((ROOT/'Saved/OfflineIntake/20261017/task1_face_eyes/report/v10e_face_follow_readback.json').read_text())
        assert check['gate_pass'], 'Dana native deformation gate failed'
    elif version!='v01':
        raise RuntimeError('Unapproved candidate version')
    asset_name='SK_'+character+'_Film304_'+version; asset_path=destination+'/'+asset_name
    eal=unreal.EditorAssetLibrary
    report={'character':character,'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'destination':destination,'expected_slots':expected_slots,'expected_morph_count':expected_morphs,
        'scene_modified':False}
    if eal.does_asset_exist(asset_path):
        imported=[asset_path]; report['import_action']='existing_candidate_readback_only'
    else:
        if character in ['David','Sam']:
            check=json.loads((source.parent/'consolidated_readback.json').read_text())
            assert check['status']=='fresh_process_readback_passed_pending_ue'
            assert check['source_sha256']==report['source_sha256'],'Candidate changed after gate'
        options=unreal.FbxImportUI()
        options.set_editor_properties({'mesh_type_to_import':unreal.FBXImportType.FBXIT_SKELETAL_MESH,
            'automated_import_should_detect_type':False,'import_mesh':True,'import_as_skeletal':True,
            'import_animations':False,'import_materials':False,'import_textures':False,
            'import_rigid_mesh':True,'create_physics_asset':False})
        data=options.get_editor_property('skeletal_mesh_import_data')
        data.set_editor_properties({'import_morph_targets':True,'import_meshes_in_bone_hierarchy':True,
            'convert_scene':True,'convert_scene_unit':True,'import_uniform_scale':1.0,
            'update_skeleton_reference_pose':False,'use_t0_as_ref_pose':False})
        task=unreal.AssetImportTask()
        task.set_editor_properties({'filename':str(source),'destination_path':destination,
            'destination_name':asset_name,'automated':True,'replace_existing':False,
            'save':True,'options':options})
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        imported=[str(p).split('.')[0] for p in task.get_editor_property('imported_object_paths')]
        report['import_action']='new_derived_candidate'
    report['imported_paths']=imported; meshes=[]
    for path in imported:
        asset=unreal.load_asset(path)
        if not isinstance(asset,unreal.SkeletalMesh):continue
        bounds=asset.get_imported_bounds()
        slots=[str(m.get_editor_property('material_slot_name')) for m in asset.get_editor_property('materials')]
        morphs=[str(m) for m in asset.get_all_morph_target_names()]
        meshes.append({'path':asset.get_path_name(),'slots':slots,'morphs':morphs,
            'bounds_origin':[bounds.origin.x,bounds.origin.y,bounds.origin.z],
            'bounds_extent':[bounds.box_extent.x,bounds.box_extent.y,bounds.box_extent.z],
            'height_cm':bounds.box_extent.z*2,'skeleton':asset.get_editor_property('skeleton').get_path_name(),
            'slot_gate':len(slots)==expected_slots,'morph_gate':len(morphs)==expected_morphs})
    report['skeletal_meshes']=meshes
    report['import_structure_gate']=len(meshes)==1 and all(m['slot_gate'] and m['morph_gate'] for m in meshes)
    report['proof']='UE saved import readback; material binding, deformation and visual gates remain separate'
    suffix='' if version=='v01' else '_'+version
    (OUT/('ue_import_'+character.lower()+suffix+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    if not report['import_structure_gate']:raise RuntimeError('Imported structure differs from candidate gate; inspect report')

if __name__=='__main__':main()
