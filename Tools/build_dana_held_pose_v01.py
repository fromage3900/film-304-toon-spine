"""Offline Dana v10e relaxed held-pose candidate; opens source FBX and saves only derivatives."""
import datetime, hashlib, json, math, traceback
from pathlib import Path
import maya.standalone
maya.standalone.initialize(name='python')
from maya import cmds, mel
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'Saved/OfflineIntake/20261017/task1_face_eyes/fbx/Dana_CleanSkin_v10e_InputConnections.fbx'
OUTDIR=ROOT/'Saved/OfflineIntake/20261017/task1_face_eyes/held_pose'
FBX=OUTDIR/'Dana_HeldPose_v05_24fps.fbx'
SCENE=OUTDIR/'Dana_HeldPose_Candidate_v05.mb'
REPORT=OUTDIR/'Dana_HeldPose_v05_build_report.json'
ATTRS=['tx','ty','tz','rx','ry','rz','sx','sy','sz']
report={'tool':'build_dana_held_pose_v01.py','status':'starting','source':str(SOURCE),'source_saved':False,'at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
def save_report(): REPORT.write_text(json.dumps(report,indent=2,default=str),encoding='utf8')
def short(n): return n.rsplit('|',1)[-1].rsplit(':',1)[-1]
def unique(name):
 hits=[n for n in (cmds.ls(long=True) or []) if short(n)==name and cmds.nodeType(n)=='joint']
 if len(hits)!=1: raise RuntimeError('Joint resolution failed '+name+': '+repr(hits))
 return hits[0]
def v3(x): return om.MVector(float(x[0]),float(x[1]),float(x[2]))
def pos(n): return v3(cmds.xform(n,q=True,ws=True,t=True))
def q_world(n): return om.MTransformationMatrix(om.MMatrix(cmds.xform(n,q=True,ws=True,m=True))).rotation(asQuaternion=True)
def set_world_q(n,q):
 e=q.asEulerRotation(); cmds.xform(n,ws=True,rotation=(math.degrees(e.x),math.degrees(e.y),math.degrees(e.z)))
def vec(v): return [float(v.x),float(v.y),float(v.z)]
def mag(v): return float(v.length())
def dot(a,b): return float(a*b)
def to_list(m): return [float(x) for row in m for x in row] if isinstance(m[0],(list,tuple)) else [float(x) for x in m]
def shape_of(tf):
 sh=cmds.listRelatives(tf,shapes=True,noIntermediate=True,fullPath=True) or []
 return sh[0] if sh else None
def meshes_by_short():
 out={}
 for tf in cmds.ls(type='transform',long=True) or []:
  n=short(tf); sh=shape_of(tf)
  if not n.startswith('Dana_'): continue
  if sh and cmds.nodeType(sh)=='mesh' and not cmds.getAttr(sh+'.intermediateObject'): out.setdefault(n,[]).append((tf,sh))
 return {n:rows[0] for n,rows in out.items() if len(rows)==1}
def get_dag_path(node):
 s=om.MSelectionList();s.add(node);return s.getDagPath(0)
def skin_of(shape):
 h=cmds.listHistory(shape,pruneDagObjects=True) or []; skins=cmds.ls(h,type='skinCluster') or []
 if len(skins)!=1: raise RuntimeError('Expected one skinCluster for '+shape+', got '+repr(skins))
 return skins[0]
def matrix_from_attr(skin,attr,index):
 vals=cmds.getAttr('%s.%s[%d]'%(skin,attr,index))
 if isinstance(vals,(list,tuple)) and len(vals)==1 and isinstance(vals[0],(list,tuple)): vals=vals[0]
 return [float(x) for x in vals]
def get_skin_snapshot(meshes):
 data={}
 for name,(tf,shape) in meshes.items():
  skins=cmds.ls(cmds.listHistory(shape,pruneDagObjects=True) or [],type='skinCluster') or []
  if not skins: continue
  if len(skins)!=1: raise RuntimeError('Skin count '+name+' '+repr(skins))
  skin=skins[0];sel=om.MSelectionList();sel.add(skin);sf=oma.MFnSkinCluster(sel.getDependNode(0)); infs=sf.influenceObjects(); names=[short(x.fullPathName()) for x in infs]
  dp=get_dag_path(shape);fn=om.MFnMesh(dp);count=fn.numVertices
  comp=om.MFnSingleIndexedComponent();compid=comp.create(om.MFn.kMeshVertComponent);comp.addElements(list(range(count)))
  weights,ninf=sf.getWeights(dp,compid)
  sparse=[]
  for vi in range(count): sparse.append(sorted((names[j],round(float(weights[vi*ninf+j]),8)) for j in range(ninf) if float(weights[vi*ninf+j])>1e-9))
  bind={}
  for idx,n in enumerate(names): bind[n]=matrix_from_attr(skin,'bindPreMatrix',idx)
  data[name]={'vertices':count,'faces':cmds.polyEvaluate(shape,face=True),'weights':sparse,'bind_pre':bind}
 return data
def geometry_local(meshes):
 out={}
 for n,(tf,sh) in meshes.items():
  fn=om.MFnMesh(get_dag_path(sh));ps=fn.getPoints(om.MSpace.kObject)
  out[n]={'vertices':len(ps),'faces':cmds.polyEvaluate(sh,face=True),'points':[round(v,7) for p in ps for v in (p.x,p.y,p.z)]}
 return out
def shader_map(meshes):
 out={}
 for n,(tf,sh) in meshes.items():
  mats=set()
  for sg in cmds.listConnections(sh,type='shadingEngine') or []:
   for m in cmds.listConnections(sg+'.surfaceShader',source=True,destination=False) or []:mats.add(short(m))
  out[n]=sorted(mats)
 return out
def blendshape_info(body_shape):
 bs=cmds.ls(cmds.listHistory(body_shape,pruneDagObjects=True) or [],type='blendShape') or []
 if len(bs)!=1: raise RuntimeError('Expected one body blendShape, got '+repr(bs))
 aliases=cmds.aliasAttr(bs[0],q=True) or []; return bs[0],{aliases[i]:aliases[i+1] for i in range(0,len(aliases),2)}
def mesh_points_world(shape):
 vals=cmds.xform(shape+'.vtx[*]',q=True,ws=True,t=True); return [v3(vals[i:i+3]) for i in range(0,len(vals),3)]
def weighted_region(mesh_shape, skin, influence_names, threshold=.12):
 fn=om.MFnMesh(get_dag_path(mesh_shape));n=fn.numVertices
 sel=om.MSelectionList();sel.add(skin);sf=oma.MFnSkinCluster(sel.getDependNode(0));infs=sf.influenceObjects();names=[short(x.fullPathName()) for x in infs]
 comp=om.MFnSingleIndexedComponent();cid=comp.create(om.MFn.kMeshVertComponent);comp.addElements(list(range(n)));w,ninf=sf.getWeights(get_dag_path(mesh_shape),cid)
 relevant=[i for i,name in enumerate(names) if name in influence_names]
 points=mesh_points_world(mesh_shape)
 return [points[vi] for vi in range(n) if sum(float(w[vi*ninf+i]) for i in relevant)>=threshold]
def bounds(points):
 if not points: return None
 return {'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}
def all_mesh_bounds(meshes):
 return {name:bounds(mesh_points_world(sh)) for name,(tf,sh) in meshes.items()}
def rest_joint_signature(joints):
 return {short(j):{'parent':short((cmds.listRelatives(j,parent=True,fullPath=True) or [''])[0]) if cmds.listRelatives(j,parent=True,fullPath=True) else None,'jointOrient':[float(x) for x in cmds.getAttr(j+'.jointOrient')[0]],'segmentScaleCompensate':bool(cmds.getAttr(j+'.segmentScaleCompensate'))} for j in joints}
def motion_group_metrics(meshes):
 body=meshes['Dana_Body_GEO']; skin=skin_of(body[1]);sel=om.MSelectionList();sel.add(skin);sf=oma.MFnSkinCluster(sel.getDependNode(0));infs=sf.influenceObjects();names=[short(x.fullPathName()) for x in infs]
 def side_set(side): return {n for n in names if n.endswith('_'+side) and any(k in n.lower() for k in ['finger','wrist','thumb','index','middle','ring','pinky','hand'])}
 torso={n for n in names if any(k in n.lower() for k in ['spine','chest','root_m','rootpart','hip_','pelvis'])}
 output={}
 torso_pts=weighted_region(body[1],skin,torso)
 tb=bounds(torso_pts)
 for side in ('L','R'):
  hand_names=side_set(side)
  pts=weighted_region(body[1],skin,hand_names)
  hb=bounds(pts)
  if not pts: raise RuntimeError('No weighted hand vertices for '+side+'; groups='+repr(sorted(hand_names)))
  sign=1 if side=='L' else -1
  clearance=(hb['min'][0]-tb['max'][0]) if sign>0 else (tb['min'][0]-hb['max'][0])
  center=[sum(p[k] for p in pts)/len(pts) for k in range(3)]
  wrist=pos(unique('Wrist_'+side));hip=pos(unique('Hip_'+side))
  output[side]={'hand_weight_groups':sorted(hand_names),'hand_vertex_count':len(pts),'hand_world_bounds_cm':hb,'hand_center_world_cm':center,'torso_weight_groups':sorted(torso),'torso_vertex_count':len(torso_pts),'torso_world_bounds_cm':tb,'lateral_hand_to_torso_clearance_cm':clearance,'wrist_world_cm':vec(wrist),'hip_world_cm':vec(hip),'wrist_to_hip_distance_cm':mag(wrist-hip),'wrist_drop_from_shoulder_cm':float(pos(unique('Shoulder_'+side)).y-wrist.y)}
 return output
def apply_world_rotation(node,delta):
 before=om.MMatrix(cmds.xform(node,q=True,ws=True,m=True));pivot=om.MVector(before[12],before[13],before[14])
 t0=om.MTransformationMatrix();t0.setTranslation(-pivot,om.MSpace.kWorld)
 t1=om.MTransformationMatrix();t1.setTranslation(pivot,om.MSpace.kWorld)
 around=t0.asMatrix()*delta.asMatrix()*t1.asMatrix()
 cmds.xform(node,ws=True,m=list(before*around));cmds.dgdirty(allPlugs=True);cmds.currentTime(cmds.currentTime(q=True),e=True,update=True)
def solve_arm(side,target_xy):
 shoulder=unique('Shoulder_'+side);elbow=unique('Elbow_'+side);wrist=unique('Wrist_'+side)
 p0=pos(shoulder);p1=pos(elbow);p2=pos(wrist);a=mag(p1-p0);b=mag(p2-p1)
 target=v3(target_xy);d=target-p0
 maxd=(a+b)*.965
 if mag(d)>maxd: target=p0+d.normal()*maxd;d=target-p0
 dist=mag(d)
 if dist<=abs(a-b)+.01: raise RuntimeError('Wrist target unreachable for '+side)
 u=d.normal();along=(a*a-b*b+dist*dist)/(2*dist);h2=a*a-along*along
 if h2<=0: raise RuntimeError('Degenerate elbow solve '+side)
 h=math.sqrt(h2)
 sign=1 if side=='L' else -1
 preferred=v3((sign*.72,0.0,.69 if side=='L' else -.69));pole=preferred-u*dot(preferred,u)
 if mag(pole)<1e-6: raise RuntimeError('Pole vector degenerate '+side)
 elbow_target=p0+u*along+pole.normal()*h
 q1=(p1-p0).rotateTo(elbow_target-p0);apply_world_rotation(shoulder,q1)
 # Use measured post-shoulder positions to solve forearm world direction to the exact target.
 p1a=pos(elbow);p2a=pos(wrist);q2=(p2a-p1a).rotateTo(target-p1a);apply_world_rotation(elbow,q2)
 p1b=pos(elbow);p2b=pos(wrist)
 if mag(p1b-elbow_target)>.02: raise RuntimeError('%s elbow solve residual %.4fcm'%(side,mag(p1b-elbow_target)))
 if mag(p2b-target)>.03: raise RuntimeError('%s wrist solve residual %.4fcm'%(side,mag(p2b-target)))
 cosang=max(-1.0,min(1.0,dot((p0-p1b).normal(),(p2b-p1b).normal())))
 bend=math.degrees(math.acos(cosang))
 return {'side':side,'shoulder_before_cm':vec(p0),'elbow_before_cm':vec(p1),'wrist_before_cm':vec(p2),'upper_arm_length_cm':a,'forearm_length_cm':b,'target_wrist_cm':vec(target),'elbow_target_cm':vec(elbow_target),'elbow_after_cm':vec(p1b),'wrist_after_cm':vec(p2b),'elbow_wrist_residual_cm':mag(p2b-target),'elbow_bend_degrees':bend,'q_shoulder_world_delta_xyzw':[q1.x,q1.y,q1.z,q1.w],'q_elbow_world_delta_xyzw':[q2.x,q2.y,q2.z,q2.w]}
try:
 if any(p.exists() for p in (FBX,SCENE,REPORT)): raise FileExistsError('Existing Dana held-pose artifact preserved')
 if not SOURCE.is_file(): raise FileNotFoundError(str(SOURCE))
 source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest();report['source_sha256_before']=source_hash
 cmds.loadPlugin('fbxmaya',quiet=True);cmds.file(str(SOURCE),open=True,force=True,ignoreVersion=True,executeScriptNodes=False,prompt=False);cmds.evaluationManager(mode='off');cmds.currentUnit(time='film');cmds.currentTime(1,e=True,update=True)
 meshes=meshes_by_short(); expected=['Dana_Body_GEO','Dana_Eyelashes_Lf_GEO','Dana_Eyelashes_Rt_GEO','Dana_Eye_Lf_GEO','Dana_Eye_Rt_GEO','Dana_Cornea_Lf_GEO','Dana_Cornea_Rt_GEO','Dana_EyeInt_Lf_GEO','Dana_EyeInt_Rt_GEO','Dana_Jeans_GEO','Dana_Shirt_GEO','Dana_Shoe_Lf_GEO','Dana_Shoe_Rt_GEO','Dana_LongHair_Bang_GEO','Dana_LongHair_Main_GEO','Dana_Lower_Teeth_GEO1','Dana_UpperTeeth_GEO','Dana_Tongue_GEO','Dana_Eyebrows_GEO']
 if set(meshes)!=set(expected): raise RuntimeError('Source mesh inventory mismatch '+repr(set(expected)^set(meshes)))
 joints=cmds.ls(type='joint',long=True) or [];transforms=cmds.ls(type='transform',long=True) or []
 if len(joints)!=777: raise RuntimeError('Expected Dana v10e 777 Maya joints; got '+str(len(joints)))
 report.update({'source_mesh_count':len(meshes),'source_joint_count':len(joints),'source_transform_count':len(transforms),'source_geometry_local':geometry_local(meshes),'source_skin':get_skin_snapshot(meshes),'source_materials':shader_map(meshes),'source_world_mesh_bounds_cm':all_mesh_bounds(meshes),'source_joint_signature':rest_joint_signature(joints)})
 bs,aliases=blendshape_info(meshes['Dana_Body_GEO'][1]);expected_morphs={'Blink_L','Blink_R','Brow_Up','Brow_Down','Smile','Frown','Mouth_Wide','Jaw_Open'}
 if set(aliases)!=expected_morphs: raise RuntimeError('Expected eight morphs, got '+repr(sorted(aliases)))
 report['morph_names']=sorted(aliases)
 foot_names={short(j) for j in joints if any(k in short(j).lower() for k in ['ankle_','toe_','toes_'])}
 foot_skin=skin_of(meshes['Dana_Body_GEO'][1]); foot_points=[]
 # Build the weighted foot envelope over all skinned geometry pieces, including shoes.
 for n,(tf,sh) in meshes.items():
  skins=cmds.ls(cmds.listHistory(sh,pruneDagObjects=True) or [],type='skinCluster') or []
  if not skins: continue
  foot_points.extend(weighted_region(sh,skins[0],foot_names,threshold=.1))
 if not foot_points: raise RuntimeError('No weighted foot vertices found')
 feet_before=bounds(foot_points);root=unique('Root_M');root_before=to_list(cmds.xform(root,q=True,ws=True,m=True));legs={n:to_list(cmds.xform(unique(n),q=True,ws=True,m=True)) for n in ['Hip_L','Hip_R','Ankle_L','Ankle_R']}
 targets={'L':(16.2,42.6,-.15),'R':(-16.8,43.0,.15)}
 pose_data={side:solve_arm(side,target) for side,target in targets.items()}
 head=unique('Head_M');head_before=to_list(cmds.xform(head,q=True,ws=True,m=True));qroll=om.MQuaternion(math.radians(2.2),om.MVector(0,0,1));qnod=om.MQuaternion(math.radians(-1.1),om.MVector(1,0,0));apply_world_rotation(head,qroll*qnod);head_after=to_list(cmds.xform(head,q=True,ws=True,m=True))
 cmds.currentTime(1,e=True,update=True);cmds.dgdirty(allPlugs=True)
 report['pose']={'arms':pose_data,'head_world_matrix_before':head_before,'head_world_matrix_after':head_after,'head_asymmetry_world_rotation_degrees':{'roll_about_world_z':2.2,'nod_about_world_x':-1.1}}
 report['hand_torso_metrics']=motion_group_metrics(meshes)
 report['foot_envelope_before_cm']=feet_before
 foot_points_after=[]
 for n,(tf,sh) in meshes.items():
  skins=cmds.ls(cmds.listHistory(sh,pruneDagObjects=True) or [],type='skinCluster') or []
  if skins: foot_points_after.extend(weighted_region(sh,skins[0],foot_names,threshold=.1))
 feet_after=bounds(foot_points_after);report['foot_envelope_after_cm']=feet_after
 report['foot_envelope_component_delta_cm']={axis:{k:feet_after[k][i]-feet_before[k][i] for k in ('min','max')} for i,axis in enumerate('xyz')}
 report['root_world_matrix_delta_max']=max(abs(a-b) for a,b in zip(root_before,to_list(cmds.xform(root,q=True,ws=True,m=True))))
 report['leg_world_matrix_delta_max']={n:max(abs(a-b) for a,b in zip(mat,to_list(cmds.xform(unique(n),q=True,ws=True,m=True)))) for n,mat in legs.items()}
 # Gate only measurable pose requests. The skin/build gates run in a fresh process.
 for side,m in report['hand_torso_metrics'].items():
  if m['wrist_drop_from_shoulder_cm']<10: raise RuntimeError(side+' wrist drop under meaningful 10cm')
  if m['lateral_hand_to_torso_clearance_cm']<.5: raise RuntimeError(side+' hand overlaps torso lateral envelope')
  if m['wrist_to_hip_distance_cm']>22: raise RuntimeError(side+' hand/wrist too far from hip pivot')
 if max(abs(v) for a in report['foot_envelope_component_delta_cm'].values() for v in a.values())>.02: raise RuntimeError('Foot weighted envelope moved >0.02 cm')
 if report['root_world_matrix_delta_max']>1e-6 or max(report['leg_world_matrix_delta_max'].values())>1e-6: raise RuntimeError('Root or leg transforms changed')
 # Key all scene transforms at two identical frames so every FBX skeleton/model node has a held track.
 cmds.playbackOptions(min=1,max=2,animationStartTime=1,animationEndTime=2);cmds.currentTime(1,e=True,update=True)
 for frame in (1,2):
  for n in transforms:
   attrs=[a for a in ATTRS if cmds.attributeQuery(a,node=n,exists=True) and not cmds.getAttr(n+'.'+a,lock=True)]
   if attrs: cmds.setKeyframe(n,attribute=attrs,time=frame,inTangentType='linear',outTangentType='linear')
 cmds.keyTangent(edit=True,g=True,inTangentType='linear',outTangentType='linear')
 report['keyed_transform_count']=len(transforms);report['keyed_frames']=[1,2];report['fps']=24
 # Save only this new derivative Maya source scene.
 cmds.file(rename=str(SCENE));cmds.file(save=True,type='mayaBinary',force=True)
 # Keep mesh present during export to preserve rest bind matrices (armature-only export bakes the pose into rest).
 mel.eval('FBXResetExport;')
 for s in ['FBXExportSkins -v true;','FBXExportShapes -v true;','FBXExportInputConnections -v true;','FBXExportIncludeChildren -v true;','FBXExportBakeComplexAnimation -v true;','FBXExportBakeComplexStart -v 1;','FBXExportBakeComplexEnd -v 2;','FBXExportBakeComplexStep -v 1;','FBXExportConstraints -v false;','FBXExportCameras -v false;','FBXExportLights -v false;','FBXExportEmbeddedTextures -v false;','FBXExportTriangulate -v false;']:
  mel.eval(s)
 mel.eval('FBXExport -f "%s";' % FBX.as_posix())
 if not FBX.is_file() or FBX.stat().st_size<100000: raise RuntimeError('FBX export missing/suspicious size')
 report['candidate_fbx']=str(FBX);report['candidate_scene']=str(SCENE);report['candidate_bytes']=FBX.stat().st_size;report['candidate_sha256']=hashlib.sha256(FBX.read_bytes()).hexdigest();report['source_sha256_after']=hashlib.sha256(SOURCE.read_bytes()).hexdigest();report['source_unchanged']=report['source_sha256_before']==report['source_sha256_after'];report['stage']='candidate_exported_pending_fresh_readback'
 save_report();print(json.dumps(report,indent=1,default=str))
except Exception:
 report['status']='blocked';report['error']=traceback.format_exc();save_report();print(report['error']);raise
finally:
 try: cmds.file(new=True,force=True);maya.standalone.uninitialize()
 except Exception: pass





