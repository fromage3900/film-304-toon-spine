"""Layer retargeted donor micro-motion onto the user's exact staged cast poses."""
import json
import math
import shutil
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir());OUT=ROOT/'Saved/Audit/Film304Idle_20261017'
DEST='/Game/Animations/Film304Idle_20261017'
AP=unreal.AnimPoseExtensions
FRAMES=48;FPS=24

def qlist(q):return [q.x,q.y,q.z,q.w]
def multiply(a,b):
    x,y,z,w=a;X,Y,Z,W=b
    return [w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z]
def inverse(a):return [-a[0],-a[1],-a[2],a[3]]
def weighted(q,weight):
    if q[3]<0:q=[-v for v in q]
    angle=math.acos(max(-1,min(1,q[3])))
    if abs(math.sin(angle))<1e-8:return [0,0,0,1]
    factor=math.sin(angle*weight)/math.sin(angle)
    return [q[0]*factor,q[1]*factor,q[2]*factor,math.cos(angle*weight)]
def xyz(v):return [v.x,v.y,v.z]
def dist(a,b):return sum((x-y)**2 for x,y in zip(xyz(a),xyz(b)))**.5
def options(mesh):
    o=unreal.AnimPoseEvaluationOptions();o.set_editor_properties({'should_retarget':False,'extract_root_motion':False,'optional_skeletal_mesh':mesh,'evaluate_curves':True});return o

def main():
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_path_name().split('.')[0]=='/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office'
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    bindings={}
    for actor in actors:
        for comp in actor.get_components_by_class(unreal.SkeletalMeshComponent):
            mesh=comp.get_skinned_asset()
            if not mesh:continue
            for char in ['Dana','David','Sam','Spider']:
                if ('/'+char+'/' in mesh.get_path_name()):bindings.setdefault(char,[]).append((actor,comp,mesh))
    assert set(bindings)=={'Dana','David','Sam','Spider'},bindings.keys()
    receipt={'world':world.get_path_name(),'frames':48,'endpoint_samples':49,'fps':24,'characters':{},'assigned':False}
    for char,items in bindings.items():
        actor,comp,mesh=items[0]
        data=comp.get_editor_property('animation_data');base=data.anim_to_play
        evaluation=options(mesh)
        pose=AP.get_anim_pose_at_time(base,data.saved_position,evaluation) if base else AP.get_reference_pose(mesh.skeleton)
        names=[str(n) for n in AP.get_bone_names(pose)]
        base_transforms={n:AP.get_bone_pose(pose,n,unreal.AnimPoseSpaces.LOCAL) for n in names}
        donor=None;donor_poses=[]
        if char!='Spider':
            take='Sitting_Idle_Loop_48f' if char=='David' else 'Idle_Loop_48f_Anim'
            donor=unreal.load_asset('/Game/Retarget/Film304Idle_20261017/RawRetarget/'+char+'/'+char+'_UAL_'+take)
            assert donor
            donor_poses=[AP.get_anim_pose_at_time(donor,donor.get_play_length()*i/FRAMES,evaluation) for i in range(FRAMES+1)]
        name='AS_'+char+'_OfficeIdle_48f_v01'
        assert not unreal.EditorAssetLibrary.does_asset_exist(DEST+'/'+name),'Existing output: inspect before replacing'
        factory=unreal.AnimSequenceFactory();factory.target_skeleton=mesh.skeleton;factory.preview_skeletal_mesh=mesh
        seq=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,DEST,unreal.AnimSequence,factory)
        ctrl=seq.controller
        ctrl.open_bracket('Film 304 donor idle over staged pose',False)
        ctrl.set_frame_rate(unreal.FrameRate(numerator=120,denominator=1),False)
        ctrl.set_frame_rate(unreal.FrameRate(numerator=FPS,denominator=1),False)
        ctrl.set_number_of_frames(unreal.FrameNumber(FRAMES),False)
        driven={}
        for bone in names:
            t=base_transforms[bone];rot=qlist(t.rotation)
            positions=[t.translation]*(FRAMES+1);scales=[t.scale3d]*(FRAMES+1);rotations=[]
            weight=0
            if char!='Spider':
                weight={'Head_M':0.85,'Neck_M':0.25,'NeckPart1_M':0.15,'NeckPart2_M':0.15}.get(bone,0)
                if bone in ['Spine1_M','Spine2_M','Chest_M'] and char!='Dana':weight=0.25
                if char=='Sam' and bone in ['Scapula_L','Scapula_R']:weight=0.2
            for i in range(FRAMES+1):
                phase=2*math.pi*i/FRAMES
                q=rot
                if weight:
                    a=qlist(AP.get_bone_pose(donor_poses[0],bone,unreal.AnimPoseSpaces.LOCAL).rotation)
                    b=qlist(AP.get_bone_pose(donor_poses[i],bone,unreal.AnimPoseSpaces.LOCAL).rotation)
                    q=multiply(rot,weighted(multiply(inverse(a),b),weight))
                if char=='Spider' and bone in ['wolfSpider_Head','wolfSpider_Thorax','wolfSpider_fangA_L_a','wolfSpider_fangA_R_a']:
                    amplitude=0.8 if bone=='wolfSpider_Head' else 0.5
                    angle=math.radians(amplitude)*math.sin(phase)
                    q=multiply(rot,[math.sin(angle/2),0,0,math.cos(angle/2)])
                rotations.append(unreal.Quat(*q))
                if bone=='Chest_M':
                    breath=1+0.0012*math.sin(phase)
                    scales[i]=unreal.Vector(t.scale3d.x*breath,t.scale3d.y*breath,t.scale3d.z*breath)
            rotations[-1]=rotations[0];scales[-1]=scales[0]
            if weight or (char=='Spider' and 'Head' in bone):driven[bone]=weight
            assert ctrl.add_bone_curve(bone,False)
            assert ctrl.set_bone_track_keys(bone,positions,rotations,scales,False),bone
        ctrl.close_bracket(False)
        morphs={str(n) for n in mesh.get_all_morph_target_names()}
        if {'Blink_L','Blink_R'}<=morphs:
            for side,offset in [('L',0),('R',0.015)]:
                curve='Blink_'+side
                unreal.AnimationLibrary.add_curve(seq,curve)
                times=[i/FPS for i in range(FRAMES+1)]
                values=[max(0,math.cos((t-1.15-offset)/0.145*math.pi/2))**2 if abs(t-1.15-offset)<0.145 else 0 for t in times]
                unreal.AnimationLibrary.add_float_curve_keys(seq,curve,times,values)
                unreal.AnimationLibrary.add_curve_meta_data(mesh.skeleton,curve)
                unreal.AnimationLibrary.set_curve_meta_data_morph_target(mesh.skeleton,curve,True)
            assert unreal.EditorAssetLibrary.save_loaded_asset(mesh.skeleton)
        assert unreal.EditorAssetLibrary.save_loaded_asset(seq)
        receipt['characters'][char]={'mesh':mesh.get_path_name(),'base_pose':base.get_path_name() if base else 'native_reference',
            'animation':seq.get_path_name(),'donor':donor.get_path_name() if donor else 'native spider secondary motion',
            'driven':driven,'actors':[a.get_path_name() for a,_,_ in items],'bones':len(names)}
        (OUT/'scene_idle_build.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps(receipt))

if __name__=='__main__':main()
