"""Repair scene assignments without touching the recovered shared toon graph."""
import json
from pathlib import Path
import unreal

def main():
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_path_name()=='/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office.L_Film_Office'
    assert not unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).is_rendering()
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    tools=unreal.AssetToolsHelpers.get_asset_tools()
    lib=unreal.MaterialEditingLibrary
    dest='/Game/Materials/Recovery_Office_20261018'
    master=unreal.load_asset(dest+'/M_WindowGlass_Restored')
    if master is None:
        source=unreal.load_asset('/Game/Recovery/VerifiedOriginals_20261018/M_Master_Toon_Glass')
        assert source and source.get_editor_property('blend_mode')==unreal.BlendMode.BLEND_TRANSLUCENT
        master=tools.duplicate_asset('M_WindowGlass_Restored',dest,source)
        expressions=list(lib.get_material_expressions(master))
        toon=next(x for x in expressions if isinstance(x,unreal.MaterialExpressionSubstrateToonBSDF))
        opacity=next(x for x in expressions if x.get_name()=='MaterialExpressionLinearInterpolate_3')
        weight=lib.create_material_expression(master,unreal.MaterialExpressionSubstrateWeight,850,200)
        assert lib.connect_material_expressions(toon,'',weight,'A')
        assert lib.connect_material_expressions(opacity,'',weight,'Weight')
        assert lib.connect_material_property(weight,'',unreal.MaterialProperty.MP_FRONT_MATERIAL)
        master.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT_COLORED_TRANSMITTANCE)
        lib.recompile_material(master)
        assert unreal.EditorAssetLibrary.save_loaded_asset(master)
    glass=unreal.load_asset(dest+'/MI_WindowGlass_Restored')
    if glass is None:
        glass=tools.duplicate_asset('MI_WindowGlass_Restored',dest,unreal.load_asset('/Game/Materials/Instances/MI_Toon_Glass'))
    lib.set_material_instance_parent(glass,master)
    assert unreal.EditorAssetLibrary.save_loaded_asset(glass)
    changes=[]
    for actor in actors:
        if 'Glass_WindowBay' in actor.get_actor_label():
            c=actor.get_component_by_class(unreal.StaticMeshComponent)
            changes.append({'actor':actor.get_actor_label(),'before':[m.get_path_name() if m else None for m in c.get_materials()],'after':glass.get_path_name()})
            c.set_material(0,glass)
    dana=next(a for a in actors if a.get_actor_label()=='Film_Subject_Dana_v08_CleanSkin')
    comp=dana.get_component_by_class(unreal.SkeletalMeshComponent)
    before=[m.get_path_name() if m else None for m in comp.get_materials()]
    root='/Game/Materials/Instances/Film304/Cast/Dana/'
    slot_paths=[root+'Closeout20261018/MI_Dana_Skin_Toon_UDIMCorrect_v01']+[root+'MI_Film304_Dana_'+p+'_Toon' for p in ['Hair','Iris','EyeWhite']]+['/Game/Materials/Instances/DanaFilm/MI_DanaFilm_Cornea']+[root+'MI_Film304_Dana_'+p+'_Toon' for p in ['EyeInterior','Cloth','Shirt','Shoes','Mouth','Teeth','Mouth']]
    mesh=comp.get_editor_property('skeletal_mesh_asset')
    assert len(comp.get_materials())==12
    for i,path in enumerate(slot_paths):
        material=unreal.load_asset(path)
        assert material,path
        comp.set_material(i,material)
    changes.append({'actor':dana.get_actor_label(),'slot_names':[str(m.material_slot_name) for m in mesh.get_editor_property('materials')],'before':before,'after':[m.get_path_name() for m in comp.get_materials()]})
    mobility=[]
    for actor in actors:
        c=actor.get_component_by_class(unreal.LightComponent)
        if c and c.get_editor_property('mobility')!=unreal.ComponentMobility.MOVABLE:
            mobility.append({'actor':actor.get_actor_label(),'before':str(c.get_editor_property('mobility'))})
            c.set_mobility(unreal.ComponentMobility.MOVABLE)
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    report={'world':world.get_path_name(),'assignment_changes':changes,'dynamic_preview_text_fix':mobility,'glass_restore':'Archived original plus its existing disconnected opacity curve restored through the SubstrateWeight path already specified by build_master_toon_glass.py. Only the isolated recovery copy was edited.','shared_toon_graphs_changed':False}
    (Path(unreal.Paths.project_dir())/'Saved/Audit/Closeout_20261018/shot_material_recovery.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report))

if __name__=='__main__':main()
