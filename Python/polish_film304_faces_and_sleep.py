"""Author the approved sleeping David beat and restrained facial idle variants."""
import json
import math
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir());OUT=ROOT/'Saved/Audit/Film304Idle_20261017'
AP=unreal.AnimPoseExtensions;LIB=unreal.AnimationLibrary
DEST='/Game/Animations/Film304Idle_20261017'

def curve(seq,mesh,name,values):
    if LIB.does_curve_exist(seq,name,unreal.RawCurveTrackTypes.RCT_FLOAT):LIB.remove_curve(seq,name)
    LIB.add_curve(seq,name)
    LIB.add_float_curve_keys(seq,name,[i/24 for i in range(49)],values)
    LIB.add_curve_meta_data(mesh.skeleton,name);LIB.set_curve_meta_data_morph_target(mesh.skeleton,name,True)

def main():
    receipt=json.loads((OUT/'scene_idle_build.json').read_text())
    solved=json.loads((OUT/'david_sleep_pose_solution.json').read_text())
    assert solved['max_target_error_cm']<2.5
    tools=unreal.AssetToolsHelpers.get_asset_tools();results={}
    for char in ['Dana','David','Sam']:
        entry=receipt['characters'][char];source=unreal.load_asset(entry['animation']);mesh=unreal.load_asset(entry['mesh'])
        name='AS_'+char+('_DeskSleep_48f_v02' if char=='David' else '_OfficeFaceIdle_48f_v02')
        assert not unreal.EditorAssetLibrary.does_asset_exist(DEST+'/'+name)
        seq=tools.duplicate_asset(name,DEST,source);assert seq
        ctrl=seq.controller
        opt=unreal.AnimPoseEvaluationOptions();opt.optional_skeletal_mesh=mesh;opt.should_retarget=False
        poses=[AP.get_anim_pose_at_time(source,i/24,opt) for i in range(49)]
        if char=='David':
            ctrl.open_bracket('Sleeping desk contact pose',False)
            for bone,q in solved['bone_rotations'].items():
                t=AP.get_bone_pose(poses[0],bone,unreal.AnimPoseSpaces.LOCAL)
                assert ctrl.set_bone_track_keys(bone,[t.translation]*49,[unreal.Quat(*q)]*49,[t.scale3d]*49,False)
            ctrl.close_bracket(False)
            for side in ['L','R']:curve(seq,mesh,'Blink_'+side,[1.0]*49)
        else:
            peak=33 if char=='Dana' else 20
            for side,delay in [('L',0),('R',0.35)]:
                values=[]
                for i in range(49):
                    d=i-peak-delay
                    # Fast close, short hold, slower opening; exact full closure sample.
                    if -2<=d<0:v=0.5-0.5*math.cos(math.pi*(d+2)/2)
                    elif 0<=d<=0.7:v=1
                    elif 0.7<d<4:v=0.5+0.5*math.cos(math.pi*(d-0.7)/3.3)
                    else:v=0
                    values.append(v)
                curve(seq,mesh,'Blink_'+side,values)
        if char=='Dana':
            curve(seq,mesh,'Smile',[0.07+0.07*(.5-.5*math.cos(2*math.pi*i/48)) for i in range(49)])
            curve(seq,mesh,'Brow_Up',[0.03+0.12*(.5-.5*math.cos(2*math.pi*i/48)) for i in range(49)])
        if char=='Sam':
            modifier=unreal.SkeletonModifier();modifier.set_skeletal_mesh(mesh)
            ctrl.open_bracket('Subtle asymmetric skeptical brow',False)
            for bone,amount in [('browInnerJoint_L',0.10),('browHalfJoint_L',0.08),('browOuterJoint_L',0.04),('browInnerJoint_R',-0.025)]:
                parent=str(modifier.get_parent_name(bone));positions=[];rotations=[];scales=[]
                for i,p in enumerate(poses):
                    t=AP.get_bone_pose(p,bone,unreal.AnimPoseSpaces.LOCAL)
                    parent_t=AP.get_bone_pose(p,parent,unreal.AnimPoseSpaces.WORLD)
                    weight=.5-.5*math.cos(2*math.pi*i/48)
                    delta=parent_t.inverse_transform_location(unreal.Vector(0,0,amount*weight))-parent_t.inverse_transform_location(unreal.Vector(0,0,0))
                    positions.append(t.translation+delta);rotations.append(t.rotation);scales.append(t.scale3d)
                assert ctrl.set_bone_track_keys(bone,positions,rotations,scales,False)
            ctrl.close_bracket(False)
        assert unreal.EditorAssetLibrary.save_loaded_asset(mesh.skeleton)
        assert unreal.EditorAssetLibrary.save_loaded_asset(seq)
        results[char]={'previous':entry['animation'],'animation':seq.get_path_name()}
    (OUT/'facial_sleep_variants.json').write_text(json.dumps(results,indent=2));print(json.dumps(results))

if __name__=='__main__':main()
