"""Fresh-process readback gate for Dana held-pose FBX; never saves source."""
import datetime, hashlib, json, math, traceback
from pathlib import Path
import maya.standalone
maya.standalone.initialize(name='python')
from maya import cmds, mel
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'Saved/OfflineIntake/20261017/task1_face_eyes/fbx/Dana_CleanSkin_v10e_InputConnections.fbx'
CAND=ROOT/'Saved/OfflineIntake/20261017/task1_face_eyes/held_pose/Dana_HeldPose_v07_24fps.fbx'
REPORT=ROOT/'Saved/OfflineIntake/20261017/task1_face_eyes/held_pose/Dana_HeldPose_v07_fresh_readback.json'
MORPHS={'Blink_L','Blink_R','Brow_Down','Brow_Up','Frown','Jaw_Open','Mouth_Wide','Smile'}
EPS_GEOM=2e-4
EPS_WEIGHT=2e-5
EPS_BIND=2e-4

def shname(n): return n.rsplit('|',1)[-1].rsplit(':',1)[-1]
def dag(n):
 s=om.MSelectionList();s.add(n);return s.getDagPath(0)
def meshmap():
 out={}
 for t in cmds.ls(type='transform',long=True) or []:
  name=shname(t)
  if not name.startswith('Dana_'): continue
  shapes=cmds.listRelatives(t,shapes=True,noIntermediate=True,fullPath=True) or []
  shapes=[x for x in shapes if cmds.nodeType(x)=='mesh' and not cmds.getAttr(x+'.intermediateObject')]
  if len(shapes)==1: out[name]=(t,shapes[0])
 return out
def joints():
 out={}
 for j in cmds.ls(type='joint',long=True) or []:
  n=shname(j)
  if n in out: raise RuntimeError('Duplicate short joint name '+n)
  out[n]=j
 return out
def points(shape):
 fn=om.MFnMesh(dag(shape)); p=fn.getPoints(om.MSpace.kObject)
 return [[round(float(v),7) for v in (x.x,x.y,x.z)] for x in p]
def skin_data(shape):
 hist=cmds.listHistory(shape,pruneDagObjects=True) or []; ss=cmds.ls(hist,type='skinCluster') or []
 if len(ss)!=1: raise RuntimeError('Expected one skin cluster, got '+repr(ss))
 skin=ss[0];sel=om.MSelectionList();sel.add(skin);sf=oma.MFnSkinCluster(sel.getDependNode(0));infs=sf.influenceObjects(); names=[shname(x.fullPathName()) for x in infs]
 fn=om.MFnMesh(dag(shape)); n=fn.numVertices; comp=om.MFnSingleIndexedComponent();cid=comp.create(om.MFn.kMeshVertComponent);comp.addElements(list(range(n)));w,ni=sf.getWeights(dag(shape),cid)
 sparse=[]
 for vi in range(n): sparse.append(sorted((names[k],round(float(w[vi*ni+k]),7)) for k in range(ni) if float(w[vi*ni+k])>1e-8))
 bind={}
 for i,name in enumerate(names):
  value=cmds.getAttr('%s.bindPreMatrix[%d]'%(skin,i))
  if value and isinstance(value[0],(list,tuple)): value=value[0]
  bind[name]=[float(x) for x in value]
 return {'skin':skin,'weights':sparse,'bind':bind,'influences':set(names)}
def morph_info(meshes):
 found={}; deltas={}
 for mn,(tf,shape) in meshes.items():
  bs=cmds.ls(cmds.listHistory(shape,pruneDagObjects=True) or [],type='blendShape') or []
  for b in bs:
   aliases=cmds.aliasAttr(b,q=True) or []
   for i in range(0,len(aliases),2): found[aliases[i]]=b+'.'+aliases[i+1]
 if not MORPHS.issubset(set(found)): return found,{}
 for name,plug in found.items():
  if name not in MORPHS: continue
  b=plug.rsplit('.',1)[0]; base=None
  for mn,(tf,shape) in meshes.items():
   if b in (cmds.ls(cmds.listHistory(shape,pruneDagObjects=True) or [],type='blendShape') or []): base=shape;break
  if base is None: continue
  cmds.setAttr(plug,0);cmds.dgdirty(allPlugs=True);p0=points(base)
  cmds.setAttr(plug,1);cmds.dgdirty(allPlugs=True);p1=points(base)
  deltas[name]=max((math.dist(a,b) for a,b in zip(p0,p1)),default=0.0)
  cmds.setAttr(plug,0);cmds.dgdirty(allPlugs=True)
 return found,deltas
def signature(js):
 d={}
 for n,j in js.items():
  p=cmds.listRelatives(j,parent=True,fullPath=True) or []
  d[n]={'parent':shname(p[0]) if p and cmds.nodeType(p[0])=='joint' else (shname(p[0]) if p else None),
        'joint_orient':[float(x) for x in cmds.getAttr(j+'.jointOrient')[0]],
        'segment_scale_compensate':bool(cmds.getAttr(j+'.segmentScaleCompensate'))}
 return d
def xform_sig(js): return {n:[float(x) for x in cmds.xform(j,q=True,ws=True,m=True)] for n,j in js.items()}
def max_delta(a,b):
 common=set(a)&set(b)
 return max((abs(x-y) for n in common for x,y in zip(a[n],b[n])),default=float('inf'))
def collect():
 mm=meshmap(); js=joints(); skin={n:skin_data(sh) for n,(tf,sh) in mm.items() if cmds.listConnections(sh,type='skinCluster') or cmds.ls(cmds.listHistory(sh,pruneDagObjects=True) or [],type='skinCluster')}
 envelopes={row['skin']:cmds.getAttr(row['skin']+'.envelope') for row in skin.values()}
 for node in envelopes: cmds.setAttr(node+'.envelope',0)
 geom={n:points(sh) for n,(tf,sh) in mm.items()}; faces={n:cmds.polyEvaluate(sh,face=True) for n,(tf,sh) in mm.items()}
 for node,value in envelopes.items(): cmds.setAttr(node+'.envelope',value)
 mats={}
 for n,(tf,shape) in mm.items():
  vals=set()
  for sg in cmds.listConnections(shape,type='shadingEngine') or []:
   for m in cmds.listConnections(sg+'.surfaceShader',source=True,destination=False) or []: vals.add(shname(m))
  mats[n]=sorted(vals)
 morphs,md=morph_info(mm)
 return {'meshes':mm,'joints':js,'geometry':geom,'faces':faces,'skin':skin,'materials':mats,'morphs':morphs,'morph_deltas':md,'signature':signature(js)}
def import_fbx(path):
 if not cmds.pluginInfo('fbxmaya',q=True,loaded=True): cmds.loadPlugin('fbxmaya')
 mel.eval('FBXResetImport;');cmds.file(str(path),i=True,type='FBX',ignoreVersion=True,mergeNamespacesOnClash=False,namespace='FBXRead',options='fbx')
report={'tool':'verify_dana_held_pose_v05.py','status':'starting','source':str(SOURCE),'candidate':str(CAND),'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256_before':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(CAND.read_bytes()).hexdigest()}
try:
 import_fbx(SOURCE); src=collect(); report['source_inventory']={'mesh_count':len(src['meshes']),'joint_count':len(src['joints']),'skinned_mesh_count':len(src['skin']),'morphs':sorted(src['morphs']),'total_vertices':sum(len(v) for v in src['geometry'].values()),'material_names':sorted({m for row in src['materials'].values() for m in row})}
 cmds.file(new=True,force=True);import_fbx(CAND); cand=collect(); report['candidate_inventory']={'mesh_count':len(cand['meshes']),'joint_count':len(cand['joints']),'skinned_mesh_count':len(cand['skin']),'morphs':sorted(cand['morphs']),'total_vertices':sum(len(v) for v in cand['geometry'].values()),'material_names':sorted({m for row in cand['materials'].values() for m in row})}
 report['mesh_names_match']=set(src['meshes'])==set(cand['meshes']);report['joint_names_match']=set(src['joints'])==set(cand['joints']);report['joint_parent_signature_match']=src['signature']==cand['signature']
 report['geometry_max_local_delta_cm']=max((max_delta({n:{'v':v} for n,v in src['geometry'].items()},{n:{'v':v} for n,v in cand['geometry'].items()}) if False else max((math.dist(a,b) for n in set(src['geometry'])&set(cand['geometry']) for a,b in zip(src['geometry'][n],cand['geometry'][n])),default=float('inf'))),0)
 report['geometry_vertex_face_match']=set(src['faces'])==set(cand['faces']) and all(len(src['geometry'][n])==len(cand['geometry'].get(n,[])) and src['faces'][n]==cand['faces'][n] for n in src['geometry'])
 report['skin_weight_max_delta']=max((abs(x[1]-y[1]) for n in set(src['skin'])&set(cand['skin']) for a,b in zip(src['skin'][n]['weights'],cand['skin'][n]['weights']) for x,y in zip(a,b) if x[0]==y[0]),default=float('inf'))
 report['skin_weights_match']=set(src['skin'])==set(cand['skin']) and all(len(src['skin'][n]['weights'])==len(cand['skin'][n]['weights']) and all(len(a)==len(b) and {x[0] for x in a}=={y[0] for y in b} for a,b in zip(src['skin'][n]['weights'],cand['skin'][n]['weights'])) for n in src['skin'] if n in cand['skin'])
 report['bind_pre_matrix_max_delta']=max((abs(x-y) for n in set(src['skin'])&set(cand['skin']) for b in set(src['skin'][n]['bind'])&set(cand['skin'][n]['bind']) for x,y in zip(src['skin'][n]['bind'][b],cand['skin'][n]['bind'][b])),default=float('inf'))
 report['materials_match']=src['materials']==cand['materials']
 report['morph_inventory_match']=set(src['morphs'])==set(cand['morphs']) and set(cand['morphs'])==MORPHS
 report['source_morph_max_deltas_cm']=src['morph_deltas'];report['candidate_morph_max_deltas_cm']=cand['morph_deltas']
 report['morph_delta_change_cm']={n:abs(src['morph_deltas'].get(n,0)-cand['morph_deltas'].get(n,0)) for n in MORPHS}
 # Capture frame endpoints, animation channel count, and held endpoint equality.
 report['fps_setting']=cmds.currentUnit(q=True,time=True);report['animation_curves']=len(cmds.ls(type='animCurve') or []);report['keyed_transform_attr_count']=sum(1 for n in cmds.ls(type='transform',long=True) or [] for a in ('tx','ty','tz','rx','ry','rz','sx','sy','sz') if cmds.keyframe(n+'.'+a,q=True,tc=True))
 pose={}
 for f in (1,2):
  cmds.currentTime(f,e=True,update=True); js=joints(); matrices=xform_sig(js)
  pose[str(f)]={'joint_world_matrices':matrices,'wrists':{s:[float(x) for x in cmds.xform(js['Wrist_'+s],q=True,ws=True,t=True)] for s in ('L','R')},'head':[float(x) for x in cmds.xform(js['Head_M'],q=True,ws=True,t=True)],'root':[float(x) for x in cmds.xform(js['Root_M'],q=True,ws=True,m=True)]}
 report['pose_frame1_wrists_cm']=pose['1']['wrists'];report['pose_frame2_wrists_cm']=pose['2']['wrists'];report['endpoint_joint_world_matrix_delta']=max_delta(pose['1']['joint_world_matrices'],pose['2']['joint_world_matrices']);report['endpoint_root_matrix_delta']=max(abs(x-y) for x,y in zip(pose['1']['root'],pose['2']['root']))
 report['wrist_drop_cm']={s:float(cand['signature'] and (cmds.xform(joints()['Shoulder_'+s],q=True,ws=True,t=True)[1]-pose['1']['wrists'][s][1])) for s in ('L','R')}
 report['source_sha256_after']=hashlib.sha256(SOURCE.read_bytes()).hexdigest();report['source_unchanged']=report['source_sha256_before']==report['source_sha256_after']
 checks={'mesh_inventory':report['mesh_names_match'] and len(cand['meshes'])==19,'joint_inventory':report['joint_names_match'] and len(cand['joints'])==777,'hierarchy_rest_signature':report['joint_parent_signature_match'],'geometry':report['geometry_max_local_delta_cm']<=EPS_GEOM and report['geometry_vertex_face_match'],'weights':report['skin_weights_match'] and report['skin_weight_max_delta']<=EPS_WEIGHT,'bind_pre_matrices':report['bind_pre_matrix_max_delta']<=EPS_BIND,'materials':report['materials_match'],'morphs':report['morph_inventory_match'] and all(v>0.05 for v in cand['morph_deltas'].values()) and max(report['morph_delta_change_cm'].values())<=EPS_GEOM,'fps_24':report['fps_setting']=='film','animation_curves':report['keyed_transform_attr_count']>=777*10,'same_endpoints':report['endpoint_joint_world_matrix_delta']<=1e-5 and report['endpoint_root_matrix_delta']<=1e-5,'wrist_pose':all(v>=10 for v in report['wrist_drop_cm'].values()),'source_unchanged':report['source_unchanged']}
 report['checks']=checks;report['stage']='pass' if all(checks.values()) else 'gated';report['status']=report['stage']
except Exception: report['status']='error';report['stage']='error';report['error']=traceback.format_exc()
finally:
 REPORT.write_text(json.dumps(report,indent=2,default=str),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k not in ('source_inventory','candidate_inventory') and k not in ('error',)},indent=2,default=str));
 try: cmds.file(new=True,force=True);maya.standalone.uninitialize()
 except Exception: pass
