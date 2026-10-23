"""Extract existing UAL takes into periodic 48-frame donor loops (Blender)."""
import json
import math
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector, Quaternion

ROOT=Path('G:/film-304-toon-spine')
SOURCE=Path('C:/EnvironmentPortfolio/BS_GodFile/Imports/Animations/Cascadeur/Inbox/A_CAS_Melusina_Idle_Loop.fbx')
OUT=ROOT/'Saved/OfflineIntake/20261017/idle_donors'

def periodic(values):
    values=np.asarray(values)
    spectrum=np.fft.rfft(values,axis=0)
    spectrum[4:]=0
    result=np.fft.irfft(spectrum,n=len(values),axis=0)
    return np.concatenate([result,result[:1]],axis=0)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report=[]
    for take in ['Idle_Loop','Sitting_Idle_Loop']:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=str(SOURCE),use_anim=True,use_image_search=False)
        arm,=[o for o in bpy.data.objects if o.type=='ARMATURE']
        action,=[a for a in bpy.data.actions if a.name.rsplit('|',1)[-1]==take]
        arm.animation_data.action=action
        arm.animation_data.action_slot=action.slots[0]
        start,end=action.frame_range
        samples={b.name:[] for b in arm.pose.bones}
        for i in range(48):
            f=start+(end-start)*i/48
            bpy.context.scene.frame_set(int(f),subframe=f-int(f))
            bpy.context.view_layer.update()
            for b in arm.pose.bones:
                loc,q,scale=b.matrix_basis.decompose()
                if q.w<0:q.negate()
                samples[b.name].append(list(loc)+list(q.to_exponential_map())+list(scale))
        filtered={n:periodic(v) for n,v in samples.items()}
        arm.animation_data_clear()
        for a in list(bpy.data.actions):bpy.data.actions.remove(a)
        bpy.context.scene.render.fps=24
        bpy.context.scene.frame_start=0;bpy.context.scene.frame_end=48
        for i in range(49):
            bpy.context.scene.frame_set(i)
            for b in arm.pose.bones:
                v=filtered[b.name][i]
                b.rotation_mode='QUATERNION'
                b.location=Vector(v[:3]);b.rotation_quaternion=Quaternion(Vector(v[3:6]));b.scale=Vector(v[6:])
                for prop in ['location','rotation_quaternion','scale']:b.keyframe_insert(prop,frame=i,group=b.name)
        # A joint-marker mesh is a source-rig transport aid, never a film character.
        verts=[];faces=[]
        for b in arm.data.bones:
            h=b.head_local
            index=len(verts)
            verts += [h+Vector((0,0,0)),h+Vector((0.005,0,0)),h+Vector((0,0.005,0))]
            faces.append((index,index+1,index+2))
        data=bpy.data.meshes.new('UAL_JointMarkers');data.from_pydata(verts,[],faces)
        mesh=bpy.data.objects.new('SK_UAL_DonorMarkers',data);bpy.context.collection.objects.link(mesh)
        mesh.matrix_world=arm.matrix_world.copy();mesh.parent=arm
        mod=mesh.modifiers.new('Skin','ARMATURE');mod.object=arm
        for i,b in enumerate(arm.data.bones):mesh.vertex_groups.new(name=b.name).add([3*i,3*i+1,3*i+2],1,'REPLACE')
        bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);mesh.select_set(True)
        bpy.context.view_layer.objects.active=arm
        target=OUT/('UAL_'+take+'_48f.fbx')
        bpy.ops.export_scene.fbx(filepath=str(target),use_selection=True,object_types={'ARMATURE','MESH'},
            add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,
            bake_anim_simplify_factor=0,axis_forward='-Y',axis_up='Z')
        report.append({'take':take,'output':str(target),'intervals':48,'samples':49,'fps':24,
                       'filter':'first three Fourier harmonics; periodic position and rotation-vector fit',
                       'source_modified':False,'donor_marker_mesh_only':True})
    (OUT/'preparation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report))

if __name__=='__main__':main()
