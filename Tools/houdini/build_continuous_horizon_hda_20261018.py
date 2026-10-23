"""Supplement the existing city kit with continuous distant massing, emissive panes and ground."""
from pathlib import Path
import hou,json
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Tools/houdini/Published/Film304Closeout_20261018/ContinuousHorizon';OUT.mkdir(exist_ok=True)
target=OUT/'Film304_ContinuousHorizon_v01.hda';assert not target.exists()
geo=hou.node('/obj').createNode('geo','Film304_ContinuousHorizon')
for n in geo.children():n.destroy()
sub=geo.createNode('subnet','continuous_horizon');p=sub.createNode('python','city_rings_ground_windows')
p.parm('python').set('''import hou,math,random
g=hou.pwd().geometry();g.clear();rng=random.Random(304)
mat=g.addAttrib(hou.attribType.Prim,'unreal_material','')
base='/Game/Materials/Recovery_Office_20261018/City/'
body=base+'MI_CityConcrete_Night_v01';window=base+'MI_CityWindows_Emissive_v01';road=base+'MI_CityRoad_Wet_v01';ground=base+'MI_CityGround_v01'
def point(x,y,z):
 p=g.createPoint();p.setPosition((x/100,z/100,y/100));return p
def quad(coords,material):
 prim=g.createPolygon()
 for xyz in coords:prim.addVertex(point(*xyz))
 prim.setAttribValue(mat,material)
def box(cx,cy,lo,w,d,h,material):
 x0,x1=cx-w/2,cx+w/2;y0,y1=cy-d/2,cy+d/2;hi=lo+h
 v=[(x0,y0,lo),(x1,y0,lo),(x1,y1,lo),(x0,y1,lo),(x0,y0,hi),(x1,y0,hi),(x1,y1,hi),(x0,y1,hi)]
 for face in [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]:quad([v[i] for i in face],material)
 return x0,x1,y0,y1,hi
z=-5500.
box(0,0,z-100,1200000,1200000,100,ground)
for offset in range(-98000,98001,14000):
 box(offset,0,z+.3,1100,210000,.8,road)
 box(0,offset,z+.3,210000,1100,.8,road)
# Rings overlap in projected angular coverage; heights remain independent and irregular.
for radius,count,hmin,hmax,phase in [(80000,48,4200,9500,.13),(190000,80,6500,14500,.51),(420000,128,11000,22500,.27)]:
 arc=2*math.pi*radius/count
 for i in range(count):
  theta=(i+phase)*2*math.pi/count;rr=radius+rng.uniform(-.035,.035)*radius
  cx,cy=math.cos(theta)*rr,math.sin(theta)*rr
  w=arc*rng.uniform(1.1,1.45);d=arc*rng.uniform(.55,.95);h=rng.uniform(hmin,hmax)
  x0,x1,y0,y1,top=box(cx,cy,z,w,d,h,body)
  # Actual separate emissive facade panes, with stable occupancy and no texture dependency.
  step=520.;floor=520.;pane=190.;ph=270.
  for level in range(1,int(h/floor)):
   zz=z+level*floor
   for side in range(4):
    length=w if side<2 else d
    for j in range(1,int(length/step)):
     if rng.random()>.24:continue
     if side<2:
      x=x0+j*step;y=y0-2 if side==0 else y1+2
      pts=[(x,y,zz),(x+pane,y,zz),(x+pane,y,zz+ph),(x,y,zz+ph)]
     else:
      y=y0+j*step;x=x0-2 if side==2 else x1+2
      pts=[(x,y,zz),(x,y+pane,zz),(x,y+pane,zz+ph),(x,y,zz+ph)]
     quad(pts,window)
''')
p.setDisplayFlag(True);p.setRenderFlag(True)
hda=sub.createDigitalAsset(name='film304::continuous_horizon::1.0',hda_file_name=str(target),description='Film304 Continuous City Horizon - Ground / Three Rings / Emissive Windows',min_num_inputs=0,max_num_inputs=0)
p=hda.node('city_rings_ground_windows');p.cook(force=True)
hou.hipFile.save(str(OUT/'Film304_ContinuousHorizon_v01.hip'))
report={'hda':str(target),'ring_buildings':[48,80,128],'ring_radii_cm':[80000,190000,420000],'coverage_degrees':360,'ground_elevation_cm':-5500,'ground_span_cm':1200000,'point_count':len(p.geometry().points()),'polygons':len(p.geometry().prims()),'existing_kit_preserved':True,'visual_coverage_gate':'pending multi-heading Unreal renders'}
(OUT/'native_continuous_horizon_proof.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
