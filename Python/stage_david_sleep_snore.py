"""Bind facial variants and stage a small translucent snore cloud in Sequencer."""
import json
import math
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir());OUT=ROOT/'Saved/Audit/Film304Idle_20261017'
DEST='/Game/Sequences/Film304Idle_20261017'

def cloud_material():
    path='/Game/Materials/Film304Idle_20261017/M_DavidSnorePuff_v01'
    m=unreal.load_asset(path)
    if not m:m=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_DavidSnorePuff_v01','/Game/Materials/Film304Idle_20261017',unreal.Material,unreal.MaterialFactoryNew())
    m.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property('two_sided',True)
    lib=unreal.MaterialEditingLibrary
    lib.delete_all_material_expressions(m)
    color=lib.create_material_expression(m,unreal.MaterialExpressionConstant3Vector,-400,-200)
    color.constant=unreal.LinearColor(.14,.22,.32,1)
    fresnel=lib.create_material_expression(m,unreal.MaterialExpressionFresnel,-600,100);fresnel.set_editor_property('exponent',1.2)
    inv=lib.create_material_expression(m,unreal.MaterialExpressionOneMinus,-400,100)
    opacity=lib.create_material_expression(m,unreal.MaterialExpressionMultiply,-200,100);opacity.set_editor_property('const_b',.97)
    assert lib.connect_material_expressions(fresnel,'',inv,'')
    assert lib.connect_material_expressions(inv,'',opacity,'A')
    # Reuse the project's native Substrate unlit pattern. This build exposes
    # EmissiveColor/TransmittanceColor rather than the older BaseColor/Opacity.
    trans=lib.create_material_expression(m,unreal.MaterialExpressionOneMinus,0,140)
    rgb=lib.create_material_expression(m,unreal.MaterialExpressionMultiply,0,-120)
    bsdf=lib.create_material_expression(m,unreal.MaterialExpressionSubstrateUnlitBSDF,240,0)
    assert lib.connect_material_expressions(opacity,'',trans,'')
    assert lib.connect_material_expressions(color,'',rgb,'A')
    assert lib.connect_material_expressions(opacity,'',rgb,'B')
    assert lib.connect_material_expressions(rgb,'',bsdf,'EmissiveColor')
    assert lib.connect_material_expressions(trans,'',bsdf,'TransmittanceColor')
    assert lib.connect_material_property(bsdf,'',unreal.MaterialProperty.MP_FRONT_MATERIAL)
    lib.recompile_material(m);assert unreal.EditorAssetLibrary.save_loaded_asset(m)
    return m

def main():
    assert not (OUT/'sleep_scene_stage.json').exists(), 'Stage already exists; inspect before changing its actors or bindings'
    unreal.LevelSequenceEditorBlueprintLibrary.close_level_sequence()
    original=unreal.load_asset(DEST+'/LS_OfficeCast_Idles_48f_v01')
    seq=unreal.load_asset(DEST+'/LS_OfficeCast_SleepFaces_48f_v02')
    if not seq:seq=unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset('LS_OfficeCast_SleepFaces_48f_v02',DEST,original)
    variants=json.loads((OUT/'facial_sleep_variants.json').read_text())
    build=json.loads((OUT/'scene_idle_build.json').read_text())
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    bypath={a.get_path_name():a for a in actors.get_all_level_actors()}
    for char,v in variants.items():
        clip=unreal.load_asset(v['animation'])
        for path in build['characters'][char]['actors']:
            a=bypath[path];c=a.get_component_by_class(unreal.SkeletalMeshComponent)
            a.modify();c.modify();c.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
            c.animation_data=unreal.SingleAnimationPlayData(anim_to_play=clip,saved_looping=True,saved_playing=True,saved_position=0,saved_play_rate=1)
            c.set_animation(clip);c.play(True);c.set_update_animation_in_editor(True)
        for binding in seq.get_bindings():
            for track in binding.get_tracks():
                if isinstance(track,unreal.MovieSceneSkeletalAnimationTrack):
                    for section in track.get_sections():
                        params=section.params
                        if params.animation and params.animation.get_path_name()==v['previous']:
                            params.animation=clip;section.params=params
    material=cloud_material();sphere=unreal.load_asset('/Engine/BasicShapes/Sphere')
    cloud=[]
    for index,(offset,ratio) in enumerate([((0,0,0),1),((2.9,.3,.6),.72),((-2.6,-.2,.9),.73),((.2,.2,-3),.30)]):
        a=next((a for a in actors.get_all_level_actors() if a.get_actor_label()=='Film_David_SnorePuff_'+str(index+1)),None)
        if not a:a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(-144,-79,79))
        a.set_actor_label('Film_David_SnorePuff_'+str(index+1));a.set_folder_path('Film304/CharacterBeats/DavidSleep')
        c=a.static_mesh_component;c.set_static_mesh(sphere);c.set_material(0,material);c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);c.set_cast_shadow(False)
        a.set_actor_scale3d(unreal.Vector(.0001,.0001,.0001))
        binding=seq.add_possessable(a);track=binding.add_track(unreal.MovieScene3DTransformTrack);section=track.add_section();section.set_range(0,48)
        channels=section.get_all_channels()
        for i in range(49):
            phase=i/48
            size=(math.sin(math.pi*phase)**2)*.060*ratio
            values=[-144+offset[0]+5*phase,-79+offset[1]+2*math.sin(math.pi*phase),79+offset[2]+12*phase,0,0,0,max(.0001,size),max(.0001,size),max(.0001,size)]
            for channel,value in zip(channels,values):channel.add_key(unreal.FrameNumber(i),value,interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
        cloud.append(a.get_path_name())
    cam=actors.spawn_actor_from_class(unreal.CineCameraActor,unreal.Vector(-235,-165,104))
    cam.set_actor_label('Film_Cam_David_DeskSleep');cam.set_folder_path('Film304/CharacterBeats/DavidSleep')
    cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(cam.get_actor_location(),unreal.Vector(-146,-77,70)),False)
    cine=cam.get_cine_camera_component();cine.current_focal_length=38;cine.current_aperture=8
    focus=cine.focus_settings;focus.focus_method=unreal.CameraFocusMethod.DISABLE;cine.focus_settings=focus
    assert unreal.EditorAssetLibrary.save_loaded_asset(seq)
    result={'sequence':seq.get_path_name(),'cloud_actors':cloud,'camera':cam.get_path_name(),
            'cloud':'four softly edged translucent puff lobes, rising 12cm and shrinking to invisibility at loop seam',
            'duration_seconds':2,'frames':48,'map_saved':False,'visual_gate':False}
    (OUT/'sleep_scene_stage.json').write_text(json.dumps(result,indent=2))
    unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(seq)
    unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(20)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_set_viewport_realtime(True)
    print(json.dumps(result))

if __name__=='__main__':main()
