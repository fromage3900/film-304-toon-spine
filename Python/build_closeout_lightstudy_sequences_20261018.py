"""Bake native light-variant values into self-contained MRQ shot variants."""
import json
from pathlib import Path
import unreal

import film304_fog

def capture_light_state(seq,actors):
    """Keep a shot's light recipe reproducible without relying on editor state."""
    lights=[]
    for a in actors.get_all_level_actors():
        if not isinstance(a,unreal.Light) or a.get_actor_label()=='Light_AviationBeacon_HeroSpire':continue
        c=a.get_component_by_class(unreal.LightComponent)
        if c is None:continue
        binding=seq.add_possessable(c)
        for prop,value in [('Intensity',c.intensity),('Temperature',c.temperature),
                           ('VolumetricScatteringIntensity',c.volumetric_scattering_intensity)]:
            t=binding.add_track(unreal.MovieSceneFloatTrack);t.set_property_name_and_path(prop,prop)
            s=t.add_section();s.set_range(0,48);s.get_all_channels()[0].set_default(float(value))
        t=binding.add_track(unreal.MovieSceneBoolTrack);t.set_property_name_and_path('bUseTemperature','bUseTemperature')
        s=t.add_section();s.set_range(0,48);s.get_all_channels()[0].set_default(c.use_temperature)
        t=binding.add_track(unreal.MovieSceneColorTrack);t.set_property_name_and_path('LightColor','LightColor')
        s=t.add_section();s.set_range(0,48)
        for channel,value in zip(s.get_all_channels(),c.light_color.to_tuple()):channel.set_default(value/255)
        lights.append({'actor':a.get_actor_label(),'intensity':c.intensity,'kelvin':c.temperature,
                       'volumetric_scattering':c.volumetric_scattering_intensity})
    # Label-resolved with a singleton assert; the old first-match isinstance() lookup
    # would have configured the wrong actor once a duplicate fog existed.
    fog=film304_fog.get_fog_actor(actors)
    fc=film304_fog.get_fog_component(actors)
    binding=seq.add_possessable(fc)
    t=binding.add_track(unreal.MovieSceneFloatTrack);t.set_property_name_and_path('FogDensity','FogDensity')
    s=t.add_section();s.set_range(0,48);s.get_all_channels()[0].set_default(fc.fog_density)
    return lights,fc.fog_density

def main():
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert 'L_Film_Office_Assembly_20261018_v02.' in world.get_path_name()
    lvs=unreal.load_asset('/Game/Variants/Film304Closeout_20261018/LVS_Office_LightingCloseout_v01')
    variants=lvs.get_variant_set(0)
    source=unreal.load_asset('/Game/Sequences/Film304Closeout_20261018/LS_Closeout_Medium48f_v01')
    records=[]
    for index in range(4):
        variant=variants.get_variant(index);variant.switch_on()
        name='LS_Closeout_Lighting_'+chr(65+index)+'48f_v01'
        dest='/Game/Sequences/Film304Closeout_20261018'
        assert not unreal.EditorAssetLibrary.does_asset_exist(dest+'/'+name)
        seq=unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(name,dest,source)
        lights=[]
        for a in actors.get_all_level_actors():
            if not isinstance(a,unreal.Light) or a.get_actor_label()=='Light_AviationBeacon_HeroSpire':continue
            c=a.get_component_by_class(unreal.LightComponent)
            if c is None:continue
            binding=seq.add_possessable(c)
            for prop,value in [('Intensity',c.intensity),('Temperature',c.temperature)]:
                t=binding.add_track(unreal.MovieSceneFloatTrack);t.set_property_name_and_path(prop,prop)
                s=t.add_section();s.set_range(0,48);s.get_all_channels()[0].set_default(float(value))
            t=binding.add_track(unreal.MovieSceneBoolTrack);t.set_property_name_and_path('bUseTemperature','bUseTemperature')
            s=t.add_section();s.set_range(0,48);s.get_all_channels()[0].set_default(c.use_temperature)
            t=binding.add_track(unreal.MovieSceneColorTrack);t.set_property_name_and_path('LightColor','LightColor')
            s=t.add_section();s.set_range(0,48)
            for channel,value in zip(s.get_all_channels(),c.light_color.to_tuple()):channel.set_default(value/255)
            lights.append({'actor':a.get_actor_label(),'intensity':c.intensity,'kelvin':c.temperature})
        # Label-resolved with a singleton assert, replacing the first-match isinstance()
    # lookup that would have configured the wrong actor once a duplicate fog existed.
        fc=film304_fog.get_fog_component(actors)
        binding=seq.add_possessable(fc)
        t=binding.add_track(unreal.MovieSceneFloatTrack);t.set_property_name_and_path('FogDensity','FogDensity')
        s=t.add_section();s.set_range(0,48);s.get_all_channels()[0].set_default(fc.fog_density)
        assert unreal.EditorAssetLibrary.save_loaded_asset(seq)
        records.append({'variant':str(variant.get_display_text()),'sequence':seq.get_path_name(),
                        'lights':lights,'fog_density':fc.fog_density})
    variants.get_variant(2).switch_on()
    out=Path(unreal.Paths.project_dir())/'Saved/Audit/Closeout_20261018/lighting_shot_sequences.json'
    out.write_text(json.dumps(records,indent=2));print('LIGHTSTUDY_SEQUENCES_SAVED',len(records))

if __name__=='__main__':main()
