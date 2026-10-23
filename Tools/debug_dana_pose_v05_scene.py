import maya.standalone
maya.standalone.initialize(name='python')
from maya import cmds
p=r'G:/film-304-toon-spine/Saved/OfflineIntake/20261017/task1_face_eyes/held_pose/Dana_HeldPose_Candidate_v05.mb'
cmds.file(p,o=True,force=True)
print('current',cmds.currentTime(q=True),'curves',len(cmds.ls(type='animCurve') or []),'joint',len(cmds.ls(type='joint') or []),'transforms',len(cmds.ls(type='transform') or []))
for j in cmds.ls(type='joint',long=True) or []:
 if j.rsplit('|',1)[-1] in ['Wrist_L','Shoulder_L','Root_M']:
  print(j,[(a,cmds.getAttr(j+'.'+a),cmds.keyframe(j+'.'+a,q=True,tc=True) or []) for a in ['tx','ty','tz','rx','ry','rz']])
cmds.file(new=True,force=True);maya.standalone.uninitialize()
