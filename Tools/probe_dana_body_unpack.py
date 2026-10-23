import hou,json,traceback
from pathlib import Path
out=Path('G:/film-304-toon-spine/Saved/Audit/HoudiniDanaHidden_20261016')
r={'stage':'initializing','production_ready':False}
try:
 hou.hipFile.load(str(out/'Dana_HiddenGeometry_Probe.hip'),suppress_save_prompt=True)
 geo=hou.node('/obj/DANA_FBX_READONLY_PROBE')
 select=geo.createNode('python','BODY_ONLY_ISOLATED')
 select.setInput(0,geo.node('INSPECT_rest_geometry'))
 select.parm('python').set("import hou\ng=hou.pwd().geometry()\ng.deletePrims([p for p in g.prims() if 'Dana_Body_GEOBase' not in p.attribValue('name')],keep_points=False)")
 unpack=geo.createNode('unpack','BODY_REAL_VERTICES');unpack.setInput(0,select)
 g=unpack.geometry()
 r['select_errors']=select.errors();r['unpack_errors']=unpack.errors()
 if g is None:raise RuntimeError(str(r))
 r.update({'points':len(g.points()),'primitives':len(g.prims()),'point_attributes':[a.name() for a in g.pointAttribs()], 'unpack_parameters':{p.name():p.eval() for p in unpack.parms() if p.parmTemplate().type()!=hou.parmTemplateType.Button}})
 capture=g.findPointAttrib('boneCapture')
 if capture:
  r['weighted_points']=sum(any(v[i]>=0 and v[i+1]>1e-6 for i in range(0,len(v)-1,2)) for v in [p.attribValue(capture) for p in g.points()])
 else:r['weighted_points']=0
 r['errors']=unpack.errors();r['warnings']=unpack.warnings();r['stage']='unpacked_body_measured'
 r['note']='Packed prim.geometry() returns its owning geometry, not packed contents; ignore inner_points/inner_attributes in earlier roundtrip.json. This SOP unpack measurement is the actual body geometry.'
 hou.hipFile.save(str(out/'Dana_Body_Unpack_Proof.hip'))
except Exception:r['stage']='blocked';r['error']=traceback.format_exc()
(out/'body_unpack.json').write_text(json.dumps(r,indent=2,default=str));print(json.dumps(r,indent=2,default=str))
