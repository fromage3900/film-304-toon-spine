"""Measured floor overlay for live Houdini Engine; existing floor retained."""
from pathlib import Path
import json,hou
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Tools/houdini/Published/Film304Closeout_20261018/Floor';OUT.mkdir(exist_ok=True)
path=OUT/'Film304_MeasuredFloor_v01.hda';assert not path.exists()
geo=hou.node('/obj').createNode('geo','Film304_MeasuredFloor')
for n in geo.children():n.destroy()
sub=geo.createNode('subnet','measured_floor')
p=sub.createNode('python','measured_tiles')
p.parm('python').set('''import hou,math
g=hou.pwd().geometry();g.clear()
mat=g.addAttrib(hou.attribType.Prim,'unreal_material','')
group=g.addAttrib(hou.attribType.Prim,'name','')
xmin,xmax=-382.788672,1056.220520
ymin,ymax=-580.343970,817.5
yaw=math.radians(-25);co,si=math.cos(yaw),math.sin(yaw)
pitch=80.;gap=.28;count=0
for ix in range(math.ceil((xmax-xmin)/pitch)):
 for iy in range(math.ceil((ymax-ymin)/pitch)):
  x0=xmin+ix*pitch+gap;x1=min(xmin+(ix+1)*pitch-gap,xmax-gap)
  y0=ymin+iy*pitch+gap;y1=min(ymin+(iy+1)*pitch-gap,ymax-gap)
  if x1<=x0 or y1<=y0:continue
  pts=[]
  for x,y,z in [(x0,y0,-.72),(x1,y0,-.72),(x1,y1,-.72),(x0,y1,-.72),(x0,y0,.08),(x1,y0,.08),(x1,y1,.08),(x0,y1,.08)]:
   wx,wy=co*x-si*y,si*x+co*y
   pt=g.createPoint();pt.setPosition((wx/100,z/100,wy/100));pts.append(pt)
  for face in [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]:
   prim=g.createPolygon();[prim.addVertex(pts[k]) for k in face]
   prim.setAttribValue(mat,'/Game/Materials/Recovery_Office_20261018/Floor/MI_FloorTile_'+('Warm' if (ix+iy)%5 else 'Cool')+'_v01')
   prim.setAttribValue(group,'FloorTile_%03d'%count)
  count+=1
''')
p.setDisplayFlag(True);p.setRenderFlag(True)
hda=sub.createDigitalAsset(name='film304::measured_floor::1.0',hda_file_name=str(path),description='Film304 Measured Office Floor Tiles',min_num_inputs=0,max_num_inputs=0)
p=hda.node('measured_tiles');p.cook(force=True)
assert len(p.geometry().prims())>0
hou.hipFile.save(str(OUT/'Film304_MeasuredFloor_v01.hip'))
(OUT/'native_floor_proof.json').write_text(json.dumps({'hda':str(path),'points':len(p.geometry().points()),'polygons':len(p.geometry().prims()),'room_yaw':-25,'tile_cm':80,'grout_gap_cm':.56,'overlay_top_cm':.08,'existing_floor_preserved':True},indent=2))
print('FLOOR_HDA_NATIVE_COOK_OK',len(p.geometry().prims()))
