"""Extend the trimmed Universal candidate with film print and smooth/wash variants.
Never reparent existing scene instances or alter actors, cameras, lights or maps.
"""
import json
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
AUDIT=ROOT/'Saved/Audit/EveningExecution_20261017'
SOURCE='/Game/Materials/Masters/Film304/M_UniversalToon_Film304_v01'
DEST='/Game/Materials/Masters/Film304/M_UniversalToon_Film304_v04'
MI_DIR='/Game/Materials/Instances/Film304'
ME=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary

PARAMS={
 'FilmPrintFrequency':(48,1,512), 'FilmPrintRotation':(0,-360,360),
 'FilmPrintCoverage':(0.35,0,1), 'FilmHalftoneStrength':(0,0,1),
 'FilmPrintShadowWeight':(0,0,1), 'FilmPrintShadowContrast':(1,0.1,8),
 'FilmPrintSeed':(0,0,65535), 'FilmDitherMode':(0,0,1),
 'FilmDitherBands':(8,2,32), 'FilmDitherStrength':(0,0,1),
 'FilmWatercolourStrength':(0,0,1), 'FilmPaperScale':(120,1,1024),
 'FilmGranulation':(0.25,0,1), 'FilmPooling':(1,0,8), 'FilmPaperLift':(0,0,1)}
INPUTS={'Frequency':'FilmPrintFrequency','Rotation':'FilmPrintRotation','Coverage':'FilmPrintCoverage',
 'HalftoneStrength':'FilmHalftoneStrength','ShadowWeight':'FilmPrintShadowWeight',
 'ShadowContrast':'FilmPrintShadowContrast','Seed':'FilmPrintSeed','DitherMode':'FilmDitherMode',
 'DitherBands':'FilmDitherBands','DitherStrength':'FilmDitherStrength',
 'WatercolourStrength':'FilmWatercolourStrength','PaperScale':'FilmPaperScale',
 'Granulation':'FilmGranulation','Pooling':'FilmPooling','PaperLift':'FilmPaperLift'}

def connect(source,target,target_pin,source_pin=''):
    if not ME.connect_material_expressions(source,source_pin,target,target_pin):
        raise RuntimeError('Connection failed: '+target.get_name()+':'+target_pin)

def gate_optional_film_print(material):
    nodes=list(ME.get_material_expressions(material))
    for node in nodes:
        if isinstance(node,unreal.MaterialExpressionStaticSwitchParameter) and str(node.get_editor_property('parameter_name'))=='bFilmPrintActive':
            return False
    custom=next(node for node in nodes if isinstance(node,unreal.MaterialExpressionCustom)
                and node.get_editor_property('description')=='Film304 print and pigment surface')
    original_inputs=dict(zip([str(n) for n in ME.get_material_expression_input_names(custom)],
                            ME.get_inputs_for_material_expression(material,custom)))
    switch=ME.create_material_expression(material,unreal.MaterialExpressionStaticSwitchParameter,4000,-300)
    switch.set_editor_properties({'parameter_name':'bFilmPrintActive','default_value':False,'group':'Film Look'})
    connect(custom,switch,'True');connect(original_inputs['BaseColor'],switch,'False')
    for target in nodes:
        for name,source in zip(ME.get_material_expression_input_names(target),ME.get_inputs_for_material_expression(material,target)):
            if source==custom:connect(switch,target,str(name))
    return True

def finish_physical_inputs(material):
    nodes=list(ME.get_material_expressions(material))
    if any(str(n.get_editor_property('desc'))=='Film304 physical input finish' for n in nodes):return False
    toon=next(n for n in nodes if isinstance(n,unreal.MaterialExpressionSubstrateToonBSDF))
    slab=next(n for n in nodes if isinstance(n,unreal.MaterialExpressionSubstrateSlabBSDF))
    def inputs(node):return dict(zip([str(n) for n in ME.get_material_expression_input_names(node)],ME.get_inputs_for_material_expression(material,node)))
    source=inputs(toon); slab_source=inputs(slab)
    for name in ['Roughness','Metallic']:
        clamp=ME.create_material_expression(material,unreal.MaterialExpressionClamp,4000,2100)
        clamp.set_editor_properties({'min_default':0.0,'max_default':1.0,'desc':'Film304 physical input finish' if name=='Metallic' else 'Film roughness boundary'})
        connect(source[name],clamp,'');connect(clamp,toon,name)
        source[name]=clamp
    connect(source['Roughness'],slab,'Roughness')
    one_minus=ME.create_material_expression(material,unreal.MaterialExpressionOneMinus,4200,2400)
    connect(source['Metallic'],one_minus,'')
    diffuse=ME.create_material_expression(material,unreal.MaterialExpressionMultiply,4400,2400)
    connect(slab_source['Diffuse Albedo'],diffuse,'A');connect(one_minus,diffuse,'B')
    connect(diffuse,slab,'Diffuse Albedo')
    f0=ME.create_material_expression(material,unreal.MaterialExpressionLinearInterpolate,4400,2700)
    dielectric=ME.create_material_expression(material,unreal.MaterialExpressionConstant3Vector,4100,2700)
    dielectric.set_editor_property('constant',unreal.LinearColor(0.04,0.04,0.04,1))
    connect(dielectric,f0,'A');connect(slab_source['Diffuse Albedo'],f0,'B');connect(source['Metallic'],f0,'Alpha')
    connect(f0,slab,'F0')
    return True

def main():
    if unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).is_rendering():
        raise RuntimeError('Render active: deferred')
    if EAL.does_asset_exist(DEST): raise RuntimeError('Existing look candidate preserved')
    assert EAL.duplicate_asset(SOURCE,DEST)
    mat=unreal.load_asset(DEST); nodes={n.get_name():n for n in ME.get_material_expressions(mat)}
    expressions=list(nodes.values())
    toon=next(n for n in expressions if isinstance(n,unreal.MaterialExpressionSubstrateToonBSDF))
    # Read the actual surviving inputs rather than rebuilding the working graph.
    inputs=ME.get_inputs_for_material_expression(mat,toon)
    names=ME.get_material_expression_input_names(toon)
    original={str(name):node for name,node in zip(names,inputs) if node}
    if 'BaseColor' not in original: raise RuntimeError('BaseColor input unavailable: '+str(names))
    params={}
    for i,(name,(default,low,high)) in enumerate(PARAMS.items()):
        node=ME.create_material_expression(mat,unreal.MaterialExpressionScalarParameter,3200,i*90)
        node.set_editor_properties({'parameter_name':name,'default_value':default,
            'slider_min':low,'slider_max':high,'group':'Film Print and Watercolour'})
        params[name]=node
    for name,color in [('FilmInkTint',(0.16,0.12,0.22,1)),('FilmPaperTint',(0.88,0.86,0.79,1))]:
        node=ME.create_material_expression(mat,unreal.MaterialExpressionVectorParameter,3200,1600)
        node.set_editor_properties({'parameter_name':name,'default_value':unreal.LinearColor(*color),
                                    'group':'Film Print and Watercolour'})
        params[name]=node
    custom=ME.create_material_expression(mat,unreal.MaterialExpressionCustom,3700,0)
    custom.set_editor_properties({'code':(ROOT/'Python/film304_print_surface.hlsl').read_text(),
        'description':'Film304 print and pigment surface',
        'output_type':unreal.CustomMaterialOutputType.CMOT_FLOAT3})
    custom_names=['BaseColor','UV','ShadowDriver','InkTint','PaperTint']+list(INPUTS)
    custom_inputs=[]
    for name in custom_names:
        item=unreal.CustomInput(); item.set_editor_property('input_name',name)
        custom_inputs.append(item)
    custom.set_editor_property('inputs',custom_inputs)
    connect(original['BaseColor'],custom,'BaseColor')
    uv=ME.create_material_expression(mat,unreal.MaterialExpressionTextureCoordinate,3200,-200)
    connect(uv,custom,'UV')
    # Reuse the source's ramp driver for an artist-directed shadow print gate.
    driver=nodes.get('MaterialExpressionDotProduct_0')
    if not driver:
        driver=ME.create_material_expression(mat,unreal.MaterialExpressionConstant,3200,-400)
        driver.set_editor_property('r',0.5)
    connect(driver,custom,'ShadowDriver')
    connect(params['FilmInkTint'],custom,'InkTint'); connect(params['FilmPaperTint'],custom,'PaperTint')
    for input_name,param in INPUTS.items(): connect(params[param],custom,input_name)
    connect(custom,toon,'BaseColor')
    # Runtime clamps on existing normalized material controls. Metadata sliders
    # are only an authoring aid; the graph enforces these bounds for all instances.
    clamped=[]
    for node in expressions:
        if not isinstance(node,unreal.MaterialExpressionScalarParameter): continue
        name=str(node.get_editor_property('parameter_name'))
        if name not in ['Roughness','Metallic','TextureWeight','OpacityStrength','LayerA_TextureWeight','LayerB_TextureWeight','LayerC_TextureWeight']: continue
        clamp=ME.create_material_expression(mat,unreal.MaterialExpressionClamp,2800,2000+len(clamped)*100)
        clamp.set_editor_properties({'min_default':0.0,'max_default':1.0})
        # Find current consumers BEFORE attaching the clamp, preserving exact pins.
        for target in expressions:
            target_inputs=ME.get_inputs_for_material_expression(mat,target)
            target_names=ME.get_material_expression_input_names(target)
            for target_name,source in zip(target_names,target_inputs):
                if source==node: connect(clamp,target,str(target_name))
        connect(node,clamp,''); clamped.append(name)
    # A true smooth substrate branch shares the processed color/normal/roughness.
    slab=ME.create_material_expression(mat,unreal.MaterialExpressionSubstrateSlabBSDF,4200,600)
    slab_names=[str(n) for n in ME.get_material_expression_input_names(slab)]
    def slab_pin(*choices):
        for choice in choices:
            if choice in slab_names: return choice
        raise RuntimeError('Slab input not found: '+str(choices)+' available='+str(slab_names))
    connect(custom,slab,slab_pin('Diffuse Albedo','DiffuseAlbedo','Diffuse Albedo (V3)'))
    for name in ['Roughness','Normal','EmissiveColor']:
        if name in original:
            candidates={'Roughness':['Roughness'],'Normal':['Normal'],
                'EmissiveColor':['Emissive Color','EmissiveColor']}[name]
            connect(original[name],slab,slab_pin(*candidates))
    selector=ME.create_material_expression(mat,unreal.MaterialExpressionStaticSwitchParameter,4600,0)
    selector.set_editor_properties({'parameter_name':'bFilmSmoothShading','default_value':False,'group':'Film Look'})
    connect(slab,selector,'True'); connect(toon,selector,'False')
    assert ME.connect_material_property(selector,'',unreal.MaterialProperty.MP_FRONT_MATERIAL)
    gate_optional_film_print(mat)
    finish_physical_inputs(mat)
    ME.recompile_material(mat)
    assert EAL.save_loaded_asset(mat,only_if_is_dirty=False)
    report={'candidate':DEST,'clamped_controls':clamped,'slab_inputs':slab_names,
            'status':'graph_authored_pending_compile_and_variant_instances'}
    (AUDIT/'film_look_build.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__': main()
