"""Read-only native Dana rig inspection; no source save or export."""
import json,hashlib,traceback,datetime
from pathlib import Path
source=Path('G:/Film304_AssetIntake_20261016_Source/3rd Year Film/Rigs/Temp/Dana_Rig_v1.5/Dana_Rig_v1.5.mb')
out=Path('G:/film-304-toon-spine/Saved/Audit/MayaDanaNative_20261016')
out.mkdir(parents=True,exist_ok=True)
r={'source':str(source),'source_modified':False,'scene_scripts_enabled':False,'stage':'starting','at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
def write(): (out/'inspection.json').write_text(json.dumps(r,indent=2,default=str))
write()
try:
 r['source_sha256_before']=hashlib.sha256(source.read_bytes()).hexdigest()
 import maya.standalone
 r['stage']='initializing_maya';write()
 maya.standalone.initialize(name='python')
 from maya import cmds
 import maya.api.OpenMaya as om
 import maya.api.OpenMayaAnim as oma
 r['maya_version']=cmds.about(version=True)
 r['stage']='opening_native_scene';write()
 cmds.file(str(source),open=True,force=True,ignoreVersion=True,executeScriptNodes=False,loadReferenceDepth='none',prompt=False)
 r['references']=cmds.file(query=True,reference=True) or []
 r['joints']=len(cmds.ls(type='joint') or [])
 r['mesh_shapes']=[]
 for shape in cmds.ls(type='mesh',long=True) or []:
  r['mesh_shapes'].append({'shape':shape,'vertices':cmds.polyEvaluate(shape,vertex=True),'intermediate':bool(cmds.getAttr(shape+'.intermediateObject')),'skin_history':cmds.ls(cmds.listHistory(shape,pruneDagObjects=True) or [],type='skinCluster') or []})
 r['skin_clusters']=[]
 r['stage']='measuring_native_skin';write()
 for name in cmds.ls(type='skinCluster') or []:
  selection=om.MSelectionList();selection.add(name)
  fn=oma.MFnSkinCluster(selection.getDependNode(0))
  influences=fn.influenceObjects()
  entry={'name':name,'influences':[p.fullPathName() for p in influences],'geometries':[]}
  for obj in fn.getOutputGeometry():
   dag=om.MDagPath.getAPathTo(obj)
   if not dag.node().hasFn(om.MFn.kMesh):continue
   mesh=om.MFnMesh(dag);n=mesh.numVertices
   compfn=om.MFnSingleIndexedComponent();component=compfn.create(om.MFn.kMeshVertComponent);compfn.setCompleteData(n)
   weights,count=fn.getWeights(dag,component)
   weighted=0;active=set();minsum=None;maxsum=None
   for i in range(n):
    row=weights[i*count:(i+1)*count]
    total=sum(row);minsum=total if minsum is None else min(minsum,total);maxsum=total if maxsum is None else max(maxsum,total)
    if total>1e-6:weighted+=1
    active.update(j for j,w in enumerate(row) if w>1e-6)
   entry['geometries'].append({'shape':dag.fullPathName(),'vertices':n,'weighted_vertices':weighted,'weight_sum_min':minsum,'weight_sum_max':maxsum,'active_influences':[influences[j].partialPathName() for j in sorted(active)]})
  r['skin_clusters'].append(entry);write()
 r['source_sha256_after']=hashlib.sha256(source.read_bytes()).hexdigest()
 r['source_unchanged']=r['source_sha256_before']==r['source_sha256_after']
 r['stage']='native_scene_skin_inspected';r['deformation_tested']=False;r['export_tested']=False;write()
 print(json.dumps({'stage':r['stage'],'meshes':len(r['mesh_shapes']),'skin_clusters':len(r['skin_clusters']),'source_unchanged':r['source_unchanged']}))
 cmds.file(new=True,force=True)
 maya.standalone.uninitialize()
except Exception:
 r['stage']='native_inspection_blocked';r['error']=traceback.format_exc();write();print(r['error'])
