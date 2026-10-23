import json, hashlib, datetime, traceback, math
from pathlib import Path
import maya.standalone
maya.standalone.initialize(name='python')
from maya import cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
ROOT=Path('G:/film-304-toon-spine')
SRC=ROOT/'Saved/OfflineIntake/20261017/task1_face_eyes/fbx/Dana_CleanSkin_v09.fbx'
DST=ROOT/'Saved/OfflineIntake/20261017/task1_face_eyes/fbx/Dana_CleanSkin_v10e_InputConnections.fbx'
REPORT=ROOT/'Saved/OfflineIntake/20261017/task1_face_eyes/report/v10e_face_follow_readback.json'
EXPECTED={'Dana_Body_GEO':9249,'Dana_Eyelashes_Lf_GEO':39,'Dana_Eyelashes_Rt_GEO':39,'Dana_Eye_Lf_GEO':1121,'Dana_Eye_Rt_GEO':1121,'Dana_Cornea_Lf_GEO':161,'Dana_Cornea_Rt_GEO':161,'Dana_EyeInt_Lf_GEO':51,'Dana_EyeInt_Rt_GEO':51,'Dana_Jeans_GEO':2172,'Dana_Shirt_GEO':1564,'Dana_Shoe_Lf_GEO':1031,'Dana_Shoe_Rt_GEO':1031,'Dana_LongHair_Bang_GEO':474,'Dana_LongHair_Main_GEO':566,'Dana_Lower_Teeth_GEO1':2192,'Dana_UpperTeeth_GEO':2194,'Dana_Tongue_GEO':165,'Dana_Eyebrows_GEO':178}
MORPHS={'Blink_L','Blink_R','Brow_Up','Brow_Down','Smile','Frown','Mouth_Wide','Jaw_Open'}
report={'tool':'verify_dana_v10_face_follow.py','stage':'starting','source':str(SRC),'candidate':str(DST),'source_saved':False,'at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
def save(): REPORT.write_text(json.dumps(report,indent=2,default=str),encoding='utf8')
def sn(n): return n.rsplit('|',1)[-1].rsplit(':',1)[-1]
def mesh_map():
 d={}
 for t in cmds.ls(type='transform',long=True) or []:
  name=sn(t)
  if name in EXPECTED:
   sh=cmds.listRelatives(t,shapes=True,noIntermediate=True,fullPath=True) or []
   if sh: d[name]=(t,sh[0])
 return d
def om_mesh(shape):
 sel=om.MSelectionList(); sel.add(shape); return om.MFnMesh(sel.getDagPath(0))
def capture(path):
 cmds.file(new=True,force=True); cmds.loadPlugin('fbxmaya',quiet=True); cmds.file(str(path),open=True,force=True,ignoreVersion=True,executeScriptNodes=False,prompt=False); cmds.evaluationManager(mode='off'); cmds.currentTime(1,e=True,update=True)
 mm=mesh_map()
 if set(mm)!=set(EXPECTED): raise RuntimeError('mesh inventory mismatch '+repr(sorted(set(EXPECTED)^set(mm))))
 data={'meshes':{},'joints':{},'morphs':{},'follow_parent':None,'materials':{}}
 for name,(tf,sh) in mm.items():
  fn=om_mesh(sh); pts=fn.getPoints(om.MSpace.kWorld); faces=cmds.polyEvaluate(sh,face=True)
  # Quantized world positions permit stable content comparison with tiny FBX float error.
  xyz=[round(v,7) for p in pts for v in (p.x,p.y,p.z)]
  data['meshes'][name]={'vertices':len(pts),'faces':faces,'xyz':xyz}
  sg=set(cmds.listConnections(sh,type='shadingEngine') or [])
  mats=set()
  for x in sg:
   shd=cmds.listConnections(x+'.surfaceShader',source=True,destination=False) or []
   mats.update(sn(z) for z in shd)
  data['materials'][name]=sorted(mats)
  skins=cmds.ls(cmds.listHistory(sh,pruneDagObjects=True) or [],type='skinCluster') or []
  if len(skins)!=1: raise RuntimeError('%s skin count=%d'%(name,len(skins)))
  skin=skins[0]; sel=om.MSelectionList(); sel.add(skin); sf=oma.MFnSkinCluster(sel.getDependNode(0)); infs=sf.influenceObjects(); names=[sn(x.fullPathName()) for x in infs]
  # influence weights are captured in API component order by querying all vertices
  c=om.MFnSingleIndexedComponent(); cobj=c.create(om.MFn.kMeshVertComponent); c.addElements(list(range(len(pts))))
  weights,ic=sf.getWeights(sel.getDagPath(0) if False else (lambda s: (lambda q:q.getDagPath(0))( (lambda l:(l.add(sh),l)[1])(om.MSelectionList()) ))(sh),cobj)
  # use sparse canonical names/values, preserve zero exclusion
  rows=[]
  for vi in range(len(pts)):
   row=sorted((names[j],round(float(weights[vi*ic+j]),8)) for j in range(ic) if float(weights[vi*ic+j])>1e-9)
   rows.append(row)
  data['meshes'][name]['weights']=rows
 for j in (cmds.ls(type='joint',long=True) or []):
  par=cmds.listRelatives(j,parent=True,fullPath=True) or ['']
  data['joints'][sn(j)]={'parent':sn(par[0]) if par[0] else None,'matrix':[round(float(v),8) for v in cmds.xform(j,q=True,ws=True,m=True)]}
 follow=[n for n in (cmds.ls(long=True) or []) if sn(n)=='FaceDeformationFollowHead' and cmds.nodeType(n)=='transform']
 if len(follow)!=1: raise RuntimeError('Follow transform count '+str(follow))
 data['follow_parent']=sn((cmds.listRelatives(follow[0],parent=True,fullPath=True) or [''])[0])
 data['follow_world_matrix']=[round(float(v),9) for v in cmds.xform(follow[0],q=True,ws=True,m=True)]
 body=mm['Dana_Body_GEO'][0]; shape=mm['Dana_Body_GEO'][1]
 bsn=cmds.ls(cmds.listHistory(shape,pruneDagObjects=True) or [],type='blendShape') or []
 if len(bsn)!=1: raise RuntimeError('blendshape count='+str(len(bsn)))
 bs=bsn[0]; aliases=cmds.aliasAttr(bs,q=True) or []; amap={aliases[i]:aliases[i+1] for i in range(0,len(aliases),2)}
 rest=om_mesh(shape).getPoints(om.MSpace.kObject)
 for alias,plug in amap.items():
  cmds.setAttr(bs+'.'+plug,1.0); cmds.dgdirty(allPlugs=True); cmds.currentTime(2,e=True,update=True); cmds.currentTime(1,e=True,update=True)
  cur=om_mesh(shape).getPoints(om.MSpace.kObject)
  data['morphs'][alias]=[round(math.sqrt((cur[i].x-rest[i].x)**2+(cur[i].y-rest[i].y)**2+(cur[i].z-rest[i].z)**2),7) for i in range(len(rest))]
  cmds.setAttr(bs+'.'+plug,0); cmds.dgdirty(allPlugs=True); cmds.currentTime(2,e=True,update=True); cmds.currentTime(1,e=True,update=True)
 # verify head rotation changes eye world position via actual imported hierarchy
 head=[j for j in (cmds.ls(type='joint',long=True) or []) if sn(j)=='Head_M']
 eye=[j for j in (cmds.ls(type='joint',long=True) or []) if sn(j)=='Eye_L']
 if len(head)!=1 or len(eye)!=1: raise RuntimeError('head/eye joint resolution failure')
 ep0=cmds.xform(eye[0],q=True,ws=True,t=True); head_m0=om.MMatrix(cmds.xform(head[0],q=True,ws=True,m=True)); rot=cmds.getAttr(head[0]+'.rotateX'); cmds.setAttr(head[0]+'.rotateX',rot+10); cmds.dgdirty(allPlugs=True); cmds.currentTime(2,e=True,update=True); cmds.currentTime(1,e=True,update=True); ep1=cmds.xform(eye[0],q=True,ws=True,t=True); head_m1=om.MMatrix(cmds.xform(head[0],q=True,ws=True,m=True)); head_pos0=[head_m0[12],head_m0[13],head_m0[14]]; head_pos1=[head_m1[12],head_m1[13],head_m1[14]]
 predicted=om.MPoint(ep0[0],ep0[1],ep0[2],1.0)*head_m0.inverse()*head_m1
 cmds.setAttr(head[0]+'.rotateX',rot); cmds.dgdirty(allPlugs=True)
 data['head_world_rest_position_cm']=[round(float(v),8) for v in head_pos0]
 data['eye_l_world_rest_position_cm']=[round(float(v),8) for v in ep0]
 data['eye_l_minus_head_rest_cm']=[round(float(ep0[k]-head_pos0[k]),8) for k in range(3)]
 data['eye_l_world_after_head_plus10deg_cm']=[round(float(v),8) for v in ep1]
 data['eye_l_expected_rigid_world_after_head_plus10deg_cm']=[round(float(predicted[k]),8) for k in range(3)]
 data['eye_motion_10deg']=math.sqrt(sum((ep1[k]-ep0[k])**2 for k in range(3)))
 data['eye_motion_expected_rigid_10deg']=math.sqrt(sum((float(predicted[k])-ep0[k])**2 for k in range(3)))
 data['eye_motion_rigid_error_cm']=math.sqrt(sum((ep1[k]-float(predicted[k]))**2 for k in range(3)))
 return data
try:
 if not DST.is_file(): raise FileNotFoundError(str(DST))
 report['source_sha256_before']=hashlib.sha256(SRC.read_bytes()).hexdigest()
 report['candidate_sha256']=hashlib.sha256(DST.read_bytes()).hexdigest()
 a=capture(SRC); b=capture(DST)
 report['source']={k:v for k,v in a.items() if k not in ('meshes','joints','morphs')}
 report['candidate']={k:v for k,v in b.items() if k not in ('meshes','joints','morphs')}
 report['mesh_inventory_pass']=set(a['meshes'])==set(b['meshes'])==set(EXPECTED)
 report['mesh_vertex_face_pass']=all(a['meshes'][n]['vertices']==b['meshes'][n]['vertices']==EXPECTED[n] and a['meshes'][n]['faces']==b['meshes'][n]['faces'] for n in EXPECTED)
 report['geometry_delta_by_mesh_cm']={n:max((abs(x-y) for x,y in zip(a['meshes'][n]['xyz'],b['meshes'][n]['xyz'])),default=0) for n in EXPECTED}
 report['rest_geometry_max_delta_cm']=max(report['geometry_delta_by_mesh_cm'].values())
 report['geometry_pass']=report['rest_geometry_max_delta_cm']<1e-4
 report['skin_weight_pass']=all(a['meshes'][n]['weights']==b['meshes'][n]['weights'] for n in EXPECTED)
 report['materials_pass']=a['materials']==b['materials']
 report['morph_names_source']=sorted(a['morphs']); report['morph_names_candidate']=sorted(b['morphs'])
 report['morph_inventory_pass']=set(a['morphs'])==set(b['morphs']) and set(a['morphs'])==MORPHS
 common=set(a['morphs']) & set(b['morphs'])
 report['morph_delta_max_error_cm']=max((abs(x-y) for n in common for x,y in zip(a['morphs'][n],b['morphs'][n])),default=None)
 report['morphs_pass']=report['morph_inventory_pass'] and report['morph_delta_max_error_cm'] is not None and report['morph_delta_max_error_cm']<1e-5
 report['face_follow_parent_pass']=b['follow_parent']=='Head_M'
 report['face_follow_rest_matrix_max_error']=max(abs(x-y) for x,y in zip(a['follow_world_matrix'],b['follow_world_matrix']))
 report['face_follow_rest_matrix_pass']=report['face_follow_rest_matrix_max_error']<1e-4
 report['eye_motion_pass']=b['eye_motion_10deg']>0.05
 report['eye_motion_pivot_error_cm']=b['eye_motion_rigid_error_cm']
 report['eye_motion_pivot_pass']=b['eye_motion_rigid_error_cm']<1e-4 and b['eye_motion_expected_rigid_10deg']>0.05
 report['joint_count_source']=len(a['joints']); report['joint_count_candidate']=len(b['joints'])
 report['source_sha256_after']=hashlib.sha256(SRC.read_bytes()).hexdigest(); report['source_unchanged']=report['source_sha256_before']==report['source_sha256_after']
 report['gate_pass']=all(report[k] for k in ['mesh_inventory_pass','mesh_vertex_face_pass','geometry_pass','skin_weight_pass','materials_pass','morph_inventory_pass','morphs_pass','face_follow_parent_pass','face_follow_rest_matrix_pass','eye_motion_pass','eye_motion_pivot_pass','source_unchanged'])
 report['comparison_detail']={'material_slots_by_mesh':b['materials'],'mesh_counts':{n:{'vertices':b['meshes'][n]['vertices'],'faces':b['meshes'][n]['faces']} for n in EXPECTED},'morph_max_displacement_cm':{n:max(v) for n,v in b['morphs'].items()},'eye_motion_10deg_cm':b['eye_motion_10deg']}
 report['stage']='gated'; save(); print(json.dumps({k:v for k,v in report.items() if k not in ('source','candidate','comparison_detail')},indent=2))
except Exception:
 report['stage']='blocked';report['error']=traceback.format_exc();save();print(report['error']);raise
finally:
 try: cmds.file(new=True,force=True);maya.standalone.uninitialize()
 except Exception:pass









