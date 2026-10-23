"""Converge existing ceiling geometry against measured walls and fixture centres."""
import json,math
from pathlib import Path
import hou

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Tools/houdini/Published/Film304Closeout_20261018/MainOfficeFit_v05'
data=json.loads((ROOT/'Saved/Audit/Closeout_20261018/main_room_ceiling_fit_input.json').read_text())
assert not (OUT/'main_room_fit.json').exists()
OUT.mkdir(parents=True,exist_ok=True)
source=(ROOT/'Tools/build_office_ceiling.py').read_text()
prefix=source[:source.index('# --------------------------------------------------- 1. ceiling')]
ns={'__name__':'existing_ceiling_helpers'};exec(compile(prefix,'existing_ceiling_helpers','exec'),ns)
place=ns['place'];xmin,xmax,ymin,ymax=data['interior_local_cm']
co,si=math.cos(math.radians(data['yaw'])),math.sin(math.radians(data['yaw']))
def local(p):return p[0]*co+p[1]*si,-p[0]*si+p[1]*co,p[2]
def lines(lo,hi,origin,pitch):
    return [lo]+[origin+i*pitch for i in range(math.floor((lo-origin)/pitch)+1,math.ceil((hi-origin)/pitch))]+[hi]
# Existing fixture centres are 125 cm across and 120 cm between rows.
fx,fy,_=data['fixtures_local_cm'][0]
xs=lines(xmin,xmax,fx-62.5,125);ys=lines(ymin,ymax,fy-60,120)
tiles=hou.Geometry();metal=hou.Geometry()
for x0,x1 in zip(xs,xs[1:]):
    for y0,y1 in zip(ys,ys[1:]):
        if x1-x0>2.4 and y1-y0>2.4:
            place(tiles,(x0+x1)/2,(y0+y1)/2,337.5,x1-x0-2.4,y1-y0-2.4,1.6)
for x in xs:place(metal,x,(ymin+ymax)/2,334.6,2.4,ymax-ymin,3.6)
for y in ys:place(metal,(xmin+xmax)/2,y,334.6,xmax-xmin,2.4,3.6)
# Retain the existing native detailed HVAC boxes, clipping only wall overrun.
old=hou.Geometry();old.loadFromFile(str(ROOT/'Tools/houdini/Published/Film304Closeout_20261018/Ceiling/geometry/CeilMetal.bgeo.sc'))
points=list(old.points());retained=0
for offset in range(42*8,len(points),8):
    group=[local(p.position()) for p in points[offset:offset+8]]
    low=[min(p[i] for p in group) for i in range(3)];high=[max(p[i] for p in group) for i in range(3)]
    low[0]=max(low[0],xmin);high[0]=min(high[0],xmax);low[1]=max(low[1],ymin);high[1]=min(high[1],ymax)
    if high[0]<=low[0] or high[1]<=low[1]:continue
    place(metal,*[(low[i]+high[i])/2 for i in range(3)],*[(high[i]-low[i]) for i in range(3)]);retained+=1
rows=[]
for name,geo in [('Tiles',tiles),('Metal',metal)]:
    for p in geo.points():
        x,y,z=local(p.position());assert xmin-1.21<=x<=xmax+1.21 and ymin-1.21<=y<=ymax+1.21
    for i,prim in enumerate(geo.prims()):
        box=list(geo.points())[i//6*8:i//6*8+8];center=sum((p.position() for p in box),hou.Vector3())/8
        face=sum((v.point().position() for v in prim.vertices()),hou.Vector3())/len(prim.vertices())
        assert prim.normal().dot(face-center)>0
    # FBX right-to-left conversion mirrors Y in Unreal. Rebuild each box in
    # mirrored export coordinates, retaining outward winding, so UE recovers
    # the exact measured world coordinates rather than the opposite room yaw.
    export_geo=hou.Geometry()
    ns['YAW']=25.;ns['_CY']=math.cos(math.radians(25));ns['_SY']=math.sin(math.radians(25))
    points=list(geo.points())
    for offset in range(0,len(points),8):
        group=[local(p.position()) for p in points[offset:offset+8]]
        low=[min(p[i] for p in group) for i in range(3)];high=[max(p[i] for p in group) for i in range(3)]
        cx,cy,cz=[(low[i]+high[i])/2 for i in range(3)]
        place(export_geo,cx,-cy,cz,*[(high[i]-low[i]) for i in range(3)])
    ns['YAW']=-25.;ns['_CY']=co;ns['_SY']=si
    geo.saveToFile(str(OUT/(name+'_UE_Target.bgeo.sc')))
    bgeo=OUT/(name+'.bgeo.sc');export_geo.saveToFile(str(bgeo))
    obj=hou.node('/obj').createNode('geo','MainOffice_'+name);f=obj.createNode('file','OUT');f.parm('file').set(str(bgeo));f.setDisplayFlag(True);f.setRenderFlag(True)
    rop=obj.createNode('rop_fbx','EXPORT');rop.setInput(0,f);rop.parm('sopoutput').set(str(OUT/(name+'.fbx')))
    rop.parm('axissystem').set(2);rop.parm('convertunits').set(0);rop.parm('convertaxis').set(0);rop.parm('execute').pressButton()
    rows.append({'part':name,'points':len(geo.points()),'quads':len(geo.prims()),'min':list(geo.boundingBox().minvec()),'max':list(geo.boundingBox().maxvec())})
hou.hipFile.save(str(OUT/'MainOffice_CeilingFit_v05.hip'))
report={'input':data,'grid_pitch_cm':[125,120],'grid_phase_fixture_1':data['fixtures_local_cm'][0],'retained_hvac_boxes':retained,'meshes':rows,'native_winding_and_wall_bounds_verified':True}
(OUT/'main_room_fit.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
