exec(open('Tools/patch_dana_v10_binary_parent.py',encoding='utf8').read().split("source_hash=")[0])
for path in [ROOT/'Saved/OfflineIntake/20261017/task1_face_eyes/fbx/Dana_CleanSkin_v09.fbx', ROOT/'Saved/OfflineIntake/20261017/task1_face_eyes/fbx/Dana_CleanSkin_v10_FaceFollow.fbx']:
 ver,roots,nodes=parse_file(path.read_bytes()); objects=next(n for n in roots if n['name']=='Objects')
 print('\n',path.name)
 for o in objects['children']:
  if o['name']=='Model' and len(o['props'])>1 and txt(o['props'][1]).split(':')[-1] in ('FaceDeformationFollowHead','Head_M'):
   print('\nMODEL',txt(o['props'][1]))
   p70=next((c for c in o['children'] if c['name']=='Properties70'),None)
   for p in (p70['children'] if p70 else []):
    if p['name']=='P' and p['props']: print(txt(p['props'][0]), [(x['type'],x['value']) for x in p['props'][1:]])
