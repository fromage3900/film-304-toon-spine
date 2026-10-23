"""Isolated evaluated mesh + exact native skin copy; original source never saved.
No production approval: facial blendshape transport and deformation remain gates.
"""
import json,hashlib,traceback,sys
from pathlib import Path
import maya.standalone
maya.standalone.initialize(name='python')
from maya import cmds,mel
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
ROOT=Path('G:/film-304-toon-spine/Saved/Audit/MayaDanaNative_20261016/ExportCandidate')
SOURCE=Path('G:/Film304_AssetIntake_20261016_Source/3rd Year Film/Rigs/Temp/Dana_Rig_v1.5/Dana_Rig_v1.5.mb')
OUTPUT=ROOT/'Dana_CleanSkin_v08.fbx'
report={'stage':'starting','source_saved':False,'deformation_tested':False,'facial_blendshapes_copied':False}
def save():(ROOT/'v08_report.json').write_text(json.dumps(report,indent=2,default=str))
def dag(name):
 s=om.MSelectionList();s.add(name);return s.getDagPath(0)
def skinfn(name):
 s=om.MSelectionList();s.add(name);return oma.MFnSkinCluster(s.getDependNode(0))
def component(n):
 f=om.MFnSingleIndexedComponent();c=f.create(om.MFn.kMeshVertComponent);f.setCompleteData(n);return c
try:
 if OUTPUT.exists():raise RuntimeError('Refusing to overwrite existing isolated candidate')
 report['source_sha256_before']=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
 cmds.file(str(SOURCE),open=True,force=True,ignoreVersion=True,executeScriptNodes=False,loadReferenceDepth='none',prompt=False)
 cmds.evaluationManager(mode='off');cmds.currentTime(1,edit=True,update=True)
 # Identify native blink controls for a subsequent facial transport gate.
 report['blink_controls']={}
 for node in cmds.ls(transforms=True,long=True) or []:
  attrs=cmds.listAttr(node,keyable=True) or []
  match=[a for a in attrs if any(k in a.lower() for k in ['blink','eyelid'])]
  if match or 'blink' in node.rsplit('|',1)[-1].lower():report['blink_controls'][node]=match or attrs
 # Reuse the authoritative mesh contract, not a broad geometry selection.
 import importlib.util
 spec=importlib.util.spec_from_file_location('old_export',str(ROOT/'export_dana_native_candidate.py'))
 old=importlib.util.module_from_spec(spec)
 # That helper reads argv paths at import time.
 sys.argv=[sys.argv[0],str(SOURCE),str(OUTPUT),str(ROOT/'v08_report.json')];spec.loader.exec_module(old)
 old.MESHES.update({
  '|Group|Geometry|Dana_Jeans_GEO':2172,
  '|Group|Geometry|Dana_Shirt_GEO':1564,
  '|Group|Geometry|Dana_Shoe_Lf_GEO':1031,
  '|Group|Geometry|Dana_Shoe_Rt_GEO':1031,
  '|Group|Geometry|Dana_Hair_Options_GRP|Dana_LongHair_GRP|Dana_LongHair_Bang_GEO':474,
  '|Group|Geometry|Dana_Hair_Options_GRP|Dana_LongHair_GRP|Dana_LongHair_Main_GEO':566,
  '|Group|Geometry|Dana_Lower_Teeth_GEO1':2192,
  '|Group|Geometry|Dana_UpperTeeth_GEO':2194,
  '|Group|Geometry|Dana_Tongue_GEO':165,
  '|Group|Geometry|Dana_Eyebrows_GEO':178,
 })
 report['rigid_attachment_contract']={'Dana_Eyebrows_GEO':'Head_M; evaluated against native posed geometry below'}
 report['excluded_native_visuals']=['Dana_PartialBody_GEO replaced by weighted full body','PantsButton_GEO follicle attachment pending']

 cmds.namespace(add='FilmExport')
 stage=cmds.createNode('transform',name='FilmExport:RenderMeshes')
 head_inverse=om.MMatrix(cmds.xform('Head_M',query=True,worldSpace=True,matrix=True)).inverse()
 face_copies={}
 def mapped_influence(path):
  if '|faceHeadJoint|' not in path:return path
  if path not in face_copies:
   name=path.rsplit('|',1)[-1]
   joint=cmds.createNode('joint',name='FilmExport:Face_'+name,parent='Head_M')
   matrix=cmds.createNode('multMatrix',name='FilmExport:FaceSpace_'+name)
   cmds.connectAttr(path+'.worldMatrix[0]',matrix+'.matrixIn[0]')
   cmds.setAttr(matrix+'.matrixIn[1]',*list(head_inverse),type='matrix')
   cmds.connectAttr(matrix+'.matrixSum',joint+'.offsetParentMatrix')
   face_copies[path]=cmds.ls(joint,long=True)[0]
  return face_copies[path]

 report['meshes']=[];duplicates=[]
 for path,count in old.MESHES.items():
  srcshape=(cmds.listRelatives(path,shapes=True,noIntermediate=True,fullPath=True,type='mesh') or [])[0]
  srcdag=dag(srcshape);srcmesh=om.MFnMesh(srcdag)
  if srcmesh.numVertices!=count:raise RuntimeError('Source topology changed: '+path)
  clusters=cmds.ls(cmds.listHistory(srcshape,pruneDagObjects=True) or [],type='skinCluster') or []
  if len(clusters)==1:
   srcskin=skinfn(clusters[0]);influences=srcskin.influenceObjects()
   weights,n=srcskin.getWeights(srcdag,component(count))
  elif not clusters and path.endswith('|Dana_Eyebrows_GEO'):
   srcskin=None;influences=[dag('Head_M')];weights=om.MDoubleArray([1.0]*count);n=1
  else:raise RuntimeError('Ambiguous source skin history: '+path)
  dup=cmds.createNode('transform',name='FilmExport:'+path.rsplit('|',1)[-1],parent=stage)
  cmds.xform(dup,worldSpace=True,matrix=cmds.xform(path,query=True,worldSpace=True,matrix=True))
  dstobj=om.MFnMesh().copy(srcdag.node(),dag(dup).node())
  dstshape=om.MDagPath.getAPathTo(dstobj).fullPathName()
  mapped=[mapped_influence(p.fullPathName()) for p in influences]
  dupskin=cmds.skinCluster(mapped,dup,toSelectedBones=True,normalizeWeights=0,obeyMaxInfluences=False,name='FilmExport:'+path.rsplit('|',1)[-1]+'_Skin')[0]
  dstskin=skinfn(dupskin);dstinfs=dstskin.influenceObjects()
  source_columns={p:i for i,p in enumerate(mapped)}
  order=[source_columns[p.fullPathName()] for p in dstinfs]
  copied=om.MDoubleArray([weights[v*n+j] for v in range(count) for j in order])
  dstskin.setWeights(dag(dstshape),component(count),om.MIntArray(list(range(len(order)))),copied,False)
  if clusters and cmds.objExists(clusters[0]+'.skinningMethod'):
   cmds.setAttr(dupskin+'.skinningMethod',cmds.getAttr(clusters[0]+'.skinningMethod'))
  dstskin.setBlendWeights(dag(dstshape),component(count),srcskin.getBlendWeights(srcdag,component(count)) if srcskin else om.MDoubleArray([0.0]*count))
  actual,_=dstskin.getWeights(dag(dstshape),component(count))
  delta=max(abs(a-b) for a,b in zip(actual,copied))
  if delta>1e-12:raise RuntimeError('Native skin weight copy changed values: '+path)
  # FBX drops tiny native weights. Explicit derived-copy cleanup only;
  # the exact native copy above is checked before this bounded adjustment.
  transported=[];lost_mass=0.0;maxdelta=0.0;affected=0
  for v in range(count):
   original=list(copied[v*len(order):(v+1)*len(order)])
   kept=[w if w>=0.00101 else 0.0 for w in original]
   total=sum(kept)
   if total<=0:raise RuntimeError('Transport cleanup would unweight a vertex')
   normalized=[w/total for w in kept]
   lost_mass=max(lost_mass,sum(original)-total)
   change=max(abs(a-b) for a,b in zip(original,normalized))
   maxdelta=max(maxdelta,change);affected+=change>1e-12
   transported.extend(normalized)
  dstskin.setWeights(dag(dstshape),component(count),om.MIntArray(list(range(len(order)))),om.MDoubleArray(transported),False)
  report.setdefault('transport_cleanup',[]).append({'mesh':path,'cutoff':0.00101,'max_pruned_mass':lost_mass,'max_weight_delta':maxdelta,'vertices_changed':affected})
  sgs=cmds.listConnections(srcshape,type='shadingEngine') or []
  if sgs:cmds.sets(dup,edit=True,forceElement=sgs[0])
  report['meshes'].append({'source':path,'copy':dup,'vertices':count,'source_skin':clusters[0] if clusters else None,'native_weight_copy_verified':bool(clusters),'copied_skin':dupskin,'influences':len(order),'max_weight_delta':delta})
  duplicates.append(dup);save()
 # Export the native body's evaluated eyelid closure as simple runtime morphs.
 bodyrow=next(m for m in report['meshes'] if m['source'].endswith('|Dana_Body_GEO'))
 bodycopy=bodyrow['copy'];blend=None
 for index,side in enumerate(['L','R']):
  ctrl='ctrlEye_'+side+'.blink';original=cmds.getAttr(ctrl)
  cmds.setAttr(ctrl,10.0);cmds.dgdirty(allPlugs=True);cmds.currentTime(2,edit=True,update=True);cmds.currentTime(1,edit=True,update=True)
  cmds.xform(bodyrow['source']+'.vtx[*]',query=True,worldSpace=True,translation=True)
  sourceShape=cmds.listRelatives(bodyrow['source'],shapes=True,noIntermediate=True,fullPath=True,type='mesh')[0]
  target=cmds.createNode('transform',name='FilmExport:BlinkTarget_'+side,parent=stage)
  om.MFnMesh().copy(dag(sourceShape).node(),dag(target).node())
  cmds.setAttr(ctrl,original);cmds.dgdirty(allPlugs=True);cmds.currentTime(2,edit=True,update=True);cmds.currentTime(1,edit=True,update=True)
  if blend is None:blend=cmds.blendShape(target,bodycopy,frontOfChain=True,name='FilmExport:BodyBlinkMorphs')[0]
  else:cmds.blendShape(blend,edit=True,target=(bodycopy,index,target,1.0))
  cmds.aliasAttr('Blink_'+side,blend+'.weight['+str(index)+']')
  cmds.delete(target)
  driver=cmds.createNode('multDoubleLinear',name='FilmExport:BlinkDriver_'+side)
  cmds.connectAttr(ctrl,driver+'.input1');cmds.setAttr(driver+'.input2',0.1)
  cmds.connectAttr(driver+'.output',blend+'.weight['+str(index)+']')
 report['body_blink_morphs']={'node':blend,'channels':['Blink_L','Blink_R'],'native_control_closed_value':10}
 report['export_face_influences']=face_copies
 # Compare clean native-weight copies against source through actual FK controls.
 def pts(path):
  values=cmds.xform(path+'.vtx[*]',query=True,worldSpace=True,translation=True)
  return [om.MPoint(*values[i:i+3]) for i in range(0,len(values),3)]
 import math
 report['control_deformation_tests']=[]
 runtime_snapshots=[]
 for case_index,(control,attribute,amount) in enumerate([('FKHead_M','rotateY',15.0),('FKShoulder_L','rotateZ',25.0),('ctrlEye_L','blink',10.0),('ctrlEye_R','blink',10.0),('ctrlEye_L','blink',10.0)]):
  if case_index==4:
   cmds.setAttr('FKHead_M.rotateY',15.0);cmds.dgdirty(allPlugs=True);cmds.currentTime(2,edit=True,update=True);cmds.currentTime(1,edit=True,update=True)
  matches=cmds.ls(control,long=True) or []
  if len(matches)!=1:raise RuntimeError('Missing unique native control: '+control)
  plug=matches[0]+'.'+attribute
  if not cmds.getAttr(plug,settable=True):raise RuntimeError('Native control is not settable: '+plug)
  oldvalue=cmds.getAttr(plug)
  baseline={row['source']:pts(row['source']) for row in report['meshes']}
  cmds.setAttr(plug,oldvalue+amount);cmds.dgdirty(allPlugs=True);cmds.currentTime(2,edit=True,update=True);cmds.currentTime(1,edit=True,update=True)
  tests=[]
  for row in report['meshes']:
   a=pts(row['source']);b=pts(row['copy']);base=baseline[row['source']]
   errors=[(u-v).length() for u,v in zip(a,b)]
   movement=max((u-v).length() for u,v in zip(a,base))
   tests.append({'mesh':row['source'],'max_source_copy_error_cm':max(errors),'rms_error_cm':math.sqrt(sum(e*e for e in errors)/len(errors)),'max_source_motion_cm':movement})
  joint_world={}
  expected_points={}
  for row in report['meshes']:
   expected_points[row['source'].rsplit('|',1)[-1]]=[(p.x,p.y,p.z) for p in pts(row['source'])]
   for influence in skinfn(row['copied_skin']).influenceObjects():
    name=influence.partialPathName().rsplit('|',1)[-1]
    joint_world[name]=cmds.xform(influence.fullPathName(),query=True,worldSpace=True,matrix=True)
  runtime_snapshots.append({'name':control+'.'+attribute+('_Head15' if case_index==4 else ''),'joints':joint_world,'points':expected_points,'blink':[cmds.getAttr(blend+'.weight[0]'),cmds.getAttr(blend+'.weight[1]')]})
  cmds.setAttr(plug,oldvalue);cmds.dgdirty(allPlugs=True);cmds.currentTime(2,edit=True,update=True);cmds.currentTime(1,edit=True,update=True)
  if case_index==4:
   cmds.setAttr('FKHead_M.rotateY',0.0);cmds.dgdirty(allPlugs=True);cmds.currentTime(2,edit=True,update=True);cmds.currentTime(1,edit=True,update=True)
  report['control_deformation_tests'].append({'control':plug,'control_delta':amount,'units':('degrees' if attribute.startswith('rotate') else 'native_slider'),'meshes':tests})
  save()
 # Keep DG inputs intact but exclude controller curve shapes from transport.
 for curve in cmds.ls(type='nurbsCurve',long=True) or []:cmds.setAttr(curve+'.intermediateObject',True)
 cmds.loadPlugin('fbxmaya',quiet=True);mel.eval('FBXResetExport;')
 for s in ['FBXExportSkins -v true;','FBXExportShapes -v true;','FBXExportInputConnections -v false;','FBXExportIncludeChildren -v false;','FBXExportConstraints -v false;','FBXExportCameras -v false;','FBXExportLights -v false;','FBXExportEmbeddedTextures -v false;','FBXExportTriangulate -v false;']:
  mel.eval(s)
 cmds.select(duplicates+(cmds.ls(type='joint',long=True) or []),replace=True,noExpand=True)
 report['stage']='exporting';save()
 mel.eval('FBXExport -f "%s" -s;'%OUTPUT.as_posix())
 report['candidate_bytes']=OUTPUT.stat().st_size
 cmds.file(new=True,force=True)
 cmds.file(str(OUTPUT),open=True,force=True,ignoreVersion=True,executeScriptNodes=False,prompt=False)
 report['readback']={}
 for shape in cmds.ls(type='mesh',long=True) or []:
  if cmds.getAttr(shape+'.intermediateObject'):continue
  parent=cmds.listRelatives(shape,parent=True,fullPath=True)[0];name=parent.rsplit('|',1)[-1].rsplit(':',1)[-1]
  report['readback'][name]={'shape':shape,'vertices':cmds.polyEvaluate(shape,vertex=True),'skins':cmds.ls(cmds.listHistory(shape,pruneDagObjects=True) or [],type='skinCluster') or []}
 expected={p.rsplit('|',1)[-1]:n for p,n in old.MESHES.items()}
 report['readback_pass']=all(name in report['readback'] and report['readback'][name]['vertices']==n and report['readback'][name]['skins'] for name,n in expected.items()) and set(report['readback'])==set(expected)
 # Inspect FBX object types independently of Maya's reconstructed target helpers.
 import runpy
 previous_argv=sys.argv[:];sys.argv=['raw_weights',str(OUTPUT)]
 raw_result=runpy.run_path(str(Path(__file__).parent/'check_fbx_raw_weights.py'))['report']
 sys.argv=previous_argv
 report['raw_fbx_geometry_types']=raw_result['geometry_types']
 extra=set(report['readback'])-set(expected)
 report['legacy_exact_mesh_inventory_pass']=report['readback_pass']
 report['morph_target_helpers']=sorted(extra)
 report['readback_pass']=all(name in report['readback'] and report['readback'][name]['vertices']==n and report['readback'][name]['skins'] for name,n in expected.items()) and extra=={'Blink_L','Blink_R'} and raw_result['geometry_types']=={'Mesh':len(expected),'Shape':2}
 report['fbx_runtime_pose_tests']=[]
 for snapshot in runtime_snapshots:
  cmds.file(new=True,force=True);cmds.file(str(OUTPUT),open=True,force=True,ignoreVersion=True,executeScriptNodes=False,prompt=False)
  cmds.evaluationManager(mode='off')
  imported=[]
  for name,matrix in snapshot['joints'].items():
   matches=cmds.ls(name,type='joint',long=True) or []
   if len(matches)!=1:raise RuntimeError('FBX influence name is ambiguous/missing: '+name)
   imported.append((matches[0],matrix))
  for path,matrix in sorted(imported,key=lambda row:row[0].count('|')):cmds.xform(path,worldSpace=True,matrix=matrix)
  bodyshapes=cmds.ls('FilmExport:Dana_Body_GEO',long=True) or []
  bs=cmds.ls(cmds.listHistory(bodyshapes[0],pruneDagObjects=True) or [],type='blendShape') or []
  if len(bs)!=1:raise RuntimeError('Expected one imported body blink blendShape')
  aliases=cmds.aliasAttr(bs[0],query=True) or []
  for index,side in enumerate(['L','R']):
   matches=[aliases[i+1] for i in range(0,len(aliases),2) if aliases[i].endswith('Blink_'+side)]
   if len(matches)!=1:raise RuntimeError('Imported blink channel missing: '+side)
   cmds.setAttr(bs[0]+'.'+matches[0],snapshot['blink'][index])
  cmds.dgdirty(allPlugs=True);cmds.currentTime(2,edit=True,update=True);cmds.currentTime(1,edit=True,update=True)
  measurements=[]
  for name,expected_positions in snapshot['points'].items():
   values=cmds.xform('FilmExport:'+name+'.vtx[*]',query=True,worldSpace=True,translation=True)
   errors=[math.sqrt(sum((values[i*3+k]-p[k])**2 for k in range(3))) for i,p in enumerate(expected_positions)]
   measurements.append({'mesh':name,'max_native_fbx_error_cm':max(errors),'rms_error_cm':math.sqrt(sum(e*e for e in errors)/len(errors))})
  report['fbx_runtime_pose_tests'].append({'pose':snapshot['name'],'measurements':measurements,'max_error_cm':max(m['max_native_fbx_error_cm'] for m in measurements)})
  save()
 report['fbx_pose_gate_tolerance_cm']=0.01
 report['fbx_pose_gate_pass']=all(t['max_error_cm']<=0.01 for t in report['fbx_runtime_pose_tests'])
 report['deformation_tested']=True
 report['source_sha256_after']=hashlib.sha256(SOURCE.read_bytes()).hexdigest();report['source_unchanged']=report['source_sha256_before']==report['source_sha256_after']
 report['stage']='clean_skin_transport_checked_NOT_DEFORMATION_APPROVED';save()
 print(json.dumps({'stage':report['stage'],'readback_pass':report['readback_pass'],'meshes':report['readback'],'source_unchanged':report['source_unchanged']}))
except Exception:
 report['stage']='blocked';report['error']=traceback.format_exc();save();print(report['error']);raise
finally:
 cmds.file(new=True,force=True);maya.standalone.uninitialize()
