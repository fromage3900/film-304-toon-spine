"""Evaluate imported held poses against their own reference pose, without actors."""
import json
import math
from pathlib import Path
import unreal

OUT=Path(unreal.Paths.project_dir())/'Saved/Audit/EveningExecution_20261017'
AP=unreal.AnimPoseExtensions

def xyz(v):return [v.x,v.y,v.z]
def distance(a,b):return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
def values(t):
    q=t.rotation
    return xyz(t.translation)+[q.x,q.y,q.z,q.w]+xyz(t.scale3d)

def main():
    rows=[]
    for character in ['David','Sam']:
        base='/Game/Staging/Film304Repaired_20261017/'+character
        asset=unreal.load_asset(base+'/Poses/AS_'+character+'_HeldPose_v02');assert asset
        options=unreal.AnimPoseEvaluationOptions()
        options.set_editor_properties({'should_retarget':False,'extract_root_motion':False,
            'optional_skeletal_mesh':unreal.load_asset(base+'/SK_'+character+'_Film304_v01')})
        start=AP.get_anim_pose_at_time(asset,0,options)
        end=AP.get_anim_pose_at_time(asset,asset.get_play_length(),options)
        names=[str(n) for n in AP.get_bone_names(start)]
        endpoint_error=0.0
        for name in names:
            a=values(AP.get_bone_pose(start,name,unreal.AnimPoseSpaces.LOCAL))
            b=values(AP.get_bone_pose(end,name,unreal.AnimPoseSpaces.LOCAL))
            if sum(x*y for x,y in zip(a[3:7],b[3:7]))<0:b[3:7]=[-x for x in b[3:7]]
            endpoint_error=max(endpoint_error,max(abs(x-y) for x,y in zip(a,b)))
        wrists={};feet={}
        for name in ['Wrist_L','Wrist_R']:
            assert name in names
            actual=xyz(AP.get_bone_pose(start,name,unreal.AnimPoseSpaces.WORLD).translation)
            ref=xyz(AP.get_ref_bone_pose(start,name,unreal.AnimPoseSpaces.WORLD).translation)
            wrists[name]={'posed_cm':actual,'reference_cm':ref,'drop_cm':ref[2]-actual[2]}
        for name in names:
            if any(token in name.lower() for token in ['ankle','toe','heel']):
                actual=xyz(AP.get_bone_pose(start,name,unreal.AnimPoseSpaces.WORLD).translation)
                ref=xyz(AP.get_ref_bone_pose(start,name,unreal.AnimPoseSpaces.WORLD).translation)
                feet[name]=distance(actual,ref)
        gate=endpoint_error<1e-3 and len(feet)>0 and max(feet.values())<0.05 and all(r['drop_cm']>10 for r in wrists.values())
        rows.append({'character':character,'asset':asset.get_path_name(),'bones_evaluated':len(names),
            'all_bone_local_endpoint_max_error':endpoint_error,'wrists':wrists,
            'foot_bone_reference_delta_cm':feet,'evaluated_pose_gate':gate,'visual_gate':False})
    report={'characters':rows,'scene_modified':False,'proof':'UE animation evaluation; silhouette, clipping and world grounding require owner frame'}
    (OUT/'ue_held_pose_evaluation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2));assert all(r['evaluated_pose_gate'] for r in rows)

if __name__=='__main__':main()
