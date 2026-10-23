"""Isolated transport test, deliberately NOT a production rig export."""
import hou, json, hashlib, traceback
from pathlib import Path
out=Path('G:/film-304-toon-spine/Saved/Audit/HoudiniDanaHidden_20261016')
report={'stage':'starting','production_ready':False,'purpose':'Native FBX transport capability and packed body inspection only; no rebinding or source mutation'}
def save(): (out/'roundtrip.json').write_text(json.dumps(report,indent=2,default=str))
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
try:
    source='C:/Users/froma/Downloads/C_DanaRenderTest_OSC.fbx'
    report['source_sha256_before']=digest(source)
    hou.hipFile.load(str(out/'Dana_HiddenGeometry_Probe.hip'),suppress_save_prompt=True)
    geo=hou.node('/obj/DANA_FBX_READONLY_PROBE')
    imp=geo.node('Existing_Dana_FBX')
    rest=geo.node('INSPECT_rest_geometry')
    geometry=rest.geometry()
    report['body_primitives']=[]
    for prim in geometry.prims():
        name=prim.attribValue('name')
        if 'Body' in name:
            data={'name':name,'type':str(prim.type()),'outer_points':len(prim.points())}
            if prim.type()==hou.primType.PackedGeometry:
                inner=prim.geometry()
                data['inner_points']=len(inner.points())
                data['inner_attributes']=[a.name() for a in inner.pointAttribs()]
            report['body_primitives'].append(data)
    export=geo.node('INSPECT_EXPORT_PARAMETERS_ONLY')
    report['export_input_labels']=export.inputLabels()
    # Native node accepts rest geometry, capture skeleton, and animated skeleton.
    for i in range(3): export.setInput(i,imp,i)
    filename=out/'Dana_FULL_IMPORT_TRANSPORT_TEST_NOT_PRODUCTION.fbx'
    export.parm('outputfilepath').set(str(filename))
    report['clip_range_options']=list(zip(export.parm('cliprangemode').menuItems(),export.parm('cliprangemode').menuLabels()))
    export.parm('f1').deleteAllKeyframes(); export.parm('f1').set(1)
    export.parm('f2').deleteAllKeyframes(); export.parm('f2').set(1)
    report['stage']='exporting'; save()
    export.parm('execute').pressButton()
    report['export_errors']=export.errors();report['export_warnings']=export.warnings()
    if not filename.exists() or filename.stat().st_size==0: raise RuntimeError('Native exporter produced no FBX')
    report['fbx_bytes']=filename.stat().st_size
    reimport=geo.createNode('kinefx::fbxcharacterimport','TRANSPORT_READBACK')
    reimport.parm('fbxfile').set(str(filename));reimport.parm('importinvisibleshapes').set(True)
    reimport.cook(force=True)
    report['readback_errors']=reimport.errors();report['readback_warnings']=reimport.warnings()
    readback=[]
    for i in range(3):
        n=geo.createNode('null','READBACK_'+str(i));n.setInput(0,reimport,i)
        g=n.geometry()
        data={'output':i,'points':len(g.points()),'primitives':len(g.prims()),'has_capture':bool(g.findPointAttrib('boneCapture'))}
        if i==0 and g.findPrimAttrib('name'):
            counts={}
            for name in g.primStringAttribValues('name'):counts[name]=counts.get(name,0)+1
            data['mesh_primitive_counts']=counts
        readback.append(data)
    report['readback']=readback
    report['source_sha256_after']=digest(source)
    report['source_unchanged']=report['source_sha256_before']==report['source_sha256_after']
    report['stage']='native_transport_readback_complete_NOT_RIG_APPROVED'
    hou.hipFile.save(str(out/'Dana_Transport_Roundtrip_NOT_PRODUCTION.hip'))
except Exception:report['stage']='transport_blocked';report['error']=traceback.format_exc()
save()
print(json.dumps({k:v for k,v in report.items() if k not in ['readback']},indent=2,default=str))
