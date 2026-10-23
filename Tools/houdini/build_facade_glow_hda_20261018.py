from pathlib import Path
import hou,json,shutil
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Tools/houdini/Published/Film304Closeout_20261018/FacadeGlow';OUT.mkdir(exist_ok=True)
data=ROOT/'Saved/Audit/Closeout_20261018/city_facade_window_raycasts.json'
if data.exists():shutil.copy2(data,OUT/'facade_raycasts.json')
panes=json.loads((OUT/'facade_raycasts.json').read_text())['panes'];assert panes
target=OUT/'Film304_FacadeGlow_v01.hda';assert not target.exists()
geo=hou.node('/obj').createNode('geo','Film304_FacadeGlow')
for n in geo.children():n.destroy()
sub=geo.createNode('subnet','facade_glow');p=sub.createNode('python','collision_fitted_panes')
code='import hou,json\npanes=json.loads('+repr(json.dumps(panes))+')\n'
code+='''g=hou.pwd().geometry();g.clear()
mat=g.addAttrib(hou.attribType.Prim,'unreal_material','/Game/Materials/Recovery_Office_20261018/City/MI_CityWindows_Emissive_v01')
for item in panes:
 x,y,z=item['p'];nx,ny,nz=item['n'];tx,ty=-ny,nx;w=item['width']/2;h=item['height']/2
 prim=g.createPolygon()
 for sx,sz in [(-1,-1),(1,-1),(1,1),(-1,1)]:
  q=g.createPoint();q.setPosition(((x+tx*sx*w)/100,(z+sz*h)/100,(y+ty*sx*w)/100));prim.addVertex(q)
'''
p.parm('python').set(code);p.setDisplayFlag(True);p.setRenderFlag(True)
h=sub.createDigitalAsset(name='film304::facade_glow::1.0',hda_file_name=str(target),description='Film304 Raycast Fitted Emissive City Windows',min_num_inputs=0,max_num_inputs=0)
h.node('collision_fitted_panes').cook(force=True);hou.hipFile.save(str(OUT/'Film304_FacadeGlow_v01.hip'));print('COLLISION_FITTED_WINDOW_PANES',len(panes))
