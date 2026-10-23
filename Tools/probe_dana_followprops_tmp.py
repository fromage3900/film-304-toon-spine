exec(open('Tools/patch_dana_v10_binary_parent.py',encoding='utf8').read().split("source_hash=")[0])
for path in [ROOT/'Saved/OfflineIntake/20261017/task1_face_eyes/fbx/Dana_CleanSkin_v09.fbx', ROOT/'Saved/OfflineIntake/20261017/task1_face_eyes/fbx/Dana_CleanSkin_v10_FaceFollow.fbx']:
 v,r,n=parse_file(path.read_bytes()); obj=next(x for x in r if x['name']=='Objects')
 m=next(o for o in obj['children'] if o['name']=='Model' and len(o['props'])>1 and txt(o['props'][1]).split(':')[-1]=='FaceDeformationFollowHead')
 p70=next(x for x in m['children'] if x['name']=='Properties70')
 print(path.name,[(txt(p['props'][0]),[q['value'] for q in p['props'][1:]]) for p in p70['children'] if p['name']=='P' and p['props']])
