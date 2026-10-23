import maya.standalone,hashlib,json,datetime,traceback
maya.standalone.initialize(name='python')
from maya import cmds,mel
from pathlib import Path
root=Path(r'G:/film-304-toon-spine')
scene=root/'Saved/OfflineIntake/20261017/task1_face_eyes/held_pose/Dana_HeldPose_Candidate_v05.mb'
out=root/'Saved/OfflineIntake/20261017/task1_face_eyes/held_pose/Dana_HeldPose_v07_24fps.fbx'
report=root/'Saved/OfflineIntake/20261017/task1_face_eyes/held_pose/Dana_HeldPose_v07_export_report.json'
r={'scene':str(scene),'candidate':str(out),'stage':'starting'}
try:
 cmds.file(str(scene),o=True,force=True)
 if not cmds.pluginInfo('fbxmaya',q=True,loaded=True):cmds.loadPlugin('fbxmaya')
 cmds.currentUnit(time='film');cmds.playbackOptions(min=1,max=2,animationStartTime=1,animationEndTime=2)
 dag_nodes=cmds.ls(dag=True,long=True) or []
 cmds.select(dag_nodes,replace=True)
 r['selected_count']=len(cmds.ls(selection=True,long=True) or []);r['selected_joint_count']=len(cmds.ls(selection=True,type='joint',long=True) or [])
 mel.eval('FBXResetExport;')
 opts=['FBXExportSkins -v true;','FBXExportShapes -v true;','FBXExportInputConnections -v true;','FBXExportIncludeChildren -v true;','FBXExportAnimationOnly -v false;','FBXExportBakeComplexAnimation -v true;','FBXExportBakeComplexStart -v 1;','FBXExportBakeComplexEnd -v 2;','FBXExportBakeComplexStep -v 1;','FBXExportConstraints -v false;','FBXExportCameras -v false;','FBXExportLights -v false;','FBXExportEmbeddedTextures -v false;','FBXExportTriangulate -v false;']
 for o in opts:mel.eval(o)
 mel.eval('FBXExport -f "%s" -s;'%out.as_posix())
 r.update({'size':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'scene_keyframes':len(cmds.ls(type='animCurve') or []),'status':'exported'})
except Exception:r['status']='error';r['error']=traceback.format_exc()
finally:
 report.write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps(r,indent=2));
 try:cmds.file(new=True,force=True);maya.standalone.uninitialize()
 except:pass
