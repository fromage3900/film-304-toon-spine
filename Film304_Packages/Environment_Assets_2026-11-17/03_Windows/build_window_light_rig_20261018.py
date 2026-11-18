"""Publish a small live HDA instancing native window-shaft spot lights."""
import json
from pathlib import Path
import hou

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Saved/Houdini/WindowLightRig_20261018'
OUT.mkdir(parents=True,exist_ok=True)
HDA=OUT/'Film304_WindowLightRig_v01.hda'
assert not HDA.exists(), 'Already published'
subnet=hou.node('/obj').createNode('subnet','film304_window_light_rig')
geo=subnet.createNode('geo','window_light_points')
py=geo.createNode('python','measured_window_lights')
code='''
import hou, math
g=hou.pwd().geometry();g.clear()
instance=g.addAttrib(hou.attribType.Point,'unreal_instance','')
orient=g.addAttrib(hou.attribType.Point,'orient',(0.0,0.0,0.0,1.0))
name=g.addAttrib(hou.attribType.Point,'name','')
g.addAttrib(hou.attribType.Point,'unreal_uproperty_Intensity',350.0)
g.addAttrib(hou.attribType.Point,'unreal_uproperty_VolumetricScatteringIntensity',3.0)
g.addAttrib(hou.attribType.Global,'unreal_force_instancer',1)
# UE cm -> Houdini metres, with Y as native up. All lights sit inside the glass.
windows=[(-371.195442,145.216991),(-273.993242,353.667782),(-176.791042,562.118573)]
dx,dy=math.cos(math.radians(-25)),math.sin(math.radians(-25))
direction=hou.Vector3(dx,-.48,dy).normalized()
rotation=hou.Quaternion(hou.Vector3(1,0,0).matrixToRotateTo(direction))
for i,(x,y) in enumerate(windows):
    p=g.createPoint();p.setPosition(((x+dx*22)/100,2.55,(y+dy*22)/100))
    p.setAttribValue(instance,'/Game/Blueprints/Film304Closeout_20261018/BP_Film_WindowShaftLight_v01.BP_Film_WindowShaftLight_v01_C')
    p.setAttribValue(orient,tuple(rotation));p.setAttribValue(name,'WindowShaft_%02d'%(i+1))
'''
py.parm('python').set(code);py.setDisplayFlag(True);py.setRenderFlag(True)
asset=subnet.createDigitalAsset(name='film304::window_light_rig::1.0',hda_file_name=str(HDA),
                               description='Film304 Window Shafts — Measured Native Lights',min_num_inputs=0,max_num_inputs=0)
asset.node('window_light_points/measured_window_lights').cook(force=True)
points=asset.node('window_light_points/measured_window_lights').geometry().points()
assert len(points)==3
hou.hipFile.save(str(OUT/'Film304_WindowLightRig_v01.hip'))
print(json.dumps({'hda':str(HDA),'point_count':len(points),'native_houdini_cook':True,
                  'live_unreal_cook_verified':False}))
