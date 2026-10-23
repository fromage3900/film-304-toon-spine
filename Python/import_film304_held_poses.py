"""Import verified held animations onto existing repaired skeletons, assets only."""
import hashlib
import json
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()); OUT=ROOT/'Saved/Audit/EveningExecution_20261017'

def main():
    assert unreal.Paths.project_dir().replace('\\','/').rstrip('/').lower()=='g:/film-304-toon-spine'
    assert not unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).is_rendering()
    character=json.loads((OUT/'held_pose_import_request.json').read_text())['character']
    assert character in ['David','Sam']
    folder=ROOT/'Saved/OfflineIntake/20261017/clean_cast'/character
    check=json.loads((folder/'held_pose_v02_report.json').read_text())
    assert check['status']=='offline_held_pose_candidate_built_and_fresh_reimport_verified_pending_visual_review_and_ue_import'
    source=folder/(character+'_HeldPose_v02_24fps.fbx');assert source.is_file()
    skeleton_path='/Game/Staging/Film304Repaired_20261017/'+character+'/SK_'+character+'_Film304_v01_Skeleton'
    skeleton=unreal.load_asset(skeleton_path);assert skeleton
    dest='/Game/Staging/Film304Repaired_20261017/'+character+'/Poses'
    name='AS_'+character+'_HeldPose_v02';path=dest+'/'+name
    eal=unreal.EditorAssetLibrary
    if not eal.does_asset_exist(path):
        options=unreal.FbxImportUI()
        options.set_editor_properties({'mesh_type_to_import':unreal.FBXImportType.FBXIT_ANIMATION,
            'automated_import_should_detect_type':False,'import_mesh':False,'import_as_skeletal':True,
            'import_animations':True,'import_materials':False,'import_textures':False,
            'skeleton':skeleton,'create_physics_asset':False})
        data=options.get_editor_property('anim_sequence_import_data')
        data.set_editor_properties({'animation_length':unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME,
            'use_default_sample_rate':False,'custom_sample_rate':24,
            'import_custom_attribute':False,'import_bone_tracks':True,
            'convert_scene':True,'convert_scene_unit':True})
        task=unreal.AssetImportTask()
        task.set_editor_properties({'filename':str(source),'destination_path':dest,'destination_name':name,
            'automated':True,'replace_existing':False,'save':True,'options':options})
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        imported=[str(p).split('.')[0] for p in task.get_editor_property('imported_object_paths')]
    else:imported=[path]
    rows=[]
    for imported_path in imported:
        asset=unreal.load_asset(imported_path)
        if not isinstance(asset,unreal.AnimSequence):continue
        rows.append({'path':asset.get_path_name(),'skeleton':asset.get_editor_property('skeleton').get_path_name(),
            'duration':asset.get_play_length(),'frame_intervals':unreal.AnimationLibrary.get_num_frames(asset),
            'sample_keys':unreal.AnimationLibrary.get_num_keys(asset)})
    report={'character':character,'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'animations':rows,'scene_modified':False,'proof':'saved animation import; sampled pose verification and visual review pending'}
    report['import_structure_gate']=len(rows)==1 and rows[0]['skeleton']==skeleton.get_path_name() and rows[0]['sample_keys']==2 and abs(rows[0]['duration']-1/24)<1e-6
    (OUT/('ue_held_pose_'+character.lower()+'.json')).write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2));assert report['import_structure_gate']

if __name__=='__main__':main()
