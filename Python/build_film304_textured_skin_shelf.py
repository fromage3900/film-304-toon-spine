"""Wire each cast's verified three skin tiles into every film look preset."""
import json
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()); OUT=ROOT/'Saved/Audit/EveningExecution_20261017'
PARENT='/Game/Materials/Masters/Film304/M_UniversalToon_Film304_v06'
LOOKS=['Toon','Smooth','Watercolour','Gouache','Halftone','OrderedDither','NoiseDither']
ME=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary

def main():
    if unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).is_rendering():raise RuntimeError('Render active')
    parent=unreal.load_asset(PARENT);assert parent
    for look in LOOKS:
        instance=unreal.load_asset('/Game/Materials/Instances/Film304/MI_Film304_'+look);assert instance
        current=instance.get_editor_property('parent').get_path_name().split('.')[0]
        assert current in [PARENT,'/Game/Materials/Masters/Film304/M_UniversalToon_Film304_v05']
        ME.set_material_instance_parent(instance,parent);ME.update_material_instance(instance)
        assert EAL.save_loaded_asset(instance,only_if_is_dirty=False)
    rows=[]
    for character in ['David','Sam','Dana']:
        original=unreal.load_asset('/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_'+character+'_Skin_20261016')
        tiles={str(v.get_editor_property('parameter_info').get_editor_property('name')):v.get_editor_property('parameter_value')
               for v in original.get_editor_property('texture_parameter_values')}
        assert set(tiles)=={'BaseColorTile1001','BaseColorTile1002','BaseColorTile1003'}
        assert all(t.get_editor_property('srgb') and t.get_editor_property('virtual_texture_streaming') for t in tiles.values())
        for look in LOOKS:
            folder='/Game/Materials/Instances/Film304/Cast/'+character
            name='MI_Film304_'+character+'_Skin_'+look; path=folder+'/'+name
            instance=unreal.load_asset(path) if EAL.does_asset_exist(path) else None
            if not instance:
                instance=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,folder,
                    unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew());assert instance
            ME.set_material_instance_parent(instance,unreal.load_asset('/Game/Materials/Instances/Film304/MI_Film304_'+look))
            ME.set_material_instance_static_switch_parameter_value(instance,'bFilmUseUDIM',True)
            ME.set_material_instance_scalar_parameter_value(instance,'TextureWeight',1.0)
            ME.set_material_instance_scalar_parameter_value(instance,'Roughness',0.72)
            ME.set_material_instance_vector_parameter_value(instance,'BaseTint',unreal.LinearColor(1,1,1,1))
            for parameter,texture in tiles.items():ME.set_material_instance_texture_parameter_value(instance,parameter,texture)
            ME.update_material_instance(instance);assert EAL.save_loaded_asset(instance,only_if_is_dirty=False)
            assert ME.get_material_instance_static_switch_parameter_value(instance,'bFilmUseUDIM')
            for parameter,texture in tiles.items():assert ME.get_material_instance_texture_parameter_value(instance,parameter)==texture
            rows.append({'character':character,'look':look,'instance':path,
                'tiles':{p:t.get_path_name() for p,t in tiles.items()},'saved_override_gate':True})
    report={'parent':PARENT,'instances':rows,'scene_modified':False,
        'proof':'saved texture/switch overrides; enabled permutations and visible skin approval pending'}
    (OUT/'film_textured_skin_shelf.json').write_text(json.dumps(report,indent=2));print(json.dumps({'instances':len(rows),'characters':3,'looks':7,'scene_modified':False}))

if __name__=='__main__':main()
