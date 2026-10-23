"""Add a static, opt-in three-tile VT skin path to the real Universal film graph."""
import json
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()); OUT=ROOT/'Saved/Audit/EveningExecution_20261017'
SOURCE='/Game/Materials/Masters/Film304/M_UniversalToon_Film304_v05'
DEST='/Game/Materials/Masters/Film304/M_UniversalToon_Film304_v06'
WHITE='/Game/Materials/Textures/Film304/T_Film304_White'
VTWHITE='/Game/Materials/Textures/Film304/T_Film304_WhiteVT'
ME=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary

def connect(a,b,pin,output=''):
    assert ME.connect_material_expressions(a,output,b,pin),(a.get_name(),b.get_name(),pin)

def main():
    if unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).is_rendering():raise RuntimeError('Render active')
    if not EAL.does_asset_exist(VTWHITE):assert EAL.duplicate_asset(WHITE,VTWHITE)
    texture=unreal.load_asset(VTWHITE); texture.set_editor_property('virtual_texture_streaming',True)
    assert EAL.save_loaded_asset(texture,only_if_is_dirty=False)
    if not EAL.does_asset_exist(DEST):assert EAL.duplicate_asset(SOURCE,DEST)
    mat=unreal.load_asset(DEST)
    mat.set_editor_property('used_with_skeletal_mesh',True)
    mat.set_editor_property('used_with_morph_targets',True)
    nodes={n.get_name():n for n in ME.get_material_expressions(mat)}
    source_ids={n.get_name() for n in ME.get_material_expressions(unreal.load_asset(SOURCE))}
    assert source_ids.issubset(nodes),'Candidate base differs; refuse rebuild'
    connect(nodes['MaterialExpressionTextureSample_95'],nodes['MaterialExpressionMultiply_827'],'A','RGB')
    for name,node in list(nodes.items()):
        if name not in source_ids:ME.delete_material_expression(mat,node)
    uv=ME.create_material_expression(mat,unreal.MaterialExpressionTextureCoordinate,-2000,-6000)
    fraction=ME.create_material_expression(mat,unreal.MaterialExpressionFrac,-1800,-6000);connect(uv,fraction,'')
    u=ME.create_material_expression(mat,unreal.MaterialExpressionComponentMask,-1800,-6200)
    u.set_editor_properties({'r':True,'g':False,'b':False,'a':False});connect(uv,u,'')
    tile=ME.create_material_expression(mat,unreal.MaterialExpressionFloor,-1600,-6200);connect(u,tile,'')
    samples=[]
    for index in range(3):
        sample=ME.create_material_expression(mat,unreal.MaterialExpressionTextureSampleParameter2D,-1400,-6000+index*300)
        sample.set_editor_properties({'parameter_name':'BaseColorTile'+str(1001+index),
            'texture':texture,'sampler_type':unreal.MaterialSamplerType.SAMPLERTYPE_VIRTUAL_COLOR,
            'group':'Film Skin UDIM'})
        connect(fraction,sample,'UVs');samples.append(sample)
    # floor(U) == 0/1/2 corresponds to UDIM 1001/1002/1003; source UV census
    # proves all character skin islands live in this one-row range.
    first=ME.create_material_expression(mat,unreal.MaterialExpressionIf,-1000,-5800)
    first.set_editor_properties({'const_b':0.5,'equals_threshold':0.00001});connect(tile,first,'A')
    connect(samples[1],first,'A > B','RGB');connect(samples[1],first,'A == B','RGB');connect(samples[0],first,'A < B','RGB')
    second=ME.create_material_expression(mat,unreal.MaterialExpressionIf,-700,-5800)
    second.set_editor_properties({'const_b':1.5,'equals_threshold':0.00001});connect(tile,second,'A')
    connect(samples[2],second,'A > B','RGB');connect(samples[2],second,'A == B','RGB');connect(first,second,'A < B')
    switch=ME.create_material_expression(mat,unreal.MaterialExpressionStaticSwitchParameter,-400,-5800)
    switch.set_editor_properties({'parameter_name':'bFilmUseUDIM','default_value':False,'group':'Film Skin UDIM'})
    connect(second,switch,'True');connect(nodes['MaterialExpressionTextureSample_95'],switch,'False','RGB')
    connect(switch,nodes['MaterialExpressionMultiply_827'],'A')
    ME.recompile_material(mat);assert EAL.save_loaded_asset(mat,only_if_is_dirty=False)
    report={'candidate':DEST,'source':SOURCE,'udim_tiles':[1001,1002,1003],
        'coordinates':'raw UV0, floor U selects tile, frac UV samples tile',
        'static_switch':'bFilmUseUDIM','default_enabled':False,
        'proof':'graph authored and saved; default and enabled permutation compile checks pending'}
    (OUT/'film_udim_branch.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))

if __name__=='__main__':main()
