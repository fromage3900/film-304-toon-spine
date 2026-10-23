"""Film-owned neutral defaults and reusable utilities; preserve original assets."""
import json
import struct
import zlib
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()); OUT=ROOT/'Saved/Audit/EveningExecution_20261017'
SOURCE='/Game/Materials/Masters/Film304/M_UniversalToon_Film304_v04'
DEST='/Game/Materials/Masters/Film304/M_UniversalToon_Film304_v05'
TEX='/Game/Materials/Textures/Film304'; FN='/Game/Materials/Functions/Film304'
ME=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary

def clean_artist_labels(material):
    groups={'10 | Nikki Rim & Glow':'10 | Rim and Glow',
            '11 | Nikki Dream Grade':'11 | Film Colour Grade',
            '13 | Nikki Iridescence & Sheen':'13 | Fabric and Thin Film'}
    changed=0
    for node in ME.get_material_expressions(material):
        try: group=str(node.get_editor_property('group'))
        except Exception: group=None
        if group in groups:
            node.set_editor_property('group',groups[group]);changed+=1
        desc=str(node.get_editor_property('desc'))
        if 'WPO_Resonance_Scale' in desc:
            node.set_editor_property('desc',desc.replace('WPO_Resonance_Scale','ClothDisplacementScale'));changed+=1
        if isinstance(node,unreal.MaterialExpressionCustom):
            description=str(node.get_editor_property('description'))
            if 'WPO_Resonance_Scale' in description:
                node.set_editor_property('description',description.replace('WPO_Resonance_Scale','ClothDisplacementScale'));changed+=1
    return changed

def png(path,color):
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',4,4,8,6,0,0,0))+
        chunk(b'IDAT',zlib.compress(b''.join(b'\0'+bytes(color)*4 for _ in range(4))))+chunk(b'IEND',b''))

def main():
    if unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).is_rendering():
        raise RuntimeError('Render active: deferred')
    if EAL.does_asset_exist(DEST): raise RuntimeError('Existing candidate preserved')
    textures={}
    for name,color,srgb,normal in [('White',(255,255,255,255),True,False),
        ('Gray',(128,128,128,255),True,False),('BlackColor',(0,0,0,255),True,False),
        ('Normal',(128,128,255,255),False,True),('ORM',(255,255,0,255),False,False),
        ('WhiteData',(255,255,255,255),False,False),('BlackData',(0,0,0,255),False,False)]:
        asset_name='T_Film304_'+name; path=TEX+'/'+asset_name
        if not EAL.does_asset_exist(path):
            disk=OUT/(asset_name+'.png'); png(disk,color)
            task=unreal.AssetImportTask(); task.set_editor_properties({'filename':str(disk),
                'destination_path':TEX,'destination_name':asset_name,'automated':True,'save':True})
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        texture=unreal.load_asset(path); assert texture
        texture.set_editor_property('srgb',srgb)
        texture.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP if normal else unreal.TextureCompressionSettings.TC_DEFAULT)
        assert EAL.save_loaded_asset(texture,only_if_is_dirty=False)
        textures[name]=texture
    assert EAL.duplicate_asset(SOURCE,DEST)
    mat=unreal.load_asset(DEST); nodes=ME.get_material_expressions(mat)
    function_map={}; texture_map={}
    for node in nodes:
        if isinstance(node,unreal.MaterialExpressionMaterialFunctionCall):
            original=node.get_editor_property('material_function'); path=original.get_path_name().split('.')[0]
            target=FN+'/MF_Film304_'+original.get_name().removeprefix('MF_')
            if not EAL.does_asset_exist(target): assert EAL.duplicate_asset(path,target)
            node.set_editor_property('material_function',unreal.load_asset(target))
            function_map[path]=target
        if isinstance(node,(unreal.MaterialExpressionTextureObjectParameter,unreal.MaterialExpressionTextureSampleParameter2D)):
            name=str(node.get_editor_property('parameter_name'))
            sampler=node.get_editor_property('sampler_type')
            if 'Normal' in name: key='Normal'
            elif name.endswith('ORM'): key='ORM'
            elif 'Roughness' in name: key='WhiteData'
            elif 'Metallic' in name or name=='EmissiveMap': key='BlackData'
            elif 'Height' in name: key='Gray'
            else: key='White'
            node.set_editor_property('texture',textures[key]); texture_map[name]=textures[key].get_path_name()
    # Repair validator-only null fallback fields on sampler nodes whose Texture
    # Object input already supplies the real texture. This also makes all fallback
    # asset references explicit and film-owned.
    for node in nodes:
        if not isinstance(node,unreal.MaterialExpressionTextureSample) or isinstance(node,unreal.MaterialExpressionTextureSampleParameter2D): continue
        names=ME.get_material_expression_input_names(node); inputs=ME.get_inputs_for_material_expression(mat,node)
        objects=[src for pin,src in zip(names,inputs) if src and 'Texture' in str(pin)]
        if len(objects)==1:
            texture=objects[0].get_editor_property('texture')
            node.set_editor_property('texture',texture)
    renames={'DreamSaturation':'FilmGradeSaturation','DreamContrast':'FilmGradeContrast',
        'DreamShadowLift':'FilmGradeShadowLift','DreamHighlightSoft':'FilmGradeHighlightSoft',
        'DreamTint':'FilmGradeTint','DreamWarmth':'FilmGradeWarmth',
        'WPO_Resonance_Scale':'ClothDisplacementScale'}
    for node in nodes:
        try: name=str(node.get_editor_property('parameter_name'))
        except Exception: continue
        if name in renames: node.set_editor_property('parameter_name',renames[name])
    clean_artist_labels(mat)
    ME.recompile_material(mat); assert EAL.save_loaded_asset(mat,only_if_is_dirty=False)
    instances=[]
    # These seven instances are owned by this goal and not assigned to the scene.
    for label in ['Toon','Smooth','Watercolour','Gouache','Halftone','OrderedDither','NoiseDither']:
        instance=unreal.load_asset('/Game/Materials/Instances/Film304/MI_Film304_'+label)
        assert instance and instance.get_editor_property('parent').get_path_name().split('.')[0]==SOURCE
        ME.set_material_instance_parent(instance,mat); ME.update_material_instance(instance)
        assert EAL.save_loaded_asset(instance,only_if_is_dirty=False)
        instances.append(instance.get_path_name())
    report={'candidate':DEST,'functions':function_map,'texture_defaults':texture_map,
        'parameter_renames':renames,'reparented_owned_instances':instances,
        'proof':'authored and saved; compile and recursive closure check pending'}
    (OUT/'film_dependency_sanitization.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
