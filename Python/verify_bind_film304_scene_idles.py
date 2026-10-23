"""Evaluate every stored idle frame, then bind only passing clips in the open map."""
import json
import math
import shutil
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir());OUT=ROOT/'Saved/Audit/Film304Idle_20261017'
AP=unreal.AnimPoseExtensions

def vec(v):return [v.x,v.y,v.z]
def distance(a,b):return sum((x-y)**2 for x,y in zip(vec(a),vec(b)))**.5
def angle(a,b):
    dot=abs(a.x*b.x+a.y*b.y+a.z*b.z+a.w*b.w)
    return math.degrees(2*math.acos(min(1,max(-1,dot))))

def main(bind=False):
    report=json.loads((OUT/'scene_idle_build.json').read_text())
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    by_path={a.get_path_name():a for a in actors}
    rows={}
    for char,entry in report['characters'].items():
        mesh=unreal.load_asset(entry['mesh']);seq=unreal.load_asset(entry['animation'])
        opt=unreal.AnimPoseEvaluationOptions();opt.set_editor_properties({'should_retarget':False,'extract_root_motion':False,'optional_skeletal_mesh':mesh,'evaluate_curves':True,'evaluation_type':unreal.AnimDataEvalType.COMPRESSED})
        poses=[AP.get_anim_pose_at_time(seq,i/24,opt) for i in range(49)]
        names=[str(n) for n in AP.get_bone_names(poses[0])]
        seam_pos=0;seam_rot=0;motion=0;feet=0;wrist=0;finite=True
        for n in names:
            local=[AP.get_bone_pose(p,n,unreal.AnimPoseSpaces.LOCAL) for p in poses]
            finite &= all(math.isfinite(v) for t in local for v in vec(t.translation)+vec(t.scale3d)+[t.rotation.x,t.rotation.y,t.rotation.z,t.rotation.w])
            seam_pos=max(seam_pos,distance(local[0].translation,local[-1].translation))
            seam_rot=max(seam_rot,angle(local[0].rotation,local[-1].rotation))
            if n in ['Head_M','wolfSpider_Head']:
                motion=max(angle(local[0].rotation,t.rotation) for t in local)
            is_foot=n in ['Ankle_L','Ankle_R','Toes_L','Toes_R'] or (n.startswith('wolfSpider_Leg') and n.endswith('_tip'))
            is_wrist=n in ['Wrist_L','Wrist_R']
            if is_foot or is_wrist:
                world=[AP.get_bone_pose(p,n,unreal.AnimPoseSpaces.WORLD).translation for p in poses]
                drift=max(distance(world[0],v) for v in world)
                if is_foot:feet=max(feet,drift)
                if is_wrist:wrist=max(wrist,drift)
        blink=max([AP.get_curve_weight(p,'Blink_L') for p in poses]) if char!='Spider' else None
        gate=finite and seam_pos<0.005 and seam_rot<0.1 and feet<0.01 and motion>0.01 and abs(seq.get_play_length()-2)<0.001
        rows[char]={'animation':seq.get_path_name(),'duration_seconds':seq.get_play_length(),
            'samples_evaluated':49,'bones_evaluated':len(names),'finite':finite,
            'seam_position_cm':seam_pos,'seam_rotation_deg':seam_rot,
            'head_motion_degrees':motion,'max_foot_drift_cm':feet,'max_wrist_drift_cm':wrist,
            'blink_peak':blink,'numeric_gate':gate}
    (OUT/'scene_idle_evaluation.json').write_text(json.dumps(rows,indent=2))
    print(json.dumps(rows))
    assert all(r['numeric_gate'] for r in rows.values()),'Numeric gate failed; no scene bindings changed'
    if not bind:return
    before=[]
    with unreal.ScopedEditorTransaction('Assign Film304 seamless cast idles'):
        for char,entry in report['characters'].items():
            seq=unreal.load_asset(entry['animation'])
            for index,path in enumerate(entry['actors']):
                actor=by_path[path];comp=actor.get_component_by_class(unreal.SkeletalMeshComponent)
                assert comp.get_skinned_asset().get_path_name()==entry['mesh']
                old=comp.get_editor_property('animation_data')
                before.append({'actor':path,'animation':old.anim_to_play.get_path_name() if old.anim_to_play else None,'mode':str(comp.animation_mode)})
                comp.modify();actor.modify()
                comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
                comp.set_editor_property('animation_data',unreal.SingleAnimationPlayData(anim_to_play=seq,saved_looping=True,saved_playing=True,saved_position=(index*0.43)%2,saved_play_rate=1))
                comp.set_animation(seq);comp.play(True);comp.set_update_animation_in_editor(True)
                comp.set_position((index*0.43)%2,False)
    (OUT/'scene_bindings_before.json').write_text(json.dumps(before,indent=2))
    report['assigned']=True;report['numeric_gate']=True;report['map_saved']=False
    (OUT/'scene_idle_build.json').write_text(json.dumps(report,indent=2))
    print('BOUND',len(before),'skeletal actors; scene save and visual inspection pending')

if __name__=='__main__':main()
