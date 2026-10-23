"""Create film-owned baseline part instances; no scene or source-instance edits."""
import json
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
OUT=ROOT/'Saved/Audit/EveningExecution_20261017'
ME=unreal.MaterialEditingLibrary
EAL=unreal.EditorAssetLibrary
FOLDER='/Game/Materials/Instances/Film304/Cast'
TOON='/Game/Materials/Instances/Film304/MI_Film304_Toon'

def main():
    assert unreal.Paths.project_dir().replace('\\','/').rstrip('/').lower()=='g:/film-304-toon-spine'
    assert not unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).is_rendering()
    evidence=json.loads((OUT/'source_cast_instances.json').read_text())
    # Transparent corneas retain their own proven optical graph instead of an opaque toon parent.
    cornea_path='/Game/Materials/Masters/Film304/M_Film304_CorneaClear'
    source_cornea=unreal.load_asset('/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Dana_Cornea_20261016').get_editor_property('parent')
    cornea=unreal.load_asset(cornea_path) if EAL.does_asset_exist(cornea_path) else EAL.duplicate_asset(source_cornea.get_path_name().split('.')[0],cornea_path)
    assert cornea
    cornea.set_editor_property('used_with_skeletal_mesh',True)
    cornea.set_editor_property('used_with_morph_targets',True)
    assert EAL.save_loaded_asset(cornea,only_if_is_dirty=False)
    rows=[]
    for row in evidence:
        name=row['asset'].split('.')[-1]
        tokens=name.split('_')
        if len(tokens)<5 or tokens[2] not in ['Dana','David','Sam','Spider']:continue
        character,part=tokens[2:4]
        if part in ['Skin','Detail']:continue
        dest=FOLDER+'/'+character
        instance_name='MI_Film304_'+character+'_'+part+'_Toon'
        path=dest+'/'+instance_name
        # Refuse to overwrite authored instances on rerun.
        if EAL.does_asset_exist(path):
            raise RuntimeError('Existing part candidate preserved: '+path)
        instance=unreal.AssetToolsHelpers.get_asset_tools().create_asset(instance_name,dest,unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
        assert instance
        ME.set_material_instance_parent(instance,cornea if part=='Cornea' else unreal.load_asset(TOON))
        scalar_names=['Coverage','Roughness','Specular'] if part=='Cornea' else ['Roughness']
        for parameter in scalar_names:
            if parameter in row['scalars']:
                ME.set_material_instance_scalar_parameter_value(instance,parameter,row['scalars'][parameter])
        for parameter,color in row['vectors'].items():
            ME.set_material_instance_vector_parameter_value(instance,parameter,unreal.LinearColor(*color))
        mapped={}
        if part!='Cornea':
            ME.set_material_instance_static_switch_parameter_value(instance,'bFilmUseUDIM',False)
            texture_path=row['textures'].get('BaseColorMap')
            ME.set_material_instance_scalar_parameter_value(instance,'TextureWeight',1.0 if texture_path else 0.0)
            if texture_path:
                texture=unreal.load_asset(texture_path);assert texture and not texture.get_editor_property('virtual_texture_streaming')
                ME.set_material_instance_texture_parameter_value(instance,'Albedo',texture)
                mapped={'BaseColorMap':'Albedo'}
        ME.update_material_instance(instance)
        assert EAL.save_loaded_asset(instance,only_if_is_dirty=False)
        for parameter,color in row['vectors'].items():
            actual=ME.get_material_instance_vector_parameter_value(instance,parameter)
            assert max(abs(a-b) for a,b in zip([actual.r,actual.g,actual.b,actual.a],color))<1e-6
        if mapped:assert ME.get_material_instance_texture_parameter_value(instance,'Albedo')==texture
        rows.append({'character':character,'part':part,'source':row['asset'],'instance':path,
            'parent':instance.get_editor_property('parent').get_path_name(),'texture_mapping':mapped,
            'unmapped_old_controls':[] if part=='Cornea' else [k for k in row['scalars'] if k not in scalar_names],
            'saved_binding_gate':True,'visual_gate':False})
    report={'instances':rows,'scene_modified':False,'source_instances_modified':False,
        'proof':'saved parameter and texture readback; old opaque Specular control has no asserted equivalent; visual approval pending'}
    (OUT/'film_cast_part_instances.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'created_instances':len(rows),'texture_atlases_mapped':sum(bool(r['texture_mapping']) for r in rows),'scene_modified':False}))

if __name__=='__main__':main()
