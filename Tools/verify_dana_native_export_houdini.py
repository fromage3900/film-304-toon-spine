"""Read-only independent native-export check. Hython SCRIPT CANDIDATE.fbx.

Data checks only: does not certify animation, facial behavior or render quality.
Writes evidence beneath Humber Saved/Audit; never changes the input FBX.
"""
import sys,json,hashlib,traceback
from pathlib import Path
import hou
source=Path(sys.argv[1]).resolve()
if source.suffix.lower()!='.fbx' or not source.is_file():raise RuntimeError('Supply an existing isolated FBX candidate')
out=Path('G:/film-304-toon-spine/Saved/Audit/MayaDanaRoundtrip_20261016')/source.stem
out.mkdir(parents=True,exist_ok=True)
r={'source':str(source),'stage':'starting','production_ready':False,'deformation_tested':False,'animation_retarget_tested':False}
def save():(out/'verification.json').write_text(json.dumps(r,indent=2,default=str))
def digest():return hashlib.sha256(source.read_bytes()).hexdigest()
save()
try:
 r['source_sha256_before']=digest()
 geo=hou.node('/obj').createNode('geo','DANA_NATIVE_EXPORT_READBACK')
 imp=geo.createNode('kinefx::fbxcharacterimport','CANDIDATE_READ_ONLY')
 imp.parm('fbxfile').set(source.as_posix())
 imp.parm('importinvisibleshapes').set(False)
 imp.cook(force=True)
 g=imp.geometry()
 r['import_errors']=imp.errors();r['import_warnings']=imp.warnings()
 if g is None:raise RuntimeError('Native importer did not return geometry')
 capture=g.findPointAttrib('boneCapture')
 meshes={}
 for prim in g.prims():
  name=prim.attribValue('name') if g.findPrimAttrib('name') else 'UNNAMED'
  simple=name.rsplit(':',1)[-1]
  m=meshes.setdefault(simple,{'names':set(),'points':set(),'polygons':0,'packed_primitives':0,'blink_morph_targets':[]})
  m['names'].add(name)
  if prim.type()==hou.primType.PackedGeometry:
   channel=prim.attribValue('blendshape_channel') if g.findPrimAttrib('blendshape_channel') else ''
   target=prim.attribValue('blendshape_name') if g.findPrimAttrib('blendshape_name') else ''
   suffix=channel.rsplit('.',1)[-1]
   if simple=='Dana_Body_GEO' and suffix in ['Blink_L','Blink_R'] and target.endswith('.'+suffix):
    m['blink_morph_targets'].append({'channel':channel,'target':target})
   else:m['packed_primitives']+=1
  else:
   m['polygons']+=1
   m['points'].update(p.number() for p in prim.points())
 result={}
 points=g.points()
 for name,m in meshes.items():
  weighted=0;max_influences=0;minimum=None;maximum=None
  for index in m['points']:
   v=points[index].attribValue(capture) if capture else []
   weights=[v[i+1] for i in range(0,len(v)-1,2) if v[i]>=0 and v[i+1]>1e-6]
   total=sum(weights);weighted+=bool(weights);max_influences=max(max_influences,len(weights))
   minimum=total if minimum is None else min(minimum,total);maximum=total if maximum is None else max(maximum,total)
  result[name]={'names':sorted(m['names']),'polygon_points':len(m['points']),'polygons':m['polygons'],'packed_primitives':m['packed_primitives'],'blink_morph_targets':m['blink_morph_targets'],'weighted_vertices':weighted,'max_influences_per_vertex':max_influences,'weight_sum_min':minimum,'weight_sum_max':maximum}
 r['meshes']=result
 required={'Dana_Body_GEO':9249,'Dana_Eye_Lf_GEO':1121,'Dana_Eye_Rt_GEO':1121,'Dana_Cornea_Lf_GEO':161,'Dana_Cornea_Rt_GEO':161,'Dana_EyeInt_Lf_GEO':51,'Dana_EyeInt_Rt_GEO':51,'Dana_Eyelashes_Lf_GEO':39,'Dana_Eyelashes_Rt_GEO':39}
 if len(sys.argv)>2:
  required=json.loads(Path(sys.argv[2]).read_text())
  r['required_profile']=sys.argv[2]
 checks={}
 for name,count in required.items():
  m=result.get(name,{})
  checks[name]=bool(m.get('polygon_points')==count and m.get('weighted_vertices')==count and not m.get('packed_primitives') and m.get('weight_sum_min',0)>=0.999 and m.get('weight_sum_max',2)<=1.001)
 r['required_mesh_data_checks']=checks
 r['unwanted_meshes']=[n for n in result if n=='Dana_Body_GEOBase' or n.endswith('Region') or n.startswith(('FK','IK'))]
 r['unexpected_render_meshes']=[n for n,m in result.items() if m['polygon_points'] and n not in required]
 r['unexpected_packed_meshes']=[n for n,m in result.items() if m['packed_primitives']]
 r['all_required_mesh_data_pass']=all(checks.values()) and not r['import_errors'] and not r['unwanted_meshes'] and not r['unexpected_render_meshes'] and not r['unexpected_packed_meshes']
 for i,label in [(1,'capture_skeleton'),(2,'animated_hierarchy')]:
  n=geo.createNode('null',label);n.setInput(0,imp,i);s=n.geometry()
  r[label]={'points':len(s.points()),'primitives':len(s.prims())}
 r['source_sha256_after']=digest();r['source_unchanged']=r['source_sha256_before']==r['source_sha256_after']
 r['stage']='mesh_skin_data_checked_NEEDS_DEFORMATION_PROOF'
 hou.hipFile.save(str(out/'Independent_Readback.hip'))
except Exception:r['stage']='verification_blocked';r['error']=traceback.format_exc()
save()
print(json.dumps({k:v for k,v in r.items() if k not in ['meshes']},indent=2,default=str))
