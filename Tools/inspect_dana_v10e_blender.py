import bpy,json
from pathlib import Path
p=Path(r'G:/film-304-toon-spine/Saved/OfflineIntake/20261017/task1_face_eyes/fbx/Dana_CleanSkin_v10e_InputConnections.fbx')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(p),use_anim=False)
print(json.dumps({'version':bpy.app.version_string,'objects':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'verts':len(o.data.vertices) if o.type=='MESH' else None,'bones':len(o.data.bones) if o.type=='ARMATURE' else None,'armature_mods':[m.object.name for m in o.modifiers if m.type=='ARMATURE'],'materials':[m.name if m else None for m in o.data.materials] if o.type=='MESH' else None} for o in bpy.data.objects],'armatures':[{'name':a.name,'bones':len(a.data.bones),'sample':[(n,a.data.bones.get(n).head_local[:],a.data.bones.get(n).tail_local[:],a.data.bones.get(n).matrix_local[:]) for n in ['Shoulder_L','Elbow_L','Wrist_L','Shoulder_R','Head_M','Root_M'] if a.data.bones.get(n)]} for a in bpy.data.objects if a.type=='ARMATURE']},indent=2))
