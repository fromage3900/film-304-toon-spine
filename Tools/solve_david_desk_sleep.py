"""Fit a sleeping pose to the measured existing desk without changing the rig."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as R

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Saved/Audit/Film304Idle_20261017'
data=json.loads((OUT/'david_sleep_pose_input.json').read_text())
bones=data['bones'];names=list(bones);index={n:i for i,n in enumerate(names)}
parents=[index.get(bones[n]['parent'],-1) for n in names]
base=[]
for n in names:
    t=bones[n]['local'];m=np.eye(4);m[:3,:3]=R.from_quat(t['rotation']).as_matrix()@np.diag(t['scale']);m[:3,3]=t['position'];base.append(m)
a=data['actor'];actor=np.eye(4);actor[:3,:3]=R.from_quat(a['rotation']).as_matrix()@np.diag(a['scale']);actor[:3,3]=a['position']
controls=['Spine1_M','Spine2_M','Chest_M','Neck_M','Head_M','Shoulder_L','Elbow_L','Wrist_L','Shoulder_R','Elbow_R','Wrist_R']
control_index={index[n]:i for i,n in enumerate(controls)}

def fk(x):
    worlds=[];locals_=[]
    for i,m in enumerate(base):
        local=m.copy()
        if i in control_index:
            j=control_index[i];local[:3,:3]=local[:3,:3]@R.from_rotvec(x[j*3:j*3+3]).as_matrix()
        worlds.append((worlds[parents[i]] if parents[i]>=0 else actor)@local);locals_.append(local)
    return worlds,locals_

initial=np.zeros(len(controls)*3)
original,_=fk(initial)
# Desk top is z=53.8006. Arms sit above it, head rests on the left hand/forearm.
targets={'Head_M':[-148,-78,64],'Elbow_L':[-162,-66,57.5],
         'Wrist_L':[-153.5,-79,58.3],'Elbow_R':[-125,-69,57.5],'Wrist_R':[-141.5,-78,59.0]}
base_head=R.from_matrix(original[index['Head_M']][:3,:3]/np.linalg.norm(original[index['Head_M']][:3,:3],axis=0))
axis=R.from_quat(a['rotation']).apply([1,0,0])
desired_head=R.from_rotvec(axis*np.deg2rad(-78))*base_head

def residual(x):
    world,_=fk(x);res=[]
    for n,target in targets.items():res.extend((world[index[n]][:3,3]-target)*(2 if n=='Head_M' else 1))
    h=world[index['Head_M']][:3,:3];h=h/np.linalg.norm(h,axis=0)
    res.extend((desired_head.inv()*R.from_matrix(h)).as_rotvec()*8)
    res.extend(x*.35)
    return res

solution=least_squares(residual,initial,max_nfev=250,ftol=1e-9,xtol=1e-9,gtol=1e-9,bounds=(-2.6,2.6))
world,local=fk(solution.x)
result={'success':bool(solution.success),'cost':solution.cost,'iterations':solution.nfev,
        'desk_top_cm':53.800625,'targets':targets,'actual':{},'bone_rotations':{}}
for n in targets:result['actual'][n]=world[index[n]][:3,3].tolist()
for n in controls:
    m=local[index[n]][:3,:3];m=m/np.linalg.norm(m,axis=0)
    result['bone_rotations'][n]=R.from_matrix(m).as_quat().tolist()
for side,direction in [('L',[0,-1,.08]),('R',[0,-1,.08])]:
    wrist='Wrist_'+side
    fingertip='MiddleFinger3_'+side
    forward=world[index[fingertip]][:3,3]-world[index[wrist]][:3,3]
    width=world[index['IndexFinger1_'+side]][:3,3]-world[index['PinkyFinger1_'+side]][:3,3]
    normal=np.cross(width,forward)*(-1 if side=='L' else 1);normal/=np.linalg.norm(normal)
    desired_normal=np.array([1,0,0]) if side=='L' else np.array([-1,0,0])
    delta,_=R.align_vectors([np.array(direction)/np.linalg.norm(direction),desired_normal],[forward/np.linalg.norm(forward),normal])
    wm=world[index[wrist]][:3,:3];wm=wm/np.linalg.norm(wm,axis=0)
    parent=world[parents[index[wrist]]][:3,:3];parent=parent/np.linalg.norm(parent,axis=0)
    result['bone_rotations'][wrist]=(R.from_matrix(parent).inv()*delta*R.from_matrix(wm)).as_quat().tolist()
# Relax the fingers around the skull rather than leaving a flat, open hand.
for n,q in result['bone_rotations'].items():
    i=index[n];base[i][:3,:3]=R.from_quat(q).as_matrix()@np.diag(bones[n]['local']['scale'])
for side,inward in [('L',np.array([1.,0,0])),('R',np.array([-1.,0,0]))]:
    for finger in ['Index','Middle','Ring','Pinky']:
        for segment,degrees in [(2,12),(3,8)]:
            world,_=fk(initial)
            n=finger+'Finger'+str(segment)+'_'+side;i=index[n]
            end=finger+'Finger3_'+side
            if segment==3:
                direction=world[i][:3,:3]@np.array([1.,0,0])
            else:direction=world[index[end]][:3,3]-world[i][:3,3]
            direction/=np.linalg.norm(direction)
            axis=np.cross(direction,inward)
            if np.linalg.norm(axis)<1e-6:continue
            axis/=np.linalg.norm(axis)
            wm=world[i][:3,:3];wm=wm/np.linalg.norm(wm,axis=0)
            pm=world[parents[i]][:3,:3];pm=pm/np.linalg.norm(pm,axis=0)
            q=(R.from_matrix(pm).inv()*R.from_rotvec(axis*np.deg2rad(degrees))*R.from_matrix(wm)).as_quat()
            result['bone_rotations'][n]=q.tolist()
            base[i][:3,:3]=R.from_quat(q).as_matrix()@np.diag(bones[n]['local']['scale'])
result['max_target_error_cm']=max(np.linalg.norm(np.array(result['actual'][n])-targets[n]) for n in targets)
assert result['max_target_error_cm']<2.5,result
(OUT/'david_sleep_pose_solution.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
