import maya.standalone
maya.standalone.initialize(name='python')
from maya import cmds,mel
from pathlib import Path
p=Path(r'G:/film-304-toon-spine/Saved/OfflineIntake/20261017/task1_face_eyes/held_pose/Dana_HeldPose_v05_24fps.fbx')
if not cmds.pluginInfo('fbxmaya',q=True,loaded=True):cmds.loadPlugin('fbxmaya')
mel.eval('FBXResetImport;');cmds.file(str(p),i=True,type='FBX',ignoreVersion=True,namespace='Dbg',options='fbx')
out={'time':cmds.currentTime(q=True),'range':[cmds.playbackOptions(q=True,min=True),cmds.playbackOptions(q=True,max=True)],'anim_nodes':{t:len(cmds.ls(type=t) or []) for t in ['animCurve','animCurveTA','animCurveTL','animCurveTT','animCurveTU']},'curves':[]}
for j in cmds.ls(type='joint',long=True) or []:
 if j.rsplit('|',1)[-1].split(':')[-1] in ['Wrist_L','Shoulder_L','Root_M']:
  row={'j':j}
  for a in ['tx','ty','tz','rx','ry','rz']:
   row[a]={'keys':cmds.keyframe(j+'.'+a,q=True,tc=True) or [],'vals':cmds.keyframe(j+'.'+a,q=True,vc=True) or []}
  out['curves'].append(row)
for f in [0,1,2,3]:
 cmds.currentTime(f,e=True,update=True)
 out.setdefault('frames',{})[str(f)]={n:cmds.xform(j,q=True,ws=True,t=True) for n,j in [(j.rsplit('|',1)[-1].split(':')[-1],j) for j in cmds.ls(type='joint',long=True) or [] if j.rsplit('|',1)[-1].split(':')[-1] in ['Wrist_L','Wrist_R','Shoulder_L']]}
print(out)
cmds.file(new=True,force=True);maya.standalone.uninitialize()
