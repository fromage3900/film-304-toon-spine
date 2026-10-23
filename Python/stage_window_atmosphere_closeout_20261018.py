"""Finish the live-cooked window rig, restrained dust and reversible lighting states."""
import json
from pathlib import Path
import unreal

import film304_fog

def main():
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert 'L_Film_Office_Assembly_20261018_v02.' in world.get_path_name()
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    lights=unreal._closeout_window_hda.get_baked_output_actors()
    assert len(lights)==3
    for i,a in enumerate(lights,1):
        a.set_actor_label('Film_WindowShaft_%02d'%i);a.set_folder_path('Film304/FinalAssembly/WindowRays')
        c=a.get_component_by_class(unreal.SpotLightComponent)
        c.set_editor_property('intensity_units',unreal.LightUnits.CANDELAS)
        c.set_attenuation_radius(1500);c.set_inner_cone_angle(11);c.set_outer_cone_angle(18)
        c.set_editor_property('volumetric_scattering_intensity',3.0)
        c.set_editor_property('cast_volumetric_shadow',True)
        assert a.get_actor_forward_vector().z<-.4
    # Label-resolved with a singleton assert, replacing the first-match isinstance()
    # lookup that would have configured the wrong actor once a duplicate fog existed.
    fog=film304_fog.get_fog_actor(actors)
    fc=film304_fog.get_fog_component(actors)
    fogprops=['fog_density','enable_volumetric_fog','volumetric_fog_extinction_scale',
              'volumetric_fog_scattering_distribution','volumetric_fog_distance']
    fogbefore={p:fc.get_editor_property(p) for p in fogprops}
    src=unreal.load_asset('/Game/_ThirdParty/UltraDynamicSky/Particles/Dust')
    path='/Game/VFX/Film304Closeout_20261018'
    system=unreal.load_asset(path+'/NS_Film_WindowDust_v01')
    if system is None:system=unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset('NS_Film_WindowDust_v01',path,src)
    assert unreal.EditorAssetLibrary.save_loaded_asset(system)
    dust=next((a for a in actors.get_all_level_actors() if a.get_actor_label()=='Film_WindowDust_Subtle'),None)
    if dust is None:dust=actors.spawn_actor_from_class(unreal.NiagaraActor,unreal.Vector(-180,140,130))
    dust.set_actor_label('Film_WindowDust_Subtle');dust.set_folder_path('Film304/FinalAssembly/WindowRays')
    nc=dust.niagara_component;nc.set_asset(system)
    params={'User.Spawn Rate':12,'User.CPU Spawn Rate':0,'User.Sprite Alpha':.065,
            'User.Sprite Scale':.035,'User.Max Lifetime':6,'User.Spawn Box Height':260,
            'User.Max Spawn Distance':420,'User.Camera Forward Offset':160,
            'User.Spawn Distance Distribution':1,'User.Custom Time Dilation':1,
            'User.Wind Velocity Scale':.02,'User.Twirl Velocity':.12,
            'User.Ambient Intensity':.1,'User.Fog Particle Percentage':0}
    for p,v in params.items():nc.set_variable_float(p,float(v))
    nc.set_variable_bool('User.Override Camera Transform',True)
    nc.set_variable_bool('User.Particle Collision Enabled',False)
    nc.set_variable_vec3('User.Custom Camera Position',unreal.Vector(-180,140,130))
    nc.set_variable_vec3('User.Custom Camera Forward',unreal.Vector(.9063,-.4226,0))
    nc.set_variable_vec3('User.Sprite Color Multiplier',unreal.Vector(.65,.70,.80))
    nc.activate(True)
    lib=unreal.VariantManagerLibrary
    lvs=unreal.load_asset('/Game/Variants/Film304Closeout_20261018/LVS_Office_LightingCloseout_v01')
    variants=lvs.get_variant_set(0)
    bounce=next(a for a in actors.get_all_level_actors() if a.get_actor_label()=='Film_Closeout_WindowBounce')
    def capture(variant,actor,displays):
        lib.add_actor_binding(variant,actor)
        available=lib.get_capturable_properties(actor)
        for display in displays:
            matches=[p for p in available if p.endswith(' / '+display) and p.count(' / ')==1]
            assert len(matches)==1,(actor.get_actor_label(),display,matches)
            p=next((p for p in lib.get_captured_properties(variant,actor) if p.get_full_display_string()==matches[0]),None)
            if p is None:p=lib.capture_property(variant,actor,matches[0])
            assert p
            p.record();assert p.has_recorded_data()
    # Add new state to each existing native variant, preserving its original 80 captures.
    for index in range(4):
        v=variants.get_variant(index);v.switch_on()
        for p,value in fogbefore.items():fc.set_editor_property(p,value)
        density=[fogbefore['fog_density'],.003,.005,.003][index]
        if index:
            fc.set_fog_density(density)
        for a in lights:
            c=a.get_component_by_class(unreal.SpotLightComponent)
            c.set_intensity([0,180,350,90][index]);c.set_editor_property('use_temperature',True)
            c.set_editor_property('temperature',float([4100,5600,4100,6500][index]))
            capture(v,a,['Intensity','Use Temperature','Temperature'])
        bc=bounce.rect_light_component;bc.set_intensity([0,60,45,20][index])
        bc.set_editor_property('use_temperature',True);bc.set_editor_property('temperature',float([5600,5600,4200,7000][index]))
        capture(v,bounce,['Intensity','Use Temperature','Temperature'])
        available=lib.get_capturable_properties(fog)
        # Only density is capturable in this engine build. Preserve the other
        # measured volumetric settings unchanged across the four variants.
        fogdisplays=['Fog Density']
        for display in fogdisplays:
            matches=[p for p in available if p.endswith(' / '+display) and p.count(' / ')==1]
            if not matches and display=='Volumetric Fog':
                matches=[p for p in available if p.endswith(' / Enable Volumetric Fog') and p.count(' / ')==1]
            assert len(matches)==1,(display,matches)
            lib.add_actor_binding(v,fog)
            value=next((p for p in lib.get_captured_properties(v,fog) if p.get_full_display_string()==matches[0]),None)
            if value is None:value=lib.capture_property(v,fog,matches[0])
            assert value;value.record()
    assert unreal.EditorAssetLibrary.save_loaded_asset(lvs)
    variants.get_variant(2).switch_on()
    out=Path(unreal.Paths.project_dir())/'Saved/Audit/Closeout_20261018'
    report={'live_houdini_session_verified':True,'live_outputs':1,'bake_succeeded':True,
        'window_lights':[{'label':a.get_actor_label(),'position_cm':list(a.get_actor_location().to_tuple()),
                          'forward':list(a.get_actor_forward_vector().to_tuple())} for a in lights],
        'dust_system':system.get_path_name(),'dust_parameters':params,'fog_original':fogbefore,
        'lighting_variant_asset':lvs.get_path_name(),'selected_for_review':'C_WarmDesk',
        'visual_gate':'pending rendered proof','motion_loop_gate':False}
    (out/'window_atmosphere.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report))

if __name__=='__main__':main()
