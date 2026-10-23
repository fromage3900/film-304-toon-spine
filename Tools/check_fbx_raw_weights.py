"""Read-only FBX binary cluster weights; distinguishes file data from importer behavior."""
from pathlib import Path
import sys,struct,zlib,json
raw=Path(sys.argv[1]).read_bytes();pos=23
assert raw.startswith(b'Kaydara FBX Binary  \x00')
version=struct.unpack_from('<I',raw,pos)[0];pos+=4
wide=version>=7500;header='<QQQB' if wide else '<IIIB';size=25 if wide else 13
def value():
 global pos
 t=chr(raw[pos]);pos+=1
 fmts={'Y':'h','C':'?','I':'i','F':'f','D':'d','L':'q'}
 if t in fmts:
  fmt='<'+fmts[t];v=struct.unpack_from(fmt,raw,pos)[0];pos+=struct.calcsize(fmt);return v
 if t in 'SR':
  n=struct.unpack_from('<I',raw,pos)[0];pos+=4;b=raw[pos:pos+n];pos+=n;return b.decode('utf8',errors='replace') if t=='S' else b
 if t in 'fdlibc':
  n,enc,length=struct.unpack_from('<III',raw,pos);pos+=12;b=raw[pos:pos+length];pos+=length
  if enc:b=zlib.decompress(b)
  fmt={'f':'f','d':'d','l':'q','i':'i','b':'?','c':'b'}[t]
  return struct.unpack('<'+str(n)+fmt,b)
 raise RuntimeError('Unknown FBX property '+t)
def node():
 global pos
 end,count,length,nlen=struct.unpack_from(header,raw,pos);pos+=size
 if end==0:return None
 name=raw[pos:pos+nlen].decode();pos+=nlen;props=[value() for _ in range(count)];children=[]
 while pos<end-size:
  c=node()
  if c:children.append(c)
  else:break
 pos=end;return (name,props,children)
roots=[]
while pos+size<len(raw):
 n=node()
 if not n:break
 roots.append(n)
objects=next(n for n in roots if n[0]=='Objects')[2]
connections=next(n for n in roots if n[0]=='Connections')[2]
parents={}
for _,p,_ in connections:
 if len(p)>=3 and p[0]=='OO':parents.setdefault(p[1],[]).append(p[2])
skins={n[1][0]:n for n in objects if n[0]=='Deformer' and n[1][2]=='Skin'}
clusters={n[1][0]:n for n in objects if n[0]=='Deformer' and n[1][2]=='Cluster'}
rows=[]
models={p[0]:p[1].split('\x00')[0] for kind,p,ch in objects if kind=='Model'}
for kind,p,ch in objects:
 if kind!='Geometry' or p[2]!='Mesh':continue
 vertices=next((len(v[0])//3 for k,v,_ in ch if k=='Vertices'),0)
 weights=[0.0]*vertices;entries=0
 skids={sid for sid in skins if p[0] in parents.get(sid,[])}
 for cid,(_,cp,cc) in clusters.items():
  if not skids.intersection(parents.get(cid,[])):continue
  inds=next((v[0] for k,v,_ in cc if k=='Indexes'),[]);vals=next((v[0] for k,v,_ in cc if k=='Weights'),[])
  assert len(inds)==len(vals)
  for i,w in zip(inds,vals):weights[i]+=w;entries+=1
 rows.append({'mesh':next((models[m] for m in parents.get(p[0],[]) if m in models),p[1].split('\x00')[0]),'vertices':vertices,'skin_count':len(skids),'weighted_vertices':sum(w>0 for w in weights),'weight_entries':entries,'min_sum':min(weights) if weights else None,'max_sum':max(weights) if weights else None})
types={}
for kind,p,ch in objects:
 if kind=='Geometry':types[p[2]]=types.get(p[2],0)+1
report={'fbx_version':version,'source':sys.argv[1],'geometry_types':types,'meshes':rows}
target=Path(sys.argv[1]).with_suffix('.raw_weights.json');target.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=1))
