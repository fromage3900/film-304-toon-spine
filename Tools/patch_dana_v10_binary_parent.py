import struct, json, hashlib, datetime
from pathlib import Path
ROOT=Path('G:/film-304-toon-spine')
SRC=ROOT/'Saved/OfflineIntake/20261017/task1_face_eyes/fbx/Dana_CleanSkin_v09.fbx'
OUT=ROOT/'Saved/OfflineIntake/20261017/task1_face_eyes/fbx/Dana_CleanSkin_v10d_FaceFollow.fbx'
LOCAL_REFERENCE=ROOT/'Saved/OfflineIntake/20261017/task1_face_eyes/fbx/Dana_CleanSkin_v10_FaceFollow.fbx'
REPORT=ROOT/'Saved/OfflineIntake/20261017/task1_face_eyes/report/v10d_binary_parent_patch.json'
MAGIC=b'Kaydara FBX Binary  \x00\x1a\x00'
def parse_file(data):
 if not data.startswith(MAGIC): raise ValueError('not binary FBX')
 ver=struct.unpack_from('<I',data,23)[0]
 if ver<7500: raise ValueError('parser requires FBX 7.5+ 64-bit nodes; got '+str(ver))
 nodes=[]
 def parse_node(pos,parent=''):
  start=pos
  end,nprop,proplen,nlen=struct.unpack_from('<QQQ B',data,pos); pos+=25
  if end==0 and nprop==0 and proplen==0 and nlen==0: return None,pos
  name=data[pos:pos+nlen].decode('utf8','replace');pos+=nlen;props=[]
  for _ in range(nprop):
   typ=chr(data[pos]);pos+=1; po=pos
   if typ=='C': v=bool(data[pos]);pos+=1
   elif typ=='Y': v=struct.unpack_from('<h',data,pos)[0];pos+=2
   elif typ=='I': v=struct.unpack_from('<i',data,pos)[0];pos+=4
   elif typ=='F': v=struct.unpack_from('<f',data,pos)[0];pos+=4
   elif typ=='D': v=struct.unpack_from('<d',data,pos)[0];pos+=8
   elif typ=='L': v=struct.unpack_from('<q',data,pos)[0];pos+=8
   elif typ in ('S','R'):
    n=struct.unpack_from('<I',data,pos)[0];pos+=4;v=data[pos:pos+n];pos+=n
   elif typ in ('b','c','d','f','i','l'):
    count,encoding,n=struct.unpack_from('<III',data,pos);pos+=12;v=None;pos+=n
   else: raise ValueError('unknown prop type '+repr(typ)+' at '+str(po))
   props.append({'type':typ,'value':v,'value_offset':po,'end_offset':pos})
  children=[]
  if pos<end:
   null=data[end-25:end]
   if null!=b'\0'*25: raise ValueError('bad node null record '+name+' '+str(end))
   while pos<end-25:
    ch,pos2=parse_node(pos,name)
    if ch is None: raise ValueError('unexpected child null '+name)
    children.append(ch);pos=pos2
   if pos!=end-25: raise ValueError('child parse mismatch '+name+' '+str(pos)+' '+str(end-25))
  elif pos!=end: raise ValueError('leaf property parse mismatch '+name+' '+str(pos)+' '+str(end))
  node={'name':name,'props':props,'children':children,'start':start,'end':end,'parent':parent}
  nodes.append(node);return node,end
 pos=27;root=[]
 while pos<len(data):
  node,pos2=parse_node(pos,'')
  if node is None: break
  root.append(node);pos=pos2
 return ver,root,nodes
def txt(p):
 v=p['value'];return v.decode('utf8','replace').split('\0')[0] if isinstance(v,bytes) else str(v)
source_hash=hashlib.sha256(SRC.read_bytes()).hexdigest(); raw=SRC.read_bytes();ver,roots,nodes=parse_file(raw)
refraw=LOCAL_REFERENCE.read_bytes();refver,refroots,refnodes=parse_file(refraw)
objects=next(n for n in roots if n['name']=='Objects'); conns=next(n for n in roots if n['name']=='Connections')
refobjects=next(n for n in refroots if n['name']=='Objects')
model_names={int(o['props'][0]['value']):txt(o['props'][1]) for o in objects['children'] if o['name']=='Model' and len(o['props'])>1}
follow_ids=[i for i,n in model_names.items() if n.split(':')[-1]=='FaceDeformationFollowHead']
head_ids=[i for i,n in model_names.items() if n.split(':')[-1]=='Head_M']
if len(follow_ids)!=1 or len(head_ids)!=1: raise RuntimeError(f'model lookup failed {follow_ids} {head_ids}')
fid,hid=follow_ids[0],head_ids[0]
connections=[]
for c in conns['children']:
 p=c['props']
 if c['name']=='C' and len(p)>=3 and txt(p[0])=='OO' and int(p[1]['value'])==fid:
  connections.append({'node':c,'child':fid,'parent':int(p[2]['value']),'parent_name':model_names.get(int(p[2]['value']))})
if len(connections)!=1: raise RuntimeError(f'expected one parent connection for follow node, got {connections}')
cn=connections[0]
if cn['parent']==hid: raise RuntimeError('already parented to Head_M; no patch needed')
if cn['parent_name'] is None or cn['parent_name'].split(':')[-1]!='FaceDeformationSystem': raise RuntimeError('unexpected existing parent '+repr(cn['parent_name']))
prop=cn['node']['props'][2]
if prop['type']!='L': raise RuntimeError('parent id is not FBX int64')
def find_model(objects, short_name):
 hits=[o for o in objects['children'] if o['name']=='Model' and len(o['props'])>1 and txt(o['props'][1]).split(':')[-1]==short_name]
 if len(hits)!=1: raise RuntimeError('model lookup '+short_name+' count='+str(len(hits)))
 return hits[0]
src_follow=find_model(objects,'FaceDeformationFollowHead');ref_follow=find_model(refobjects,'FaceDeformationFollowHead')
def transform_props(model):
 p70=next((c for c in model['children'] if c['name']=='Properties70'),None)
 result={}
 for p in p70['children'] if p70 else []:
  if p['name']=='P' and p['props'] and txt(p['props'][0]) in ('Lcl Translation','Lcl Rotation','Lcl Scaling'):
   key=txt(p['props'][0]); vals=[x for x in p['props'][1:] if x['type']=='D']
   if len(vals)==3: result[key]=vals
 return result
src_xf=transform_props(src_follow);ref_xf=transform_props(ref_follow)
if not all(k in ref_xf for k in ('Lcl Translation','Lcl Rotation')): raise RuntimeError('reference transform properties missing')
if not all(k in src_xf for k in ('Lcl Translation','Lcl Rotation')): raise RuntimeError('source transform properties missing')
out=bytearray(raw);struct.pack_into('<q',out,prop['value_offset'],hid)
patched_xf={}
for key in ('Lcl Translation','Lcl Rotation'):
 srcvals=src_xf[key]; refvals=ref_xf[key]
 for a,b in zip(srcvals,refvals): struct.pack_into('<d',out,a['value_offset'],float(b['value']))
 patched_xf[key]=[float(v['value']) for v in refvals]
if OUT.exists():
 if OUT.read_bytes()!=bytes(out): raise FileExistsError('Existing candidate differs; preserved: '+str(OUT))
else: OUT.write_bytes(out)
# Parse candidate fresh and confirm exact directed parent; compare all bytes except the one ID field.
raw2=OUT.read_bytes();ver2,roots2,nodes2=parse_file(raw2);obj2=next(n for n in roots2 if n['name']=='Objects');con2=next(n for n in roots2 if n['name']=='Connections')
names2={int(o['props'][0]['value']):txt(o['props'][1]) for o in obj2['children'] if o['name']=='Model' and len(o['props'])>1}
found=[]
for c in con2['children']:
 p=c['props']
 if c['name']=='C' and len(p)>=3 and txt(p[0])=='OO' and int(p[1]['value'])==fid:found.append(names2.get(int(p[2]['value'])))
if found!=[next(n for i,n in names2.items() if i==hid)]: raise RuntimeError('candidate parent readback failed '+repr(found))
changed=[i for i,(a,b) in enumerate(zip(raw,raw2)) if a!=b]
allowed=[range(prop['value_offset'],prop['value_offset']+8)]+[range(v['value_offset'],v['value_offset']+8) for k in ('Lcl Translation','Lcl Rotation') for v in src_xf[k]]
if not changed or not all(any(i in rg for rg in allowed) for i in changed): raise RuntimeError('unexpected byte change offsets '+repr(changed[:20]))
report={'tool':'v10d_binary_parent_patch.py','source':str(SRC),'candidate':str(OUT),'local_transform_reference':str(LOCAL_REFERENCE),'stage':'patched_pending_maya_readback','fbx_version':ver,'source_sha256':source_hash,'source_sha256_after':hashlib.sha256(SRC.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(raw2).hexdigest(),'source_unchanged':hashlib.sha256(SRC.read_bytes()).hexdigest()==source_hash,'follow_model_id':fid,'head_model_id':hid,'parent_before':cn['parent_name'],'parent_after':found[0],'parent_id_field_offset':prop['value_offset'],'local_transform_values_from_rest_preserving_maya_reparent':patched_xf,'changed_bytes':len(changed),'only_parent_and_local_transform_fields_changed':all(any(i in rg for rg in allowed) for i in changed),'source_bytes':len(raw),'candidate_bytes':len(raw2),'at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
REPORT.write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2))


