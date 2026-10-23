"""Use native UE IK retargeting for the prepared periodic Melodia UAL donors."""
import json
from pathlib import Path
import unreal

BASE='/Game/Retarget/Film304Idle_20261017'
OUT=Path(unreal.Paths.project_dir())/'Saved/Audit/Film304Idle_20261017'

def main():
    tools=unreal.AssetToolsHelpers.get_asset_tools()
    donor_mesh=unreal.load_asset(BASE+'/UALDonor/UAL_Idle_Loop_48f')
    donor_idle=unreal.load_asset(BASE+'/UALDonor/UAL_Idle_Loop_48f_Anim')
    assert donor_mesh and donor_idle
    sit_path=BASE+'/UALDonor/UAL_Sitting_Idle_Loop_48f'
    if not unreal.EditorAssetLibrary.does_asset_exist(sit_path):
        task=unreal.AssetImportTask();task.filename=str(Path(unreal.Paths.project_dir())/'Saved/OfflineIntake/20261017/idle_donors/UAL_Sitting_Idle_Loop_48f.fbx')
        task.destination_path=BASE+'/UALDonor';task.destination_name='UAL_Sitting_Idle_Loop_48f'
        task.automated=True;task.save=True;task.replace_existing=False
        ui=unreal.FbxImportUI();ui.import_mesh=False;ui.import_animations=True;ui.skeleton=donor_mesh.skeleton
        ui.import_materials=False;ui.import_textures=False;ui.automated_import_should_detect_type=False
        ui.mesh_type_to_import=unreal.FBXImportType.FBXIT_ANIMATION
        task.options=ui;tools.import_asset_tasks([task])
        print('SITTING_IMPORT',list(task.imported_object_paths))
    sit=unreal.load_asset(sit_path);assert sit,sit_path
    rig=unreal.load_asset(BASE+'/IKR_UAL_FilmIdle_v01')
    existing=unreal.IKRigController.get_controller(unreal.load_asset('/Game/Retarget/IKRig_Sparrow'))
    chains=[]
    for row in existing.get_retarget_chains():
        name=str(row.chain_name)
        start=str(existing.get_retarget_chain_start_bone(name));end=str(existing.get_retarget_chain_end_bone(name))
        if name=='Neck':end='neck_01'
        chains.append((name,start,end))
    if not rig:
        rig=tools.create_asset('IKR_UAL_FilmIdle_v01',BASE,unreal.IKRigDefinition,unreal.IKRigDefinitionFactory())
        c=unreal.IKRigController.get_controller(rig);assert c.set_skeletal_mesh(donor_mesh)
        assert c.set_retarget_root('pelvis')
        for name,start,end in chains:assert str(c.add_retarget_chain(name,start,end,''))==name
        assert unreal.EditorAssetLibrary.save_loaded_asset(rig)
    report={}
    for character in ['Dana','David','Sam']:
        target_rig=unreal.load_asset(BASE+'/IKR_'+character+'_FilmIdle_v01')
        target=unreal.IKRigController.get_controller(target_rig).get_skeletal_mesh()
        name='RTG_UALTo'+character+'_FilmIdle_v01'
        rtg=unreal.load_asset(BASE+'/'+name)
        if not rtg:
            rtg=tools.create_asset(name,BASE,unreal.IKRetargeter,unreal.IKRetargetFactory())
            c=unreal.IKRetargeterController.get_controller(rtg)
            c.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE,rig)
            c.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET,target_rig);c.add_default_ops()
            for chain,_,_ in chains:assert c.set_source_chain(chain,chain)
            assert unreal.EditorAssetLibrary.save_loaded_asset(rtg)
        donor=sit if character=='David' else donor_idle
        destination=BASE+'/RawRetarget/'+character
        results=unreal.IKRetargetBatchOperation.duplicate_and_retarget(
            [unreal.EditorAssetLibrary.find_asset_data(donor.get_path_name())],donor_mesh,target,rtg,
            prefix=character+'_',target_path=destination,include_referenced_assets=False,overwrite_existing_files=False)
        paths=[str(a.package_name) for a in results];assert paths,(character,'No retarget output')
        for path in paths:assert unreal.EditorAssetLibrary.save_asset(path)
        report[character]={'retargeter':rtg.get_path_name(),'donor':donor.get_path_name(),'outputs':paths,'visual_gate':False}
    (OUT/'ual_retarget.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))

if __name__=='__main__':main()
