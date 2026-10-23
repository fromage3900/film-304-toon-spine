"""Compressed-frame seam/contact and expression checks for the facial variants."""
import json
import math
from pathlib import Path
import unreal

OUT=Path(unreal.Paths.project_dir())/'Saved/Audit/Film304Idle_20261017'
AP=unreal.AnimPoseExtensions

def xyz(v):return [v.x,v.y,v.z]
def dist(a,b):return sum((x-y)**2 for x,y in zip(xyz(a),xyz(b)))**.5
def main():
    variants=json.loads((OUT/'facial_sleep_variants.json').read_text());base=json.loads((OUT/'scene_idle_build.json').read_text());result={}
    for ch,row in variants.items():
        seq=unreal.load_asset(row['animation']);mesh=unreal.load_asset(base['characters'][ch]['mesh'])
        o=unreal.AnimPoseEvaluationOptions();o.set_editor_properties({'should_retarget':False,'optional_skeletal_mesh':mesh,'evaluation_type':unreal.AnimDataEvalType.COMPRESSED,'evaluate_curves':True})
        poses=[AP.get_anim_pose_at_time(seq,i/24,o) for i in range(49)]
        seam=0;rot=0;feet=0;finite=True
        for n in AP.get_bone_names(poses[0]):
            local=[AP.get_bone_pose(p,n,unreal.AnimPoseSpaces.LOCAL) for p in poses]
            seam=max(seam,dist(local[0].translation,local[-1].translation))
            a=local[0].rotation;b=local[-1].rotation
            rot=max(rot,math.degrees(2*math.acos(min(1,abs(a.x*b.x+a.y*b.y+a.z*b.z+a.w*b.w)))))
            finite &= all(math.isfinite(v) for t in local for v in xyz(t.translation)+xyz(t.scale3d)+[t.rotation.x,t.rotation.y,t.rotation.z,t.rotation.w])
            if str(n) in ['Ankle_L','Ankle_R','Toes_L','Toes_R']:
                world=[AP.get_bone_pose(p,n,unreal.AnimPoseSpaces.WORLD).translation for p in poses]
                feet=max(feet,max(dist(world[0],v) for v in world))
        curves={}
        for name in ['Blink_L','Blink_R']+(['Smile','Brow_Up'] if ch=='Dana' else []):
            values=[AP.get_curve_weight(p,name) for p in poses]
            curves[name]={'min':min(values),'max':max(values),'seam':abs(values[0]-values[-1])}
        gate=finite and seam<.005 and rot<.1 and feet<.01 and all(v['seam']<1e-5 for v in curves.values())
        result[ch]={'animation':row['animation'],'samples':49,'seconds':seq.get_play_length(),
            'compressed_seam_cm':seam,'compressed_seam_degrees':rot,'foot_drift_cm':feet,'curves':curves,'numeric_gate':gate}
    (OUT/'sleep_faces_evaluation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
    assert all(r['numeric_gate'] for r in result.values())

if __name__=='__main__':main()
