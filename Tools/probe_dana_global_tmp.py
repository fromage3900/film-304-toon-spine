exec(open('Tools/patch_dana_v10_binary_parent.py',encoding='utf8').read().split("source_hash=")[0])
for path in [ROOT/'Saved/OfflineIntake/20261017/task1_face_eyes/fbx/Dana_CleanSkin_v09.fbx',ROOT/'Saved/OfflineIntake/20261017/task1_face_eyes/fbx/Dana_CleanSkin_v10_FaceFollow.fbx']:
 v,r,n=parse_file(path.read_bytes());g=next(x for x in r if x['name']=='GlobalSettings');p=next((x for x in g['children'] if x['name']=='Properties70'),None)
 print(path.name)
 for x in p['children'] if p else []:
  if x['name']=='P' and x['props'] and txt(x['props'][0]) in ('UpAxis','UpAxisSign','FrontAxis','FrontAxisSign','CoordAxis','CoordAxisSign','UnitScaleFactor','OriginalUnitScaleFactor','TimeMode'):
   print(txt(x['props'][0]),[q['value'] for q in x['props'][1:]])
