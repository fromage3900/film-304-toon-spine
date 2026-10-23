"""Bind only newly imported repaired meshes; preserve existing actors and MIs."""
import json
import struct
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()); OUT=ROOT/'Saved/Audit/EveningExecution_20261017'
MI='/Game/Materials/Instances/OneDriveRigs_20261016'
NEW_MI='/Game/Materials/Instances/Film304/Cast'
PARENT='/Game/Materials/Masters/Film304/M_UniversalToon_Film304_v05'
ROLES={
 'body_skin':'Skin','body_skin_section_default_shader':'Skin','cornea':'Cornea',
 'eye_interior_auxiliary':'EyeInterior','eyeball_sclera':'EyeWhite','footwear':'Shoes',
 'hair_brow_and_lash':'Hair','hair_and_lash':'Hair','hair':'Hair','eyelashes':'Hair',
 'iris':'Iris','jeans_trousers':'Cloth','pants_trousers':'Cloth','shirt':'Shirt',
 'teeth':'Teeth','gum_oral_soft_tissue':'Mouth','tongue':'Mouth','tongue_and_oral_soft_tissue':'Mouth'}

def texture_evidence(material):
    result=[]
    for item in material.get_editor_property('texture_parameter_values'):
        texture=item.get_editor_property('parameter_value')
        name=str(item.get_editor_property('parameter_info').get_editor_property('name'))
        files=texture.get_editor_property('asset_import_data').extract_filenames() if texture else []
        dimensions=[]
        for filename in files:
            file=Path(filename)
            if file.is_file() and file.suffix.lower()=='.png':
                with file.open('rb') as stream: header=stream.read(24)
                if header[:8]==b'\x89PNG\r\n\x1a\n':dimensions.append(list(struct.unpack('>II',header[16:24])))
        result.append({'parameter':name,'texture':texture.get_path_name() if texture else None,
            'srgb':texture.get_editor_property('srgb') if texture else None,
            'vt':texture.get_editor_property('virtual_texture_streaming') if texture else None,
            'source_png_dimensions':dimensions})
    return result

def main():
    if unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).is_rendering(): raise RuntimeError('Render active')
    eal=unreal.EditorAssetLibrary; me=unreal.MaterialEditingLibrary
    role_map=json.loads((OUT/'cast_section_role_map_20261017.json').read_text())
    report={'scene_modified':False,'characters':{}}
    for character in ['David','Sam','Dana']:
        path='/Game/Staging/Film304Repaired_20261017/'+character+'/SK_'+character+'_Film304_v01'
        mesh=unreal.load_asset(path); assert mesh
        declarations={r['source_section_name'].lower():r for r in role_map['characters'][character]['slots']}
        slots=list(mesh.get_editor_property('materials')); assignment=[]
        for slot in slots:
            name=str(slot.get_editor_property('material_slot_name')); declaration=declarations[name.lower()]
            part=ROLES[declaration['intended_role']]
            existing=MI+'/MI_OneDriveRigs_'+character+'_'+part+'_20261016'
            material=unreal.load_asset(existing) if eal.does_asset_exist(existing) else None
            if not material:
                if part not in ['Teeth','Mouth']: raise RuntimeError('Required cast instance missing: '+existing)
                new_name='MI_Film304_'+character+'_'+part; new_path=NEW_MI+'/'+new_name
                material=unreal.load_asset(new_path) if eal.does_asset_exist(new_path) else None
                if not material:
                    material=unreal.AssetToolsHelpers.get_asset_tools().create_asset(new_name,NEW_MI,
                        unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew()); assert material
                    me.set_material_instance_parent(material,unreal.load_asset(PARENT))
                    color=(0.82,0.78,0.68,1) if part=='Teeth' else (0.18,0.035,0.05,1)
                    me.set_material_instance_vector_parameter_value(material,'BaseTint',unreal.LinearColor(*color))
                    for parameter,value in {'TextureWeight':0,'Roughness':0.5,'Iridescence':0,
                        'BoilIntensity':0,'SmearStrength':0,'TemporalStrength':0}.items():
                        me.set_material_instance_scalar_parameter_value(material,parameter,value)
                    me.update_material_instance(material); assert eal.save_loaded_asset(material,only_if_is_dirty=False)
            textures=texture_evidence(material)
            if part=='Skin':
                expected={'BaseColorTile1001','BaseColorTile1002','BaseColorTile1003'}
                assert {r['parameter'] for r in textures}==expected
                assert all(r['vt'] and r['srgb'] and r['source_png_dimensions']==[[2048,2048]] for r in textures),textures
            if part in ['Shoes','Cloth']:
                assert any(r['parameter']=='BaseColorMap' and r['texture'] for r in textures),'Atlas not bound: '+material.get_path_name()
            slot.set_editor_property('material_interface',material)
            assignment.append({'slot':name,'part':part,'material':material.get_path_name(),
                'parent':material.get_editor_property('parent').get_path_name(),'textures':textures})
        mesh.set_editor_property('materials',slots); assert eal.save_loaded_asset(mesh,only_if_is_dirty=False)
        readback=unreal.load_asset(path).get_editor_property('materials')
        for actual,wanted in zip(readback,assignment):
            assert actual.get_editor_property('material_interface').get_path_name()==wanted['material']
            assert not wanted['material'].startswith('/Engine/')
        report['characters'][character]={'mesh':path,'slots':assignment,'saved_binding_gate':True,
            'unmapped_slots':[],'null_slots':[],'engine_default_slots':[]}
    report['proof']='saved mesh bindings and texture metadata/source dimensions; visual proof remains open'
    (OUT/'repaired_cast_bindings.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'characters':{n:{'slots':len(r['slots']),'saved_binding_gate':r['saved_binding_gate']}
        for n,r in report['characters'].items()},'scene_modified':False},indent=2))

if __name__=='__main__':main()
