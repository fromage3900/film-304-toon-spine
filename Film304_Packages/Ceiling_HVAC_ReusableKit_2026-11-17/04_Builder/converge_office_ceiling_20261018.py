"""Reuse the measured ceiling builder, verifying native winding and correcting FBX up-axis.

Run only in a separate Hython process. Original source and published assets are preserved.
"""
import hashlib
import json
from pathlib import Path
import hou

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'Tools/build_office_ceiling.py'
OUT = ROOT/'Saved/Houdini/OfficeCeiling_Closeout_20261018_v03'
REPORT = ROOT/'Saved/Audit/Closeout_20261018/ceiling_native_convergence.json'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    assert not (OUT/'OfficeCeiling_Converged_v03.hip').exists(), 'Existing native publish; inspect before rebuilding'
    source = SOURCE.read_text(encoding='utf-8')
    old = 'OUT_DIR = r"G:\\film-304-toon-spine\\Content\\Meshes\\Architecture"'
    assert source.count(old)==1
    source = source.replace(old, 'OUT_DIR = '+repr(str(OUT)))
    assert source.count('for i in face:')==1
    # Houdini's polygon convention is clockwise. Keep the source winding and
    # verify actual hou primitive normals rather than assuming cross-product order.
    # Converge the detailed existing service builder with the full-room T-bars.
    # Keep original hand-placed fixtures, so no second diffuser/housing set is emitted.
    start=source.index('for k, y in enumerate(')
    end=source.index('out_metal = publish',start)
    source=source[:start]+source[end:]
    service_source=(ROOT/'Tools/houdini/bake_cinematic_cubicle_ceiling.py').read_text(encoding='utf-8')
    service_code=service_source.split("code = r'''",1)[1].split("'''",1)[0]
    ducts=service_code[service_code.index('duct_y ='):service_code.index('# 3. Suspended')]
    conduits=service_code[service_code.index('for cx in [-0.2'):]
    # Route trunk/branch ducts to the service aisle to clear the six hero fixtures.
    # Conduits remain on separate lanes and below the concrete tile plenum.
    ducts=ducts.replace('add_box(', 'add_hvac_box(')
    conduits=conduits.replace('[-0.2, 2.2, 4.8]', '[-1.5, 3.4, 7.0]').replace('3.42','3.30').replace('add_box(', 'add_conduit_box(')
    injection='''
def add_hvac_box(cx,cy,cz,sx,sy,sz,material):
    place(metal,(cx+2.60)*100,cz*100,cy*100,sx*100,sz*100,sy*100)
def add_conduit_box(cx,cy,cz,sx,sy,sz,material):
    place(metal,cx*100,cz*100,cy*100,sx*100,sz*100,sy*100)
exec(converged_service_code, dict(add_hvac_box=add_hvac_box,add_conduit_box=add_conduit_box,
     MAT_METAL='metal',z_start=-3.0,z_end=8.5,trunk_len=11.5))
'''
    source=source.replace('out_metal = publish',injection+'\nout_metal = publish',1)
    source = source.replace('    fbx.parm("execute").pressButton()',
        '    fbx.parm("axissystem").set(2)  # Explicit Z-up right-handed metadata\n'
        '    fbx.parm("exportkind").set(0)  # Binary FBX\n'
        '    fbx.parm("execute").pressButton()')
    ns = {'__name__':'ceiling_native_reuse','__file__':str(SOURCE),'converged_service_code':ducts+'\n'+conduits}
    exec(compile(source,str(SOURCE),'exec'),ns)
    assert ns['ok'], 'Original measured geometry gate failed'
    rows=[]
    for material,node,stem in ns['GROUPS']:
        geo=node.node('OUT').geometry()
        primitives=list(geo.prims()); points=list(geo.points())
        bad=[]
        # Each box consists of 8 points and 6 quads in the reused builder.
        for index,prim in enumerate(primitives):
            box=index//6
            center=sum((p.position() for p in points[box*8:box*8+8]),hou.Vector3())/8
            face=sum((v.point().position() for v in prim.vertices()),hou.Vector3())/len(prim.vertices())
            if prim.normal().dot(face-center)<=0: bad.append(index)
        assert not bad, (stem,'inward faces',bad[:8])
        bbox=geo.boundingBox()
        fbx=OUT/(stem+'.fbx')
        assert fbx.exists() and fbx.stat().st_size>1000
        rows.append({'source_stem':stem,'material_class':material,'points':len(points),
            'quads':len(primitives),'inward_faces':len(bad),
            'bounds_min_cm':list(bbox.minvec()),'bounds_max_cm':list(bbox.maxvec()),
            'fbx':str(fbx),'fbx_bytes':fbx.stat().st_size,
            'sha256':hashlib.sha256(fbx.read_bytes()).hexdigest()})
    hip=OUT/'OfficeCeiling_Converged_v03.hip'
    hou.hipFile.save(str(hip))
    result={'source':str(SOURCE),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'native_hip':str(hip),'room_cm':2200,'room_yaw_baked_degrees':-25,
        'fbx_axis':'Z-up right-handed','convert_units':False,'convert_axis':False,
        'reuses_existing_troffers':True,'hvac_source':str(ROOT/'Tools/houdini/bake_cinematic_cubicle_ceiling.py'),
        'hvac_details':['two trunk ducts','cross branches','joint flanges','threaded hangers','conduit runs','junction boxes'],
        'service_aisle_offset_x_cm':260,'meshes':rows,'unreal_import_verified':False}
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
