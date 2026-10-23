"""Create explicit film look instances; no actor or existing instance changes."""
import json
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
PARENT='/Game/Materials/Masters/Film304/M_UniversalToon_Film304_v04'
FOLDER='/Game/Materials/Instances/Film304'
PRESETS={
 'Toon':{'scalars':{},'switches':{}},
 'Smooth':{'scalars':{'Roughness':0.5},'switches':{'bFilmSmoothShading':True}},
 'Watercolour':{'scalars':{'FilmWatercolourStrength':1,'FilmGranulation':0.65,
        'FilmPooling':2,'FilmPaperScale':96,'FilmPaperLift':0.2,'Roughness':0.85},'switches':{}},
 'Gouache':{'scalars':{'FilmWatercolourStrength':0.7,'FilmGranulation':0.85,
        'FilmPooling':0.5,'FilmPaperLift':0.05,'FilmPaperScale':72,
        'ImpastoCoverage':0.7,'ImpastoRoughness':0.7,'Roughness':0.9},
        'switches':{'bImpasto_Active':True}},
 'Halftone':{'scalars':{'FilmHalftoneStrength':0.65,'FilmPrintFrequency':48,
        'FilmPrintCoverage':0.4,'FilmPrintRotation':22.5},'switches':{}},
 'OrderedDither':{'scalars':{'FilmDitherStrength':1,'FilmDitherMode':0,
        'FilmDitherBands':6,'FilmPrintFrequency':96},'switches':{}},
 'NoiseDither':{'scalars':{'FilmDitherStrength':0.7,'FilmDitherMode':1,
        'FilmDitherBands':8,'FilmPrintFrequency':96,'FilmPrintSeed':17},'switches':{}}}

def main():
    if unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).is_rendering():
        raise RuntimeError('Render active: deferred')
    me=unreal.MaterialEditingLibrary; eal=unreal.EditorAssetLibrary
    assert hasattr(me,'set_material_instance_static_switch_parameter_value')
    parent=unreal.load_asset(PARENT); assert parent
    eal.make_directory(FOLDER)
    results=[]
    for label,preset in PRESETS.items():
        name='MI_Film304_'+label
        path=FOLDER+'/'+name
        if eal.does_asset_exist(path): raise RuntimeError('Existing preset preserved: '+path)
        instance=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,FOLDER,
            unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
        assert instance
        me.set_material_instance_parent(instance,parent)
        for key,value in {'TextureWeight':0,'BoilIntensity':0,'SmearStrength':0,'TemporalStrength':0,
                          'Iridescence':0,**preset['scalars']}.items():
            me.set_material_instance_scalar_parameter_value(instance,key,value)
        for key,value in {'bFilmSmoothShading':False,'bImpasto_Active':False,
                          'bFilmPrintActive':label not in ['Toon','Smooth'],
                          'bClothWind_Active':False,**preset['switches']}.items():
            me.set_material_instance_static_switch_parameter_value(instance,key,value)
        me.update_material_instance(instance)
        assert eal.save_loaded_asset(instance,only_if_is_dirty=False)
        readback=unreal.load_asset(path)
        assert readback.get_editor_property('parent')==parent
        for key,value in preset['scalars'].items():
            assert abs(me.get_material_instance_scalar_parameter_value(readback,key)-value)<0.0001
        for key,value in preset['switches'].items():
            assert me.get_material_instance_static_switch_parameter_value(readback,key)==value
        results.append({'look':label,'instance':path,'overrides':preset,'saved_readback':True})
    report={'parent':PARENT,'looks':results,'scene_changed':False,
        'proof':'instances authored and saved overrides read back; compile permutations and visual judgment pending'}
    (ROOT/'Saved/Audit/EveningExecution_20261017/film_instance_shelf.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
