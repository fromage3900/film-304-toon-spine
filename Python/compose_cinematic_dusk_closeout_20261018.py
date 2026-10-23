"""A closer hero composition and a restrained fifth light study, preserving prior shots."""
import json
from pathlib import Path
import unreal

import film304_fog

def main():
    root=Path(unreal.Paths.project_dir());actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert 'L_Film_Office_Assembly_20261018_v02.' in world.get_path_name()
    assert not unreal._closeout_mrq_executor.is_rendering()
    lib=unreal.VariantManagerLibrary
    lvs=unreal.load_asset('/Game/Variants/Film304Closeout_20261018/LVS_Office_LightingCloseout_v01')
    variants=lvs.get_variant_set(0);assert variants.get_num_variants()==4
    bylabel={a.get_actor_label():a for a in actors.get_all_level_actors()}
    def capture(variant,actor,displays):
        lib.add_actor_binding(variant,actor)
        available=lib.get_capturable_properties(actor)
        for display in displays:
            matches=[p for p in available if p.endswith(' / '+display) and p.count(' / ')==1]
            assert len(matches)==1,(actor.get_actor_label(),display,matches)
            existing=next((p for p in lib.get_captured_properties(variant,actor) if p.get_full_display_string()==matches[0]),None)
            value=existing or lib.capture_property(variant,actor,matches[0]);assert value;value.record()
    shafts=[bylabel['Film_WindowShaft_%02d'%i] for i in range(1,4)]
    for index in range(4):
        v=variants.get_variant(index);v.switch_on()
        for a in shafts:
            a.spot_light_component.set_editor_property('volumetric_scattering_intensity',3.0)
            capture(v,a,['Volumetric Scattering Intensity'])
    variants.get_variant(2).switch_on()
    for a in shafts:
        c=a.spot_light_component;c.set_intensity(180)
        c.set_editor_property('volumetric_scattering_intensity',8.0)
        c.set_editor_property('temperature',4300.0)
    c=bylabel['Film_Closeout_WindowBounce'].rect_light_component
    c.set_intensity(20);c.set_editor_property('temperature',6500.0)
    bylabel['EST_Fill_E1'].get_component_by_class(unreal.LightComponent).set_intensity(1.1)
    bylabel['SpotLight'].get_component_by_class(unreal.LightComponent).set_intensity(15)
    # Label-resolved with a singleton assert, replacing the first-match isinstance()
    # lookup that would have configured the wrong actor once a duplicate fog existed.
    fog=film304_fog.get_fog_actor(actors)
    film304_fog.apply_shot_look(.0075,actors=actors)
    variant=unreal.Variant();variant.set_display_text('E_CinematicDusk');lib.add_variant(variants,variant)
    for a in actors.get_all_level_actors():
        if isinstance(a,unreal.Light) and a.get_actor_label()!='Light_AviationBeacon_HeroSpire':
            capture(variant,a,['Intensity','Light Color','Use Temperature','Temperature','Volumetric Scattering Intensity'])
    capture(variant,fog,['Fog Density']);assert unreal.EditorAssetLibrary.save_loaded_asset(lvs)
    camera=actors.spawn_actor_from_class(unreal.CineCameraActor,unreal.Vector(360,-330,150))
    camera.set_actor_label('Film_Cam_Closeout_DuskHero_v02');camera.set_folder_path('Film304/FinalAssembly/Cameras')
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(),unreal.Vector(-70,80,120)),False)
    cine=camera.get_cine_camera_component();cine.current_focal_length=35;cine.current_aperture=8
    fb=cine.filmback;fb.sensor_width=36;fb.sensor_height=20.25;cine.filmback=fb
    focus=cine.focus_settings;focus.focus_method=unreal.CameraFocusMethod.DISABLE;cine.focus_settings=focus
    source=unreal.load_asset('/Game/Sequences/Film304Closeout_20261018/LS_Closeout_WindowHero48f_v01')
    name='LS_Closeout_DuskHero48f_v01';dest='/Game/Sequences/Film304Closeout_20261018'
    assert not unreal.EditorAssetLibrary.does_asset_exist(dest+'/'+name)
    seq=unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(name,dest,source)
    for t in list(seq.get_tracks()):
        if isinstance(t,unreal.MovieSceneCameraCutTrack):seq.remove_track(t)
    for b in list(seq.get_possessables()):
        if b.get_name()=='Film_Cam_Closeout_WindowLightHero':b.remove()
    binding=seq.add_possessable(camera);track=seq.add_track(unreal.MovieSceneCameraCutTrack)
    section=track.add_section();section.set_range(0,48)
    oid=unreal.MovieSceneObjectBindingID();oid.set_editor_property('guid',binding.get_id());section.set_camera_binding_id(oid)
    ns={'__name__':'light_recipe_helpers','__file__':str(root/'Python/build_closeout_lightstudy_sequences_20261018.py')}
    exec(compile(open(ns['__file__'],encoding='utf-8').read(),ns['__file__'],'exec'),ns)
    lights,density=ns['capture_light_state'](seq,actors)
    assert unreal.EditorAssetLibrary.save_loaded_asset(seq)
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    report={'sequence':seq.get_path_name(),'camera':camera.get_actor_label(),'focal_mm':35,
            'filmback_mm':[36,20.25],'lighting_variant':'E_CinematicDusk','lights':lights,'fog_density':density,
            'previous_cameras_preserved':True,'shared_shader_changes':False,'visual_gate':'pending MRQ proof'}
    (root/'Saved/Audit/Closeout_20261018/cinematic_dusk_composition.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'sequence':seq.get_path_name(),'variants':variants.get_num_variants(),'camera':camera.get_actor_label()}))

if __name__=='__main__':main()
